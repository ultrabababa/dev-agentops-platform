# L4 Self-built ReAct Runtime Design

> Current-state note (2026-08-19): this document now distinguishes the frozen historical L4 V1 base contract from the later same-L4 Batch + Parallel Tool Policy refinement. ADR 0128 + ADR 0129 remain the historical V1 base contract. The completed Batch + Parallel experiment recommends `batch + parallel + independent-call handling` for new L4 evaluations while preserving historical `single + sequential + reject-all` identities and results.

## 1. Goal and boundary

L4 is the smallest trustworthy adaptive Agent Runtime for one frozen CI/test-failure Case:

```text
case/workspace + citation coordinates
        -> model decision
        -> optional read-only tool action(s)
        -> bounded observation(s)
        -> updated typed conversation
        -> next decision or final Structured Triage Report V1
```

L4 is the first Agentic Product Runtime. Batch + Parallel does not create a new rung or a new Product Runtime; it is a separately frozen Tool Policy Treatment inside `runtime_variant=self_built_react`.

Ownership remains:

```text
LLM / Provider
  proposes AssistantMessage

ReAct Runtime
  owns loop, state, action interpretation, policy, budgets, stop

Tools
  own bounded read/search/list behavior over RuntimeCaseWorkspace

Environment
  is the frozen Case Investigation Workspace

Trace
  owns execution/lifecycle observations

Trajectory persistence
  owns complete ordered Agent messages

Evaluator
  owns hidden Required Evidence, Expected Answer, report validation, scoring
```

The Runtime must never read evaluator-only artifacts through normal Agent paths. `SubmitReportAction` is semantic Runtime behavior, not a native tool.

## 2. Code shape

Keep the implementation compact:

```text
src/devagentops/runtime/
├── workspace.py
├── messages.py
├── react.py
├── tool_policy.py
└── tools/
    ├── read.py
    ├── grep.py
    ├── find.py
    └── ls.py

src/devagentops/conditions/l4/
└── react_condition.py
```

Do not split state/context/stopping into a framework hierarchy unless later evidence requires it.

## 3. Provider-neutral message contract

Canonical Runtime-facing messages remain provider-neutral:

```text
UserMessage
AssistantMessage
  -> TextContent | ThinkingContent | ToolCall
ToolResultMessage
```

`ToolCall` preserves parsed arguments when valid plus raw provider/model argument text when available. Malformed inner argument JSON remains measurable model behavior; Runtime does not semantically repair it.

`AssistantMessage.provider_fields` remains opaque to Runtime code and is interpreted only by the provider adapter for continuation.

`CompletionProvider.complete(request)` returns one normalized `AssistantMessage` or raises a typed provider error before a Model Decision is created.

## 4. MiniMax adapter boundary

Qualified route:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

The transport owns one HTTP/JSON attempt. It does not own Agent retry or hidden SDK retry.

`MiniMaxProvider` owns typed-message/tool serialization, visible text/thinking/ToolCall parsing, strict raw argument preservation, provider continuation replay, usage/model/request/finish metadata normalization, and provider response-status interpretation.

## 5. L4 context accounting — ADR 0129

L4 does **not** perform mandatory local exact-token preflight before a Model Decision.

```text
build logical request
    -> complete_with_request_retry(request)
    -> provider processes request
    -> AssistantMessage.usage records observed usage
```

For completed requests:

- provider-reported `usage.input_tokens` is authoritative observed input accounting;
- Trace records usage per successful Model Decision;
- Sample result records the per-step input-token sequence;
- Treatment retains context-window metadata;
- Runtime does not block solely on a locally reconstructed token count.

Frozen context identity:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

No compaction, summarization, history trimming, or automatic context compression is performed in current L4.

## 6. Initial model-visible input and Runtime-control identity

The shared diagnosis Task Contract remains Runtime-neutral. L4-specific tool/loop/stopping/report instructions are separate frozen `prompt` components referenced through `contracts.runtime_control`.

Initial model-visible input contains:

- Case ID/public metadata needed for triage;
- Agent-visible workspace description (`/raw.log`, `/repository/...`);
- statement that physical contents must be acquired through tools;
- complete answer-neutral Canonical Evidence coordinate universe usable for final citations.

It must not expose Required Evidence, Expected Answer, evaluator labels, curator/reviewer reasoning, or evaluator/scorer internals.

Historical and Batch Runtime-control prompts are separate identities:

```text
historical: l4-react-runtime-control-v1
batch:      l4-react-runtime-control-batch-parallel-v1
```

Do not mix one prompt with the other policy.

## 7. Tool surface and hard bounds

Expose exactly four read-only investigation tools:

- `read(path, offset?, limit?)`: max 2000 lines/call, 1-based offset, <=50 KiB, explicit continuation;
- `grep(...)`: max 100 matches, <=50 KiB, max 500 chars/source line;
- `find(...)`: max 1000 results, <=50 KiB, deterministic relative paths;
- `ls(...)`: max 500 entries, one layer, <=50 KiB, deterministic alphabetical order, dotfiles included, directories `/` suffixed.

