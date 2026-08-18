from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

from devagentops.providers.contracts import (
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.runtime.messages import (
    AssistantContent,
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
    ToolCall,
    ToolDefinition,
    ToolResultMessage,
    UserMessage,
    assistant_text,
    assistant_thinking,
)


MINIMAX_M3_TOKENIZER_REPOSITORY = "MiniMaxAI/MiniMax-M3"
MINIMAX_M3_TOKENIZER_REVISION = "f0e1c1e04d40177e4673a22097036854f536e9c0"
MINIMAX_M3_TOKENIZER_SHA256 = (
    "bb1f1626cf01448f1e3b6036d0a061ffc66c91d9046aada14ea23a5441b5ad6e"
)
MINIMAX_M3_CHAT_TEMPLATE_SHA256 = (
    "11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64"
)
MINIMAX_M3_TOKEN_COUNT_METHOD = "minimax_m3_official_chat_template_adaptive_v1"
MINIMAX_M3_TOKENIZER_PATH = (
    Path(__file__).parent.parent / "assets" / "minimax_m3_tokenizer.json"
)
MINIMAX_M3_CHAT_TEMPLATE_PATH = (
    Path(__file__).parent.parent / "assets" / "minimax_m3_chat_template.jinja"
)
from devagentops.providers.openai_compatible import (
    OpenAICompatibleChatCompletionsTransport,
    OpenAICompatibleTransportError,
)


class ChatCompletionsTransport(Protocol):
    def complete(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]: ...


@dataclass(frozen=True)
class _SerializedMiniMaxRequest:
    payload: dict[str, Any]
    messages: tuple[dict[str, Any], ...]
    template_messages: tuple[dict[str, Any], ...]
    tools: tuple[dict[str, Any], ...]
    thinking_mode: str


class MiniMaxProvider:
    """MiniMax official API profile over an OpenAI-compatible transport."""

    def __init__(self, *, transport: ChatCompletionsTransport) -> None:
        self._transport = transport
        self._tokenizer: Tokenizer | None = None
        self._chat_template = None

    def count_input_tokens(
        self, request: LogicalCompletionRequest
    ) -> ExactTokenCount:
        serialized = self._serialize_request(request)
        if self._tokenizer is None or self._chat_template is None:
            try:
                _verify_asset(
                    MINIMAX_M3_TOKENIZER_PATH,
                    MINIMAX_M3_TOKENIZER_SHA256,
                )
                _verify_asset(
                    MINIMAX_M3_CHAT_TEMPLATE_PATH,
                    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
                )
                self._tokenizer = Tokenizer.from_file(
                    str(MINIMAX_M3_TOKENIZER_PATH)
                )
                template_source = MINIMAX_M3_CHAT_TEMPLATE_PATH.read_text(
                    encoding="utf-8"
                )
                environment = ImmutableSandboxedEnvironment(
                    trim_blocks=True,
                    lstrip_blocks=True,
                    extensions=["jinja2.ext.loopcontrols"],
                )
                environment.globals["raise_exception"] = _raise_template_error
                environment.filters["tojson"] = _tojson_filter
                self._chat_template = environment.from_string(template_source)
            except Exception as exc:
                raise OpenAICompatibleTransportError(
                    "MiniMax-M3 tokenizer assets could not be loaded",
                    code="model_tokenizer_unavailable",
                ) from exc
        rendered = self._chat_template.render(
            messages=list(serialized.template_messages),
            tools=list(serialized.tools) or None,
            add_generation_prompt=True,
            thinking_mode=serialized.thinking_mode,
        )
        return ExactTokenCount(
            input_tokens=len(
                self._tokenizer.encode(rendered, add_special_tokens=False).ids
            ),
            method=MINIMAX_M3_TOKEN_COUNT_METHOD,
        )

    def complete(self, request: LogicalCompletionRequest) -> AssistantMessage:
        serialized = self._serialize_request(request)
        document, latency_ms = self._transport.complete(serialized.payload)
        _validate_provider_status(document)
        try:
            choice = document["choices"][0]
            if not isinstance(choice, dict):
                raise TypeError("completion choice is not an object")
            message = choice["message"]
            if not isinstance(message, dict):
                raise TypeError("completion message is not an object")
            content = _assistant_content(message)
            usage = _token_usage(document.get("usage", {}))
            raw_stop_reason = choice.get("finish_reason")
            if raw_stop_reason is not None and not isinstance(raw_stop_reason, str):
                raise TypeError("finish reason is not a string")
            stop_reason = _normalize_stop_reason(raw_stop_reason, content)
            response_id = _optional_string(document, "id")
            response_model = _optional_string(document, "model")
            provider_fields = {
                key: value
                for key, value in message.items()
                if key not in {"role", "content", "tool_calls"}
            }
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OpenAICompatibleTransportError(
                "MiniMax returned an invalid completion protocol response",
                code="model_provider_protocol_error",
            ) from exc
        return AssistantMessage(
            content=content,
            response_id=response_id,
            response_model=response_model,
            usage=usage,
            stop_reason=stop_reason,
            raw_stop_reason=raw_stop_reason,
            provider_fields=provider_fields,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _serialize_request(
        request: LogicalCompletionRequest,
    ) -> _SerializedMiniMaxRequest:
        expected_reasoning = {
            "thinking": {"type": "adaptive"},
            "reasoning_split": True,
        }
        expected_generation = {
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        }
        if (
            request.model != "MiniMax-M3"
            or request.reasoning != expected_reasoning
            or request.generation != expected_generation
        ):
            raise OpenAICompatibleTransportError(
                "request does not match the MiniMax-M3 development profile",
                code="unsupported_model_request",
            )
        messages = _serialize_messages(request)
        tools = tuple(_serialize_tool(tool) for tool in request.tools)
        generation = request.generation
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": list(messages),
            "thinking": request.reasoning["thinking"],
            "reasoning_split": request.reasoning["reasoning_split"],
            "temperature": generation["temperature"],
            "max_completion_tokens": generation["max_completion_tokens"],
            "n": generation["n"],
            "stream": generation["stream"],
        }
        if tools:
            payload["tools"] = list(tools)
        return _SerializedMiniMaxRequest(
            payload=payload,
            messages=messages,
            template_messages=_template_messages(messages),
            tools=tools,
            thinking_mode=request.reasoning["thinking"]["type"],
        )


def create_minimax_provider(
    *,
    base_url: str,
    timeout_seconds: float,
) -> MiniMaxProvider:
    return MiniMaxProvider(
        transport=OpenAICompatibleChatCompletionsTransport(
            base_url=base_url,
            api_key=os.environ.get("MINIMAX_API_KEY", ""),
            timeout_seconds=timeout_seconds,
        )
    )


def _reasoning_output(message: dict[str, Any]) -> str | None:
    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str):
        return reasoning_content
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return None
    text_parts = [
        item["text"]
        for item in details
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    return "".join(text_parts) or None


def _serialize_messages(
    request: LogicalCompletionRequest,
) -> tuple[dict[str, Any], ...]:
    messages: list[dict[str, Any]] = []
    if request.system_prompt is not None:
        messages.append({"role": "system", "content": request.system_prompt})
    for message in request.messages:
        if isinstance(message, UserMessage):
            messages.append({"role": "user", "content": message.content})
            continue
        if isinstance(message, ToolResultMessage):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "name": message.tool_name,
                    "content": message.content,
                }
            )
            continue
        if not isinstance(message, AssistantMessage):
            raise OpenAICompatibleTransportError(
                "request contains an unsupported typed message",
                code="unsupported_model_request",
            )
        wire_message: dict[str, Any] = dict(message.provider_fields)
        wire_message.update({
            "role": "assistant",
            "content": assistant_text(message) or None,
        })
        if (
            "reasoning_content" not in wire_message
            and (thinking := assistant_thinking(message)) is not None
        ):
            wire_message["reasoning_content"] = thinking
        calls = [block for block in message.content if isinstance(block, ToolCall)]
        if calls:
            wire_message["tool_calls"] = [_serialize_tool_call(call) for call in calls]
        messages.append(wire_message)
    return tuple(messages)


