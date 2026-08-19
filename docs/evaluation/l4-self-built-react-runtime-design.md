# L4 Self-built ReAct Runtime Design

This document is the implementation guide for Issue #52, ADR 0128, and the
accepted ADR 0129 Human amendment.

> Current-state refinement (2026-08-19): ADR 0128 + ADR 0129 remain the frozen
> historical L4 V1 base contract. The later L4 Batch + Parallel ToolCalls
> experiment has completed implementation, formal qualification and fresh
> replication. For **new L4 evaluations**, the recommended Tool Policy is now
> `batch + parallel + independent-call handling`; historical
> `single + sequential + reject-all` components, matrices, fingerprints and
> results remain immutable reference evidence. This refinement stays within
> `runtime_variant=self_built_react` and does not create a new capability rung.

ADR 0129 supersedes only ADR 0128's mandatory **L4 local exact-token
preflight** requirement. The rest of the Human-frozen L4 V1 base contract remains
unchanged. In particular, L4 keeps full provider-origin conversation replay,
`max_steps=100`, bounded read-only tools, Tool Registry / Tool Policy identity,
same-logical-request retry, Trace / trajectory separation, and no compaction.

## 1. Goal

Implement the smallest trustworthy adaptive Agent Runtime for one frozen
CI/test-failure Case:

```text
case/workspace + citation coordinates
        -> model decision
        -> optional read-only tool action(s)
        -> bounded observation(s)
        -> updated typed conversation
        -> next decision or final Structured Triage Report V1
```

L4 is the first Agentic Product Runtime. It is not a framework-building
exercise and does not attempt to implement unrelated L5+ capabilities.

## 2. Architectural boundary

Use this ownership model:

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

The Runtime must never read `evaluator/required-evidence.json` or
`evaluator/expected-answer.json` through normal Agent paths.

A Runtime action is:

```text
ToolAction | SubmitReportAction
```

`SubmitReportAction` is semantic Runtime behavior, not a native tool.

## 3. Code shape

Keep the implementation compact under the existing Runtime package:

```text
src/devagentops/runtime/
├── workspace.py
├── messages.py
├── react.py
├── tool_policy.py
└── tools/
    ├── __init__.py
    ├── read.py
    ├── grep.py
    ├── find.py
    └── ls.py

src/devagentops/conditions/l4/
├── __init__.py
└── react_condition.py
```

Do not split state/context/stopping into a framework hierarchy unless later
evidence makes that complexity necessary.

## 4. Provider-neutral messages and requests

The canonical Runtime-facing types are provider-neutral.

```python
@dataclass(frozen=True)
class TextContent:
    text: str

@dataclass(frozen=True)
class ThinkingContent:
    thinking: str

@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, JsonValue] | None
    raw_arguments: str | None

AssistantContent = TextContent | ThinkingContent | ToolCall

@dataclass(frozen=True)
class UserMessage:
    content: str

@dataclass(frozen=True)
class AssistantMessage:
    content: tuple[AssistantContent, ...]
    response_id: str | None
    response_model: str | None
    usage: TokenUsage
    stop_reason: Literal["stop", "length", "tool_use"]
    raw_stop_reason: str | None
    provider_fields: dict[str, JsonValue]

@dataclass(frozen=True)
class ToolResultMessage:
    tool_call_id: str
    tool_name: str
    content: str
    is_error: bool
```

`provider_fields` is opaque to Runtime code. Only the provider adapter may
interpret or reconstruct provider continuation state.

The logical request shape is:

```python
@dataclass(frozen=True)
class LogicalCompletionRequest:
    model: str
    system_prompt: str | None
    messages: tuple[Message, ...]
    tools: tuple[ToolDefinition, ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
```

`CompletionProvider.complete(request)` returns one normalized
`AssistantMessage` or raises a typed provider error before a Model Decision is
created.

`count_input_tokens()` may remain on provider implementations where L1/L2/Oracle
or offline diagnostics require exact local counting, but **L4 `run_react()` must
not call it on the critical path**.

## 5. MiniMax adapter boundary

Keep the qualified route:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

The transport owns one HTTP/JSON attempt. It does not own Agent retry or hidden
SDK retry.

`MiniMaxProvider` owns:

1. typed-message and ToolDefinition serialization;
2. native `tools` serialization;
3. visible text / thinking / ToolCall parsing;
4. strict parsing of `function.arguments` while preserving the exact raw
   provider string;
5. full provider continuation replay, including MiniMax reasoning fields;
6. usage/model/request/finish metadata normalization;
7. provider-level response-status interpretation where applicable.

Malformed inner `function.arguments` is not a malformed outer provider
envelope. If the provider returns such a ToolCall, Runtime preserves the raw
AssistantMessage and follows the recoverable Agent-action path.

Do not broaden L4 into a generic multi-provider framework.

## 6. L4 context accounting — ADR 0129

L4 does **not** perform mandatory local exact-token preflight before a Model
Decision.

The critical path is:

```text
build logical request
    -> complete_with_request_retry(request)
    -> provider processes request
    -> AssistantMessage.usage records observed usage
```

For completed requests:

- provider-reported `usage.input_tokens` is the authoritative observed input
  token count;
- Trace records provider usage per successful Model Decision;
- the Sample result records the per-step observed input-token sequence;
- Treatment retains the advertised context-window metadata;
- Runtime does not block solely on a locally reconstructed token count.

The frozen Matrix context identity is:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L4 still performs no compaction, summarization, history trimming, or automatic
context compression.

A real context-limit rejection is provider/execution evidence. Predictive
budgeting or compaction is deferred until real trajectories justify a new ADR.

Pinned MiniMax tokenizer/chat-template assets and local exact counting remain
available for existing L1/L2/Oracle behavior and offline diagnostics. They are
not L4 Agent Treatment behavior and are not part of the L4 critical execution
path.

## 7. Initial model-visible input and Runtime-control identity

The shared diagnosis Task Contract remains the existing frozen Runtime-neutral
`prompt` component.

L4-specific instructions for tool use, investigation semantics, loop behavior,
stopping, and final report submission are a **separate frozen `prompt`
component** referenced under `contracts.runtime_control`.

The first user message contains:

- Case ID and public Case metadata needed for triage;
- Agent-visible workspace description (`/raw.log`, `/repository/...`);
- an explicit statement that physical contents must be acquired through tools;
- the complete answer-neutral Canonical Evidence coordinate universe usable for
  final citations.

It must not expose:

- Required Evidence;
- Expected Answer;
- evaluator labels;
- curator/reviewer reasoning;
- package-internal evaluator filenames or scorer state.

Historical and current-forward Runtime-control identities remain separate:

```text
historical reference: l4-react-runtime-control-v1
recommended forward: l4-react-runtime-control-batch-parallel-v1
```

The historical prompt explicitly says zero-or-one ToolCall, so it must not be
silently paired with the Batch Tool Policy. The Batch prompt exposes batching
neutrally and does not instruct the model to prefer it.

## 8. Tool surface and hard bounds

Expose exactly four read-only investigation tools.

### `read(path, offset?, limit?)`

- Agent-visible path only;
- `offset` is 1-based;
- `limit` range is `1..2000`;
- output <= 2000 lines and <= 50 KiB;
- when complete lines remain, include an explicit continuation notice and next
  offset;
- a single source line larger than the hard cap returns a bounded error/notice
  rather than byte slicing.

### `grep(pattern, path?, glob?, ignore_case?, literal?, context?, limit?)`

- maximum 100 matches;
- output <= 50 KiB;
- each emitted source line <= 500 characters;
- match and context lines are distinguishable;
- truncation/limit notices are model-visible;
- operate over frozen visible workspace membership; do not re-apply
  `.gitignore`.

### `find(pattern, path?, limit?)`

- glob path matching;
- deterministic output over visible workspace membership;
- maximum 1000 results;
- output <= 50 KiB;
- relative paths only.

### `ls(path?, limit?)`

- one directory layer;
- maximum 500 entries;
- output <= 50 KiB;
- deterministic alphabetical order;
- directories suffixed with `/`;
- dotfiles included.

Tool truncation is both Agent-visible and represented in Trace metadata.

## 9. Tool Registry and Tool Policy identity

The frozen `tool_registry` is the single source of truth for provider-visible
tool contracts and deterministic tool behavior. Its behavior identity includes:

- names and descriptions;
- complete parameter JSON Schemas;
- workspace/search semantics;
- ordering;
- output/count/line limits;
- truncation/continuation behavior.

