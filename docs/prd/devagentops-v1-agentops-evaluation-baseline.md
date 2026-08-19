# PRD: DevAgentOps V1 AgentOps Evaluation Baseline

> Current-state revision: 2026-08-19. This PRD describes the current V1 product/evaluation boundary and delivered foundation. Oracle↔L4 Pair Analysis, shared deterministic Evidence Reference Canonicalization, fresh L1/L2/Oracle/L4 canonicalized generation, and the L4 Batch + Parallel Tool Policy experiment with replication are complete. Batch + Parallel is the recommended forward Tool Policy for new L4 evaluations; historical single/sequential contracts remain immutable references. Historical PRs, dated milestones and archived micro ADRs preserve earlier project states but do not override current-facing documents.

## 1. Problem Statement

DevAgentOps needs a reproducible CI/Test Failure Triage AgentOps system where Runtime behavior, evidence acquisition, model usage, Tool Policy, reports and badcases can be compared honestly across controlled conditions.

The system should answer questions such as:

- how does adaptive ReAct investigation differ from fixed model-backed conditions on the same failures?
- when an Agent fails, was decisive evidence never found, found but not cited correctly, or available but reasoned about incorrectly?
- did a Runtime/prompt/tool-policy change improve one quality dimension while degrading another?
- when Oracle Evidence is supplied, how much evidence-conditioned diagnosis capability is available, and how much does the real Agent System realize?
- are apparent failures Agent capability outcomes or provider/Runtime/evaluation infrastructure failures?
- can a result be reproduced from frozen Case/Suite/Component identity plus execution code revision?
- can deterministic output-representation defects be separated from evidence acquisition and reasoning defects?
- what quality/resource tradeoff is paid by more adaptive Runtime behavior?

## 2. V1 Product Boundary

V1 Product Runtimes are limited to:

1. deterministic Fixed Pipeline (`runtime_variant="pipeline_baseline"` historically);
2. L4 self-built ReAct (`runtime_variant="self_built_react"`).

L1 Full-context One-shot, L2 Fixed Model Workflow and optional L3 Static Retrieval are diagnostic/comparison conditions, not Product Runtimes. Oracle Evidence is an orthogonal evaluator intervention.

V1 remains diagnosis-only. It does not edit code, run tests, rerun CI, create PRs, deploy, or otherwise mutate the development workflow.

## 3. Delivered Foundation

As of 2026-08-19, the following foundation is implemented:

- Offline Case Schema V2 with Physical / Canonical / Evaluator separation;
- frozen `triage-suite-v1`, exactly 20 Human-reviewed Cases and 4 Cases per V1 Failure Type;
- frozen Canonicalization Profile v1;
- Structured Triage Report V1 and deterministic scorer;
- Evaluation Matrix v2;
- Treatment, Condition, Execution Policy and Run Configuration identities;
- Component Registry / frozen Component fingerprints;
- doctor-first formal preflight;
- repeated-Sample execution engine and bounded cross-Case concurrency;
- Case-first Suite / Failure-Type aggregation;
- SQLite persistence, Trace, JSON/Markdown artifacts;
- sample-scoped complete Agent trajectory persistence;
- provider-neutral typed completion/message contracts;
- MiniMax-M3 adapter with native ToolCall and continuation support;
- historical L1/L2/Oracle/L4 full-Suite formal milestones;
- L4 self-built ReAct implementation, deterministic tests and live qualification;
- ADR 0129 provider-reported L4 context accounting;
- Oracle↔L4 Pair Analyzer and real pair analysis covering all 20 Cases with 15 Detailed Review Cases;
- shared deterministic Evidence Reference Canonicalization (`canonical-line-range-normalization-v1`) with historical offline replay and fresh L1/L2/Oracle/L4 `20×3` generation;
- L4 Batch + Parallel ToolCalls implementation with frozen Runtime-control / Tool Policy identities;
- Batch + Parallel deterministic gates: `29 passed`, formal doctor PASS, full regression `377 passed, 2 skipped, 30 subtests passed`;
- initial Batch + Parallel `20×3` formal run and a fresh back-to-back single/sequential vs Batch + Parallel replication block.

Historical L4 Suite metrics remain immutable evidence:

```text
Execution Coverage            98.33%
Failure Type Exact Match      88.33%
Evidence Hit Rate             65.51%
Required Fields Completeness  96.67%
Protocol Validity             81.36%
```

Fresh canonicalized L4 generation produced:

