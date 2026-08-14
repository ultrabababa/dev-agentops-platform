# L2 MiniMax-M3 Full-Suite Milestone — 2026-08-15

## Overview

This document records the first formal full-Suite L2 development-treatment
milestone experiment for DevAgentOps.

The evaluated capability condition is a fixed two-stage Runtime-managed
workflow using MiniMax-M3 over the frozen `triage-suite-v1`:

    complete evidence
      -> evidence_analysis
      -> explicit canonical handoff
      -> complete evidence + intermediate artifact
      -> report_synthesis
      -> stop

The MiniMax provider, model, reasoning policy, generation policy, context
policy, frozen Suite, and scorer are held equal to the corresponding L1
development milestone.

The L2 capability delta is the fixed two-stage workflow and explicit
intermediate working state.

This report is a compact repository-tracked index of the immutable experiment
bundle. The detailed raw and derived artifacts remain in the ignored milestone
bundle and are identified below by SHA256.

## Experiment Identity

- Run ID: `82372eec-204f-4223-b87e-0f26a9ae3fb5`
- Execution code revision: `b874d691c43415cbd1f55f35304513140af33bbb`
- Git dirty at execution: `false`
- Suite: `triage-suite-v1`
- Suite version: `1`
- Model: `MiniMax-M3`
- Runtime condition: L2 fixed two-stage workflow
- Workflow: `evidence_analysis -> report_synthesis -> stop`
- Cases: `20`
- Repeats per Case: `3`
- Planned samples: `60`
- Expected model calls per successful Sample: `2`

### Fingerprints

