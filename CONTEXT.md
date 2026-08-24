# DevAgentOps — Current Project Context

> Updated 2026-08-24. This file is a current-orientation document, not a historical log. Dated milestone documents, merged PR bodies, Case review packets, and `docs/adr/archive/` preserve historical state and may intentionally contain superseded wording. For milestone status, see `docs/evaluation/milestones/README.md`.

## Project

DevAgentOps is a developer-focused **CI/Test Failure Triage Agent Runtime and Formal Evaluation system**.

The central question is:

> How much diagnosis capability can different Runtime / evidence-acquisition / Agent-control treatments realize on the same frozen engineering failures, and how can failures be attributed without conflating model reasoning, evidence acquisition, reporting protocol, and infrastructure?

Current end-to-end loop:

```text
Frozen Case / Environment
    -> Runtime / Agent execution
    -> Trace + complete Agent trajectory
    -> deterministic validation / scoring
    -> Case-first aggregation / Oracle diagnostics
    -> badcase attribution
    -> controlled Runtime evolution
```

The current V1 domain is read-only diagnosis. It does not edit code, rerun tests/CI, open PRs, or deploy.

## Current state

Completed:

- Offline Case Schema V2;
- frozen `triage-suite-v1`, 20 Cases, exactly 4 per V1 Failure Type;
- Canonicalization Profile v1;
- Structured Triage Report V1 and deterministic scorer;
- Matrix v2, Component Registry, doctor-first formal execution;
- repeated Sample scheduler, Case-first aggregation, SQLite/Trace/artifacts;
- L1 MiniMax-M3 20×3 historical formal milestone: 60 scored, 0 execution failures;
- L2 MiniMax-M3 20×3 historical formal milestone: 60 scored / 120 model calls, 0 execution failures;
- Oracle MiniMax-M3 20×3 historical formal milestone: 60 scored, 0 execution failures;
- L4 `self_built_react` Runtime implementation, deterministic tests, live MiniMax qualification, and historical 20×3 formal milestone;
- ADR 0129 provider-reported L4 context accounting amendment;
- Oracle↔L4 Pair Analyzer and real 20-Case pair analysis, including 15 Detailed Review Cases;
- shared deterministic Evidence Reference Canonicalization implementation (`development-v2` / `canonical-line-range-normalization-v1`);
- canonicalization focused regression `100 passed, 2 skipped` and full repository regression `371 passed, 2 skipped, 30 subtests passed`;
- zero-model-cost replay of historical L1/L2/Oracle/L4 raw candidates through the canonicalizer + unchanged scorer;
- fresh canonicalized L1/L2/Oracle/L4 `20 Cases × 3 repeats` formal generation;
- L4 Batch + Parallel ToolCalls implementation with frozen Runtime-control/Tool Policy identities;
- Batch + Parallel focused regression `29 passed`, formal `eval doctor` PASS, full repository regression `377 passed, 2 skipped, 30 subtests passed`;
- initial Batch + Parallel `20×3` formal run plus a fresh back-to-back single/sequential vs Batch + Parallel `20×3 + 20×3` replication block.
- L3 `static_retrieval` V1 implementation, full regression `397 passed, 2 skipped, 30 subtests passed`, clean live MiniMax-M3 `20×3` formal milestone, and evaluator-side acquisition analysis.

Historical L4 formal milestone:

```text
20 Cases × 3 repeats = 60 Samples
59 scored / 1 provider execution failure
Execution Coverage            98.33%
Failure Type Exact Match      88.33%
Evidence Hit Rate             65.51%
Required Fields Completeness  96.67%
Protocol Validity             81.36%
```

The only historical L4 execution failure was a provider HTTP 529 sequence that exhausted the frozen initial + 3 same-logical-request retry policy. No Runtime implementation blocker was found.

Pair Analysis established that the Oracle↔L4 gap is not one mechanism. It includes Canonical reference realization failures, investigation-depth/evidence-acquisition gaps, evidence-selection gaps, genuine causal-reasoning failures, and operational execution reliability. It also found clear negative-gap Cases where autonomous L4 investigation outperformed Oracle taxonomy.

Shared Evidence Reference Canonicalization has now closed the identified deterministic report-realization slice. Historical offline replay isolated the effect:

```text
L1 Protocol   96.67% -> 96.67%    Evidence 51.38% -> 51.38%
L2 Protocol   90.00% -> 95.00%    Evidence 55.57% -> 59.46%
Oracle        100.00% -> 100.00%  Evidence 89.29% -> 89.29%
L4 Protocol   81.36% -> 96.61%    Evidence 65.51% -> 75.88%
```

