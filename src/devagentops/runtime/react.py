from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Literal

from devagentops.evaluation.evidence_reference_resolution import (
    canonicalize_evidence_references,
)
from devagentops.providers.contracts import CompletionProvider, LogicalCompletionRequest
from devagentops.providers.execution import (
    CompletionRequestAttempt,
    CompletionRequestRetryPolicy,
    ProviderRequestFailed,
    execute_completion_request,
)
from devagentops.runtime.messages import (
    AssistantMessage,
    Message,
    ToolCall,
    ToolDefinition,
    ToolResultMessage,
    UserMessage,
    assistant_text,
    tool_calls,
)
from devagentops.runtime.tool_policy import ToolPolicyMode, evaluate_baseline_policy
from devagentops.runtime.tools import TOOL_DEFINITIONS, ExpectedToolError, execute_tool
from devagentops.runtime.tools._common import bound_tool_result_text
from devagentops.runtime.workspace import RuntimeCaseWorkspace
from devagentops.scoring.report import analyze_candidate_report


MAX_STEPS = 100
ORDINARY_RETRY_BACKOFF_SECONDS = (2.0, 4.0, 8.0)
TIMEOUT_RETRY_BACKOFF_SECONDS = (2.0,)

TerminalReason = Literal[
    "report_submitted",
    "model_stopped_without_valid_report",
    "max_steps_exhausted",
]
RuntimeEventCallback = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class ReactConfiguration:
    model: str
    system_prompt: str
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    context_limit_tokens: int
    max_completion_tokens: int
    tools: tuple[ToolDefinition, ...] = TOOL_DEFINITIONS
    max_steps: int = MAX_STEPS
    resolve_evidence_references: bool = False
    tool_policy_mode: ToolPolicyMode = "single_sequential"


@dataclass(frozen=True)
class ReactRuntimeResult:
    terminal_reason: TerminalReason
    candidate_document: Any
    visible_output: str | None
    messages: tuple[Message, ...]
    steps: int
    request_attempts: int
    provider_input_tokens: tuple[int | None, ...]
    final_assistant: AssistantMessage | None
    final_latency_ms: int | None
    model_candidate_document: Any = None


@dataclass(frozen=True)
class _ToolCallOutcome:
    message: ToolResultMessage
    event_type: Literal["tool_call_completed", "tool_call_error"]
    payload: dict[str, Any]


class ReactInfrastructureError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        stage: str,
        messages: tuple[Message, ...],
        steps: int,
        request_attempts: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.messages = messages
        self.steps = steps
        self.request_attempts = request_attempts


def serialize_initial_runtime_input(workspace: RuntimeCaseWorkspace) -> str:
    """Serialize only public metadata, virtual workspace, and citation coordinates."""
    document = {
        "runtime_input_serialization_version": "l4_tool_workspace_runtime_input_v1",
        "case": {
            "case_id": workspace.case.case_id,
            "case_schema_version": workspace.case.case_schema_version,
            "case_fingerprint": workspace.case.case_fingerprint,
            "forbidden_actions": list(workspace.case.forbidden_actions),
        },
        "agent_visible_workspace": {
            "root": "/",
            "raw_log": "/raw.log",
            "repository": "/repository/",
            "content_access": (
                "Physical artifact contents are not included in this message. "
                "Acquire them only through read, grep, find, and ls."
            ),
        },
        "canonical_evidence_coordinate_vocabulary": [
            coordinate.as_dict() for coordinate in workspace.canonical_coordinates
        ],
    }
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_initial_user_message(
    workspace: RuntimeCaseWorkspace,
    *,
    task_contract_template: str,
    output_contract_suffix: str,
) -> UserMessage:
    runtime_input = serialize_initial_runtime_input(workspace)
    try:
        content = task_contract_template.format(runtime_input=runtime_input)
    except (KeyError, ValueError) as exc:
        raise ReactInfrastructureError(
            "L4 Task Contract could not be rendered",
            code="l4_prompt_render_failed",
            stage="l4_execution",
            messages=(),
            steps=0,
            request_attempts=0,
        ) from exc
    return UserMessage(content=content + output_contract_suffix)