- Suite: `b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Treatment: `10361eddc287886ef5d634d2a81b163cd859c0802b40ec164f34c5fb240a0f50`
- Condition: `92e4260209f63d8c13eea5de821ea0e53ba40d47b468b14feac4ab163d9335d1`
- Execution Policy: `c1f3aa8327a858befa9b77a8cc4bce80798c5c98a5125a0c31158ce109225e5b`
- Run Configuration: `d3f71107043e472e7bf6063b53571f9ed7ccdfbf0fed7dbbc71edea0fbbf0669`

The experiment was executed on the implementation commit above. This milestone
report is intentionally committed afterwards so that experiment provenance
continues to identify the exact code that produced the Run.

## Live Qualification

Before the formal full-Suite Run, one real MiniMax-M3 L2 Sample was executed as
a provider/infrastructure qualification.

Qualification Case:

`bugswarm-traccar-170287308`

Observed Stage-1 token accounting:

- local exact prompt tokens: `107220`
- hosted API prompt tokens: `107220`

Observed Stage-2 token accounting:

- local exact prompt tokens: `108835`
- hosted API prompt tokens: `108835`

Both calls completed with `finish_reason=stop`.

The final report was protocol-valid and scored:

- Failure Type Exact Match: `1.0`
- Evidence Hit Rate: `0.6666666666666666`
- Required Fields Completeness: `1.0`

Qualification verdict: **PASS**

Qualification was defined as a provider/protocol/infrastructure gate rather
than a diagnostic-quality tuning gate. No Prompt or Treatment change was made
after qualification.

## Execution

- Scored samples: `60/60`
- Execution failures: `0`
- Execution coverage: `100.00%`
- Model calls started: `120`
- Model calls completed: `120`
- Retry count: `0`
- Local / hosted prompt-token parity: `120/120`
- Token parity errors: `0`
- Same-Case repeats: verified serial
- Maximum observed active Cases: `6`
- Run wall-clock time: approximately `16m25s`
- Suite quality status: `complete`

Every successful Sample executed exactly:

    model_call #1: evidence_analysis
      ->
    model_call #2: report_synthesis

No execution-level provider, Runtime, or context failure occurred.

## L2 Workflow Integrity

Human review reconstructed the L2 handoff independently for all 60 Samples.

Verified:

- Stage-1 visible output was preserved exactly
- Stage-1 visible-output SHA256 matched
- canonical handoff SHA256 matched
- Stage-2 Runtime input contained the reconstructed canonical handoff
- Stage-2 retained the complete original Runtime Evidence Universe
- Stage ordering was exact
- logical call numbers were exactly `1` then `2`
- handoff reconstruction errors: `0`
- raw/private reasoning protocol fields persisted: `0`

The Runtime did not use hidden conversation history, retry, repair,
regeneration, or adaptive branching.

## Stage-1 Memo Observations

Stage-1 protocol validity is observational and does not gate Stage 2.

`9/60` Stage-1 memo observations had at least one protocol or grounding issue:

- `7` Samples referenced at least one unknown Evidence ID
- `1` Sample returned non-JSON output
- `1` Sample returned JSON that did not satisfy the memo schema

Affected Samples:

- `bugswarm-apache-struts-190697114`, repeat `0` — unknown Evidence ID
- `bugswarm-apache-struts-190697114`, repeat `1` — unknown Evidence ID
- `bugswarm-mypy-237548392`, repeat `0` — invalid JSON
- `bugswarm-mypy-237548392`, repeat `1` — schema-invalid memo
- `bugswarm-byte-buddy-149441998`, repeat `0` — unknown Evidence ID
- `bugswarm-byte-buddy-149441998`, repeat `2` — unknown Evidence ID
- `bugswarm-traccar-221926468`, repeat `1` — unknown Evidence ID
- `bugswarm-nukkit-94403868`, repeat `2` — unknown Evidence ID
- `bugswarm-cola-12505170926`, repeat `2` — unknown Evidence ID

These observations were preserved unchanged and Stage 2 continued as specified
by the Treatment.

Five of these nine affected Samples still produced a protocol-valid final
report. This demonstrates that report synthesis can sometimes recover from an
imperfect intermediate artifact when it also receives the complete original
Evidence Universe.

At the same time, four final protocol-invalid Sample identities coincide with
Stage-1 unknown-Evidence-ID observations. This is consistent with the explicit
intermediate artifact acting as an error-propagation channel. The identity
correlation does not by itself prove that each exact invalid locator was copied
unchanged from Stage 1 into the final report.

## Final Output Protocol

- Protocol-valid samples: `54/60`
- Protocol-invalid samples: `6/60`
- Protocol validity: `90.00%`

Protocol-invalid observations:

- `bugswarm-apache-struts-190697114`, repeat `0`
  - unknown Evidence IDs
- `bugswarm-apache-struts-190697114`, repeat `1`
  - unknown Evidence IDs
- `bugswarm-retrofit-113047638`, repeat `1`
  - missing `root_cause`
  - unexpected typo field `root_ause`
- `bugswarm-byte-buddy-149441998`, repeat `0`
  - unknown Evidence ID
- `bugswarm-byte-buddy-149441998`, repeat `2`
  - unknown Evidence ID
- `github-osquery-issue-7718`, repeat `2`
  - missing `confidence`

These Samples remained scored according to the frozen evaluation semantics.

No repair, regeneration, retry, field substitution, Evidence-ID correction, or
Human Review score adjustment was performed.

## Suite Diagnostic Metrics

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.850000` | `85.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.555688` | `55.57%` |
| Required Fields Completeness | `0.995833` | `99.58%` |

The Suite quality status is `complete` with full Case and configured
Suite-weight coverage.

Aggregation is Case-first:

`Sample -> Case mean -> fixed-weight Suite aggregate`

Samples are not flattened directly into Suite metrics.

The complete aggregate chain was independently recomputed during Human Review:

`Sample -> Case -> Failure Type -> Suite`

Recomputation verdict: **PASS**

## By Failure Type

### `test_assertion_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.435185` | `43.52%` |
| Required Fields Completeness | `0.989583` | `98.96%` |

### `lint_or_type_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.541667` | `54.17%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

### `dependency_or_install_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `1.000000` | `100.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.447222` | `44.72%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

### `config_or_environment_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.750000` | `75.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.641667` | `64.17%` |
| Required Fields Completeness | `1.000000` | `100.00%` |

### `timeout_or_flaky_failure`

| Metric | Value | Percentage |
|---|---:|---:|
| Failure Type Exact Match | `0.500000` | `50.00%` |
| Reviewed Acceptable Match | `0.000000` | `0.00%` |
| Evidence Hit Rate | `0.712698` | `71.27%` |
| Required Fields Completeness | `0.989583` | `98.96%` |

## Repeat-Stability Findings

`16/20` Cases achieved exact taxonomy classification in all three repeats.

Persistent or partial taxonomy failures were concentrated in four Cases:

