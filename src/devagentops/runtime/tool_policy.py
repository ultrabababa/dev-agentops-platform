from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class ToolCallLike(Protocol):
    id: str
    name: str


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