```text
Execution Coverage            100.00%
Failure Type Exact Match       81.67%
Evidence Hit Rate              71.83%
Required Fields Completeness   99.58%
Protocol Validity              93.33%
```

The Batch + Parallel replication compared a fresh single/sequential reference to Batch + Parallel on the same Suite and code revision:

```text
Model Decisions       877 -> 571   (-34.89%)
Executed ToolCalls     809 -> 775   (-4.20%)
Wall time            978.27s -> 806.69s (-17.54%)
Taxonomy              71.67% -> 75.00%
Evidence              74.64% -> 73.50%
Required Fields       93.33% -> 98.13%
Protocol              93.33% -> 91.67%
```

The initial Batch quality drop did not reproduce, while the Model Decision reduction reproduced across both fresh Batch runs (`798 -> 547`, then `877 -> 571`). Current evidence therefore supports Batch + Parallel as the recommended forward L4 Tool Policy without demonstrating a material diagnosis-quality regression.

Historical L4 is recorded in [L4 MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md). Current Batch decision and replication are recorded in [L4 Batch + Parallel ToolCalls Milestone](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md). Dated milestone status is indexed in [Milestone Status Index](../evaluation/milestones/README.md).

## 4. Runtime Capability Ladder

```text
L0 deterministic pipeline
    -> L1 full-context one-shot
    -> L2 fixed model workflow
    -> L3 static retrieval
    -> L4 self-built ReAct
    -> L5+ incremental Agent capabilities
```

The ladder is a capability-attribution model, not a mandatory implementation sequence. L3 does not block L4 or evidence-driven L5+ work.

| Level | Role | Current state |
| --- | --- | --- |
| L0 | deterministic Product Runtime baseline | implemented |
| L1 | one-shot diagnostic/comparison condition | historical milestone + canonicalized fresh generation complete |
| L2 | fixed multi-stage diagnostic/comparison condition | historical milestone + canonicalized fresh generation complete |
| L3 | static-retrieval diagnostic | optional; not implemented |
| L4 | first Agentic Product Runtime | **historical/fresh milestones + Batch/Parallel replication complete; Batch + Parallel recommended forward** |
| Oracle | orthogonal evidence-conditioned diagnostic | historical milestone + canonicalized fresh generation complete |

## 5. Core Evaluation Requirements

### 5.1 Reproducibility

Formal evaluation requires:

- immutable Suite/Case identities;
- explicit Matrix conditions;
- versioned/fingerprinted behavior-affecting Components/contracts;
- recorded code revision / dirty state;
- explicit Execution Policy;
- repeatable Sample identity and Case-first aggregation;
- formal/debug separation;
- no hidden or unversioned report repair, regeneration or retries.

Deterministic Evidence Reference Canonicalization is allowed only as an explicit shared output-realization behavior with recorded identity. Historical runs that did not have it remain historical and are never retroactively rewritten.

Likewise, Batch + Parallel is a distinct L4 Treatment identity. Historical single/sequential Runtime-control / Tool Policy components, matrices, fingerprints, and results remain unchanged.

### 5.2 Agent observability

The system preserves both:

```text
Run Trace
= execution events / attempts / timing / usage / tool lifecycle / terminal & failure metadata

Agent Trajectory
= complete ordered per-sample User / Assistant / ToolResult message history
```

Trace must remain an operational event record, not a duplicate transcript store.

Provider-returned thinking/reasoning may be persisted in Agent trajectory for diagnostic analysis. It is not deterministic score input and is not claimed to expose faithful hidden neural computation.

### 5.3 Evidence-grounded diagnosis

Reports cite stable Canonical Evidence IDs and are scored against hidden Human-reviewed Ground Truth without exposing evaluator labels to the normal Agent.

```text
Physical Artifacts       -> sole facts
Canonical Evidence       -> answer-neutral coordinates
Required Evidence        -> hidden Evidence Ground Truth
Expected Answer          -> hidden Diagnosis Ground Truth
```

Final-report representation normalization may map a model-authored explicit line range with a matching frozen source identity to the overlapping Canonical unit(s), but must not use Required Evidence, Expected Answer, fuzzy semantic matching, or diagnosis-aware evidence selection.

### 5.4 Controlled safety

V1 Agent actions are diagnosis-only and read-oriented. Mutation behavior remains forbidden.

L4 executable Tool Registry contains only `read`, `grep`, `find`, `ls`. Final report submission is a semantic Runtime terminal, not a native mutation/report tool.