L4 replay recovered 9 historical invalid Samples, removed all 12 historical unknown Evidence IDs and the duplicate-only failure, while leaving Failure Type Exact Match unchanged at 88.33%. This is the causal isolation result because the historical model candidates were held fixed.

Fresh canonicalized formal generation then produced:

```text
L1      59/60 scored   taxonomy 80.00%   evidence 52.16%   protocol 96.61%
L2      58/60 scored   taxonomy 83.33%   evidence 54.15%   protocol 98.28%
L3      60/60 scored   taxonomy 88.33%   evidence 50.67%   protocol 98.33%
Oracle  60/60 scored   taxonomy 83.33%   evidence 85.40%   protocol 96.67%
L4      60/60 scored   taxonomy 81.67%   evidence 71.83%   protocol 93.33%
```

Fresh-generation deltas are operational confirmation rather than single-variable causal estimates. The fresh Oracle run had `canonicalization_changed_samples = 0` but still moved from its historical metrics, demonstrating material model/provider regeneration variance.

L3 Trace then enabled a zero-model-cost evaluator-side decomposition: Case-first Required Evidence acquisition recall was `76.56%`, final Report Evidence Hit was `50.67%`, and acquired-Required-Evidence utilization was `66.18%`. All 20 Cases had deterministic retrieval input hashes across three repeats. L3 is therefore accepted as a reproducible diagnostic baseline, while its quality result does not demonstrate an Evidence Hit improvement over L1/L2.

Batch + Parallel then tested the observed multi-call friction independently of canonicalization. Two fresh Batch runs reduced Model Decisions by about `31–35%`. In the clean back-to-back replication, single/sequential vs Batch + Parallel was:

```text
Model Decisions       877 -> 571   (-34.89%)
Executed ToolCalls     809 -> 775   (-4.20%)
Raw input tokens     23.45M -> 15.70M
Wall time            978.27s -> 806.69s (-17.54%)
Taxonomy              71.67% -> 75.00%
Evidence              74.64% -> 73.50%
Required Fields       93.33% -> 98.13%
Protocol              93.33% -> 91.67%
```

The initial Batch run's larger quality drop did not reproduce; taxonomy and Required Fields reversed direction, while the efficiency mechanism reproduced at similar magnitude. Current evidence therefore does not demonstrate a material Batch-induced quality regression. Batch + Parallel is now the recommended forward L4 Tool Policy for new evaluations; historical single/sequential remains an immutable reference Treatment.

Do not continue widening the canonicalizer or Batch policy without new evidence. The next large capability direction is executable repair / sandboxed remediation outside the current read-only V1 boundary.

## Core terminology

### LLM / Model

Decision and reasoning engine only. It proposes assistant content/tool actions; it does not own execution authority.

### Agent Runtime

The system kernel that owns authoritative state, loop execution, action interpretation, tool validation/execution, policy, budgets, Trace hooks, and terminal handling.

### Agent System

```text
Model
+ Agent Runtime
+ Tools
+ Environment
+ Prompt / State
```

“Agent” normally refers to this whole system, not only the model.

### Product Runtime

A supported runtime lineage. V1 Product Runtimes are Fixed Pipeline and L4 self-built ReAct. L1/L2/L3 are diagnostic/comparison conditions, not Product Runtimes.

### Runtime Capability Ladder

```text
L0 deterministic pipeline
L1 full-context one-shot
L2 fixed model workflow
L3 static retrieval
L4 self-built ReAct
L5+ incremental Agent capabilities
```

The ladder is an attribution framework, not a required implementation order. L3 is a completed optional diagnostic baseline and does not block L4 or later evidence-driven work.

## Case and evidence model

### Evidence Universe

The authentic, frozen, offline, bounded-but-realistic physical world of a Formal Case:

```text
raw failure log
+ bounded exact-revision repository snapshot
```

### Physical Artifact

Sole fact source. Current Formal Case V2 physical artifacts are `raw.log` and manifest-declared repository files.

### Canonical Evidence Unit

Deterministic, answer-neutral source-span coordinate over a Physical Artifact. It provides stable IDs for citation/measurement; it is not a second editable copy of source truth and not a mandatory Retrieval chunk.

### Evidence Ground Truth

Hidden evaluator-only `required-evidence.json`, containing Human-reviewed Required/Optional Canonical IDs. Never directly visible to normal model-backed conditions.

### Diagnosis Ground Truth

Hidden evaluator-only `expected-answer.json` containing expected diagnosis semantics. Separate from Evidence Ground Truth.

### L4 Canonical vocabulary