- `bugswarm-blueflood-80881330`: `0/3` exact
- `github-osquery-issue-7718`: `0/3` exact
- `odrepair-dubbo-737f7a7e`: `1/3` exact
- `odrepair-remoting-abf0455a`: `2/3` exact

The L2 workflow substantially stabilized several Cases that exposed taxonomy
boundary instability in the L1 milestone.

In particular:

- `bugswarm-traccar-221926468` achieved `3/3` exact under L2
- `bugswarm-traccar-166900445` achieved `3/3` exact under L2

Both Cases had shown final-taxonomy instability under L1 despite relatively
stable causal understanding.

The remaining flaky/order-dependent Cases show that a fixed intermediate
working-memory stage does not eliminate all taxonomy instability.

## Token Observations

### Stage 1 — `evidence_analysis`

- Calls: `60`
- Prompt tokens: `7,890,330`
- Completion tokens: `280,663`

### Stage 2 — `report_synthesis`

- Calls: `60`
- Prompt tokens: `7,979,160`
- Completion tokens: `98,657`

### Total L2

- Model calls: `120`
- Prompt tokens: `15,869,490`
- Completion tokens: `379,320`
- Total tokens: `16,248,810`

Token observations do not participate in diagnostic-quality aggregation.

## L1 vs L2 Comparison

The preserved L1 and L2 milestones use:

- the same frozen Suite
- the same MiniMax-M3 foundation model
- the same adaptive reasoning policy
- the same generation configuration
- the same context policy
- the same scorer
- the same repeat count
- the same outer Execution Policy

The complete Treatment fingerprints intentionally differ because the L2
workflow, stage controls, and handoff contract are capability-affecting
Treatment state.

### Suite-Level Comparison

| Metric | L1 | L2 | L2 - L1 |
|---|---:|---:|---:|
| Execution Coverage | `100.00%` | `100.00%` | `0.00 pp` |
| Failure Type Exact Match | `76.67%` | `85.00%` | `+8.33 pp` |
| Evidence Hit Rate | `51.38%` | `55.57%` | `+4.19 pp` |
| Required Fields Completeness | `96.67%` | `99.58%` | `+2.92 pp` |
| Protocol Validity | `96.67%` | `90.00%` | `-6.67 pp` |

### Failure-Type Exact Match

| Failure Type | L1 | L2 | Delta |
|---|---:|---:|---:|
| `test_assertion_failure` | `100.00%` | `100.00%` | `0.00 pp` |
| `lint_or_type_failure` | `91.67%` | `100.00%` | `+8.33 pp` |
| `dependency_or_install_failure` | `83.33%` | `100.00%` | `+16.67 pp` |
| `config_or_environment_failure` | `66.67%` | `75.00%` | `+8.33 pp` |
| `timeout_or_flaky_failure` | `41.67%` | `50.00%` | `+8.33 pp` |

### Failure-Type Evidence Hit Rate

| Failure Type | L1 | L2 | Delta |
|---|---:|---:|---:|
| `test_assertion_failure` | `46.16%` | `43.52%` | `-2.64 pp` |
| `lint_or_type_failure` | `45.14%` | `54.17%` | `+9.03 pp` |
| `dependency_or_install_failure` | `46.25%` | `44.72%` | `-1.53 pp` |
| `config_or_environment_failure` | `54.72%` | `64.17%` | `+9.44 pp` |
| `timeout_or_flaky_failure` | `64.60%` | `71.27%` | `+6.67 pp` |

### Inference Consumption

L1:

- Model calls: `60`
- Prompt tokens: `7,901,430`
- Completion tokens: `283,392`
- Total tokens: `8,184,822`

L2:

- Model calls: `120`
- Prompt tokens: `15,869,490`
- Completion tokens: `379,320`
- Total tokens: `16,248,810`

L2 therefore consumed approximately:

- `2.01x` L1 prompt tokens
- `1.99x` L1 total tokens

## Interpretation

The observed L2 Treatment produced a meaningful diagnostic-quality uplift:

- taxonomy exact match increased by `8.33` percentage points
- Evidence Hit Rate increased by `4.19` percentage points
- required-field completeness increased by `2.92` percentage points

The taxonomy improvement is distributed across several Failure Types rather
than being isolated to a single category.