## 6. Formal Case / Evidence Contract

A Formal Case V2 contains:

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/...
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

The Evidence Universe is authentic, frozen, offline and bounded-but-realistic. It preserves natural neighboring information rather than being curator-reduced to only Required Evidence.

Project Knowledge is not part of the current Formal Case Physical Universe and may enter later only as an independently versioned Runtime/Retrieval Treatment.

## 7. L4 Self-built ReAct Product Contract

L4 is the first Agentic Product Runtime and the baseline kernel for future self-built Runtime evolution.

```text
Model Decision
    -> Runtime validates action / schema / Tool Policy / budget
    -> optional read-only Tool execution
    -> ToolResult observation
    -> authoritative typed message-state update
    -> next Model Decision or terminal report
```

The model chooses what to investigate next; Runtime owns execution authority, policy, budgets, persistence, Trace and forced stop.

### 7.1 Provider-neutral conversation

Canonical L4 messages:

```text
UserMessage
AssistantMessage
  -> TextContent | ThinkingContent | ToolCall
ToolResultMessage
```

`ToolCall` preserves parsed arguments when valid and raw provider/model argument text when available. Malformed argument JSON remains measurable model behavior rather than being silently repaired.

Successful `CompletionProvider.complete()` returns an `AssistantMessage`. Provider failures before a valid Model Decision raise typed provider errors.

### 7.2 Native tools and workspace

L4 V1 exposes exactly:

```text
read
grep
find
ls
```

Agent-visible workspace:

```text
/raw.log
/repository/...
```

No Bash/edit/write/test/CI tool exists in V1.

Repository manifest metadata, Canonical Evidence files, evaluator directories and other package internals are not tool-readable.

`submit_report` is **not** a native provider tool. An AssistantMessage with 0 ToolCalls attempts to terminate; its visible text is parsed as Structured Triage Report V1.

### 7.3 Canonical citation vocabulary and output normalization

Historical L4 V1 model-visible input includes the complete **answer-neutral Canonical coordinate vocabulary** for citation.

It does not disclose Physical Artifact content, Required/Optional labels, which coordinates matter, Expected Answer, or evaluator reasoning/metadata. The Agent must still discover physical facts through tools and choose which facts support its report.

The historical L4 run produced a concentrated unknown-ID failure class even after useful investigation. Pair Analysis superseded the earlier L4-only helper idea. Shared deterministic Evidence Reference Canonicalization is now implemented for L1/L2/Oracle/L4:

```text
exact Canonical ID
    -> preserve

matching frozen source identity + explicit line range
    -> deterministic physical-overlap mapping
    -> stable deduplication

unresolvable
    -> remain invalid
```

The resolver normalizes representation only. It does not choose evidence semantically and does not inspect Required Evidence / Expected Answer.

### 7.4 Tool Registry / Tool Policy

Tool Registry freezes provider-visible Tool contracts and deterministic ToolResult behavior: names, descriptions, parameter schemas, workspace/search semantics, ordering, bounds and truncation/continuation behavior.

Tool Policy freezes cross-call execution semantics.

Historical reference:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Recommended forward L4 Treatment:

```text
call_mode = batch
execution_mode = parallel
multiple_calls = accept_independently
```

Batch + Parallel semantics:

- zero, one, or multiple ToolCalls per Model Decision;
- no arbitrary ordinary-call count cap;
- malformed / expected tool errors isolated per call;
- valid siblings execute concurrently;
- duplicate calls are not deduplicated;
- barrier before the next Model Decision;
- ToolResults appended in original model-authored ToolCall order;
- one N-call Model Decision still consumes one step;
- unexpected Runtime/workspace/tool implementation defects remain Sample-level infrastructure failures;
- `stop_reason=length` executes none of the returned calls;
- the Runtime-control prompt exposes batching neutrally and does not tell the model to prefer it.

Tool availability comes from Tool Registry; Tool Policy does not duplicate a second allowlist. Historical single/sequential and Batch + Parallel remain distinct frozen Treatment identities.

### 7.5 Tool output bounds

- shared ToolResult text hard cap: 50 KiB;
- `read`: max 2000 lines, 1-based pagination;
- `grep`: max 100 matches, max 500 chars per emitted source line;
- `find`: max 1000 results;
- `ls`: max 500 entries, one level, alphabetical, dotfiles included, dirs suffixed `/`;
- `grep/find/ls` operate over frozen workspace membership and do not re-apply `.gitignore`.

