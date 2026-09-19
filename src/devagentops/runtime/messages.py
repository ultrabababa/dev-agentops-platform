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
    """Provider-neutral 工具动作，同时保留严格解析值和 provider 原始表示。

    ``arguments=None`` 表示 provider 确实返回了一个 ToolCall，但 arguments 不是
    严格 JSON object；它仍是一次有效 Model Decision，由 Runtime 回写可恢复错误。
    ``raw_arguments`` 用于后续 provider continuation replay，不供工具直接执行。
    """
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
    """Provider adapter 归一化后的单次 Model Decision。

    content 保留 text、provider 暴露的 thinking 与 ToolCall 的原始顺序；Runtime
    只解释 ToolCall/可见文本，不解释 ``provider_fields``。后者由同一 adapter 在
    下一轮序列化时重放，以维持 provider 特有的多轮 continuation contract。
    """
    content: tuple[AssistantContent, ...]
    response_id: str | None
    response_model: str | None
    usage: TokenUsage
    stop_reason: Literal["stop", "length", "tool_use"]
    raw_stop_reason: str | None
    provider_fields: dict[str, JsonValue] = field(default_factory=dict)


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
    """拼接模型可见文本块，不把 thinking 或 ToolCall 误当成最终报告内容。"""
    return "".join(
        block.text for block in message.content if isinstance(block, TextContent)
    )


def assistant_thinking(message: AssistantMessage) -> str | None:
    """提取 provider 暴露的 thinking，仅用于 trajectory/诊断，不参与评分。"""
    thinking = "".join(
        block.thinking
        for block in message.content
        if isinstance(block, ThinkingContent)
    )
    return thinking or None


def tool_calls(message: AssistantMessage) -> tuple[ToolCall, ...]:
    """按 provider content 顺序提取 ToolCalls，供 Tool Policy 确定性调度。"""
    return tuple(
        block for block in message.content if isinstance(block, ToolCall)
    )


def message_to_dict(message: Message) -> dict[str, JsonValue]:
    """生成 sample trajectory 的稳定 provider-neutral 持久化表示。

    该表示保留完整对话内容、ToolCall raw arguments、usage 与 continuation fields；
    它不同于只记录生命周期元数据的 Trace，也不是重新发给 provider 的 wire schema。
    """
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
    }
