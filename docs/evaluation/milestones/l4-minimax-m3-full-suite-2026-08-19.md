# L4 MiniMax-M3 Full-Suite Milestone — 2026-08-19

## Overview

This document records the first formal full-Suite L4 development-treatment
milestone for DevAgentOps.

L4 is the first Agentic Product Runtime in the capability ladder. The evaluated
condition uses the self-built ReAct Runtime to let MiniMax-M3 adaptively inspect
one frozen Case workspace through bounded read-only tools:

```text
Case / Canonical citation universe
  -> Model Decision
  -> optional read / grep / find / ls
  -> bounded ToolResult
  -> full typed conversation replay
  -> next Model Decision
  -> Structured Triage Report V1 or scored capability terminal
```

The Runtime, rather than the model, owns execution authority, Tool Policy,
step budget, retry behavior, state updates, terminal interpretation, Trace, and
formal evaluation integration.

This milestone follows ADR 0128 and the ADR 0129 Human amendment. ADR 0129
removes mandatory local exact-token preflight from the L4 critical path and
uses provider-reported usage as the authoritative observation for completed
requests. L1/L2/Oracle token-accounting behavior is unchanged.

This is a development milestone, not a final benchmark freeze and not a
leaderboard result.

## Experiment Identity

- Run ID: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`
- Execution code revision: `3fea80981fdc27ab134ceee6427e61135a506999`
- Git dirty at execution: `false`
- Suite: `triage-suite-v1`
- Suite version: `1`
- Model: `MiniMax-M3`
- Provider: `minimax-official`
- Runtime variant: `self_built_react`
- Experiment identity: `l4-self-built-react-development`
- Condition: `l4-minimax-m3-adaptive-development-v1`
- Cases: `20`
- Repeats per Case: `3`
- Planned Samples: `60`
- Maximum cross-Case concurrency: `6`
- Provider-request retry count: `3`
- Request timeout: `600 s`

### Fingerprints

- Suite: `b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Treatment: `612c58a36df42c316e7d3908721f87a6b29104215989201b1c65843c7bfe084f`
- Condition: `4a0cf08eb0a6d770d40547e07d98227e8950a708c7271ea9b99063f6119fd507`
- Execution Policy: `14e21cd921a1729991f83aa83ce3c9ba8f4603526c3782181255886bbf30461a`
- Run Configuration: `269f8fef6f073f23f885d45b8891f1f38e1e347bcf892f88a8081a04dc9440f1`

The formal JSON artifact uploaded for Human Review has SHA256:

`a2cc05a7f6258db5face6d4740da554149a36f2ef24fa35e88193ddea9fdd217`

The ignored local formal bundle was written under:

`.devagentops/l4-formal-20x3-artifacts/dd8ca829-5051-43b6-a0c2-b3c2889acae0/`

## Deterministic and Live Gates

Before this formal Run, the implementation passed:

- targeted Issue #52 tests: `37 passed`
- full repository suite: `361 passed, 2 skipped`
- `git diff --check`

A real MiniMax-M3 qualification Case then exercised the L4 Agent loop before
the full-Suite milestone.

Qualification observations included:

- `9` Model Decisions / provider requests
- `8` native ToolCalls
- `8` successful ToolResults
- `reasoning_details` observed and replayed across all continuations
- provider-reported input-token usage recorded for every successful Model Decision
- no evaluator leakage marker in the initial Agent input
- ToolCall continuation preserved protocol-significant `id`, `type`,
  `function.name`, and raw `function.arguments`

The qualification's final report was protocol-invalid because the model
invented an unavailable Evidence ID. That was treated as a scored model /
Evidence-coordinate mapping badcase rather than as an infrastructure failure.

Qualification verdict: **PASS**

## Formal Execution

- Planned Samples: `60`
- Scored Samples: `59`
- Execution failures: `1`
- Execution coverage: `98.33%`
- Suite quality status: `complete`
- Model-call attempts started: `807`
- Successful Model Decisions: `802`
- Failed provider attempts: `5`
- Run wall-clock time: approximately `35m00.8s`
- Maximum configured cross-Case concurrency: `6`

The formal runner completed the full 60-Sample plan without a run-level crash.
No Sample reached `max_steps_exhausted`.

### Single execution failure

The only execution failure was:

- Case: `bugswarm-pygithub-36442425251`
- Repeat: `2`
- Failure code: `provider_request_failed`
- Failure stage: `model_provider`
- Agent steps completed: `0`
- Provider request attempts: `4`