Truncation is model-visible and Trace-visible.

### 7.6 Budget and stop

L4 V1 hard Agent budget:

```text
max_steps = 100
```

One step is one successful provider completion normalized into a valid `AssistantMessage` Model Decision. Failed provider attempts do not consume steps. A Batch decision with N ToolCalls still consumes one step.

Decision #100 may execute valid ToolAction(s), but no #101 Model Decision is requested.

V1 does not add a cumulative token hard budget, new sample wall-clock hard budget, forced finalization call, or automatic compaction.

### 7.7 Recoverable action errors

Recoverable model/tool-use errors become Agent-visible error ToolResults and allow another Model Decision:

- unknown/disallowed tool;
- malformed/invalid arguments;
- expected tool-domain error;
- `length + ToolCall`;
- multiple calls under historical `single` policy.

Under Batch + Parallel, malformed/expected-error calls do not cancel valid siblings. Runtime does not semantically repair malformed model ToolCall arguments. Unexpected Runtime/workspace/tool implementation exceptions remain infrastructure failures; partial sibling ToolResults are not fed back to the model after such a failure.

### 7.8 Terminal/sample semantics

`SampleResult.status` remains:

```text
scored | execution_failed
```

Scored capability terminals:

- `report_submitted`;
- `model_stopped_without_valid_report`;
- `max_steps_exhausted`.

Execution failures are reserved for infrastructure conditions such as exhausted provider-request failure, malformed provider envelope, unexpected Runtime/workspace/tool defect, or evaluation/persistence defect.

Report invalidity after a valid execution opportunity is a scored capability observation unless an explicitly versioned deterministic output-normalization rule resolves the representation before validation.

## 8. MiniMax Provider Route

L4 uses:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

Provider-specific ToolCalls, `reasoning_content`, `reasoning_details`, status envelopes and continuation fields remain adapter-owned opaque state from the Runtime perspective.

The OpenAI-compatible transport is one-attempt infrastructure; provider-request retry is owned by the Runtime/provider execution layer above it.

## 9. Context Accounting

### L4

ADR 0129 supersedes the original ADR 0128 mandatory local exact-preflight requirement for L4.

L4 Runtime behavior:

```text
step-budget check
    -> build LogicalCompletionRequest
    -> execute provider request
    -> successful AssistantMessage.usage
    -> record provider-reported input usage
```

Current Treatment context identity:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L4 does not compact, summarize or trim history automatically. A real provider context-limit rejection is observed through provider/execution evidence.

### L1/L2/Oracle

ADR 0129 does not change their existing exact-token behavior. Condition-specific exact preflight remains where already defined.

## 10. Provider-request Retry

L4 request retry is infrastructure handling for the **same logical Model Decision**, not whole-sample restart.

- ordinary transient errors: initial attempt + up to 3 retries, 2s/4s/8s backoff;
- request timeout: at most 1 retry;
- auth/billing/invalid request/context-token limit/deterministic protocol or config error/policy block/abort: no same-request retry;
- SDK/provider hidden retries remain disabled;
- failed attempts are Trace events only, do not enter trajectory and do not consume Agent steps;
- exhausted request retry -> `execution_failed / provider_request_failed`.

Historical L4 exercised retry recovery and retry exhaustion against real provider HTTP 529 responses. The initial Batch + Parallel formal run exercised a real 600-second timeout followed by successful same-request retry; the replication had no provider retry failure.

## 11. Matrix v2 / Treatment Requirements

New Formal conditions use Matrix v2:

```text
id
type
runtime_variant
suite
evaluation_method
treatment
execution_policy
```

L4 Treatment references and Registry-validates:

- shared Task Contract prompt;
- separate L4 Runtime-control prompt;
- Tool Registry;
- Tool Policy;
- provider/model/reasoning/generation/context contracts.

Runtime implementation itself is not a Component Registry type; implementation provenance remains `runtime_variant + code_revision`.

For L4, current `execution_policy.retry_count` means provider-request retry count. It must never silently become whole-sample retry.

Shared Evidence Reference Canonicalization is not a new `runtime_variant`; it belongs to explicit shared output-realization identity.

Recommended new L4 evaluations use `evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json`. The canonicalized single/sequential Matrix remains available for controlled historical/fresh comparison and is not rewritten.

## 12. Oracle Evidence and completed Realization Gap analysis