The result is consistent with the hypothesis that an explicit intermediate
analysis state can stabilize some final structured classification decisions,
particularly where L1 causal understanding was stronger than its final taxonomy
selection.

However, L2 also increased final output-protocol failures:

- L1 protocol validity: `96.67%`
- L2 protocol validity: `90.00%`

The Stage-1 review further shows that explicit intermediate working state can
become an error-propagation surface, especially for hallucinated or malformed
Evidence references.

The fixed two-stage workflow therefore exposes a real tradeoff:

    more explicit intermediate reasoning state
        ->
    improved taxonomy and aggregate evidence grounding
        +
    additional inference cost
        +
    additional protocol / grounding propagation surface

This suggests that a later Agent Runtime may benefit more from verification of
intermediate claims and evidence than from simply adding additional fixed
reasoning stages.

The observed difference should be interpreted as the effect of the complete L2
fixed-workflow Treatment relative to L1 under the held-constant foundation. It
does not isolate the causal effect of the second model call alone.

## Human Review

Human Review verdict: **PASS**

Verified during review:

- clean committed execution revision
- frozen Suite identity
- L2 Treatment / Condition / Execution Policy identity
- 20 Cases x 3 repeats
- 60 unique Samples
- 120 model-call starts
- 120 model-call completions
- zero execution failures
- zero hidden retries
- exact two-stage ordering
- same-Case serialization
- maximum cross-Case concurrency of 6
- 120/120 exact local / hosted token-accounting parity
- 60/60 handoff reconstruction
- Sample -> Case -> Failure-Type -> Suite recomputation
- no flattening
- no failure-driven Suite-weight renormalization
- Stage-1 protocol defects preserved unchanged
- final protocol-invalid observations preserved unchanged
- no raw/private reasoning protocol fields persisted

No experiment-invalidating infrastructure defect was found.

Observed Stage-1 defects, final protocol errors, taxonomy instability, evidence
selection variability, and error propagation are retained as experimental
evidence.

No quality result was altered by Human Review.

## Artifact Integrity

The immutable milestone bundle is:

`artifacts/evaluation-milestones/l2-minimax-m3-full-suite-20260815-004143/`

Tracked SHA256 values:

- `cli-output.json`: `7a19f397536ec3fb8faed71968bcc439b975360af1f5c71c57e2a5cdf3c6de48`
- `evaluation.json`: `acf25ec5b1d6f19318c783bdd493b88368cb1daf0dfeddac2198e3a63f2bc957`
- `evaluation.md`: `a0445bd90c947bfa500231a562936086d4c8afa06951270408a38195dd15c13d`
- `devagentops.db`: `f4579295c634d00d4f8a4d128e87520803df5faa91afa9171092695e4e1e39c8`
- `review-summary.json`: `ab5e2b62e9529491d52353276d637f8449e04b4fe63fa6db6980dadde64387d9`
- `progress.log`: `704ebe6d20a6360f9be175cc36c0b81b0e48b914368dbbd56832ea4b2ab99e04`
- `doctor.json`: `e4b1c53bebe8d9ab762d2820bf057202d475322630262758280f8c86ea1baa58`
- `code-revision.txt`: `9b30f0a80d741dccc5fb20694aede14a5f503852cf1e2b17f6ec9d0b971e5317`
- `pre-run-git-status.txt`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `cli-exit-code.txt`: `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `qualification.json`: `c735a96a16902390ec768a0ed370610a332a1e2ff98c33caffd0d0dcffd63cf5`
- `human-review.md`: `fe1468d3e9714154659adf7a8937fc589ce6a907cdabb2d5241534b200678070`

`SHA256SUMS.txt` in the immutable bundle is the canonical checksum index.

The ignored artifact bundle is the canonical detailed experiment record. This
document is a compact repository-tracked summary and provenance index.

## Non-Claims

This result is:

**an L2 development-treatment milestone experiment**

It is **not**:

- the final frozen L1-L4 benchmark
- a final Prompt freeze
- a final Treatment freeze
- a Quality Gate
- a leaderboard result
- a model comparison
- proof that the second model call alone caused the observed improvement
- proof that additional fixed reasoning stages will continue to improve quality

The result motivates later verification, retrieval, evidence-selection, and
adaptive Runtime experiments, but does not predetermine their outcome.
