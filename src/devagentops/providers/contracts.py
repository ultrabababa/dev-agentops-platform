from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LogicalCompletionRequest:
    model: str
    messages: tuple[dict[str, str], ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    tools: None = None


@dataclass(frozen=True)
class CompletionObservation:
    visible_output: str
    reasoning_output: str | None
    provider_request_id: str | None
    returned_model: str | None
    usage: dict[str, Any]
    finish_reason: str | None
    latency_ms: int


@dataclass(frozen=True)
class ExactTokenCount:
    input_tokens: int
    method: str


class CompletionProvider(Protocol):
    def count_input_tokens(
        self, request: LogicalCompletionRequest
    ) -> ExactTokenCount: ...

    def complete(
        self, request: LogicalCompletionRequest
    ) -> CompletionObservation: ...
