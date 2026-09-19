from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from devagentops.runtime.messages import (
    AssistantMessage,
    Message,
    ToolDefinition,
)


@dataclass(frozen=True)
class LogicalCompletionRequest:
    """Runtime 与具体 Provider adapter 之间的逻辑请求合同。

    Runtime 用 provider-neutral typed messages/tools 描述一次调用；adapter 再把它们
    转成 wire payload。``system_prompt`` 与 message history 分离，reasoning/generation
    保留 Treatment 原值，避免控制循环理解 MiniMax 等 provider 私有字段。
    """
    model: str
    messages: tuple[Message, ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    system_prompt: str | None = None
    tools: tuple[ToolDefinition, ...] = ()


@dataclass(frozen=True)
class ExactTokenCount:
    input_tokens: int
    method: str


RetryDisposition = Literal["ordinary", "timeout", "nonretryable"]


class CompletionProviderError(RuntimeError):
    """尚未产生有效 AssistantMessage 的 provider-neutral 失败。

    ``retry_disposition`` 是确定性请求重试层的输入；错误本身不是 Model Decision，
    不进入 trajectory 或消耗 Agent step。HTTP/status 映射由具体 adapter/transport 给出。
    """

    def __init__(
        self,
        message: str,
        *,
        code: str,
        retry_disposition: RetryDisposition,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retry_disposition = retry_disposition
        self.http_status = http_status


class CompletionProvider(Protocol):
    """不同 provider 需实现的最小同步接口。

    ``complete`` 要么返回标准化 AssistantMessage，要么抛 typed error。L1/L2/L3/Oracle
    可调用 ``count_input_tokens`` 做本地 preflight；ADR 0129 后的 L4 critical path 不调用它。
    """
    def count_input_tokens(
        self, request: LogicalCompletionRequest
    ) -> ExactTokenCount: ...

    def complete(
        self, request: LogicalCompletionRequest
    ) -> AssistantMessage: ...
