# Oracle MiniMax-M3 Full-Suite Milestone — 2026-08-15

## Overview

This document records the first formal full-Suite Oracle Evidence Diagnostic
milestone experiment for DevAgentOps.

The evaluated condition uses MiniMax-M3 with a fixed one-shot model execution
while replacing the normal Runtime evidence universe with a deterministic,
Human-reviewed selected-evidence input derived from each Case's frozen
`required_evidence_ids`.

Oracle is an evaluator diagnostic intervention.

It is:

- not a Product Runtime
- not a capability-ladder rung
- not L1 Full-Context One-Shot
- not an Agent condition

Its purpose is to control evidence availability so that later experiments can
separate evidence-acquisition failures from failures that remain after relevant
evidence is already available to the model.

The frozen Suite, Case Packages, Evidence Ground Truth, Expected Answers,
Structured Triage Report contract, and scorer were not modified.

This report is a compact repository-tracked index of the immutable experiment
bundle. Detailed raw and derived artifacts remain in the ignored milestone
bundle identified below.

## Experiment Identity

- Run ID: `388dc6a6-6483-4e11-9b4a-5c935929bd5a`
- Execution code revision: `f96a305c9bf42574447d60c9c3dbb96d390910f0`
- Git dirty at execution: `false`
- Suite: `triage-suite-v1`
- Suite version: `1`
- Model: `MiniMax-M3`
- Runtime variant: `model_one_shot`
- Experiment identity: `oracle-evidence-diagnostic-development`
- Cases: `20`
- Repeats per Case: `3`
- Planned Samples: `60`
- Expected model calls per successful Sample: `1`

### Fingerprints

