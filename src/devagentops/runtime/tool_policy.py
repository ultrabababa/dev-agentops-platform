from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence


class ToolCallLike(Protocol):
    id: str
    name: str


ToolPolicyMode = Literal["single_sequential", "batch_parallel"]


@dataclass(frozen=True)
class ToolPolicyDecision:
    accepted: bool
    error: str | None = None


BASELINE_TOOL_POLICY = {
    "scope": "model_decision",
    "call_mode": "single",
    "execution_mode": "sequential",
    "multiple_calls": "reject_all_with_error_results",
}

BATCH_PARALLEL_TOOL_POLICY = {
    "scope": "model_decision",
    "call_mode": "batch",
    "execution_mode": "parallel",
    "multiple_calls": "accept_independently",
}


def evaluate_baseline_policy(
    calls: Sequence[ToolCallLike],
) -> ToolPolicyDecision:
    """实现历史 single/sequential policy 的 Model Decision 级检查。

    零或一个调用可继续；多个调用整体拒绝，由循环为每个原始 call ID 生成错误
    ToolResult。这里不检查工具名称或参数，那些由 Tool Registry/execute_tool 负责。
    """
    if len(calls) <= 1:
        return ToolPolicyDecision(accepted=True)
    return ToolPolicyDecision(
        accepted=False,
        error=(
            "tool policy allows one ToolCall per Model Decision; all calls in "
            "this decision were rejected and none executed"
        ),
    )


def tool_policy_mode(behavior: dict[str, object]) -> ToolPolicyMode | None:
    """把冻结 Component behavior 精确映射为 Runtime 分支，不接受近似配置。

    精确相等防止 Registry 声明与实际调度语义漂移；未知 behavior 返回 None，
    Condition adapter 会在首次模型调用前将其视为配置错误。
    """
    if behavior == {"rules": [BASELINE_TOOL_POLICY]}:
        return "single_sequential"
    if behavior == {"rules": [BATCH_PARALLEL_TOOL_POLICY]}:
        return "batch_parallel"
    return None
