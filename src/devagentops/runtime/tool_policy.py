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
    if behavior == {"rules": [BASELINE_TOOL_POLICY]}:
        return "single_sequential"
    if behavior == {"rules": [BATCH_PARALLEL_TOOL_POLICY]}:
        return "batch_parallel"
    return None