Historical L4 V1 receives the complete **answer-neutral Canonical coordinate vocabulary** in the initial model-visible input so it can cite valid Evidence IDs.

That does **not** expose evidence content or Ground Truth:

```text
visible upfront:
- neutral coordinate IDs / source-span vocabulary

not visible upfront:
- Physical Artifact contents
- which IDs are required/optional
- Expected Answer
- evaluator metadata
```

The Agent must discover physical facts through tools. The first L4 formal milestone showed a representation defect: the model could locate a physical line range but still serialize a non-canonical aggregate Evidence ID.

Deterministic Evidence Reference Canonicalization is now implemented as shared final-report/output infrastructure for L1/L2/L3/Oracle/L4: exact frozen IDs are preserved; if source identity matches and an authored line range can be parsed, the resolver maps by deterministic physical overlap to the actual frozen Canonical unit IDs; results are stably deduplicated; unresolved references remain invalid. The resolver does not use Required Evidence, Expected Answer, fuzzy matching, semantic repair, or Agent read-history as a repair gate.

Fresh L4 residual unknown IDs were source-identity typos, not missed line-range repairs. They were intentionally left invalid because correcting them would require guessing the intended source.

## L4 Runtime contract

### Control

```text
Model proposes Action
    -> Runtime validates policy / schema / budget
    -> Runtime optionally executes Tool
    -> ToolResult returned
    -> Runtime appends authoritative message state
    -> next Model Decision or terminal
```

### Native tools

Exactly four read-only investigation tools in L4 V1:

```text
read
grep
find
ls
```

There is no Bash/edit/write/test/CI mutation tool.

`submit_report` is **not** a native L4 tool. Report submission is a semantic terminal Runtime action: 0 ToolCalls means the model attempts to finish; visible assistant text is parsed as Structured Triage Report V1.

### Agent-visible workspace

```text
/raw.log
/repository/...
```

Evaluator directories, canonical-evidence files, package metadata, and repository manifest are not tool-readable.

### Tool Registry

Frozen provider-visible contracts and deterministic Tool behavior: names, descriptions, parameter JSON Schemas, workspace/search semantics, output bounds, ordering and truncation. Behavior changes alter Tool Registry fingerprint.

### Tool Policy

Only cross-ToolCall execution semantics. Historical L4 V1 baseline:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Current recommended forward L4 treatment:

```text
call_mode = batch
execution_mode = parallel
multiple_calls = accept_independently
```

For Batch + Parallel, malformed/expected errors remain per-call; valid siblings execute concurrently; the Runtime waits for the batch barrier and appends ToolResults in the original model-authored call order before the next Model Decision. Duplicate calls are not deduplicated. No arbitrary ordinary ToolCall count cap is imposed. One N-call Model Decision still consumes one `max_steps` unit.

Tool availability is defined by Tool Registry; do not duplicate a second allowlist in Tool Policy. Historical single/sequential and recommended Batch + Parallel remain distinct frozen Treatment identities so results stay attributable.

### Tool bounds

- shared ToolResult hard cap: 50 KiB text;
- `read`: max 2000 lines/call, 1-based offset, explicit continuation;
- `grep`: max 100 matches, 500 chars per emitted source line;
- `find`: max 1000 results;
- `ls`: max 500 entries, one level, deterministic alphabetical order, dotfiles included, dirs `/` suffixed;
- `grep/find/ls` do not re-apply `.gitignore` beyond frozen workspace membership.

### Agent step

One `step` = one successfully returned provider completion that normalizes into a valid `AssistantMessage` Model Decision.

Failed provider/transport attempts do not consume steps.

Hard V1 Agent limit:

```text
max_steps = 100
```

No cumulative token hard budget, no new sample wall-clock hard budget, and no automatic compaction baseline.

### Tool/action recovery

Recoverable Agent-visible errors return `ToolResult(is_error=True)` and allow another Model Decision:

- unknown/disallowed tool;
- invalid schema arguments;
- malformed raw argument JSON;
- expected tool/domain errors;
- `length + ToolCall` — execute none;
- multiple ToolCalls under historical `single` policy — execute none, error result per call ID;
- under Batch + Parallel, one malformed/expected-error call does not cancel otherwise valid siblings.

Unexpected Runtime/workspace/tool implementation exceptions are infrastructure failures, not Agent observations. In Batch + Parallel, an unexpected worker/runtime defect fails the Sample after the barrier; partial sibling ToolResults are not fed back to the model.

### Terminal taxonomy

`SampleResult.status` remains:

```text
scored | execution_failed
```

Scored capability terminals:

- `report_submitted`;
- `model_stopped_without_valid_report`;
- `max_steps_exhausted`.