- Suite: `b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Evidence Delivery: `3a0fbbbc16b66eacd5c058afe233383e55d18987a138e16187ebc3561e7afbee`
- Treatment: `3140864b09ef6aaf0be883ff63ff5ec436fdf93fa29fbfae2631cd63525066f7`
- Condition: `2cac4e956bb6d0f1d5aecbf50bdde34cebc6478b0c94e3034f75e47217923721`
- Execution Policy: `c1f3aa8327a858befa9b77a8cc4bce80798c5c98a5125a0c31158ce109225e5b`
- Run Configuration: `fadfeec66e32bd2f7cab1db92a7449c96bac2b3555c7eb2fe007184c275c0ab6`

The experiment was executed on the implementation commit above. This milestone
report is intentionally committed afterwards so that experiment provenance
continues to identify the exact code that produced the Run.

## Oracle Evidence Contract

For each Case, the trusted evaluator resolves:

    frozen required_evidence_ids
      -> Canonical Evidence
      -> exact Physical Artifact spans
      -> deterministic selected-evidence Runtime Input

The required IDs are treated as a set. Model-visible ordering is derived from
answer-neutral canonical coordinates rather than curator ordering.

The model-visible Oracle Runtime Input contains only allowlisted source-faithful
data, including:

- public Case identity required by the task
- Stable Evidence IDs
- frozen source/path coordinates
- exact canonical spans
- exact source-faithful content
- integrity metadata where applicable

It does not intentionally expose:

- Expected Answer
- required/optional labels
- curator ordering semantics
- evaluator reasoning
- scorer state
- prior evaluation outcomes
- `case_fingerprint`
- Oracle control-policy identifiers

Oracle evidence packs are derived at Runtime and are not copied into frozen
Case Packages.

## Live Qualification

Before the formal full-Suite Run, one real MiniMax-M3 Oracle Sample was
executed as a provider/protocol/infrastructure qualification.

Qualification Case:

`bugswarm-traccar-170287308`

Observed token accounting:

- local exact prompt tokens: `5194`
- hosted API prompt tokens: `5194`
- completion tokens: `3937`

Observed execution:

- provider completion calls: `1`
- finish reason: `stop`
- final report protocol-valid: `true`
- delivered Evidence Items: `3`
- referenced Evidence IDs: all within the delivered Oracle evidence set

Qualification diagnostic metrics:

- Failure Type Exact Match: `1.0`
- Evidence Hit Rate: `1.0`
- Required Fields Completeness: `1.0`

Qualification verdict: **PASS**

Qualification was an infrastructure and protocol gate rather than a
diagnostic-quality tuning gate.

No Prompt, Treatment, frozen evaluation data, or scorer change was made in
response to the qualification result.

## Execution

- Scored Samples: `60/60`
- Execution failures: `0`
- Execution coverage: `100.00%`
- Model calls started: `60`
- Model calls completed: `60`
- Retry count: `0`
- Local / hosted prompt-token parity: `60/60`
- Token parity errors: `0`
- Provider request IDs: `60` unique
- Finish reason: `stop` for `60/60`
- Same-Case repeats: verified serial
- Maximum observed active Samples: `6`
- Formal runner wall-clock: `317 s`
- Suite quality status: `complete`

Every successful Sample executed exactly one model call.

No execution-level provider, Runtime, or context failure occurred.

## Trace and Scheduler Audit

The formal artifact contains `422` Trace events:

| Event | Count |
|---|---:|
| `run_started` | `1` |
| `sample_started` | `60` |
| `oracle_execution_started` | `60` |
| `model_call_started` | `60` |
| `model_call_completed` | `60` |
| `report_submitted` | `60` |
| `evaluation_completed` | `60` |
| `sample_completed` | `60` |
| `run_completed` | `1` |

The Trace confirms:

- exactly one logical model call per Sample
- `attempt_index = 0`
- `retry_count = 0`
- all Sample identities joined correctly across Trace and persisted results
- same-Case repeats remained serial
- cross-Case active-Sample concurrency never exceeded `6`

An initial read-only audit script omitted the scheduler-level
`sample_started` and `sample_completed` events from its expected event set.
That produced one audit-script false positive. The persisted Trace itself was
correct and complete.

## Oracle Input Integrity

Human and machine review independently re-resolved the Oracle Runtime Input
from the frozen Case Packages for all 20 Cases.

Verified:

- all 20 Case Runtime Inputs independently reproduced
- all 60 persisted Runtime-input SHA256 values matched recomputation
- all three repeats of each Case used the same Runtime-input SHA256
- all reports referenced only Evidence IDs actually delivered to that Sample
- unknown Evidence-ID references: `0`
- duplicate Evidence-ID references: `0`
- leakage-marker checks passed
- raw/private reasoning fields persisted: `0`

The Oracle condition therefore behaved as a controlled evidence-delivery
intervention rather than as a hidden answer channel.

## Output Protocol

- Protocol-valid Samples: `60/60`
- Protocol-invalid Samples: `0/60`
- Protocol validity: `100.00%`
- Required Fields Completeness: `100.00%`

No output repair, regeneration, retry, field substitution, Evidence-ID
correction, or Human Review score adjustment was performed.

## Suite Diagnostic Metrics

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.850000` | `85.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.892884` | `89.29%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

The Suite quality status is `complete` with:

- execution coverage: `100.00%`
- protocol validity: `100.00%`
- quality Case coverage: `100.00%`
- quality Suite-weight coverage: `100.00%`

Aggregation is Case-first:

    Sample
      -> Case arithmetic mean
      -> fixed-weight Failure-Type / Suite aggregate

Samples are not flattened directly into Suite metrics.

The complete aggregate chain was independently recomputed during Human Review.

Recomputation verdict: **PASS**

## By Failure Type

### `test_assertion_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.847884` | `84.79%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

Protocol validity: `100.00%`

### `lint_or_type_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.916667` | `91.67%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

Protocol validity: `100.00%`

### `dependency_or_install_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.916667` | `91.67%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `1.000000` | `100.00%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

Protocol validity: `100.00%`

### `config_or_environment_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.908333` | `90.83%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

Protocol validity: `100.00%`

### `timeout_or_flaky_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.333333` | `33.33%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.791534` | `79.15%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

Protocol validity: `100.00%`

## Taxonomy Stability

`51/60` Sample realizations matched the frozen primary failure type.

The nine taxonomy mismatches were concentrated in four Cases:

- `bugswarm-traccar-221926468`: `2/3` exact
- `github-osquery-issue-7718`: `0/3` exact
- `odrepair-dubbo-737f7a7e`: `1/3` exact
- `odrepair-remoting-abf0455a`: `0/3` exact

This concentration is diagnostically important because several mismatches were
not evidence-availability failures.

## Human-Review Semantic Findings

Human Review verdict: **PASS**

The PASS verdict means that the experiment realization is scientifically usable
and that execution, evidence delivery, identity, protocol, persistence, and
aggregation were trustworthy.

It does not mean that all model diagnoses were semantically correct.

Human Review identified several model-quality observations that are not fully
represented by the frozen metric vector.

### `bugswarm-traccar-221926468`