`grep/find/ls` operate over frozen visible workspace membership and do not re-apply `.gitignore`. Truncation is model-visible and Trace-visible.

## 8. Tool Registry and Tool Policy identity

The frozen Tool Registry is the single source of truth for provider-visible tool contracts and deterministic tool behavior: names/descriptions, parameter schemas, workspace/search semantics, ordering, bounds, and truncation/continuation behavior.

Historical L4 V1 Tool Policy:

```json
{
  "rules": [{
    "scope": "model_decision",
    "call_mode": "single",
    "execution_mode": "sequential",
    "multiple_calls": "reject_all_with_error_results"
  }]
}
```

Recommended forward Tool Policy:

```json
{
  "rules": [{
    "scope": "model_decision",
    "call_mode": "batch",
    "execution_mode": "parallel",
    "multiple_calls": "accept_independently"
  }]
}
```

Tool availability comes from Tool Registry; do not maintain a second per-tool allowlist in Tool Policy.

### Batch + Parallel frozen semantics

For one AssistantMessage containing ToolCalls:

1. zero/one/multiple calls are allowed; there is no arbitrary ordinary-call count cap;
2. `stop_reason=length` still executes none;
3. existing lightweight structural interpretation occurs before execution;
4. malformed calls become per-call error outcomes and do not cancel valid siblings;
5. valid siblings execute concurrently;
6. expected tool/domain errors remain per-call Agent-visible outcomes;
7. duplicate calls are not deduplicated;
8. Runtime waits for all runnable siblings at a barrier;
9. successful/error ToolResults are appended in original model-authored ToolCall order;
10. only then may the next Model Decision begin;
11. unexpected Runtime/workspace/tool implementation exceptions fail the Sample after the barrier, and partial sibling ToolResults are not fed back to the model;
12. one N-call Model Decision consumes one `max_steps` unit.

The prompt exposes capability neutrally and does not instruct the model to prefer batching.

## 9. ReAct loop

Conceptually:

```text
messages = [initial_user_message]
steps = 0

while True:
    if steps >= max_steps:
        return scored(max_steps_exhausted)

    assistant = complete_with_request_retry(build_request(messages))
    steps += 1
    persist assistant
    trace provider usage / metadata

    tool_calls = assistant ToolCalls

    if no tool_calls:
        parse final Structured Triage Report
        return scored(report_submitted | model_stopped_without_valid_report)

    if stop_reason == length:
        append ordered error ToolResults; continue

    dispatch according to frozen Tool Policy

    historical single:
        reject multi-call decisions or execute the one allowed call

    batch parallel:
        prepare per-call outcomes
        concurrently execute valid siblings
        barrier
        if unexpected infrastructure defect: fail Sample
        else append ToolResults in source order
```

`max_steps=100` remains the only Agent-level hard budget. The 100th Model Decision is allowed; legal ToolAction(s) may execute, but no 101st Model Decision is requested.

## 10. Provider-request retry

Retry handles the **same logical request**, not Agent behavior and not whole-sample restart.

- ordinary retryable provider/network failures: initial + up to 3 retries with 2s/4s/8s backoff;
- request timeout: at most one retry;
- auth/billing/invalid request/context-limit/deterministic protocol/config/policy/abort: no same-request retry;
- every attempt enters Trace;
- only a successful AssistantMessage enters trajectory;
- exhaustion -> `execution_failed / provider_request_failed`.

The historical L4 run exercised 529 retry recovery/exhaustion. The initial Batch run exercised a real 600-second timeout followed by successful same-request retry.

## 11. Error and terminal boundaries

Recoverable Agent-visible action errors include unknown/disallowed tool, schema-invalid/malformed arguments, expected tool/domain errors, `length + ToolCall`, and historical single-policy multi-call rejection.

Under Batch + Parallel, malformed/expected-error siblings do not cancel valid siblings.

Capability terminals remain:

```text
report_submitted
model_stopped_without_valid_report
max_steps_exhausted
```

All are `status=scored`.

Infrastructure failures include exhausted provider-request failure, malformed provider envelope, Runtime/workspace invariant defect, unexpected tool implementation exception, and evaluator/scorer/persistence defect. These are `status=execution_failed`.

## 12. Trace vs Agent trajectory

```text
Trace
= lifecycle / execution observations
  request attempts
  provider usage / latency / IDs
  tool lifecycle / errors / truncation
  budgets / terminals / infrastructure failures

Agent trajectory
= complete ordered UserMessage / AssistantMessage / ToolResultMessage history
```

Provider-returned thinking is diagnostic trajectory evidence, not a score input and not a claim about faithful hidden neural computation.

## 13. Matrix and Treatment integration

L4 remains:

```text
runtime_variant = self_built_react
```

Treatment identity references shared Task Contract, L4 Runtime-control prompt, Tool Registry, Tool Policy, provider/model/reasoning/generation/context, and output-realization identity.