Execution failures include exhausted provider-request infrastructure failure, malformed provider envelopes, unexpected Runtime/workspace/tool defects, and evaluator/scorer/persistence infrastructure defects.

Under ADR 0129, L4 has no mandatory local exact-preflight terminal. A real provider context-limit rejection is observed through the provider/execution failure path.

## Provider-neutral message contract

L4 uses typed messages, not provider wire dictionaries:

```text
UserMessage
AssistantMessage
  content[]:
    TextContent
    ThinkingContent
    ToolCall
ToolResultMessage
```

`ToolCall` preserves strictly parsed `arguments` when valid and raw provider/model `raw_arguments` when available. Malformed JSON is therefore a measurable model action rather than something the Runtime silently repairs.

`AssistantMessage` carries normalized response/usage/stop metadata plus opaque adapter-owned `provider_fields` for continuation. Runtime must not interpret provider-specific continuation state.

Successful `CompletionProvider.complete()` returns `AssistantMessage` directly. Provider infrastructure failures before a valid Model Decision raise typed provider errors.

## MiniMax route and context accounting

L4 V1 uses:

```text
DevAgentOps
    -> MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

MiniMax-specific `tool_calls`, `reasoning_content`, `reasoning_details`, `base_resp` and wire serialization stay inside `MiniMaxProvider`.

ADR 0129 defines the L4 context-accounting boundary:

- Runtime does **not** call `count_input_tokens()` as a mandatory gate before each L4 Model Decision;
- successful `AssistantMessage.usage.input_tokens` is the per-step observed input-token source;
- L4 sample result records `assessment=provider_reported`, `method=provider_response_usage`, and `local_preflight=false`;
- configured context-window metadata remains Treatment identity;
- no compaction/summarization/history trimming is performed in V1;
- L1/L2/Oracle retain their existing exact-token paths; L3 uses its frozen L1-style exact-token preflight.

The historical L4 formal milestone observed a maximum provider-reported request of `98,893` input tokens, far below the configured 1M context metadata; no real context-limit rejection occurred.

## Request retry

Request retry is infrastructure handling, not whole-sample retry and not Agent behavior.

- ordinary transient errors: initial attempt + up to 3 retries, backoff 2s/4s/8s;
- request timeout: at most one retry;
- auth/billing/invalid request/context-token limit/deterministic config or protocol error/policy block/abort: no same-request retry;
- SDK/provider hidden retries remain 0;
- failed attempts do not enter trajectory or consume `max_steps`;
- exhausted retry -> `execution_failed / provider_request_failed`.

The same logical request must preserve model/system/tools/messages/reasoning/generation exactly.

The historical formal L4 run exercised both paths: one transient 529 recovered on retry, and one 529 sequence exhausted all four attempts and remained visible as the sole execution failure. The initial Batch + Parallel formal run also exercised a real 600-second provider timeout followed by successful same-request retry; the replication block had no provider retry failures.

## Trace vs Agent Trajectory

### Run Trace

Structured execution/event record:

- model request attempts;
- provider usage / latency / response IDs;
- tool-call lifecycle;
- truncation metadata;
- budgets/terminal reasons;
- failures/evaluation lifecycle.

Trace is **not** the complete conversation store.

### Agent Trajectory

Complete ordered per-sample conversation:

```text
UserMessage
AssistantMessage
ToolResultMessage
...
```

It includes finalized assistant text, provider-returned thinking, ToolCalls and opaque continuation fields needed for replay/badcase analysis.

Provider-exposed thinking is diagnostic trajectory evidence only: it is not deterministic score input and not claimed to be faithful hidden neural computation.

## Prompt / Treatment identity

Shared diagnosis Task Contract remains Runtime-neutral.

L4-specific system instructions for tools/loop/stopping/report semantics are a separate frozen `prompt` component referenced as `contracts.runtime_control`.

L4 Treatment Registry-validates:

- shared Task prompt;
- Runtime-control prompt;
- Tool Registry;
- Tool Policy.

The historical `l4-react-runtime-control-v1` + `l4-single-sequential-tool-policy-v1` pair and the recommended `l4-react-runtime-control-batch-parallel-v1` + `l4-batch-parallel-tool-policy-v1` pair remain independently frozen. Mixed/unknown pairs are invalid Treatment identities.

Do not add a `runtime` Component type; Runtime implementation provenance remains `runtime_variant + code_revision`.

Shared Evidence Reference Canonicalization is implemented at the final report/output-realization boundary, not as a new `runtime_variant`. The canonicalized L1/L2/L3/Oracle/L4 matrices use output contract `development-v2` with resolver identity `canonical-line-range-normalization-v1`, while historical matrices remain unchanged.

## Matrix v2

Active formal condition shape:

```text
id
type
runtime_variant
suite
evaluation_method
treatment
execution_policy
```

Treatment contains provider/model/reasoning/generation/contracts/context. Execution Policy contains repeat count, case concurrency, retry count, and request timeout.

For L4, `execution_policy.retry_count` is interpreted as provider-request retry count by the L4 execution path; it must never mean whole-sample replay.

Recommended new L4 evaluation uses `evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json`. The single/sequential canonicalized matrix remains available as a historical/fresh controlled reference and is not rewritten.

Legacy Defaults/`extends` Matrix v1 remains historical compatibility, not the current L4 template.

## Oracle and Realization Gap

Oracle Evidence is implemented and has a preserved 20×3 MiniMax-M3 historical formal milestone. It supplies reviewed Required Evidence source content while hiding labels/answers, thereby bypassing ordinary discovery.

L4 is different: it receives the broad physical workspace + neutral citation vocabulary and must discover facts itself.

Oracle↔L4 Pair Analysis is complete. The Pair Analyzer performs deterministic alignment, aggregate comparison, and evidence packaging; Human/AI review interpreted the 15 detailed Cases. The observed gap decomposed into at least:

```text
Canonical reference / report realization
Investigation depth / evidence acquisition
Evidence selection
Causal reasoning
Operational execution reliability
```

Important positive counterexamples also exist: `github-osquery-issue-7718` showed historical L4 taxonomy `3/3` versus Oracle `0/3`, demonstrating that autonomous investigation can add real causal-diagnosis value rather than merely approximating Oracle evidence delivery.

The canonical reference/report-realization slice identified by Pair Analysis has now been addressed and measured. Offline replay is the causal isolation result; fresh four-condition generation is the operational confirmation. Do not reinterpret historical Oracle/L4 pair metrics as if they already included the new normalization behavior.

## Current next work / evidence-gated work

Completed and no longer current work:

- shared deterministic Evidence Reference Canonicalization implementation;
- historical L1/L2/Oracle/L4 offline replay;
- fresh canonicalized L1/L2/Oracle/L4 `20×3` formal generation;
- L4 Batch + Parallel Tool Policy implementation, initial formal run, and fresh single/sequential vs Batch + Parallel replication.
- L3 Static Retrieval V1 implementation, live `20×3` qualification, and acquisition-vs-report evidence analysis.

Current recommended L4 state:

```text
historical reference
single + sequential + reject-all

