from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


class OpenAICompatibleTransportError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


class OpenAICompatibleChatCompletionsTransport:
    """One-attempt OpenAI-compatible `/chat/completions` HTTP transport."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
    ) -> None:
        if not api_key:
            raise OpenAICompatibleTransportError(
                "MINIMAX_API_KEY is not configured",
                code="model_provider_credentials_missing",
            )
        self._endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def complete(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint,
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
                request,
                timeout=self._timeout_seconds,
            ) as response:
                raw_response = response.read()
        except urllib.error.HTTPError as exc:
            code = (
                "model_provider_rate_limited"
                if exc.code == 429
                else "model_provider_http_error"
            )
            raise OpenAICompatibleTransportError(
                f"OpenAI-compatible request failed with HTTP {exc.code}",
                code=code,
                http_status=exc.code,
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible request failed before a completion was returned",
                code="model_provider_transport_error",
            ) from exc
        latency_ms = round((time.monotonic() - started) * 1000)
        try:
            document = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible provider returned an invalid JSON response envelope",
                code="model_provider_protocol_error",
            ) from exc
        if not isinstance(document, dict):
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible provider returned an invalid response envelope",
                code="model_provider_protocol_error",
            )
        return document, latency_ms
