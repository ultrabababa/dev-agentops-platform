from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tokenizers import Tokenizer


SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
QWEN3_5_4B_TOKENIZER_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
QWEN3_5_4B_TOKENIZER_SHA256 = (
    "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42"
)
QWEN3_5_4B_TOKEN_COUNT_METHOD = (
    "qwen3_5_4b_official_tokenizer_chat_template_v1"
)
QWEN3_5_4B_TOKENIZER_PATH = (
    Path(__file__).parent.parent / "assets" / "qwen3_5_4b_tokenizer.json"
)


class ModelProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "model_provider_failed",
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class TokenCount:
    input_tokens: int
    method: str


@dataclass(frozen=True)
class ModelRequest:
    model: str
    messages: tuple[dict[str, str], ...]
    response_format: dict[str, Any]
    enable_thinking: bool
    temperature: int
    max_tokens: int
    completions: int
    stream: bool
    tools: None = None

    def provider_payload(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": list(self.messages),
            "response_format": self.response_format,
            "enable_thinking": self.enable_thinking,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "n": self.completions,
            "stream": self.stream,
        }


@dataclass(frozen=True)
class ModelResponse:
    visible_output: str
    provider_request_id: str | None
    returned_model: str | None
    usage: dict[str, Any]
    finish_reason: str | None
    latency_ms: int


class ModelProvider(Protocol):
    def count_input_tokens(self, request: ModelRequest) -> TokenCount: ...

    def complete(self, request: ModelRequest) -> ModelResponse: ...


class SiliconFlowProvider:
    """One-call OpenAI-compatible SiliconFlow adapter with no retry layer."""

    def __init__(self, *, api_key: str, timeout_seconds: float = 60.0) -> None:
        if not api_key:
            raise ModelProviderError(
                "SILICONFLOW_API_KEY is not configured",
                code="model_provider_credentials_missing",
            )
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._tokenizer: Tokenizer | None = None

    def count_input_tokens(self, request: ModelRequest) -> TokenCount:
        rendered_input = _render_qwen3_5_l1_chat_input(request)
        if self._tokenizer is None:
            try:
                with QWEN3_5_4B_TOKENIZER_PATH.open("rb") as tokenizer_file:
                    tokenizer_sha256 = hashlib.file_digest(
                        tokenizer_file,
                        "sha256",
                    ).hexdigest()
                if tokenizer_sha256 != QWEN3_5_4B_TOKENIZER_SHA256:
                    raise ValueError("tokenizer asset fingerprint changed")
                self._tokenizer = Tokenizer.from_file(
                    str(QWEN3_5_4B_TOKENIZER_PATH)
                )
            except Exception as exc:
                raise ModelProviderError(
                    "Qwen3.5-4B tokenizer asset could not be loaded",
                    code="model_tokenizer_unavailable",
                ) from exc
        return TokenCount(
            input_tokens=len(
                self._tokenizer.encode(
                    rendered_input,
                    add_special_tokens=False,
                ).ids
            ),
            method=QWEN3_5_4B_TOKEN_COUNT_METHOD,
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        body = json.dumps(request.provider_payload(), ensure_ascii=False).encode(
            "utf-8"
        )
        provider_request = urllib.request.Request(
            SILICONFLOW_BASE_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(
                provider_request,
                timeout=self._timeout_seconds,
            ) as response:
                raw_response = response.read()
        except urllib.error.HTTPError as exc:
            code = (
                "model_provider_rate_limited"
                if exc.code == 429
                else "model_provider_http_error"
            )
            raise ModelProviderError(
                f"SiliconFlow request failed with HTTP {exc.code}",
                code=code,
                http_status=exc.code,
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ModelProviderError(
                "SiliconFlow request failed before a completion was returned",
                code="model_provider_transport_error",
            ) from exc
        latency_ms = round((time.monotonic() - started) * 1000)
        try:
            document = json.loads(raw_response)
            choice = document["choices"][0]
            visible_output = choice["message"]["content"]
            if not isinstance(visible_output, str):
                raise TypeError("completion content is not a string")
            usage = document.get("usage", {})
            if not isinstance(usage, dict):
                raise TypeError("usage is not an object")
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError(
                "SiliconFlow returned an invalid completion protocol response",
                code="model_provider_protocol_error",
            ) from exc
        return ModelResponse(
            visible_output=visible_output,
            provider_request_id=document.get("id"),
            returned_model=document.get("model"),
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            latency_ms=latency_ms,
        )


def create_model_provider() -> ModelProvider:
    return SiliconFlowProvider(api_key=os.environ.get("SILICONFLOW_API_KEY", ""))


def _render_qwen3_5_l1_chat_input(request: ModelRequest) -> str:
    if request.model != "Qwen/Qwen3.5-4B":
        raise ModelProviderError(
            "token counting supports only Qwen/Qwen3.5-4B",
            code="unsupported_tokenizer_model",
        )
    if (
        len(request.messages) != 1
        or request.messages[0].get("role") != "user"
        or not isinstance(request.messages[0].get("content"), str)
        or request.tools is not None
        or request.enable_thinking is not False
    ):
        raise ModelProviderError(
            "Qwen3.5-4B L1 token counting requires one non-thinking user message without tools",
            code="unsupported_tokenizer_request_shape",
        )
    content = request.messages[0]["content"].strip()
    # Exact text-only branch of the pinned Qwen3.5-4B chat template for the
    # Human-frozen L1 request shape, with add_generation_prompt=True. SiliconFlow
    # private structured-output injection is not client-observable and is not
    # guessed or encoded here.
    return (
        f"<|im_start|>user\n{content}<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