recommended forward treatment
batch + parallel + independent-call handling
```

The Batch result does not justify arbitrary call-count caps, forced-batching prompt language, scheduler heuristics, or output repair. Evidence Precision / Citation Specificity remains a separate evaluator question only if broad over-citation proves material; do not encode arbitrary width heuristics in the canonicalizer.

Next large capability direction:

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

This is executable repair / sandboxed remediation after the read-only V1 boundary. It should reuse the L4 Runtime kernel without silently mutating historical L4 Treatment identities.

Still evidence-gated / deferred:

- L3 retrieval optimization or new retrieval quality metrics; any tuning requires a separate calibration/dev set and a new frozen Treatment rather than hidden-Ground-Truth tuning on `triage-suite-v1`;
- compaction / summarization / history trimming;
- predictive context budgeting;
- planner/verifier/reflection unless repair-loop evidence requires it;
- multi-agent / subagents;
- memory / skills / MCP;
- read byte/column slicing for oversized single lines.

Do not mix these deferred capabilities into the repair/sandbox work without new evidence.

## Current source-of-truth order

When sources disagree, use:

1. `docs/adr/README.md` Active ADR index;
2. current `README.md` / `CONTEXT.md` and active evaluation methodology;
3. ADR 0128 for the frozen base L4 V1 contract **plus ADR 0129 for the context-accounting amendment**;
4. current Matrix/Registry/source-code contracts;
5. `docs/evaluation/milestones/l3-static-retrieval-2026-08-24.md` for the completed L3 formal baseline and acquisition-vs-report diagnostic;
6. `docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md` for the current recommended Tool Policy decision and replication evidence;
7. `docs/evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md` for the completed canonicalization experiment;
8. `docs/evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md` for the historical Pair Analysis that motivated canonicalization;
9. `docs/evaluation/milestones/README.md` to classify dated milestone status;
10. other dated milestone/history only for historical facts.

Archived micro ADRs and old PR/Issue bodies must not override active/current decisions. Historical L4 V1 documents remain authoritative for their frozen baseline behavior, but they do not override the later explicit Batch + Parallel Treatment decision.
