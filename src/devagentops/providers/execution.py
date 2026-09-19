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
    """执行一个逻辑请求及其同请求重试，不修改模型可见上下文。

    每次 attempt 调用同一 ``provider.complete(request)``；before/after callbacks 用于
    Trace，latency 为单次 attempt 耗时。根据错误类别选择 ordinary/timeout backoff 表，
    但两者共用累计 ``attempt_index``，切换错误类别不会重新计数；仅当累计索引小于
    当前类别的 backoff 表长度时才允许再次尝试。nonretryable 不等待、直接失败。

    成功返回最终 AssistantMessage、最后一次 attempt latency 和总 attempts。耗尽后抛
    ``ProviderRequestFailed`` 并保留最后 typed error；函数不会把失败写成 ToolResult、
    不会重放 sample，也不会进行隐藏 SDK retry。
    """
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
            # attempt_index 只标记同一逻辑请求的基础设施尝试；成功 AssistantMessage
            # 尚未存在，因此 Agent step 和 trajectory 都由上层保持不变。
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
