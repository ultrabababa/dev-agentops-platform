# Use an OpenAI-Compatible LLM Provider Boundary

## Status

Accepted.

## Decision

V1 defines a small provider-neutral LLM completion interface while allowing concrete provider adapters to use OpenAI-compatible Chat Completions transports where appropriate. This provides portability without making provider wire JSON part of Agent Runtime semantics.

The common Runtime contract must remain provider-neutral. Provider-specific request/response serialization, continuation metadata, error interpretation, and tool-call wire formats belong inside the provider adapter.

## Current L4 Refinement

ADR 0128 freezes the first L4 route as:

```text
DevAgentOps ReAct Runtime
    -> MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

This does **not** create a generic `OpenAICompatibleProvider` abstraction and does not make OpenAI wire dictionaries the Runtime message contract. L4 uses typed provider-neutral messages; `MiniMaxProvider` owns MiniMax-specific `tool_calls`, reasoning continuation, `base_resp`, and serialization.

The shared transport remains reusable HTTP plumbing. A future provider/API change should replace or add an adapter rather than force the ReAct Runtime to understand a new wire protocol.

Exact token counting for L4 must use the same model-visible MiniMax serialization path as actual completion requests so context preflight and real requests cannot drift.

## Consequences

- Existing qualified MiniMax-M3 Chat Completions behavior is preserved while L4 adds native tool calling.
- Runtime code does not depend on MiniMax/OpenAI message JSON.
- Future Anthropic-style or other provider adapters can reuse the Runtime contract without redesigning the Agent loop.
- V1 avoids premature multi-provider framework work.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