All four attempts for the first logical Model Decision returned HTTP `529`.
The Runtime applied the frozen same-logical-request retry policy and exhausted
the initial attempt plus three retries. The other two repeats of the same Case
completed and were scored successfully.

A second transient `529` occurred on
`bugswarm-spring-hateoas-232784946`, repeat `0`, but the next same-request
attempt succeeded. The combination of these observations is consistent with a
transient provider operational failure rather than a deterministic Case or
Runtime defect.

The retry behavior therefore received real hosted-provider coverage during the
formal milestone.

## Runtime / Tool Operational Observations

The Trace records substantial real adaptive tool use:

| Tool | Executed calls started |
|---|---:|
| `read` | `472` |
| `grep` | `203` |
| `ls` | `38` |
| `find` | `20` |
| **Total** | **`733`** |

Tool error / recovery events:

| Recovery class | Count |
|---|---:|
| `multiple_tool_calls_rejected` | `26` ToolCall IDs |
| `schema_invalid_arguments` | `13` |
| `path_not_found` | `2` |

These remained Agent-visible recoverable action errors rather than becoming
infrastructure failures.

`283` completed ToolResults were marked truncated by the bounded ToolResult
implementation:

- `read`: `240`
- `grep`: `43`

The formal milestone therefore exercised the output-bounding path extensively,
not only the happy path.

## Agent-Step and Context Observations

Among the `59` scored Samples:

- minimum Agent steps: `4`
- median Agent steps: `10`
- mean Agent steps: `13.59`
- p95 Agent steps: `28`
- maximum Agent steps: `52`
- maximum provider-reported input tokens on any completed Model Decision:
  `98,893`

The largest observed request remained far below the configured `1,000,000`
context-window metadata. No real context-limit rejection occurred.

This formal evidence supports the ADR 0129 V1 choice to keep mandatory local
exact-token reconstruction out of the L4 critical path. It does not establish
that context management will never be needed; it shows only that this baseline
milestone did not approach the configured context boundary.

## Provider Token Observations

Across the `802` successful Model Decisions recorded in Trace:

- prompt tokens: `24,720,712`
- completion tokens: `328,447`
- total tokens: `25,049,159`
- cached prompt tokens: `22,543,162`
- provider-reported reasoning tokens: `181,472`

Approximately `91.2%` of successful-call prompt tokens were reported as cached.
These token observations are operational diagnostics and do not participate in
quality aggregation.

## Final Output Protocol

Among the `59` scored Samples:

- protocol-valid Samples: `48`
- protocol-invalid Samples: `11`
- protocol validity: `81.36%`
- `report_submitted`: `48`
- `model_stopped_without_valid_report`: `11`

The 11 invalid reports contained the following validation errors:

- `12` `unknown_evidence_id` errors across `8` Samples
- `2` `invalid_report_type` errors
- `1` `duplicate_evidence_reference` error

The dominant L4 protocol failure mode is therefore not failure to investigate
or failure to classify. It is the model inventing a citation coordinate from a
physical span it actually inspected, instead of selecting an exact ID from the
frozen Canonical Evidence vocabulary.

Examples include invented IDs such as:

- `log:raw-log:lines-2300-2632`
- `log:raw-log:lines-20601-20718`
- `repo:httpannotationsendtoendtest-java:lines-0001-0159`

L4 V1 intentionally provides no dynamic physical-span -> Canonical Evidence-ID
mapping helper. These failures are therefore legitimate baseline observations,
not a reason to silently repair final reports.

No report repair, regeneration, Evidence-ID correction, or Human Review score
substitution was performed.

## Suite Diagnostic Metrics

Aggregation remains Case-first under the frozen evaluation method:

`Sample -> Case mean -> fixed-weight Failure Type / Suite aggregate`

| Metric | Value | Percentage |
|---|---:|---:|
| Execution Coverage | `0.983333` | `98.33%` |
| Failure Type Exact Match | `0.883333` | `88.33%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.655139` | `65.51%` |
| Required Fields Completeness | `0.966667` | `96.67%` |
| Protocol Validity | `0.813559` | `81.36%` |

The Suite quality status is `complete` with:

- quality Case coverage: `100.00%`
- quality Suite-weight coverage: `100.00%`

The one execution failure remains visible through execution coverage. The
frozen aggregation semantics are not replaced by Human renormalization.