Implementation paths and review notes are not behavior identity.

Historical reference Tool Policy:

```json
{
  "rules": [
    {
      "scope": "model_decision",
      "call_mode": "single",
      "execution_mode": "sequential",
      "multiple_calls": "reject_all_with_error_results"
    }
  ]
}
```

If one AssistantMessage emits multiple ToolCalls under historical `single`:

- execute none;
- preserve the AssistantMessage;
- emit one policy-error ToolResult for every declared ToolCall ID;
- allow the next Model Decision.

Recommended forward Tool Policy:

```json
{
  "rules": [
    {
      "scope": "model_decision",
      "call_mode": "batch",
      "execution_mode": "parallel",
      "multiple_calls": "accept_independently"
    }
  ]
}
```

Batch + Parallel frozen semantics:

- one Model Decision may contain zero, one, or multiple ToolCalls;
- no artificial ordinary-call count cap;
- existing lightweight structural interpretation happens before execution;
- malformed calls become per-call error outcomes and do not cancel valid
  siblings;
- valid sibling calls execute concurrently;
- expected tool/domain errors remain per-call Agent-visible outcomes;
- duplicate calls are not deduplicated;
- Runtime waits for all runnable siblings at a barrier;
- ToolResults are materialized in original model-authored ToolCall order;
- only then may the next Model Decision start;
- one N-call Model Decision still consumes one `max_steps` unit;
- unexpected Runtime/workspace/tool implementation exceptions fail the Sample
  after the barrier, with no partial sibling ToolResults fed back to the model;
- `stop_reason=length` continues to execute none of the returned ToolCalls.

Tool availability comes from Tool Registry; do not maintain a second per-tool
allowlist in Tool Policy.

These are two separately frozen same-L4 Treatment identities. Do not rewrite the
historical one to make old runs appear to have used the new policy.

## 10. ReAct loop

Shared loop skeleton:

```text
messages = [initial_user_message]
steps = 0

while True:
    if steps >= max_steps:
        return scored(max_steps_exhausted, report=None)

    request = build_request(system_prompt, messages, tools)
    assistant = complete_with_request_retry(request)

    steps += 1
    persist assistant in trajectory
    trace provider-reported completion metadata and usage

    tool_calls = assistant ToolCall blocks

    if tool_calls is empty:
        report = parse_structured_report(assistant_text(assistant))
        if report valid:
            return scored(report_submitted, report)
        return scored(model_stopped_without_valid_report, raw_report)

    if assistant.stop_reason == length:
        execute none
        append one error ToolResult for every declared ToolCall
        continue

    dispatch according to the frozen Tool Policy
```

Historical single/sequential dispatch:

```text
if policy rejects the call set:
    execute none
    append policy-error ToolResult for every declared ToolCall
    continue

selected_call = the single allowed call

if raw arguments malformed or schema invalid:
    append error ToolResult
    continue

try:
    result = execute_tool(selected_call)
except ExpectedToolDomainError:
    append error ToolResult
    continue
except Exception:
    raise infrastructure failure

append successful ToolResult
```

Batch + Parallel dispatch:

```text
prepare per-call outcomes in source order
malformed calls -> prepared error outcomes
runnable valid calls -> submit concurrently
wait for all runnable siblings (barrier)

if any unexpected Runtime/tool exception:
    fail Sample; do not append partial sibling ToolResults

otherwise:
    append success/error ToolResults in original ToolCall order
    continue to next Model Decision
```

`max_steps = 100` is the only Agent-level hard budget in current read-only L4.

One step is one successfully returned provider completion normalized into a
valid AssistantMessage. Failed provider attempts do not consume steps or enter
trajectory. A Batch decision with N ToolCalls still consumes one step.

The 100th Model Decision is allowed. If it submits a valid report, accept it. If
it executes legal ToolAction(s), execute and persist the ToolResult(s), then
stop before any 101st Model Decision with `max_steps_exhausted`.

## 11. Provider-request retry

Retry is infrastructure handling of the **same logical request**, not Agent
behavior and not whole-sample restart.

For ordinary retryable provider/network failures:

```text
attempt 1 -> failure
wait 2s
attempt 2 -> failure
wait 4s
attempt 3 -> failure
wait 8s
attempt 4 -> success or terminal failure
```

