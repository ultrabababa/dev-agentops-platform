# L1 MiniMax-M3 Full-Suite Milestone — 2026-08-14

## Overview

This document records the first formal full-Suite L1 development-treatment
milestone experiment for DevAgentOps.

The evaluated capability condition is a Full-Context One-Shot L1 treatment
using MiniMax-M3 over the frozen `triage-suite-v1`.

This report is a compact repository-tracked index of the immutable experiment
bundle. The detailed raw and derived artifacts remain in the ignored milestone
bundle and are identified below by SHA256.

## Experiment Identity

- Run ID: `de1809aa-3506-4e04-843b-099f4be00df4`
- Execution code revision: `73271cf402c9d8b111f66dc963aa9eb30154ee8b`
- Git dirty at execution: `false`
- Suite: `triage-suite-v1`
- Suite version: `1`
- Model: `MiniMax-M3`
- Runtime condition: L1 Full-Context One-Shot
- Cases: `20`
- Repeats per Case: `3`
- Planned samples: `60`

### Fingerprints

- Suite: `b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Treatment: `1d6387a25f7722c30b36be82eaf5f7699550472a9b136db5964a783c3da758f4`
- Condition: `c199208feb41748fd67095512871bcd406d108ed3444b98854adecf0aa1fcb2a`
- Execution Policy: `c1f3aa8327a858befa9b77a8cc4bce80798c5c98a5125a0c31158ce109225e5b`
- Run Configuration: `952a262dff16737a62f8bf597e6eca9ec1c54948d55df17cd6ee1e763c54c694`

The experiment was executed on the implementation commit above. This milestone
report is intentionally committed afterwards so that experiment provenance
points to the exact code that produced the Run.

## Execution

- Scored samples: `60/60`
- Execution failures: `0`
- Execution coverage: `100.00%`
- Provider attempts: `60`
- Retry count: `0`
- Local / hosted prompt-token parity: `60/60`
- Same-Case repeats: verified serial
- Cross-Case concurrency: observed
- Observed cross-Case overlap pairs: `266`

No execution failure occurred.

## Output Protocol

- Protocol-valid samples: `58/60`
- Protocol-invalid samples: `2/60`
- Protocol validity: `96.67%`

Protocol-invalid observations:

- `bugswarm-pygithub-36442425251`, repeat `2` — `invalid_report_type`: semantically complete JSON report text was returned as a string instead of a JSON object.
- `bugswarm-traccar-221926468`, repeat `1` — `invalid_report_type`: semantically complete JSON report text was returned as a string instead of a JSON object.

These samples were preserved and scored according to the frozen evaluation
semantics. No repair, regeneration, retry, or score substitution was performed.

They are treated as genuine model/output-protocol observations rather than
experiment-infrastructure failures.

## Suite Diagnostic Metrics

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.766667` | `76.67%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.513757` | `51.38%` |
| Required Fields Completeness | `0.966667` | `96.67%` |

The Suite quality status is `complete` with:

- Quality Case coverage: `100.00%`
- Quality Suite-weight coverage: `100.00%`

Aggregation is Case-first:

`Sample -> Case mean -> fixed-weight Suite aggregate`

Samples are not flattened directly into Suite metrics.

### Suite Weight Normalization

`triage-suite-v1` stores relative unit weights rather than pre-normalized
probability weights: all 20 Cases have weight `1`, so the frozen configured
Suite weight is `20.0`.

Suite aggregation therefore uses the fixed configured weighted mean:

`sum(case_metric * frozen_weight) / configured_suite_weight`

The denominator is the frozen configured total and does not change with sample
success or failure. This is fixed normalization of relative Suite weights, not
failure-driven renormalization.

Accordingly, `quality_suite_weight_coverage` is reported as available frozen
weight divided by configured frozen weight, and is `1.0` for this complete
20-Case Run.

## By Failure Type

### `test_assertion_failure`

- Protocol validity: `100.00%`
- Quality status: `complete`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.461640` | `46.16%` |
| Required Fields Completeness | `1.000000` | `100.00%` |
### `lint_or_type_failure`

- Protocol validity: `91.67%`
- Quality status: `complete`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.916667` | `91.67%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.451389` | `45.14%` |
| Required Fields Completeness | `0.916667` | `91.67%` |
### `dependency_or_install_failure`

- Protocol validity: `91.67%`
- Quality status: `complete`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.833333` | `83.33%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.462500` | `46.25%` |
| Required Fields Completeness | `0.916667` | `91.67%` |
### `config_or_environment_failure`

- Protocol validity: `100.00%`
- Quality status: `complete`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.666667` | `66.67%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.547222` | `54.72%` |
| Required Fields Completeness | `1.000000` | `100.00%` |
### `timeout_or_flaky_failure`