def run_react(
    *,
    workspace: RuntimeCaseWorkspace,
    provider: CompletionProvider,
    configuration: ReactConfiguration,
    initial_user_message: UserMessage,
    on_event: RuntimeEventCallback | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> ReactRuntimeResult:
    messages: tuple[Message, ...] = (initial_user_message,)
    provider_input_tokens: list[int | None] = []
    steps = 0
    request_attempts = 0
    final_assistant: AssistantMessage | None = None
    final_latency_ms: int | None = None

    while True:
        if steps >= configuration.max_steps:
            _emit(
                on_event,
                "budget_exhausted",
                {"steps": steps, "max_steps": configuration.max_steps},
            )
            _emit(
                on_event,
                "agent_terminal",
                {"terminal_reason": "max_steps_exhausted", "steps": steps},
            )
            return ReactRuntimeResult(
                terminal_reason="max_steps_exhausted",
                candidate_document=None,
                visible_output=None,
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
                provider_input_tokens=tuple(provider_input_tokens),
                final_assistant=final_assistant,
                final_latency_ms=final_latency_ms,
            )

        request = LogicalCompletionRequest(
            model=configuration.model,
            system_prompt=configuration.system_prompt,
            messages=messages,
            tools=configuration.tools,
            reasoning=configuration.reasoning,
            generation=configuration.generation,
        )

        try:
            execution = execute_completion_request(
                provider,
                request,
                retry_policy=CompletionRequestRetryPolicy(
                    ordinary_backoffs=ORDINARY_RETRY_BACKOFF_SECONDS,
                    timeout_backoffs=TIMEOUT_RETRY_BACKOFF_SECONDS,
                ),
                before_attempt=lambda attempt_index: _emit(
                    on_event,
                    "model_call_started",
                    {"step": steps + 1, "attempt_index": attempt_index},
                ),
                after_attempt=lambda attempt: _record_model_attempt(
                    on_event,
                    step=steps + 1,
                    attempt=attempt,
                ),
                sleep=sleep,
            )
        except ProviderRequestFailed as exc:
            request_attempts += exc.attempts
            raise ReactInfrastructureError(
                "L4 provider request failed after same-request retry policy",
                code="provider_request_failed",
                stage="model_provider",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            ) from exc

        assistant = execution.assistant
        request_attempts += execution.attempts
        steps += 1
        provider_input_tokens.append(assistant.usage.input_tokens)
        final_assistant = assistant
        final_latency_ms = execution.latency_ms
        messages = (*messages, assistant)
        calls = tool_calls(assistant)

        if not calls:
            visible_output = assistant_text(assistant)
            try:
                model_candidate_document: Any = json.loads(visible_output)
            except json.JSONDecodeError:
                model_candidate_document = visible_output
            candidate_document = (
                canonicalize_evidence_references(
                    model_candidate_document,
                    workspace.canonical_coordinates,
                )
                if configuration.resolve_evidence_references
                else model_candidate_document
            )
            analysis = analyze_candidate_report(
                candidate_document,
                case_id=workspace.case.case_id,
                evidence_ids=tuple(
                    coordinate.evidence_id
                    for coordinate in workspace.canonical_coordinates
                ),
            )
            terminal_reason: TerminalReason = (
                "report_submitted"
                if analysis.validation.valid
                else "model_stopped_without_valid_report"
            )
            if terminal_reason == "report_submitted":
                _emit(
                    on_event,
                    "report_submitted",
                    {"steps": steps, "response_id": assistant.response_id},
                )
            _emit(
                on_event,
                "agent_terminal",
                {"terminal_reason": terminal_reason, "steps": steps},
            )
            return ReactRuntimeResult(
                terminal_reason=terminal_reason,
                candidate_document=candidate_document,
                visible_output=visible_output,
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
                provider_input_tokens=tuple(provider_input_tokens),
                final_assistant=assistant,
                final_latency_ms=execution.latency_ms,
                model_candidate_document=model_candidate_document,
            )

        if assistant.stop_reason == "length":
            error = (
                "ToolCalls returned with stop_reason=length are truncated; "
                "none were executed"
            )
            messages = _append_error_results(messages, calls, error)
            for call in calls:
                _emit(
                    on_event,
                    "tool_call_error",
                    {
                        "step": steps,
                        "tool_call_id": call.id,
                        "tool_name": call.name,
                        "code": "truncated_tool_call",
                    },
                )
            continue

        if configuration.tool_policy_mode == "batch_parallel":
            messages = _execute_parallel_tool_batch(
                workspace=workspace,
                messages=messages,
                calls=calls,
                step=steps,
                request_attempts=request_attempts,
                on_event=on_event,
            )
            continue

        if configuration.tool_policy_mode != "single_sequential":
            raise ReactInfrastructureError(
                "L4 Runtime received an unsupported Tool Policy mode",
                code="invalid_l4_tool_policy",
                stage="l4_execution",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            )

        policy = evaluate_baseline_policy(calls)
        if not policy.accepted:
            assert policy.error is not None
            messages = _append_error_results(messages, calls, policy.error)
            for call in calls:
                _emit(
                    on_event,
                    "tool_call_error",
                    {
                        "step": steps,
                        "tool_call_id": call.id,
                        "tool_name": call.name,
                        "code": "multiple_tool_calls_rejected",
                    },
                )
            continue

        call = calls[0]
        if call.arguments is None:
            result_message = _malformed_tool_arguments_result(call)
            messages = (*messages, result_message)
            _emit(
                on_event,
                "tool_call_error",
                {
                    "step": steps,
                    "tool_call_id": call.id,
                    "tool_name": call.name,
                    "code": "malformed_tool_arguments",
                },
            )
            continue

        _emit(
            on_event,
            "tool_call_started",
            {"step": steps, "tool_call_id": call.id, "tool_name": call.name},
        )
        try:
            result = execute_tool(workspace, call.name, call.arguments)
        except ExpectedToolError as exc:
            error_content, content_truncated = bound_tool_result_text(
                f"{exc.code}: {exc}"
            )
            messages = (
                *messages,
                ToolResultMessage(
                    tool_call_id=call.id,
                    tool_name=call.name,
                    content=error_content,
                    is_error=True,
                ),
            )
            _emit(
                on_event,
                "tool_call_error",
                {
                    "step": steps,
                    "tool_call_id": call.id,
                    "tool_name": call.name,
                    "code": exc.code,
                    "truncated": content_truncated,
                },
            )
            continue
        except Exception as exc:
            raise ReactInfrastructureError(
                "unexpected L4 tool or workspace implementation failure",
                code="tool_execution_failed",
                stage="tool_execution",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            ) from exc

        messages = (
            *messages,
            ToolResultMessage(
                tool_call_id=call.id,
                tool_name=call.name,
                content=result.content,
                is_error=False,
            ),
        )
        _emit(
            on_event,
            "tool_call_completed",
            {
                "step": steps,
                "tool_call_id": call.id,
                "tool_name": call.name,
                "truncated": result.truncated,
                "result_metadata": result.metadata,
            },
        )


def _execute_parallel_tool_batch(
    *,
    workspace: RuntimeCaseWorkspace,
    messages: tuple[Message, ...],
    calls: tuple[ToolCall, ...],
    step: int,
    request_attempts: int,
    on_event: RuntimeEventCallback | None,
) -> tuple[Message, ...]:
    outcomes: list[_ToolCallOutcome | None] = [None] * len(calls)
    runnable: list[tuple[int, ToolCall]] = []

    for index, call in enumerate(calls):
        if call.arguments is None:
            outcomes[index] = _ToolCallOutcome(
                message=_malformed_tool_arguments_result(call),
                event_type="tool_call_error",
                payload={
                    "step": step,
                    "tool_call_id": call.id,
                    "tool_name": call.name,
                    "code": "malformed_tool_arguments",
                },
            )
        else:
            runnable.append((index, call))

    for _, call in runnable:
        _emit(
            on_event,
            "tool_call_started",
            {"step": step, "tool_call_id": call.id, "tool_name": call.name},
        )

    unexpected: list[tuple[ToolCall, Exception]] = []
    if runnable:
        with ThreadPoolExecutor(
            max_workers=len(runnable),
            thread_name_prefix="l4-tool",
        ) as pool:
            futures = [
                pool.submit(_execute_one_tool_call, workspace, call, step)
                for _, call in runnable
            ]
            for (index, call), future in zip(runnable, futures, strict=True):
                try:
                    outcomes[index] = future.result()
                except Exception as exc:  # infrastructure failure, never Agent-visible
                    unexpected.append((call, exc))

    if unexpected:
        first_call, exc = unexpected[0]
        raise ReactInfrastructureError(
            "unexpected L4 tool or workspace implementation failure "
            f"during parallel ToolCall {first_call.id}",
            code="tool_execution_failed",
            stage="tool_execution",
            messages=messages,
            steps=step,
            request_attempts=request_attempts,
        ) from exc

    assert all(outcome is not None for outcome in outcomes)
    ordered_outcomes = tuple(outcome for outcome in outcomes if outcome is not None)
    messages = (*messages, *(outcome.message for outcome in ordered_outcomes))
    for outcome in ordered_outcomes:
        _emit(on_event, outcome.event_type, outcome.payload)
    return messages


def _execute_one_tool_call(
    workspace: RuntimeCaseWorkspace,
    call: ToolCall,
    step: int,
) -> _ToolCallOutcome:
    assert call.arguments is not None
    try:
        result = execute_tool(workspace, call.name, call.arguments)
    except ExpectedToolError as exc:
        error_content, content_truncated = bound_tool_result_text(
            f"{exc.code}: {exc}"
        )
        return _ToolCallOutcome(
            message=ToolResultMessage(
                tool_call_id=call.id,
                tool_name=call.name,
                content=error_content,
                is_error=True,
            ),
            event_type="tool_call_error",
            payload={
                "step": step,
                "tool_call_id": call.id,
                "tool_name": call.name,
                "code": exc.code,
                "truncated": content_truncated,
            },
        )

    return _ToolCallOutcome(
        message=ToolResultMessage(
            tool_call_id=call.id,
            tool_name=call.name,
            content=result.content,
            is_error=False,
        ),
        event_type="tool_call_completed",
        payload={
            "step": step,
            "tool_call_id": call.id,
            "tool_name": call.name,
            "truncated": result.truncated,
            "result_metadata": result.metadata,
        },
    )


def _malformed_tool_arguments_result(call: ToolCall) -> ToolResultMessage:
    return ToolResultMessage(
        tool_call_id=call.id,
        tool_name=call.name,
        content=(
            "malformed tool arguments: arguments must be one strict JSON object; "
            "the Runtime did not repair the provider-emitted representation"
        ),
        is_error=True,
    )


def _record_model_attempt(
    on_event: RuntimeEventCallback | None,
    *,
    step: int,
    attempt: CompletionRequestAttempt,
) -> None:
    if attempt.error is not None:
        _emit(
            on_event,
            "model_call_failed",
            {
                "step": step,
                "attempt_index": attempt.attempt_index,
                "code": attempt.error.code,
                "http_status": attempt.error.http_status,
                "latency_ms": attempt.latency_ms,
            },
        )
        return
    assert attempt.assistant is not None
    assistant = attempt.assistant
    _emit(
        on_event,
        "model_call_completed",
        {
            "step": step,
            "attempt_index": attempt.attempt_index,
            "response_id": assistant.response_id,
            "returned_model": assistant.response_model,
            "usage": assistant.usage.as_dict(),
            "latency_ms": attempt.latency_ms,
            "stop_reason": assistant.stop_reason,
            "raw_stop_reason": assistant.raw_stop_reason,
        },
    )


def _append_error_results(
    messages: tuple[Message, ...],
    calls,
    error: str,
) -> tuple[Message, ...]:
    return (
        *messages,
        *(
            ToolResultMessage(
                tool_call_id=call.id,
                tool_name=call.name,
                content=error,
                is_error=True,
            )
            for call in calls
        ),
    )


def _emit(
    callback: RuntimeEventCallback | None,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    if callback is not None:
        callback(event_type, payload)