Request timeout is allowed at most one retry.

Auth/billing/invalid request/context-limit/deterministic protocol or config
errors/policy block/explicit abort are non-retryable.

Every attempt is recorded in Trace. Only the successful AssistantMessage enters
trajectory. Exhaustion becomes:

```text
execution_failed / provider_request_failed
```

Matrix `execution_policy.retry_count` means provider-request retry for L4. It
must not trigger whole-sample replay.

The historical L4 formal run exercised both transient 529 recovery and retry
exhaustion. The initial Batch run additionally exercised a real 600-second
provider timeout followed by successful same-request retry; its extreme wall
latency was therefore a provider straggler, not observed parallel-tool deadlock.

## 12. Error and terminal boundaries

### Recoverable Agent-visible action errors

Examples:

- unknown/disallowed tool;
- schema-invalid arguments;
- malformed raw arguments;
- expected tool-domain failure such as path-not-found;
- `length + ToolCall`;
- multiple calls under historical `single`.

Under Batch + Parallel, malformed/expected-error calls remain independent and
do not cancel otherwise valid siblings.

Runtime emits error ToolResult messages and allows another Model Decision.
Runtime does not semantically repair the model action.

### Capability terminals

```text
valid final report
  -> report_submitted
  -> status=scored

zero ToolCalls + invalid/missing report
  -> model_stopped_without_valid_report
  -> status=scored

no report before max_steps
  -> max_steps_exhausted
  -> status=scored
```

`stop_reason=length` with zero ToolCalls follows the same final-report parse
rule. There is no rescue/regeneration call.

### Infrastructure terminals

Examples:

- provider request failure after frozen retry policy;
- malformed provider envelope that yields no AssistantMessage;
- Runtime/workspace invariant defect;
- unexpected tool implementation exception;
- evaluator/scorer/persistence defect.

Result:

```text
status=execution_failed
```

L4 no longer has a local static exact-preflight infeasibility terminal. A real
provider context-limit rejection is surfaced through the provider/execution
error path under ADR 0129.

## 13. Trace vs Agent trajectory

These are separate records.

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

Persist complete normalized AssistantMessages needed for badcase analysis,
including visible text, provider-returned thinking, ToolCalls, metadata, and
opaque provider continuation fields required for replay.

Provider-returned thinking is diagnostic trajectory evidence. It is not a
score input and is not claimed to be faithful hidden neural chain-of-thought.

Reuse the existing Trace recorder/table. The trajectory store must remain the
smallest sample-scoped linear persistence extension required to reconstruct one
sample; do not add sessions, branches, parent pointers, resume state, or a
second storage subsystem.

## 14. Matrix and Treatment integration

L4 remains Matrix v2:

```text
runtime_variant = self_built_react
```

Treatment identity references the frozen:

- shared Task Contract prompt;
- L4 Runtime-control prompt;
- Tool Registry;
- Tool Policy;
- provider/model/reasoning/generation/context contract;
- output-realization contract where applicable.

Formal validation resolves and checks the Task prompt, Runtime-control prompt,
Tool Registry, and Tool Policy against Component Registry. The current loader
accepts exactly the supported historical pair or Batch + Parallel pair and
rejects mixed/unknown identities.

Runtime implementation is **not** a Component Registry component. Implementation
provenance remains:

```text
runtime_variant + code_revision
```

Execution policy, including concurrency and provider-request retry, remains
outside Treatment/Condition behavior identity and participates in Run
Configuration identity as already frozen.

Historical/fresh single-sequential reference Matrix:

```text
evaluation/matrices/l4-minimax-m3-canonicalized-v2.json
```

Recommended new L4 evaluation Matrix:

```text
evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json
```

## 15. Canonical Evidence and citation behavior

The complete Canonical coordinate universe is disclosed as answer-neutral
citation vocabulary in the initial input. This is different from exposing
Canonical Evidence content or hidden Required Evidence.

The Agent must:

1. acquire physical content through tools;
2. reason over that content;
3. identify relevant physical facts;
4. submit Evidence references within the frozen citation vocabulary/explicit
   physical span representation supported by the current output contract.

Badcase analysis distinguishes:

```text
A. required physical content not found/seen
   -> acquisition/tool-use problem

B. physical content found but correct Evidence ID not cited
   -> mapping/evidence-selection/report problem

C. correct Evidence ID cited but diagnosis wrong
   -> reasoning problem
```