- Protocol validity: `100.00%`
- Quality status: `complete`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.416667` | `41.67%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.646032` | `64.60%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

## Repeat-Stability Findings

Repeated evaluation exposed meaningful hosted-model variability despite
`temperature=0`.

- `bugswarm-pygithub-36442425251`: the semantic classification remained
  `lint_or_type_failure` across repeats; the apparent metric instability was
  primarily caused by one output-protocol failure.

- `bugswarm-traccar-221926468`: all repeats identified the Java 7 / Java 8
  incompatibility, but the final taxonomy alternated between
  `config_or_environment_failure` and `dependency_or_install_failure`,
  exposing a dependency/environment taxonomy-boundary instability.

- `bugswarm-traccar-166900445`: all repeats identified the live SMTP /
  placeholder-credential root cause, while the final taxonomy varied between
  `test_assertion_failure` and `config_or_environment_failure`.

- `odrepair-dubbo-737f7a7e`: all repeats identified order-dependent shared
  RpcContext/thread-local state, while classification varied between
  `timeout_or_flaky_failure` and `test_assertion_failure`; evidence selection
  also varied substantially.

These observations indicate that causal understanding can be more stable than
the final structured taxonomy decision.

## Performance Observations

- Minimum latency: `8588 ms`
- Median latency: `30153 ms`
- p95 latency: `166742.2 ms`
- Maximum latency: `309495 ms`
- Total prompt tokens: `7,901,430`
- Total completion tokens: `283,392`
- Median prompt tokens: `94,341`
- Maximum prompt tokens: `708,226`

Performance and token observations do not participate in diagnostic-quality
aggregation.

## Interpretation

The L1 milestone shows four distinct properties:

1. **Execution reliability is high.** All 60 planned samples completed.
2. **Output-protocol reliability is high but not perfect.** Two of 60 returned
   reports violated the outer JSON-object contract.
3. **Taxonomy classification is substantially less stable than execution or
   report completeness.** Suite exact match is `76.67%`.
4. **Evidence grounding is a major L1 weakness.** Suite Evidence Hit Rate is
   `51.38%` despite
   `96.67%` required-field completeness.

Repeated evaluation also shows that `temperature=0` should not be interpreted
as fully deterministic hosted-model execution.

These observations motivate later L2/L3/L4 comparisons, including structured
workflow, retrieval/evidence selection, and iterative verification hypotheses.
They do **not** establish that those future conditions will improve these
metrics.

## Human Review

Human Review verdict: **PASS**

Verified during review:

- clean committed execution revision
- frozen Suite and capability identities
- 20 Cases x 3 repeats
- 60 unique Sample identities
- 60 provider attempts
- zero hidden retries
- same-Case serialization
- real cross-Case concurrency
- 60/60 exact token-accounting parity
- Sample -> Case -> Suite recomputation
- no flattening
- no failure-driven weight renormalization
- SQLite / JSON consistency
- protocol-invalid observations preserved unchanged
- API secret exclusion
- no raw/private reasoning persistence

No experiment-invalidating infrastructure defect was found.

Observed protocol failures, taxonomy instability, evidence-selection
variability, hosted-model variability, and latency variability are retained as
experimental evidence.

## Artifact Integrity

The immutable milestone bundle is:

`artifacts/evaluation-milestones/l1-minimax-m3-full-suite-20260814-204616/`

Tracked SHA256 values:

- `cli-output.json`: `a499d02e3fd91d66e548963146ab35e352e271a99cc78e7ff1007079973f0fbe`
- `evaluation.json`: `f8d25ce8b06968381f9b954dc0eb423d120533114a79d1519a6d63529b6d593e`
- `evaluation.md`: `7254237957e5f387a1b635ae981e1e3e7a642e49ad1ea2cb236234823f1e6983`
- `devagentops.db`: `edaf3f7997db175e49493372249b20c5680bb9dd7494031e90b652cbb7988235`
- `human-review.md`: `47ae4e34a944910356ed6f47554d59723b7ca7a2be3b88daf1a3c6dc75fd5b51`

The ignored artifact bundle is the canonical detailed experiment record. This
document is a compact repository-tracked summary and provenance index.

## Non-Claims

This result is:

**an L1 development-treatment milestone experiment**

It is **not**:

- the final frozen L1-L4 benchmark
- a final Prompt freeze
- a final Treatment freeze
- a Quality Gate
- a leaderboard result
- a model comparison
- evidence that L2/L3/L4 will necessarily improve performance

The benchmark treatment and broader cross-condition evaluation remain future
work.
