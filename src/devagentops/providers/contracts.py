from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from devagentops.runtime.messages import (
    AssistantMessage,
    Message,
    ToolDefinition,
)


@dataclass(frozen=True)
class LogicalCompletionRequest:
    model: str
    messages: tuple[Message, ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    system_prompt: str | None = None
    tools: tuple[ToolDefinition, ...] = ()


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
    ) -> AssistantMessage: ...