## By Failure Type

### `test_assertion_failure`

- Execution coverage: `100.00%`
- Protocol validity: `75.00%`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Evidence Hit Rate | `0.431217` | `43.12%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

### `lint_or_type_failure`

- Execution coverage: `91.67%`
- Protocol validity among scored Samples: `100.00%`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Evidence Hit Rate | `0.906250` | `90.63%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

### `dependency_or_install_failure`

- Execution coverage: `100.00%`
- Protocol validity: `66.67%`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.916667` | `91.67%` |
| Evidence Hit Rate | `0.636111` | `63.61%` |
| Required Fields Completeness | `0.916667` | `91.67%` |

### `config_or_environment_failure`

- Execution coverage: `100.00%`
- Protocol validity: `75.00%`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.833333` | `83.33%` |
| Evidence Hit Rate | `0.633333` | `63.33%` |
| Required Fields Completeness | `0.916667` | `91.67%` |

### `timeout_or_flaky_failure`

- Execution coverage: `100.00%`
- Protocol validity: `91.67%`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.666667` | `66.67%` |
| Evidence Hit Rate | `0.668783` | `66.88%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

## Case-Level Taxonomy Stability

`14/20` Cases achieved exact taxonomy classification in every scored repeat.
The six non-perfect Cases were:

- `bugswarm-traccar-221926468`: `2/3` exact
- `bugswarm-traccar-166900445`: `2/3` exact
- `bugswarm-blueflood-80881330`: `2/3` exact
- `odrepair-dubbo-737f7a7e`: `2/3` exact
- `odrepair-remoting-abf0455a`: `0/3` exact
- `bugswarm-pygithub-36442425251`: `2/2` scored repeats exact, with repeat `2` lost to provider execution failure

The PyGithub Case has a Case aggregate exact-match value of `1.0` under the
frozen scored-repeat aggregation semantics; it is listed separately here
because execution coverage was only `2/3`.

## L1 / L2 / L4 / Oracle Comparison

The capability milestones use the same frozen 20-Case Suite and the same
MiniMax-M3 foundation model. Their Runtime/evidence-delivery Treatments differ
by design.

Oracle is an evaluator diagnostic intervention, not a capability-ladder rung,
so its results must not be interpreted as a Runtime that L4 is expected to
"beat" globally.

### Suite-Level Comparison

| Metric | L1 | L2 | L4 | Oracle |
|---|---:|---:|---:|---:|
| Execution Coverage | `100.00%` | `100.00%` | `98.33%` | `100.00%` |
| Failure Type Exact Match | `76.67%` | `85.00%` | `88.33%` | `85.00%` |
| Evidence Hit Rate | `51.38%` | `55.57%` | `65.51%` | `89.29%` |
| Required Fields Completeness | `96.67%` | `99.58%` | `96.67%` | `100.00%` |
| Protocol Validity | `96.67%` | `90.00%` | `81.36%` | `100.00%` |

Relative to L2, L4 changed the Suite metrics by:

- Failure Type Exact Match: `+3.33 pp`
- Evidence Hit Rate: `+9.95 pp`
- Required Fields Completeness: `-2.92 pp`
- Protocol Validity: `-8.64 pp`
- Execution Coverage: `-1.67 pp` because of one exhausted provider-529 retry sequence

The result is not a simple monotonic "more Agent = better" outcome. Adaptive
investigation improved evidence grounding and taxonomy on this Suite, while the
larger action/report surface exposed more citation/protocol failures.

### Failure-Type Exact Match

| Failure Type | L1 | L2 | L4 | Oracle |
|---|---:|---:|---:|---:|
| `test_assertion_failure` | `100.00%` | `100.00%` | `100.00%` | `100.00%` |
| `lint_or_type_failure` | `91.67%` | `100.00%` | `100.00%` | `100.00%` |
| `dependency_or_install_failure` | `83.33%` | `100.00%` | `91.67%` | `91.67%` |
| `config_or_environment_failure` | `66.67%` | `75.00%` | `83.33%` | `100.00%` |
| `timeout_or_flaky_failure` | `41.67%` | `50.00%` | `66.67%` | `33.33%` |

### Failure-Type Evidence Hit Rate

