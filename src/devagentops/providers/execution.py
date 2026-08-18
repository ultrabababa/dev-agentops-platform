from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from devagentops.providers.contracts import (
    CompletionProvider,
    CompletionProviderError,
    LogicalCompletionRequest,
)
from devagentops.runtime.messages import AssistantMessage


@dataclass(frozen=True)
class CompletionRequestRetryPolicy:
    ordinary_backoffs: tuple[float, ...] = ()
    timeout_backoffs: tuple[float, ...] = ()


@dataclass(frozen=True)
class CompletionRequestAttempt:
    attempt_index: int
    latency_ms: int
    assistant: AssistantMessage | None
    error: CompletionProviderError | None


@dataclass(frozen=True)
class CompletionRequestExecution:
    assistant: AssistantMessage
    latency_ms: int
    attempts: int


class ProviderRequestFailed(RuntimeError):
    def __init__(
        self,
        *,
        attempts: int,
        last_error: CompletionProviderError,
    ) -> None:
        super().__init__(str(last_error))
        self.attempts = attempts
        self.last_error = last_error
        self.code = last_error.code
        self.http_status = last_error.http_status


def execute_completion_request(
    provider: CompletionProvider,
    request: LogicalCompletionRequest,
    *,
    retry_policy: CompletionRequestRetryPolicy = CompletionRequestRetryPolicy(),
    before_attempt: Callable[[int], None] | None = None,
    after_attempt: Callable[[CompletionRequestAttempt], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> CompletionRequestExecution:
    """Execute retries without mutating the provider-neutral logical request."""
    attempt_index = 0
    while True:
        if before_attempt is not None:
            before_attempt(attempt_index)
        started = monotonic()
        try:
            assistant = provider.complete(request)
            if not isinstance(assistant, AssistantMessage):
                raise CompletionProviderError(
                    "completion provider returned an invalid response type",
                    code="model_provider_protocol_error",
                    retry_disposition="nonretryable",
                )
        except CompletionProviderError as error:
            latency_ms = round((monotonic() - started) * 1000)
            if after_attempt is not None:
                after_attempt(
                    CompletionRequestAttempt(
                        attempt_index=attempt_index,
                        latency_ms=latency_ms,
                        assistant=None,
                        error=error,
                    )
                )
            backoffs = (
                retry_policy.ordinary_backoffs
                if error.retry_disposition == "ordinary"
                else retry_policy.timeout_backoffs
                if error.retry_disposition == "timeout"
                else ()
            )
            if attempt_index >= len(backoffs):
                raise ProviderRequestFailed(
                    attempts=attempt_index + 1,
                    last_error=error,
                ) from error
            sleep(backoffs[attempt_index])
            attempt_index += 1
            continue

        latency_ms = round((monotonic() - started) * 1000)
        if after_attempt is not None:
            after_attempt(
                CompletionRequestAttempt(
                    attempt_index=attempt_index,
                    latency_ms=latency_ms,
                    assistant=assistant,
                    error=None,
                )
            )
        return CompletionRequestExecution(
            assistant=assistant,
            latency_ms=latency_ms,
            attempts=attempt_index + 1,
        )
