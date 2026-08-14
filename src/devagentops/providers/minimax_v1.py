from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Protocol

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

from devagentops.providers.contracts import (
    CompletionObservation,
    ExactTokenCount,
    LogicalCompletionRequest,
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


class MiniMaxProvider:
    """MiniMax official API profile over an OpenAI-compatible transport."""

    def __init__(self, *, transport: ChatCompletionsTransport) -> None:
        self._transport = transport
        self._tokenizer: Tokenizer | None = None
        self._chat_template = None

    def count_input_tokens(
        self, request: LogicalCompletionRequest
    ) -> ExactTokenCount:
        self._provider_payload(request)
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
                self._chat_template = environment.from_string(template_source)
            except Exception as exc:
                raise OpenAICompatibleTransportError(
                    "MiniMax-M3 tokenizer assets could not be loaded",
                    code="model_tokenizer_unavailable",
                ) from exc
        rendered = self._chat_template.render(
            messages=list(request.messages),
            tools=None,
            add_generation_prompt=True,
            thinking_mode="adaptive",
        )
        return ExactTokenCount(
            input_tokens=len(
                self._tokenizer.encode(rendered, add_special_tokens=False).ids
            ),
            method=MINIMAX_M3_TOKEN_COUNT_METHOD,
        )

    def complete(self, request: LogicalCompletionRequest) -> CompletionObservation:
        payload = self._provider_payload(request)
        document, latency_ms = self._transport.complete(payload)
        try:
            choice = document["choices"][0]
            message = choice["message"]
            visible_output = message["content"]
            if not isinstance(visible_output, str):
                raise TypeError("completion content is not a string")
            usage = document.get("usage", {})
            if not isinstance(usage, dict):
                raise TypeError("usage is not an object")
            reasoning_output = _reasoning_output(message)
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAICompatibleTransportError(
                "MiniMax returned an invalid completion protocol response",
                code="model_provider_protocol_error",
            ) from exc
        return CompletionObservation(
            visible_output=visible_output,
            reasoning_output=reasoning_output,
            provider_request_id=document.get("id"),
            returned_model=document.get("model"),
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            latency_ms=latency_ms,
        )

    @staticmethod
    def _provider_payload(request: LogicalCompletionRequest) -> dict[str, Any]:
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
            or request.tools is not None
        ):
            raise OpenAICompatibleTransportError(
                "request does not match the MiniMax-M3 development profile",
                code="unsupported_model_request",
            )
        generation = expected_generation
        return {
            "model": request.model,
            "messages": list(request.messages),
            "thinking": request.reasoning["thinking"],
            "reasoning_split": request.reasoning["reasoning_split"],
            "temperature": generation["temperature"],
            "max_completion_tokens": generation["max_completion_tokens"],
            "n": generation["n"],
            "stream": generation["stream"],
        }


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


def _verify_asset(path: Path, expected_sha256: str) -> None:
    with path.open("rb") as asset_file:
        actual = hashlib.file_digest(asset_file, "sha256").hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"asset fingerprint changed: {path.name}")


def _raise_template_error(message: str) -> None:
    raise ValueError(message)
