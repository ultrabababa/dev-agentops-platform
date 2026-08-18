from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from devagentops.providers.contracts import (
    CompletionProvider,
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.providers.openai_compatible import OpenAICompatibleTransportError
from devagentops.runtime.messages import (
    AssistantMessage,
    Message,
    ToolResultMessage,
    UserMessage,
    ToolDefinition,
    assistant_text,
    tool_calls,
)
from devagentops.runtime.tool_policy import evaluate_baseline_policy
from devagentops.runtime.tools import TOOL_DEFINITIONS, ExpectedToolError, execute_tool
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


@dataclass(frozen=True)
class ReactRuntimeResult:
    terminal_reason: TerminalReason
    candidate_document: Any
    visible_output: str | None
    messages: tuple[Message, ...]
    steps: int
    request_attempts: int
    token_counts: tuple[ExactTokenCount, ...]
    final_assistant: AssistantMessage | None


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
    token_counts: list[ExactTokenCount] = []
    steps = 0
    request_attempts = 0
    final_assistant: AssistantMessage | None = None

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
                token_counts=tuple(token_counts),
                final_assistant=final_assistant,
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
            token_count = provider.count_input_tokens(request)
        except Exception as exc:
            raise ReactInfrastructureError(
                "L4 exact input-token preflight failed",
                code=getattr(exc, "code", "l4_token_preflight_failed"),
                stage="context_feasibility",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            ) from exc
        token_counts.append(token_count)
        if (
            token_count.input_tokens + configuration.max_completion_tokens
            > configuration.context_limit_tokens
        ):
            raise ReactInfrastructureError(
                "L4 request exceeds the configured model context capability",
                code="l4_context_infeasible",
                stage="context_feasibility",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            )

        try:
            assistant, attempts = _complete_with_retry(
                provider=provider,
                request=request,
                step=steps + 1,
                input_tokens=token_count.input_tokens,
                on_event=on_event,
                sleep=sleep,
            )
        except _ProviderRequestExhausted as exc:
            request_attempts += exc.attempts
            raise ReactInfrastructureError(
                "L4 provider request failed after same-request retry policy",
                code="provider_request_failed",
                stage="model_provider",
                messages=messages,
                steps=steps,
                request_attempts=request_attempts,
            ) from exc
        request_attempts += attempts
        steps += 1
        final_assistant = assistant
        messages = (*messages, assistant)
        calls = tool_calls(assistant)

        if not calls:
            visible_output = assistant_text(assistant)
            try:
                candidate_document: Any = json.loads(visible_output)
            except json.JSONDecodeError:
                candidate_document = visible_output
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
                token_counts=tuple(token_counts),
                final_assistant=assistant,
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
                    {"step": steps, "tool_call_id": call.id, "tool_name": call.name,
                     "code": "truncated_tool_call"},
                )
            continue

        policy = evaluate_baseline_policy(calls)
        if not policy.accepted:
            assert policy.error is not None
            messages = _append_error_results(messages, calls, policy.error)
            for call in calls:
                _emit(
                    on_event,
                    "tool_call_error",
                    {"step": steps, "tool_call_id": call.id, "tool_name": call.name,
                     "code": "multiple_tool_calls_rejected"},
                )
            continue

        call = calls[0]
        if call.arguments is None:
            result_message = ToolResultMessage(
                tool_call_id=call.id,
                tool_name=call.name,
                content=(
                    "malformed tool arguments: arguments must be one strict JSON object; "
                    "the Runtime did not repair the provider-emitted representation"
                ),
                is_error=True,
            )
            messages = (*messages, result_message)
            _emit(
                on_event,
                "tool_call_error",
                {"step": steps, "tool_call_id": call.id, "tool_name": call.name,
                 "code": "malformed_tool_arguments"},
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
            messages = (
                *messages,
                ToolResultMessage(
                    tool_call_id=call.id,
                    tool_name=call.name,
                    content=f"{exc.code}: {exc}",
                    is_error=True,
                ),
            )
            _emit(
                on_event,
                "tool_call_error",
                {"step": steps, "tool_call_id": call.id, "tool_name": call.name,
                 "code": exc.code},
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


@dataclass(frozen=True)
class _ProviderRequestExhausted(RuntimeError):
    attempts: int


def _complete_with_retry(
    *,
    provider: CompletionProvider,
    request: LogicalCompletionRequest,
    step: int,
    input_tokens: int,
    on_event: RuntimeEventCallback | None,
    sleep: Callable[[float], None],
) -> tuple[AssistantMessage, int]:
    attempt = 0
    while True:
        _emit(
            on_event,
            "model_call_started",
            {"step": step, "attempt_index": attempt, "input_tokens": input_tokens},
        )
        try:
            assistant = provider.complete(request)
        except OpenAICompatibleTransportError as exc:
            _emit(
                on_event,
                "model_call_failed",
                {"step": step, "attempt_index": attempt, "code": exc.code,
                 "http_status": exc.http_status},
            )
            backoffs = _retry_backoffs(exc)
            if attempt >= len(backoffs):
                raise _ProviderRequestExhausted(attempts=attempt + 1) from exc
            sleep(backoffs[attempt])
            attempt += 1
            continue
        if not isinstance(assistant, AssistantMessage):
            raise _ProviderRequestExhausted(attempts=attempt + 1)
        _emit(
            on_event,
            "model_call_completed",
            {
                "step": step,
                "attempt_index": attempt,
                "response_id": assistant.response_id,
                "returned_model": assistant.response_model,
                "usage": assistant.usage.as_dict(),
                "latency_ms": assistant.latency_ms,
                "stop_reason": assistant.stop_reason,
                "raw_stop_reason": assistant.raw_stop_reason,
            },
        )
        return assistant, attempt + 1


def _retry_backoffs(exc: OpenAICompatibleTransportError) -> tuple[float, ...]:
    if exc.code == "model_provider_timeout":
        return TIMEOUT_RETRY_BACKOFF_SECONDS
    if exc.code in {"model_provider_transport_error", "model_provider_rate_limited"}:
        return ORDINARY_RETRY_BACKOFF_SECONDS
    if exc.code == "model_provider_http_error" and (
        exc.http_status is not None and exc.http_status >= 500
    ):
        return ORDINARY_RETRY_BACKOFF_SECONDS
    return ()


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
