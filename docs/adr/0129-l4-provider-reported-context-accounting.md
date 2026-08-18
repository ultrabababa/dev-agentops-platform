# ADR 0129 — L4 Provider-Reported Context Accounting

Status: Accepted — Human amendment on 2026-08-18

## Context

ADR 0128 originally required an exact local input-token preflight before every L4 Model Decision. The implementation therefore reconstructed the MiniMax-M3 server prompt locally with a pinned chat template and tokenizer before sending each request.

That requirement proved to be unnecessary on the L4 critical execution path and introduced provider-specific coupling that can interfere with normal Agent recovery. In particular, a provider may return a syntactically valid assistant ToolCall whose `function.arguments` string is malformed JSON. ADR 0128 correctly classifies that Model action as recoverable: Runtime preserves the AssistantMessage, appends an error ToolResult, and allows the next Model Decision. A mandatory local renderer can fail on that provider-origin history before the provider itself is even called.

The primary L4 objective is to evaluate the Agent loop and its evidence-acquisition behavior, not to reproduce the provider's internal request tokenization pipeline. Mature Agent runtimes generally treat provider-reported usage as the authoritative observation for completed requests and add context management only when real trajectories justify it.

## Decision

For L4 V1:

1. The Runtime **does not perform mandatory local exact-token preflight before a Model Decision**.
2. A logical completion request is sent directly through the provider-request execution layer after the normal Runtime step-budget check.
3. Provider-returned usage is authoritative for observed request accounting. In particular, `AssistantMessage.usage.input_tokens` is the source for per-step observed input-token counts.
4. Trace records provider usage for every successful Model Decision. The L4 sample result records provider-reported per-step input tokens and identifies the accounting method as `provider_response_usage`.
5. The configured model context-window metadata remains part of Treatment context identity, but L4 V1 does not block a request solely on a locally reconstructed token count.
6. L4 V1 still performs no compaction, summarization, trimming, or automatic context compression. A real provider context-limit rejection is surfaced as provider/execution evidence and can motivate a later context-management ADR.
7. The pinned MiniMax tokenizer/chat-template assets and `count_input_tokens()` remain available where already needed by L1/L2/Oracle and for offline qualification or diagnostics. They are not part of the L4 Agent critical path.
8. Malformed ToolCall recovery remains unchanged: preserve the provider-origin AssistantMessage and raw arguments, append an Agent-visible error ToolResult, then allow the next Model Decision without Runtime repair or history rewriting.

## Treatment and identity

L4 Matrix context identity uses:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

The model's advertised context-window capability remains recorded. L4 does not include local tokenizer/chat-template assets in this Treatment context identity because they do not affect L4 execution behavior.

This does not change the existing retry identity boundary: provider-request retry remains execution/request policy, not Treatment behavior.

## Consequences

Positive:

- malformed provider-origin ToolCalls can follow the frozen self-repair path instead of being terminated by local preflight machinery;
- the Runtime is less coupled to MiniMax-internal prompt serialization;
- the observed token numbers come from the provider that actually processed the request;
- L4 baseline complexity stays focused on the Agent loop, tools, trajectory, policy, and evaluation semantics.

Trade-offs:

- L4 no longer rejects a request locally just before it would exceed the advertised context window;
- context-limit failures, if they occur, are observed from the provider rather than prevented by a local exact replica;
- provider usage may be absent on a malformed/failed provider response, so per-step observed input-token entries may be `null` when the provider does not report usage.

These trade-offs are accepted for V1. Context compaction or predictive budgeting should be designed only from qualification/formal-run evidence.

## Supersession

This ADR supersedes only the **mandatory L4 local exact-preflight** requirements in:

- ADR 0128, section `Exact token accounting`;
- `docs/evaluation/l4-self-built-react-runtime-design.md`, the corresponding exact-token-preflight section and pseudocode step.

All other ADR 0128 semantics remain frozen, including typed messages, full provider-origin trajectory replay, ToolCall recovery, retry semantics, `max_steps=100`, Tool Registry/Policy identity, Trace/trajectory separation, and no-compaction V1 behavior.

## Verification requirements

Deterministic L4 tests must prove that:

- `CompletionProvider.count_input_tokens()` is not called by `run_react()`;
- provider-reported `usage.input_tokens` is recorded per successful Model Decision;
- malformed raw ToolCall arguments remain recoverable and can reach the next provider call;
- Trace still records provider usage without persisting full reasoning/report bodies;
- L1/L2/Oracle token-accounting behavior is unchanged.
