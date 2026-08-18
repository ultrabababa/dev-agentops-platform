# L4 Self-built ReAct Runtime Contract

## Status

Accepted.

## Context

Issue #52 introduces `self_built_react`, the first Agentic Product Runtime in DevAgentOps. Earlier ADRs establish the lightweight self-built ReAct direction, the Runtime Capability Ladder, the bounded Investigation Workspace, Structured Triage Report V1, Component Registry, Trace, and formal evaluation seams. They do not freeze the concrete L4 loop semantics, provider-neutral message contract, read-only tool surface, policy behavior, budget semantics, trajectory persistence boundary, or MiniMax tool-calling integration.

L4 must remain small enough to expose the actual Agent Runtime kernel while being precise enough for deterministic fake-provider testing and one trustworthy formal comparison. Pi is used only as a reference architecture; no Pi package, API, or compatibility contract is adopted.

## Decision

### 1. Control model and scope

L4 uses an explicit adaptive loop:

```text
Model Decision
    -> Runtime validates Action
    -> optional Tool execution
    -> ToolResult observation
    -> authoritative message-state update
    -> next Model Decision or stop
```

The Model chooses the next action. The Runtime owns allowlisting, schema validation, policy enforcement, execution, budgets, trace, persistence, and forced termination.

V1 does not add planner, verifier, memory, multi-agent coordination, subagents, reflection loops, Bash, mutation tools, dynamic skills, MCP, automatic context compression, or OS-level sandbox complexity.

A Runtime action is either a `ToolAction` or terminal report submission. Report submission is semantic Runtime behavior, not a fake native tool.

### 2. Conversation state

The authoritative Agent trajectory is the complete ordered sequence of typed:

- `UserMessage`;
- `AssistantMessage`;
- `ToolResultMessage`.

Each successful model turn is preserved in full and the relevant history is resent on the next request. There is no separate memory, summary, observed-evidence ledger, or transcript abstraction in L4 V1.

The trajectory is distinct from Trace. Trace records lifecycle and execution observations; it is not the conversation store and does not duplicate complete message bodies.

### 3. Provider-neutral completion contract

`LogicalCompletionRequest` separates:

- `model`;
- `system_prompt`;
- typed `messages`;
- typed `tools`;
- `reasoning` configuration;
- `generation` configuration.

Successful `CompletionProvider.complete()` returns one provider-neutral `AssistantMessage` directly. The legacy `CompletionObservation` envelope is retired from the common contract.

`AssistantMessage.content` is an ordered sequence of:

- `TextContent`;
- `ThinkingContent`;
- `ToolCall`.

`AssistantMessage` also carries normalized token usage, `response_id`, `response_model`, normalized `stop_reason`, optional `raw_stop_reason`, and adapter-owned opaque `provider_fields` required for exact provider continuation. Runtime code must not interpret `provider_fields`.

Provider/transport failures that occur before a valid Model Decision are typed provider errors, not Assistant messages.

`ToolCall` preserves both strictly parsed arguments and the provider/model-emitted raw argument representation when available. Malformed argument JSON remains a real Model Decision; the Runtime does not semantically repair it.

### 4. MiniMax provider route

L4 V1 preserves the already-qualified provider route:

```text
DevAgentOps
  -> MiniMaxProvider
  -> OpenAICompatibleChatCompletionsTransport
  -> MiniMax OpenAI Chat Completions API
```

The Runtime and common message types are provider-neutral. MiniMax-specific serialization, `reasoning_content`, `reasoning_details`, `tool_calls`, `base_resp`, and other continuation details remain inside `MiniMaxProvider`.

The transport remains a one-attempt generic HTTP transport. Provider-specific response interpretation belongs to `MiniMaxProvider`.

### 5. Exact token accounting

Every L4 Model Decision performs exact input-token preflight before the provider request.

Token counting and actual request serialization must share the same MiniMax message/tool serialization path. Exact counting renders the same logical `system_prompt`, complete typed message history, tool definitions, provider continuation fields, thinking mode, and generation prompt through the frozen MiniMax-M3 chat template/tokenizer assets used by the provider profile. A second approximate or independently maintained serializer is forbidden.

This requirement extends the existing exact-token method to structured tools and multi-turn messages. It does not introduce context compaction. Dynamic context exhaustion behavior beyond existing preflight remains deferred until observed in qualification or real trajectories.

### 6. Model-step budget

L4 V1 has one Agent-level hard budget: `max_steps = 100`.

One step is one successfully returned valid Model Decision, i.e. one provider/model completion that normalizes into an `AssistantMessage`. Failed provider/transport attempts that return no valid Model Decision do not consume Agent steps; they are separately counted as request attempts.

