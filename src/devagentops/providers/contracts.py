from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

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


RetryDisposition = Literal["ordinary", "timeout", "nonretryable"]


class CompletionProviderError(RuntimeError):
    """Provider-neutral failure before a valid AssistantMessage exists."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        retry_disposition: RetryDisposition,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retry_disposition = retry_disposition
        self.http_status = http_status


class CompletionProvider(Protocol):
    def count_input_tokens(
        self, request: LogicalCompletionRequest
    ) -> ExactTokenCount: ...

    def complete(
        self, request: LogicalCompletionRequest
    ) -> AssistantMessage: ...