Runtime implementation is not a Component Registry component; provenance remains `runtime_variant + code_revision`.

Historical canonicalized single/sequential reference Matrix:

```text
evaluation/matrices/l4-minimax-m3-canonicalized-v2.json
```

Recommended new L4 evaluation Matrix:

```text
evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json
```

Historical matrices remain unchanged.

## 14. Canonical Evidence and final-report normalization

The complete Canonical coordinate universe is answer-neutral citation vocabulary, not Evidence Ground Truth.

Current shared final-report path:

```text
raw candidate document
    -> canonical-line-range-normalization-v1
    -> validation
    -> frozen scorer
```

Exact IDs are preserved. A parseable explicit line range with matching frozen source identity maps deterministically by physical overlap to Canonical units and is stably deduplicated. Unresolvable references remain invalid. Resolver never reads Required Evidence / Expected Answer and never performs fuzzy/semantic repair.

## 15. Testing and qualification

Historical L4 V1 tests cover multi-step trajectory, stopping, max-step semantics, tool errors, single-policy multi-call rejection, provider retry, Trace/trajectory separation, leakage boundaries, bounds, provider-reported context accounting, MiniMax continuation, and Matrix identity.

Batch + Parallel adds focused tests for:

- actual concurrency;
- barrier/source-order ToolResults;
- one N-call decision consuming one step;
- mixed valid/malformed/expected-error siblings;
- duplicate calls;
- unexpected worker exception -> infrastructure failure with no partial ToolResults fed back;
- `stop_reason=length` executing none;
- candidate component/Matrix identity.

Maintainer validation:

```text
focused regression: 29 passed
formal doctor: PASS
full regression: 377 passed, 2 skipped, 30 subtests passed
```

## 16. Formal experiment result

Initial Batch run:

```text
Run 010e9a75-8ca8-44b5-8445-d82d188d11f3
60/60 scored, 0 execution failures
Model Decisions 547 vs prior fresh single reference 798 (-31.45%)
257 multi-call decisions across 55/60 Samples
```

The initial run's quality metrics were lower, but all eight protocol-invalid Samples were `invalid_report_type`, and hosted regeneration variance was already known. A fresh back-to-back replication was therefore run.

Replication:

```text
single run: b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8
batch run:  d76ac5ca-22a3-4c67-acf3-c33bba68f0d5

Model Decisions       877 -> 571   (-34.89%)
Executed ToolCalls     809 -> 775   (-4.20%)
Input tokens          23.45M -> 15.70M (-33.06%)
Wall time            978.27s -> 806.69s (-17.54%)
Taxonomy              71.67% -> 75.00%
Evidence              74.64% -> 73.50%
Required Fields       93.33% -> 98.13%
Protocol              93.33% -> 91.67%
```

The initial apparent quality regression did not reproduce; taxonomy and Required Fields reversed direction. Paired 20-Case diagnostic intervals span zero for all four quality metrics. Efficiency improvement reproduced at similar magnitude.

Raw token traffic fell, but non-cached prompt tokens increased slightly in replication because cache behavior differed, so the experiment does not claim a 33% billing reduction.

## 17. Current decision

Batch + Parallel is the **recommended forward Tool Policy for new L4 evaluations and Runtime evolution**.

Historical `single + sequential + reject-all` remains an immutable reference Treatment. Do not retroactively change its prompt/policy components, matrices, fingerprints, or results. The direct `ReactConfiguration` baseline default may remain historical for backward compatibility; recommendation is expressed through explicit Treatment/Matrix identity rather than a silent global switch.

Do not add, based on this experiment:

- arbitrary batch-size caps;
- forced-batching prompt language;
- output repair;
- scheduler heuristics;
- a new Runtime rung.

## 18. Deferred / next work

The Batch experiment is complete. The next large capability direction is executable repair / sandboxed remediation:

```text
investigate -> diagnose -> mutate/edit -> execute/test -> observe -> retry -> verify -> report
```

This is outside the completed read-only V1 boundary and must be designed as an explicit next phase while reusing the L4 kernel.

Still evidence-gated:

- L3 retrieval internals;
- compaction / predictive context budgeting;
- dynamic context-exhaustion handling;
- planner/verifier/reflection unless repair-loop evidence requires it;
- skills/MCP/memory/multi-agent;
- oversized-line byte/column slicing.

## 19. Source references

- [ADR 0128 — historical L4 V1 base contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129 — provider-reported L4 context accounting](../adr/0129-l4-provider-reported-context-accounting.md)
- [Evaluation Matrix & Component Registry](evaluation-matrix-and-component-registry.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [L4 Historical Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md)
- [Shared Evidence Reference Canonicalization Milestone](milestones/evidence-reference-canonicalization-2026-08-19.md)
- [L4 Batch + Parallel ToolCalls Milestone](milestones/l4-batch-parallel-toolcalls-2026-08-19.md)