Historical L4 V1 had no dynamic physical-span -> Evidence-ID helper. Pair
Analysis later showed that a deterministic representation subset of B was shared
across conditions rather than L4-specific.

Current canonicalized output path is therefore shared across L1/L2/Oracle/L4:

```text
raw model candidate document
    -> canonical-line-range-normalization-v1
    -> report validation
    -> frozen scorer
```

The resolver preserves exact legal IDs; if frozen source identity matches and an
explicit line range is parseable, it maps deterministically by physical overlap
to Canonical unit(s) and stably deduplicates. Unresolvable references remain
invalid. It never reads Required Evidence / Expected Answer and does not perform
fuzzy or semantic repair.

## 16. Deterministic testing

Historical/base fake-provider tests cover at minimum:

1. multi-step tool trajectory ending in a valid report;
2. model stops without valid report;
3. exact max-step semantics;
4. unknown tool recovery;
5. schema-invalid arguments;
6. malformed raw arguments and next-turn recovery;
7. `length + ToolCall` rejection;
8. multi-ToolCall rejection under historical `single`;
9. expected tool-domain error recovery;
10. unexpected Runtime/tool exception -> execution failure;
11. transient provider failure -> same-request retry -> success;
12. retry exhaustion -> execution failure;
13. Trace / trajectory separation and persistence;
14. evaluator/package leakage boundary;
15. 50 KiB/count/line truncation semantics;
16. L4 `run_react()` does **not** call `count_input_tokens()`;
17. provider-reported input usage is recorded per successful Model Decision;
18. MiniMax assistant continuation fields and raw ToolCall arguments round-trip;
19. Matrix doctor rejects missing/mismatched Runtime-control, Tool Registry, or
    Tool Policy identity.

Batch + Parallel focused tests additionally cover:

20. actual sibling-call concurrency;
21. barrier plus original source-order ToolResults/events;
22. N ToolCalls in one decision still consume one step;
23. mixed valid/malformed/expected-error calls remain independent;
24. duplicate calls execute independently;
25. unexpected worker exception -> Sample infrastructure failure with no partial
    ToolResults fed back;
26. `stop_reason=length` executes none of the batch;
27. frozen Batch prompt/policy/Matrix identity and supported-pair validation.

Maintainer validation for PR #62 passed:

```text
focused regression: 29 passed
formal candidate doctor: PASS
full repository regression: 377 passed, 2 skipped, 30 subtests passed
```

Existing L1/L2/Oracle exact-token tests remain unchanged.

## 17. Live qualification and formal qualification

Historical L4 live qualification proved:

- native function calling through the existing OpenAI Chat Completions route;
- full assistant `reasoning_details` / provider continuation replay;
- raw ToolCall replay preserving protocol-significant fields;
- real multi-step read-only tool trajectory;
- provider-reported usage recorded without a local preflight gate;
- correct Trace / trajectory persistence;
- no evaluator leakage.

A model capability failure in the final diagnosis/report does not invalidate the
Runtime qualification if provider protocol, loop, Tool execution, persistence,
and information boundaries function as designed.

Batch + Parallel did not widen the L1-specific Matrix-v2 `eval debug` framework
solely for qualification. It used deterministic concurrency/error/order tests,
formal `eval doctor`, and complete live/formal 20×3 execution evidence.

## 18. Formal milestone and replication interpretation

All L4 formal runs reuse the existing formal evaluation stack:

- doctor-first validation;
- full frozen Suite;
- repeated Sample scheduler;
- bounded cross-Case concurrency;
- Trace;
- SQLite persistence;
- Case-first aggregation;
- JSON/Markdown artifacts;
- existing Structured Triage Report scorer.

Do not build a parallel L4 evaluator.

Capability outcomes remain scored even when the report is invalid. Provider /
Runtime infrastructure failures remain `execution_failed` and remain visible in
execution coverage.

Historical L4 and canonicalized fresh generation remain distinct immutable
references. Batch + Parallel is evaluated as a separate same-L4 Treatment.

Initial Batch run:

```text
Run 010e9a75-8ca8-44b5-8445-d82d188d11f3
60/60 scored, 0 execution failures
successful Model Decisions 547 vs fresh reference 798 (-31.45%)
257 multi-call decisions across 55/60 Samples
```