| Failure Type | L1 | L2 | L4 | Oracle |
|---|---:|---:|---:|---:|
| `test_assertion_failure` | `46.16%` | `43.52%` | `43.12%` | `84.79%` |
| `lint_or_type_failure` | `45.14%` | `54.17%` | `90.63%` | `91.67%` |
| `dependency_or_install_failure` | `46.25%` | `44.72%` | `63.61%` | `100.00%` |
| `config_or_environment_failure` | `54.72%` | `64.17%` | `63.33%` | `90.83%` |
| `timeout_or_flaky_failure` | `64.60%` | `71.27%` | `66.88%` | `79.15%` |

## Agentic Diagnostic Findings

### `github-osquery-issue-7718`: strongest positive L4 observation

L1/L2/Oracle had persistent difficulty with this Case. Under L4, all three
repeats selected the frozen `timeout_or_flaky_failure` taxonomy and achieved
Evidence Hit Rates of `0.8`, `1.0`, and `1.0`.

More importantly, all three L4 reports recovered the readiness race:

```text
test pre-creates pidfile
  -> pidfile existence is later treated as daemon readiness
  -> readiness check can pass before osqueryd installs SIGINT handler
  -> SIGINT arrives during startup window
  -> default signal termination
  -> subprocess return code -2
```

This is evidence that adaptive repository investigation can improve temporal /
causal diagnosis even when selected Oracle evidence alone did not make the
model recover the mechanism reliably.

### `odrepair-remoting-abf0455a`: persistent reasoning badcase

All three L4 repeats still selected `test_assertion_failure` rather than the
frozen `timeout_or_flaky_failure` taxonomy. Reports recovered fragments of the
ClassFilter / invalid-regex behavior but did not stably reconstruct the full
polluter -> failed static initialization -> later victim chain.

This remains primarily a reasoning / temporal causal-chain problem rather than
an obvious evidence-acquisition problem.

### `bugswarm-spring-hateoas-232784946`: protocol weak point despite useful diagnosis

All three repeats selected the correct `dependency_or_install_failure`
taxonomy, but all three final reports were protocol-invalid. The reports
identified the Spring 5 snapshot / Jackson-version incompatibility with useful
causal detail, while Evidence-ID mapping remained unreliable.

This Case demonstrates why taxonomy correctness and semantic usefulness must be
kept separate from final output-protocol validity.

## Interpretation Boundary

The frozen scorer evaluates:

- failure-type classification
- Evidence-ID grounding
- required-field completeness
- output protocol validity

It does not directly score semantic correctness of the complete causal chain,
`root_cause`, or `recommended_action`.

Therefore L4 Failure Type Exact Match of `88.33%` must not be interpreted as
`88.33%` root-cause diagnosis accuracy.

Likewise, L4's `65.51%` Evidence Hit Rate should not be interpreted as evidence
that every cited item was sufficient or that every omitted item was required
for the report's causal claim.

## What the Milestone Establishes

The formal milestone provides real evidence that the L4 self-built Runtime can
operate as an integrated Agent System rather than as an isolated loop demo.

Observed together in one controlled run:

- provider-neutral multi-turn conversation state
- native MiniMax tool calling
- full provider continuation replay
- adaptive `read/grep/find/ls` investigation
- bounded ToolResults and truncation
- Tool Policy rejection and model self-recovery
- schema/domain tool-error recovery
- same-logical-request provider retry
- provider-reported per-step usage
- hard Agent step budget enforcement path without reaching the budget
- Trace and formal scheduler integration
- SQLite/formal artifact persistence
- Case-first aggregation and existing scorer reuse

The remaining weaknesses are now empirical Agent/System badcases rather than
unknown implementation questions.

## Follow-up Direction

Do not mutate this L4 baseline to make the recorded milestone look cleaner.

The most obvious future ablation suggested by the data is a bounded,
answer-neutral physical-span -> Canonical Evidence coordinate assistance
mechanism, because unknown Evidence IDs dominate the final protocol failures.
Such a mechanism would change Agent-visible behavior and must therefore be
introduced as an explicit future Treatment / capability decision rather than a
silent Runtime repair.

Other future work should remain evidence-driven, including context management,
batch/parallel Tool Policy, richer tools, planner/verifier structure, or
long-term experience/memory.

## Human Review

Human Review independently inspected the formal artifact, the single execution
failure, aggregate chain, protocol-invalid outputs, context observations, and
representative good/bad Cases.

Review verdict: **PASS**

Merge gate for the Issue #52 implementation: **APPROVE**, subject only to this
milestone-document and ADR-0129 design-guide consistency closeout.
