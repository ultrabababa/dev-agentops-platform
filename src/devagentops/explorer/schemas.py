from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PublicDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TokenUsageDTO(PublicDTO):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ToolCallDTO(PublicDTO):
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] | None = None


class TrajectoryMessageDTO(PublicDTO):
    message_index: int
    role: Literal["user", "assistant", "tool_result"]
    visible_content: str | None = None
    tool_calls: list[ToolCallDTO] = Field(default_factory=list)
    tool_name: str | None = None
    tool_call_id: str | None = None
    is_error: bool | None = None
    stop_reason: str | None = None
    raw_stop_reason: str | None = None
    response_model: str | None = None
    usage: TokenUsageDTO | None = None


class TrajectoryResponseDTO(PublicDTO):
    run_id: str
    case_id: str
    repeat_index: int
    messages: list[TrajectoryMessageDTO]


class TraceEventDTO(PublicDTO):
    sequence: int
    event_type: str
    occurred_at: str
    payload: dict[str, Any]


class TraceResponseDTO(PublicDTO):
    run_id: str
    case_id: str
    repeat_index: int
    events: list[TraceEventDTO]