Its quality metrics were lower, but all eight protocol-invalid Samples were
`invalid_report_type` and hosted regeneration variance was already known. A
fresh back-to-back replication was therefore run rather than attributing the
single observation to batching.

Replication:

```text
single: b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8
batch:  d76ac5ca-22a3-4c67-acf3-c33bba68f0d5

Model Decisions       877 -> 571   (-34.89%)
Executed ToolCalls     809 -> 775   (-4.20%)
Raw input tokens      23.45M -> 15.70M (-33.06%)
Wall time            978.27s -> 806.69s (-17.54%)
Taxonomy              71.67% -> 75.00%
Evidence              74.64% -> 73.50%
Required Fields       93.33% -> 98.13%
Protocol              93.33% -> 91.67%
```

The initial apparent quality regression did not reproduce; taxonomy and Required
Fields reversed direction. Paired 20-Case diagnostic intervals span zero for all
four quality metrics. Efficiency improvement reproduced at similar magnitude.

Raw token traffic reduction is **not** interpreted as equal billing reduction:
non-cached prompt tokens increased slightly in replication because cache behavior
differed.

The development milestones are evidence for Runtime behavior and diagnostic
quality. They are not final benchmark freezes or leaderboard results.

## 19. Deferred features and next large direction

Do not implement without new evidence:

- compaction / summary / history trimming;
- predictive local context budgeting;
- planner/verifier unless repair-loop evidence requires it;
- retrieval optimization;
- dynamic skills/MCP;
- long-term memory/experience;
- oversized-line slicing;
- whole-sample retry;
- dynamic context-exhaustion terminal taxonomy.

Batch/parallel Tool Policy is **no longer deferred**. Its controlled experiment
is complete and Batch + Parallel is the recommended forward L4 Tool Policy.

The next large Product Runtime capability direction is executable repair /
sandboxed remediation:

```text
investigate
    -> diagnose
    -> mutate/edit
    -> execute/test
    -> observe
    -> retry
    -> verify
    -> report
```

That phase intentionally introduces mutation/testing outside the completed
read-only V1 boundary and must receive an explicit new design/identity rather
than silently mutating historical L4 Treatment contracts.

Future behavior changes require explicit Treatment/ADR decisions rather than
silent mutation of recorded baselines.

## 20. Acceptance checklist

Historical L4 V1 base implementation is acceptable when represented in
code/config/tests according to ADR 0128 + ADR 0129:

- [x] provider-neutral typed messages and logical completion request;
- [x] MiniMax native ToolCall and continuation round-trip;
- [x] provider-reported L4 context accounting with no mandatory local preflight;
- [x] shared Task Contract plus separate frozen Runtime-control prompt;
- [x] bounded `read/grep/find/ls` contracts;
- [x] frozen Tool Registry and Tool Policy;
- [x] historical `single + sequential` policy;
- [x] exact `max_steps=100` semantics;
- [x] same-logical-request provider retry;
- [x] scored capability vs `execution_failed` infrastructure taxonomy;
- [x] complete linear trajectory persistence separate from Trace;
- [x] full answer-neutral Canonical coordinate vocabulary in initial input;
- [x] no compaction or unrelated L5+ mechanism in baseline;
- [x] deterministic test gate;
- [x] live MiniMax qualification;
- [x] one controlled formal 20 Case x 3 historical milestone.

Post-V1 same-L4 refinements now also accepted:

- [x] shared deterministic Evidence Reference Canonicalization with preserved raw
      candidate audit boundary;
- [x] separately frozen Batch Runtime-control prompt and Tool Policy;
- [x] parallel sibling execution with barrier/source-order materialization;
- [x] independent expected-error handling and Sample-level unexpected failures;
- [x] deterministic Batch-focused tests + doctor;
- [x] initial Batch 20×3 formal run;
- [x] fresh single/sequential vs Batch 20×3 replication;
- [x] Batch + Parallel recommended for new L4 evaluations while historical
      single/sequential remains immutable reference.

Full Batch experiment evidence is recorded in
[`milestones/l4-batch-parallel-toolcalls-2026-08-19.md`](milestones/l4-batch-parallel-toolcalls-2026-08-19.md).