def _serialize_tool(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _serialize_tool_call(call: ToolCall) -> dict[str, Any]:
    raw_arguments = call.raw_arguments
    if raw_arguments is None and call.arguments is not None:
        raw_arguments = json.dumps(
            call.arguments,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    return {
        "id": call.id,
        "type": "function",
        "function": {
            "name": call.name,
            "arguments": raw_arguments if raw_arguments is not None else "",
        },
    }


def _template_messages(
    messages: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    """Adapt the shared wire serialization to the pinned template's input API."""
    rendered_messages: list[dict[str, Any]] = []
    for message in messages:
        rendered = dict(message)
        calls = message.get("tool_calls")
        if isinstance(calls, list):
            rendered_calls: list[dict[str, Any]] = []
            for call in calls:
                rendered_call = dict(call)
                function = dict(rendered_call["function"])
                raw_arguments = function["arguments"]
                try:
                    parsed = json.loads(
                        raw_arguments,
                        parse_constant=_reject_nonstandard_json_constant,
                    )
                except (json.JSONDecodeError, ValueError):
                    # The official template accepts structured arguments only.
                    # Preserve malformed wire state in the HTTP payload while
                    # rendering its non-repaired empty argument object locally.
                    parsed = {}
                function["arguments"] = parsed if isinstance(parsed, dict) else {}
                rendered_call["function"] = function
                rendered_calls.append(rendered_call)
            rendered["tool_calls"] = rendered_calls
        rendered_messages.append(rendered)
    return tuple(rendered_messages)


def _assistant_content(message: dict[str, Any]) -> tuple[AssistantContent, ...]:
    blocks: list[AssistantContent] = []
    reasoning = _reasoning_output(message)
    if reasoning is not None:
        blocks.append(ThinkingContent(reasoning))
    visible_output = message.get("content")
    if visible_output is not None:
        if not isinstance(visible_output, str):
            raise TypeError("completion content is not a string or null")
        if visible_output:
            blocks.append(TextContent(visible_output))
    raw_calls = message.get("tool_calls", [])
    if raw_calls is None:
        raw_calls = []
    if not isinstance(raw_calls, list):
        raise TypeError("tool_calls is not an array")
    blocks.extend(_parse_tool_call(raw_call) for raw_call in raw_calls)
    return tuple(blocks)


def _parse_tool_call(raw_call: Any) -> ToolCall:
    if not isinstance(raw_call, dict):
        raise TypeError("tool call is not an object")
    call_id = raw_call.get("id")
    function = raw_call.get("function")
    call_type = raw_call.get("type", "function")
    if (
        not isinstance(call_id, str)
        or not call_id
        or call_type != "function"
        or not isinstance(function, dict)
    ):
        raise TypeError("tool call identity is invalid")
    name = function.get("name")
    raw_arguments = function.get("arguments")
    if not isinstance(name, str) or not name or not isinstance(raw_arguments, str):
        raise TypeError("tool call function is invalid")
    try:
        parsed = json.loads(
            raw_arguments,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if not isinstance(parsed, dict):
        parsed = None
    return ToolCall(
        id=call_id,
        name=name,
        arguments=parsed,
        raw_arguments=raw_arguments,
    )


def _reject_nonstandard_json_constant(value: str) -> Any:
    raise ValueError(f"non-standard JSON constant: {value}")


def _normalize_stop_reason(
    raw_stop_reason: str | None,
    content: tuple[AssistantContent, ...],
) -> Literal["stop", "length", "tool_use"]:
    has_tool_call = any(isinstance(block, ToolCall) for block in content)
    if raw_stop_reason in {"tool_calls", "function_call", "tool_use"}:
        return "tool_use"
    if raw_stop_reason == "length":
        return "length"
    if raw_stop_reason in {"stop", None} and not has_tool_call:
        return "stop"
    if raw_stop_reason in {"stop", None} and has_tool_call:
        return "tool_use"
    raise ValueError(f"unsupported MiniMax finish reason: {raw_stop_reason!r}")


def _token_usage(raw_usage: Any) -> TokenUsage:
    if not isinstance(raw_usage, dict):
        raise TypeError("usage is not an object")
    input_tokens = _optional_nonnegative_int(raw_usage, "prompt_tokens")
    output_tokens = _optional_nonnegative_int(raw_usage, "completion_tokens")
    total_tokens = _optional_nonnegative_int(raw_usage, "total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    provider_fields = {
        key: value
        for key, value in raw_usage.items()
        if key not in {"prompt_tokens", "completion_tokens", "total_tokens"}
    }
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        provider_fields=provider_fields,
    )


def _optional_nonnegative_int(document: dict[str, Any], key: str) -> int | None:
    value = document.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError(f"{key} is not a non-negative integer")
    return value


def _optional_string(document: dict[str, Any], key: str) -> str | None:
    value = document.get(key)
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{key} is not a string")
    return value


def _validate_provider_status(document: dict[str, Any]) -> None:
    base_resp = document.get("base_resp")
    if base_resp is None:
        return
    if not isinstance(base_resp, dict):
        raise OpenAICompatibleTransportError(
            "MiniMax returned an invalid provider status object",
            code="model_provider_protocol_error",
        )
    status_code = base_resp.get("status_code")
    if not isinstance(status_code, int) or isinstance(status_code, bool):
        raise OpenAICompatibleTransportError(
            "MiniMax returned an invalid provider status code",
            code="model_provider_protocol_error",
        )
    if status_code != 0:
        raise OpenAICompatibleTransportError(
            f"MiniMax rejected the request with provider status {status_code}",
            code="model_provider_error",
        )


def _verify_asset(path: Path, expected_sha256: str) -> None:
    with path.open("rb") as asset_file:
        actual = hashlib.file_digest(asset_file, "sha256").hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"asset fingerprint changed: {path.name}")


def _raise_template_error(message: str) -> None:
    raise ValueError(message)


def _tojson_filter(value: Any, *, ensure_ascii: bool = True) -> str:
    """Match the pinned MiniMax template's Hugging Face `tojson` filter API."""
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        separators=(",", ":"),
        sort_keys=True,
    )