All three repeats recovered the Java 7 / Java 8 bytecode incompatibility caused
by `async-http-client 2.0.31`.

One repeat classified the same mechanism as
`config_or_environment_failure` instead of
`dependency_or_install_failure`.

This is primarily a taxonomy-boundary instability rather than a causal
diagnosis failure.

### `github-osquery-issue-7718`

All three repeats selected `test_assertion_failure`.

The reports correctly described the visible symptom:

- SIGINT is sent
- exit code `0` is expected
- subprocess return code `-2` is observed

However, all three missed the frozen readiness-race mechanism.

The test pre-creates the pidfile that it subsequently uses as its own readiness
signal. That wait can therefore return before the daemon has installed its
SIGINT handler. Sending SIGINT during that window causes default signal
termination and the observed `-2` return code.

The model instead attributed the behavior to a defective or ineffective signal
handler.

This is a substantive temporal / causal reasoning failure despite Oracle
evidence availability.

### `odrepair-dubbo-737f7a7e`

Only one repeat selected the frozen `timeout_or_flaky_failure` taxonomy.

The other two selected `test_assertion_failure`.

However, those reports still recovered most of the core causal mechanism:

    RpcContextTest.testAsync
      -> started AsyncContext remains in thread-local RpcContext
      -> context is not removed
      -> later test inherits polluted state
      -> AbstractProxyInvoker follows the async path
      -> victim assertion fails

This Case therefore shows stronger causal understanding than the taxonomy
exact-match metric alone suggests.

### `odrepair-remoting-abf0455a`

All three repeats selected `test_assertion_failure`.

This was the strongest Oracle badcase observed in Human Review.

The frozen causal chain is:

    polluter test writes invalid regex override
      -> ClassFilter static initialization throws Error
      -> Java class initialization remains failed in that JVM
      -> later ClassFilterTest.userRequest becomes the victim

The model focused primarily on the polluter test's apparent contract and did
not recover the complete polluter -> static-initialization poisoning -> victim
chain.

Cross-repeat factual inconsistency was also observed around whether the polluter
was annotated with `@Test(expected=Error.class)`.

### `bugswarm-blueflood-80881330`

All three repeats selected the correct
`config_or_environment_failure` taxonomy.

Two repeats correctly identified the mapping-type mismatch:

`metrics` versus `graphite_event`.

One repeat instead attributed the failure to an Elasticsearch-version /
mapping-schema incompatibility.

This is a taxonomy-correct but causally inaccurate realization.

### `bugswarm-cola-12505170926`

All three repeats selected the correct
`config_or_environment_failure` taxonomy.

However, the reports emphasized an unavailable or unresolved JDBC driver.

The frozen root cause centers on the CI job not provisioning the MySQL endpoint
required by the Spring context.

This is another example where taxonomy exact match does not imply semantic
root-cause correctness.

## Scorer Interpretation Boundary

The frozen scorer evaluates:

- failure-type classification
- Evidence-ID grounding
- required-field completeness
- output protocol validity

It does not score semantic correctness of:

- `summary`
- `root_cause`
- `recommended_action`
- complete causal-chain reconstruction
- unsupported causal overclaim
- cross-repeat factual contradiction

Therefore:

**Oracle Failure Type Exact Match of 85.00% must not be interpreted as
85.00% root-cause diagnosis accuracy.**

Human Review demonstrated that some taxonomy-correct realizations still
contained material causal errors.

## Token Observations

- Model calls: `60`
- Prompt tokens: `442,140`
- Completion tokens: `174,538`
- Total tokens: `616,678`
- Reasoning tokens: `95,511`
- Cached prompt tokens: `282,294`

Token observations do not participate in diagnostic-quality aggregation.

## Performance Observations

- Median model latency: `13,538 ms`
- p95 model latency: `58,707.95 ms`
- Maximum model latency: `127,276 ms`
- Formal runner wall-clock: `317 s`

These operational observations are not directly comparable to L1/L2 as
capability-efficiency measurements.

Oracle intentionally changes evidence delivery and therefore presents a much
smaller selected-evidence input than the complete Evidence Universe used by
L1/L2.

Lower token consumption or latency is not evidence of greater diagnosis
capability.

## Diagnostic Context Relative to L1 and L2

The preserved MiniMax-M3 milestones have the following Suite-level diagnostic
metrics:

| Metric | L1 | L2 | Oracle |
|---|---:|---:|---:|
| Failure Type Exact Match | `76.67%` | `85.00%` | `85.00%` |
| Evidence Hit Rate | `51.38%` | `55.57%` | `89.29%` |
| Required Fields Completeness | `96.67%` | `99.58%` | `100.00%` |
| Protocol Validity | `96.67%` | `90.00%` | `100.00%` |
| Execution Coverage | `100.00%` | `100.00%` | `100.00%` |

This table is descriptive only.

Oracle is orthogonal to the capability ladder and changes the evidence-delivery
intervention directly. It must therefore not be interpreted as an L3-like
capability improvement or as another Product Runtime.

The large Evidence Hit Rate increase is consistent with the intended Oracle
intervention: relevant Human-reviewed evidence is delivered directly.

The remaining causal and taxonomy errors demonstrate that evidence availability
alone does not remove all diagnosis failures.

## Research Interpretation

The Oracle milestone provides a controlled diagnostic reference for future
evidence-acquisition experiments.

It supports distinguishing at least three classes of failure:

1. relevant evidence was not acquired or surfaced;
2. relevant evidence was available but was not used correctly;
3. the evidence was used, but causal synthesis or final taxonomy mapping was
   still incorrect.

The observed osquery and remoting failures are particularly important because
they survive direct delivery of Human-reviewed relevant evidence.

They therefore provide useful future badcases for studying temporal reasoning,
test-order reasoning, and Runtime-assisted causal reconstruction.

Oracle does not establish an Agent-System Realization Gap by itself.

A public Agent-System Realization Gap claim requires pairing Oracle with a
future Agent Product Runtime such as L4 or later under the versioned pairing and
diagnosis-pass machinery.

## Human Review

Human Review verdict: **PASS**

Verified during review:

- clean committed execution revision
- correct Oracle experiment identity
- 20 Cases x 3 repeats
- 60 unique Sample identities
- exactly 60 model calls
- zero hidden retries
- same-Case repeat serialization
- maximum active Samples of 6
- 60/60 exact local/API token-accounting parity
- deterministic Oracle Runtime-input recomputation
- Runtime-input SHA consistency
- source-faithful Evidence-ID references
- zero unknown Evidence IDs
- zero duplicate Evidence references
- Sample -> Case -> Failure Type -> Suite recomputation
- no failure-driven weight renormalization
- no raw/private reasoning persistence
- machine-readable artifact integrity
- semantic review of all 20 Cases / 60 realizations

No experiment-invalidating infrastructure defect was found.

Model-quality failures were preserved as experimental observations and were not
used as a reason to rerun or tune the condition.

## Artifact Integrity

The immutable milestone bundle is:

`artifacts/evaluation-milestones/oracle-minimax-m3-full-suite-20260814-183206/`

The ignored Chinese Human Review companion is:

`artifacts/evaluation-milestones/oracle-minimax-m3-full-suite-20260814-183206-human-review.zh-CN.md`

Seal records:

- Human Review SHA256:
  `e35066b0e2796f22e752320fc6a8bbd8fd92988a647a1a3ac8f2c487feef4a49`
- `seal-manifest.json` SHA256:
  `227d4e25b8cca25fd61a8041760043075e85a2a01949584d82734541b1c840af`
- `SHA256SUMS` SHA256:
  `001b619b88d34e60f7f6d7917df4adc0fff9babe758c19fee3f68c5feb5f8c10`

The bundle contains the original formal artifacts, SQLite database,
qualification artifact, doctor output, progress log, execution metadata,
Case-level Human Review input, seal manifest, and checksum manifest.

All files covered by `SHA256SUMS` passed independent checksum verification
before the bundle was marked locally read-only.

The ignored immutable artifact bundle is the canonical detailed experiment
record. This document is a compact repository-tracked summary and provenance
index.

## Non-Claims

This result is:

**an Oracle Evidence Diagnostic development milestone**

It is **not**:

- a Product Runtime
- an Agent
- L1, L2, L3, or L4
- a capability-ladder rung
- a leaderboard result
- a final Prompt freeze
- a final Treatment freeze
- root-cause accuracy of `85%`
- an Agent-System Realization Gap measurement
- evidence that Oracle should be used as a production Runtime
- evidence that L4 will necessarily match or exceed Oracle

No quality rerun or prompt tuning was performed after observing the formal
results.

The next research use of this milestone is as the Oracle side of the generic
pairing / gap-analysis machinery, followed later by a real Oracle-vs-Agent
comparison once an Agent Product Runtime exists.
