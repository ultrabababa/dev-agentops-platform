from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"


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

    def count_input_tokens(self, request: ModelRequest) -> TokenCount:
        # UTF-8 bytes are a conservative upper bound for byte-backed tokenizers.
        # Counting the full canonical provider payload includes message framing and
        # structured-output schema overhead; it intentionally may reject early.
        canonical_request = json.dumps(
            request.provider_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return TokenCount(
            input_tokens=len(canonical_request),
            method="qwen3_5_canonical_request_utf8_upper_bound_v1",
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