Oracle Evidence is implemented and formally evaluated. It supplies Human-reviewed Required Evidence source content while withholding labels/answers, thereby removing ordinary evidence-discovery difficulty.

Oracle is not L4 and not a Product Runtime. It is not a theoretical upper bound on every metric.

Oracle↔L4 Pair Analysis is implemented and complete. It validates comparable formal identities, uses Case aggregate as the primary comparison unit, keeps Oracle/L4 repeats independent rather than repeat-index paired, and exposes deterministic comparison/evidence packages for Human/AI review.

For higher-is-better metric `m`:

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Do not collapse the metric vector into one composite capability score.

Human/AI review found multiple mechanisms:

```text
Canonical reference / report realization
Investigation depth / evidence acquisition
Evidence selection
Causal reasoning
Operational execution reliability
```

The analysis also found clear adaptive L4 wins, so current evolution preserves autonomous investigation rather than replacing it with Oracle-style evidence delivery.

## 13. Current Empirical Findings and next controlled work

The evidence-driven sequence now completed is:

```text
Oracle↔L4 Pair Analysis
    -> shared deterministic Evidence Reference Canonicalization
    -> historical L1/L2/Oracle/L4 offline replay
    -> fresh L1/L2/Oracle/L4 20×3 generation
    -> separate L4 Batch + Parallel Tool Policy
    -> fresh back-to-back single/sequential vs Batch replication
```

Batch experiment conclusions:

- Model Decision reduction reproduced across both fresh Batch runs, about `31–35%`;
- clean replication reduced run wall time `17.54%` and p50/p95 Sample latency about `27–28%`;
- executed ToolCalls changed only `809 -> 775`, so the speedup is not explained by abandoning investigation;
- the initial apparent taxonomy/required-field regression did not reproduce and reversed direction in replication;
- paired 20-Case diagnostic intervals span zero for taxonomy, Evidence Hit, Required Fields and Protocol Validity;
- Evidence Hit and Protocol remain small residual signals to monitor, not demonstrated material regressions;
- no arbitrary batch cap, forced-batching prompt, output repair, or scheduler heuristic is justified.

Therefore Batch + Parallel is the recommended forward L4 Tool Policy for new evaluations/Runtime evolution. Historical single/sequential remains an immutable reference.

The next large Product Runtime capability direction is **executable repair / sandboxed remediation**:

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

That work is outside the current read-only V1 boundary and must be introduced as an explicit new stage rather than silently mutating historical L4 contracts.

## 14. V1 Non-goals

- code edits / patch generation / CI reruns / PR creation / deployment;
- L4 V1 Bash or mutation tools;
- planner/verifier/reflection baseline without evidence;
- multi-agent / subagents;
- cross-run memory;
- MCP/skills as required V1 Runtime capabilities;
- OS-level sandbox in the read-only V1 phase;
- automatic context compaction without evidence;
- external observability products as source of truth;
- composite overall capability score;
- model training / automatic post-training loop.

The planned repair/sandbox stage intentionally crosses some V1 non-goals, but it will do so as a separately designed post-V1 capability phase rather than by redefining what the completed read-only V1 milestone meant.

## 15. Source-of-truth order

When earlier PRD wording conflicts with current implementation/architecture, use:

1. [Active ADR Index](../adr/README.md);
2. root [README](../../README.md) and [CONTEXT](../../CONTEXT.md) for current orientation;
3. [Formal Evaluation Methodology](../evaluation/formal-evaluation-methodology.md);
4. [Evaluation Matrix & Component Registry](../evaluation/evaluation-matrix-and-component-registry.md);
5. [ADR 0128](../adr/0128-l4-self-built-react-runtime-contract.md) for the frozen historical L4 V1 contract together with [ADR 0129](../adr/0129-l4-provider-reported-context-accounting.md) for L4 context accounting;
6. current Matrix/Registry/source contracts;
7. [L4 Batch + Parallel ToolCalls Milestone](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) for the current Tool Policy recommendation and replication evidence;
8. [Shared Evidence Reference Canonicalization Milestone](../evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md) for the completed shared output-resolution decision;
9. [Oracle ↔ L4 Pair Analysis Findings](../evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md) for the historical badcase-driven decision input;
10. [Milestone Status Index](../evaluation/milestones/README.md) before using other dated milestone docs;
11. other dated milestone docs for immutable historical experiment evidence.

Dated milestone forward-looking recommendations may be superseded. Their measured artifacts, fingerprints, metrics and run identities remain historical evidence and must not be rewritten to look current.