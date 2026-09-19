from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from devagentops.providers.contracts import CompletionProviderError


class OpenAICompatibleTransportError(CompletionProviderError):
    """把 HTTP/网络错误归类为 Runtime retry layer 可理解的 disposition。"""
    def __init__(
        self,
        message: str,
        *,
        code: str,
        http_status: int | None = None,
    ) -> None:
        retry_disposition = (
            "timeout"
            if code == "model_provider_timeout"
            else "ordinary"
            if code in {
                "model_provider_transport_error",
                "model_provider_rate_limited",
            }
            or (
                code == "model_provider_http_error"
                and http_status is not None
                and http_status >= 500
            )
            else "nonretryable"
        )
        super().__init__(
            message,
            code=code,
            retry_disposition=retry_disposition,
            http_status=http_status,
        )


class OpenAICompatibleChatCompletionsTransport:
    """执行一次 OpenAI-compatible ``/chat/completions`` HTTP/JSON 传输。

    timeout 来自 Matrix Execution Policy，经 Harness/provider factory 传入单次 HTTP
    request。Transport 不重试；429、5xx、timeout 与其他网络/协议错误只做 typed
    classification，是否重试由 ``execute_completion_request`` 决定。
    """

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

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        """发送一个 JSON payload 并返回未解释的 response object。

        此层只验证外层 JSON 是 object；choices、ToolCall、usage 与 provider status
        均由 MiniMaxProvider 解析，从而使通用 HTTP 层不承担模型协议语义。
        """
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
        except (TimeoutError, socket.timeout) as exc:
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible request timed out before a completion was returned",
                code="model_provider_timeout",
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise OpenAICompatibleTransportError(
                    "OpenAI-compatible request timed out before a completion was returned",
                    code="model_provider_timeout",
                ) from exc
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible request failed before a completion was returned",
                code="model_provider_transport_error",
            ) from exc
        except OSError as exc:
            raise OpenAICompatibleTransportError(
                "OpenAI-compatible request failed before a completion was returned",
                code="model_provider_transport_error",
            ) from exc
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
        return document