The Runtime checks `max_steps` before issuing the next logical model request. The 100th decision is allowed. If it returns a valid final report, the sample succeeds normally. If it returns a legal tool action, that tool executes and its ToolResult is appended, but no 101st Model Decision is requested. The sample then stops with `max_steps_exhausted`.

There is no unaccounted rescue call, forced finalization prompt, cumulative token hard budget, or new sample wall-clock budget in L4 V1.

### 7. Provider-request retry

Retry is request-level infrastructure handling, not Agent behavior and not whole-sample retry.

A retry repeats the same logical request from the same conversation state with identical model, system prompt, tools, messages, reasoning, and generation configuration. No synthetic model-visible failure message is inserted.

V1 retry behavior:

- ordinary transient provider failures: up to three retries after the initial attempt, with 2s/4s/8s exponential backoff;
- request timeout: at most one retry;
- authentication, billing, invalid request, token/context limit, deterministic protocol/configuration error, policy block, and explicit abort: no same-request retry.

Provider/SDK hidden retries remain disabled. Every attempt is recorded in Trace. Retry exhaustion produces `execution_failed / provider_request_failed` and preserves the partial trajectory.

The existing Matrix `retry_count` field must not be interpreted as whole-sample retry for L4. Implementation may rename it to an explicit provider-request retry field through a schema migration, but the semantic boundary above is frozen.

### 8. Tool surface

L4 V1 exposes exactly four read-only investigation tools:

- `read(path, offset?, limit?)`;
- `grep(pattern, path?, glob?, ignore_case?, literal?, context?, limit?)`;
- `find(pattern, path?, limit?)`;
- `ls(path?, limit?)`.

The Agent-visible workspace is conceptually:

```text
/raw.log
/repository/...
```

Benchmark package internals, repository manifest metadata, Canonical Evidence files, and all evaluator artifacts are not directly tool-readable.

The first case input includes case/workspace description plus the complete answer-neutral Canonical Evidence coordinate universe required by Structured Triage Report V1 citation. The coordinate list is a citation vocabulary, not evidence content or evaluator Ground Truth. Physical artifact contents remain tool-acquired.

### 9. Tool result bounds

All tool results have a 50 KiB hard text-output cap.

- `read`: at most 2000 lines per call; 1-based offset; explicit returned range, total-line count, and next offset when continuation is possible;
- `grep`: at most 100 matches, 50 KiB total output, and 500 characters per emitted source line;
- `find`: at most 1000 results and 50 KiB;
- `ls`: at most 500 entries and 50 KiB, one level, deterministic alphabetical ordering, dotfiles included, directories suffixed with `/`.

User/model-supplied `limit` may request fewer results but cannot exceed these V1 hard maxima.

`grep`, `find`, and `ls` operate over the frozen Agent-visible workspace and repository membership. They do not re-apply `.gitignore`, because the frozen Case package already defines the visible evidence universe.

Truncation is both Agent-visible in ToolResult content and recorded as Trace metadata. L4 V1 does not add byte/column slicing for a single line larger than 50 KiB; qualification evidence can justify a later extension.

### 10. Treatment component identity

L4 uses existing Component Registry types; no `runtime` component type is added.

The shared diagnosis Task Contract remains one frozen `prompt` component. L4's runtime-specific model-visible system instructions for tool use, loop semantics, evidence acquisition, stopping, and report submission are frozen as a separate `prompt` component and referenced from Matrix Treatment as `contracts.runtime_control` with its version and fingerprint.

This keeps task semantics and Runtime control independently versioned while reusing the existing generic `prompt` component type. Runtime-control instructions must not be hidden in case `runtime_input`, Tool Registry, Tool Policy, or implementation constants that escape Treatment identity.

`tool_registry` is the single frozen source of provider-visible tool contracts and deterministic tool behavior. Its fingerprint covers tool names, descriptions, complete parameter JSON Schemas, workspace/search semantics, bounds, ordering, and truncation behavior.

`tool_policy` describes cross-call execution semantics only. The L4 baseline is:

