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
    """一次 L4 Runtime 执行所需的冻结配置。

    Harness/Condition adapter 负责从 Matrix 与 Component Registry 组装这些字段；
    Runtime 只消费已经解析好的 model、System Prompt、ToolDefinition 与 Tool Policy。
    ``context_limit_tokens`` 和 ``max_completion_tokens`` 随 Treatment 记录到下游结果，
    但当前控制循环并不读取它们做本地 token preflight；实际输入 token 取 provider
    usage，completion 上限则已包含在 ``generation`` 的 provider 请求配置中。
    """
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
    """把控制循环终态、完整内存轨迹和 provider 观测返回 Condition adapter。

    ``candidate_document`` 是可选 Evidence Mapping 后交给 Evaluator 的版本；
    ``model_candidate_document`` 保留模型原始 JSON 解析结果，用于区分模型输出与
    确定性引用规范化的影响。Runtime 本身不读取 Ground Truth，也不计算得分。
    """
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
    """序列化首轮模型可见输入：公开 Case 信息、虚拟工作区与引用坐标。

    这里不嵌入 ``/raw.log`` 或仓库正文，模型必须通过工具获取物理证据；完整
    Canonical coordinate vocabulary 只提供答案中可用的引用坐标，不包含哪些 ID
    是 Required/Optional。该字段边界防止正常输入泄露 evaluator Ground Truth，
    但它是应用层数据投影，不构成 OS 级文件权限隔离。
    """
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
    """用冻结 Task Contract 渲染首条 UserMessage，并追加 Output Contract。

    Task Contract 负责面向 Case 的任务说明；L4 的 System Prompt 由调用方通过
    ``ReactConfiguration.system_prompt`` 独立传入。模板变量不匹配属于 Runtime
    配置/组件错误，在首次模型请求前转成 ``ReactInfrastructureError``。
    """
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
    """控制 L4 的 Model Decision → Tool observation → 下一决策循环。

    ``messages`` 是权威会话状态：初始 UserMessage、每次成功返回的完整
    AssistantMessage，以及按策略产生的 ToolResultMessage 都以不可变 tuple 追加，
    下一次请求会重放全部历史。失败的 provider attempt 不产生 AssistantMessage，
    所以只进入 Trace，不进入 trajectory，也不消耗 ``max_steps``。

    模型决定是否提出 ToolCall 以及最终报告文本；Runtime 确定性控制 allowlist、
    参数校验、Tool Policy、执行、请求重试、step budget 和终止。函数有 provider
    请求、工具读取、等待重试与事件回调副作用；可恢复动作错误写成 ToolResult 后
    继续，不可恢复的 provider/tool 基础设施错误抛 ``ReactInfrastructureError``。
    """
    messages: tuple[Message, ...] = (initial_user_message,)
    provider_input_tokens: list[int | None] = []
    steps = 0
    request_attempts = 0
    final_assistant: AssistantMessage | None = None
    final_latency_ms: int | None = None

    while True:
        # budget 在发起下一次逻辑请求前检查：第 100 个成功 Model Decision 可以完成，
        # 也可以执行工具；若它仍未提交报告，则工具结果会保留，但不会出现第 101 次请求。
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
            # 重试层反复发送同一个 request 对象，不插入模型可见错误消息。因此 request
            # retry 是基础设施恢复，不是新的 Agent 决策，也不是重跑整个 sample。
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
            # “没有 ToolCall”是提交最终报告的唯一信号；submit_report 不是伪装的工具。
            # JSON 解析失败时保留原始字符串，交给 validator 形成可评分的协议失败。
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
            # provider 明确表示输出被截断时，任何随响应到达的 ToolCall 都可能不完整；
            # 因而全部拒绝并逐个回写 error ToolResult，避免执行半截参数。
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
            # 历史 single policy 对同轮多个调用采用 reject-all，不能只挑第一个执行，
            # 否则模型本次决策的语义会被 Runtime 暗中改写。
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
            # Provider adapter 保存 raw_arguments，却不修复非法 JSON。错误结果连同原始
            # AssistantMessage 留在 history，使模型下一轮可以自行纠正。
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
    """并发执行同一 Model Decision 中可运行的 ToolCalls，并按原顺序提交结果。

    malformed arguments 先成为独立错误 outcome；其余调用以一个
    ``ThreadPoolExecutor`` 并发执行。每个 future 都会在 barrier 内收集，outcomes
    以原 ToolCall index 落位，故完成先后不会改变下一轮模型看到的 ToolResult 顺序。

    工具只读同一个不可变 workspace，没有 Runtime 共享可变状态；重复调用不会去重。
    ``ExpectedToolError`` 只影响对应调用。任何意外异常会等兄弟 future 结束后让整个
    sample 失败，并且不把已完成的部分结果加入 history，避免模型看到半个 batch。
    """
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
                # zip 使用提交顺序而非完成顺序；future.result() 可能等待较慢的前序调用，
                # 但所有任务已经提交并发执行，因此这只固定 materialization 顺序。
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
    """把一次工具调用归一化为成功或 Agent 可见的预期错误 outcome。

    未知工具、schema/path/limit 等 ``ExpectedToolError`` 不抛出到 batch；真正的
    实现异常原样逸出，由 batch barrier 升级为 sample 级基础设施失败。
    """
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
    """把一次 provider attempt 的元数据写入 Trace，不复制完整消息正文。

    完整 AssistantMessage 由 ``messages`` trajectory 保存；Trace 只记录重试索引、
    usage、latency、response ID 与错误分类，支持区分 provider 故障和 Agent 决策。
    """
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
