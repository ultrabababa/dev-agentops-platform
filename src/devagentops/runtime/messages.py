from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias


JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


@dataclass(frozen=True)
class TextContent:
    text: str


@dataclass(frozen=True)
class ThinkingContent:
    thinking: str


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, JsonValue] | None
    raw_arguments: str | None


AssistantContent: TypeAlias = TextContent | ThinkingContent | ToolCall


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_fields: dict[str, JsonValue] = field(default_factory=dict)

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "provider_fields": self.provider_fields,
        }


@dataclass(frozen=True)
class UserMessage:
    content: str


@dataclass(frozen=True)
class AssistantMessage:
    content: tuple[AssistantContent, ...]
    response_id: str | None
    response_model: str | None
    usage: TokenUsage
    stop_reason: Literal["stop", "length", "tool_use"]
    raw_stop_reason: str | None
    provider_fields: dict[str, JsonValue] = field(default_factory=dict)
    latency_ms: int = 0


@dataclass(frozen=True)
class ToolResultMessage:
    tool_call_id: str
    tool_name: str
    content: str
    is_error: bool


Message: TypeAlias = UserMessage | AssistantMessage | ToolResultMessage


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, JsonValue]


def assistant_text(message: AssistantMessage) -> str:
    """Return visible assistant text without provider-specific interpretation."""
    return "".join(
        block.text for block in message.content if isinstance(block, TextContent)
    )


def assistant_thinking(message: AssistantMessage) -> str | None:
    """Return provider-exposed thinking for diagnostic metadata only."""
    thinking = "".join(
        block.thinking
        for block in message.content
        if isinstance(block, ThinkingContent)
    )
    return thinking or None


def tool_calls(message: AssistantMessage) -> tuple[ToolCall, ...]:
    return tuple(
        block for block in message.content if isinstance(block, ToolCall)
    )


def message_to_dict(message: Message) -> dict[str, JsonValue]:
    """Return the stable provider-neutral representation persisted per sample."""
    if isinstance(message, UserMessage):
        return {"role": "user", "content": message.content}
    if isinstance(message, ToolResultMessage):
        return {
            "role": "tool_result",
            "tool_call_id": message.tool_call_id,
            "tool_name": message.tool_name,
            "content": message.content,
            "is_error": message.is_error,
        }
    content: list[JsonValue] = []
    for block in message.content:
        if isinstance(block, TextContent):
            content.append({"type": "text", "text": block.text})
        elif isinstance(block, ThinkingContent):
            content.append({"type": "thinking", "thinking": block.thinking})
        else:
            content.append(
                {
                    "type": "tool_call",
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.arguments,
                    "raw_arguments": block.raw_arguments,
                }
            )
    return {
        "role": "assistant",
        "content": content,
        "response_id": message.response_id,
        "response_model": message.response_model,
        "usage": message.usage.as_dict(),
        "stop_reason": message.stop_reason,
        "raw_stop_reason": message.raw_stop_reason,
        "provider_fields": message.provider_fields,
        "latency_ms": message.latency_ms,
    }