```text
scope = model_decision
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

V1 does not duplicate a second allowlist through `default_action`. Tool implementation class paths do not belong in Component manifests; implementation provenance remains represented by `code_revision`.

The generic Component Registry V1 envelope is unchanged. L4 defines and validates its own semantic sub-contract within existing `tools[]` and `rules[]` behavior containers. Formal Matrix validation must resolve and verify the Task Contract, runtime-control prompt, Tool Registry, and Tool Policy references against the Component Registry.

### 11. Tool-call recovery

A successful provider response that normalizes into an AssistantMessage is part of the Agent trajectory and consumes one step, even when its proposed action is invalid.

Recoverable Agent-visible errors include:

- unknown or disallowed tool;
- invalid tool arguments;
- malformed raw arguments;
- expected tool/domain errors;
- a tool call returned with `stop_reason=length`;
- multiple ToolCalls under the baseline single-call policy.

These calls are not executed when invalid. The Runtime emits corresponding `ToolResultMessage(is_error=True)` records and allows the next Model Decision.

For `length + ToolCall`, no call is executed even if arguments appear parseable. For multiple calls under `single`, none are executed and every declared call receives a policy-error ToolResult so the provider protocol remains closed.

Unexpected Runtime, workspace, or tool-implementation exceptions are infrastructure failures and must not be converted into Agent-visible ToolResults.

### 12. Stopping and scoring

Zero ToolCalls means the Model attempted to terminate. Runtime parses the visible assistant text as Structured Triage Report V1.

- valid report -> `report_submitted`;
- invalid or missing report -> `model_stopped_without_valid_report`;
- no report within the step budget -> `max_steps_exhausted`.

No automatic report repair, regeneration, or deadline rescue prompt is added.

`SampleResult.status` remains the existing two-valued contract:

```text
scored | execution_failed
```

Capability terminals are `scored`, including `report_submitted`, `model_stopped_without_valid_report`, and `max_steps_exhausted`. Infrastructure failures such as exhausted provider request failure, Runtime/workspace/tool implementation defects, static context/preflight failure, or evaluation/persistence defects are `execution_failed`.

Recoverable tool errors and provider attempts still inside their retry budget are intermediate events, not sample terminals.

### 13. Trace and trajectory persistence

The complete linear message trajectory is persisted for L4 badcase analysis, including full finalized AssistantMessage content: visible text, provider-returned thinking, ToolCalls, normalized metadata, and opaque provider continuation fields required for replay.

This is diagnostic trajectory evidence, not deterministic score input and not a claim that provider-exposed reasoning is a faithful representation of hidden neural computation.

Trace remains an independent event/lifecycle record. It stores model-call attempts, usage, latency, IDs, tool execution, truncation, budgets, terminal reasons, report submission, and failures without duplicating complete message bodies.

L4 persistence should add the smallest sample-scoped trajectory artifact/table necessary to store the ordered messages. It must reuse the existing run/sample ownership model and SQLite migration chain; it must not introduce a Pi-style session/tree/branch/resume subsystem.

### 14. Context management deferred

L4 V1 performs no compaction, summarization, history trimming, or automatic context compression. Full relevant conversation history is retained. Per-step input token counts/context utilization are measured. Compaction is designed only if qualification or real trajectories show context growth is a material failure mode.

The terminal classification of a future dynamic context-exhaustion event is intentionally not frozen here.

## Reference Architecture Notes

Pi informed several design comparisons: typed message unions, separation of provider adapters from Agent control, native structured tool calls, ToolResult-based recovery, bounded read/search tools, and conversation/session separation from event flow.

DevAgentOps intentionally differs where evaluation semantics require it:

- malformed tool arguments are not semantically repaired by Runtime;
- unexpected Runtime/tool implementation exceptions remain infrastructure failures instead of being universally converted to ToolResults;
- no product-level session tree, branch, resume, deferred tools, images, or compaction is adopted;
- no Pi dependency or compatibility target is created.

## Consequences

Positive consequences:

- the Agent Runtime kernel is explicit and testable;
- provider protocol details do not leak into ReAct control logic;
- malformed Model actions remain measurable capability behavior;
- task semantics, Runtime control, tool behavior, and call policy have reproducible independent Treatment identity;
- full trajectory evidence supports badcase analysis without abusing Trace as a transcript store;
- L1/L2/Oracle can migrate to the same successful-completion contract without changing their evaluation semantics.

Tradeoffs:

- the provider contract and MiniMax adapter require a deliberate migration from `CompletionObservation`;
- SQLite needs a minimal trajectory persistence extension;
- exact token counting must be extended to tools and typed multi-turn messages;
- retaining full provider-exposed thinking increases artifact size;
- no compaction means a future observed context-growth failure may require a follow-up design.

## Non-Decisions

- no L3 Static Retrieval design;
- no L5+ planning, verifier, memory, skills, MCP, subagents, or retrieval optimization;
- no dynamic context-exhaustion terminal classification;
- no column/byte-range read API unless oversized single-line cases actually appear;
- no numeric batch-size cap because baseline is `single`; batch semantics are a future same-L4 ablation;
- no change to Structured Triage Report V1 or scorer formulas.

## Implementation Guide

See [L4 Self-built ReAct Runtime Design](../evaluation/l4-self-built-react-runtime-design.md).

## Refines

ADRs: `0002`, `0003`, `0005`, `0112`, `0114`, `0119`, `0120`, `0122`, `0125`, `0126`, `0127`.
