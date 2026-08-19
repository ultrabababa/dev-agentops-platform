# Shared Evidence Reference Canonicalization Milestone — 2026-08-19

> **Status: completed implementation + completed causal replay + completed fresh formal generation.** This milestone records the validation of `canonical-line-range-normalization-v1` as shared final-report/output infrastructure for L1/L2/Oracle/L4. The machine-readable result snapshot is [`evidence-reference-canonicalization-results-2026-08-19.json`](evidence-reference-canonicalization-results-2026-08-19.json).

## 1. Question

The historical MiniMax-M3 generation exposed a recurring final-report realization defect: a model could identify the correct physical source/range and still serialize a non-existent Canonical Evidence ID. That produced `unknown_evidence_id` or duplicate-reference protocol failures and could suppress Report Evidence Hit independently of diagnosis quality.

The experiment asked two separate questions:

1. Does deterministic Evidence Reference Canonicalization mechanically recover those failures without changing diagnosis semantics?
2. After the behavior is enabled for L1/L2/Oracle/L4, does a fresh `20 Cases × 3 repeats` generation remain operationally consistent with that conclusion?

These questions require two different evidence types. Offline replay isolates the deterministic transformation. Fresh model generation additionally includes provider/model regeneration variance and therefore cannot be treated as a clean causal estimate.

## 2. Implemented behavior

PR #58 introduced shared final-report Evidence Reference Canonicalization and was merged as:

- Issue: `#59` — Shared deterministic Evidence Reference Canonicalization
- PR: `#58` — `feat: canonicalize final evidence references before scoring`
- Merge commit: `de5459a099cb1d4c58b7ee9bac3ec516562cb94d`
- Output contract: `development-v2`
- Resolver identity: `canonical-line-range-normalization-v1`

The behavior is intentionally narrow:

```text
model candidate_document
    -> deterministic Evidence Reference Canonicalization
    -> existing Structured Report validator
    -> unchanged scorer
```

Per `evidence_reference`:

- an already-valid Canonical Evidence ID is preserved;
- a parseable `...:lines-START-END` reference is expanded to every existing frozen Canonical Evidence unit whose source identity matches and whose physical line range overlaps the authored range;
- resulting IDs are stably deduplicated;
- a reference that cannot be deterministically related to the frozen coordinate set is preserved and remains subject to normal validation;
- no other report field is repaired.

The resolver does **not** use Required Evidence, Expected Answer, root cause labels, failure type labels, trajectory/read history, fuzzy matching, edit distance, overlap thresholds, model correction turns, prompt-only hints, or new tools.

L1/L2/Oracle/L4 retain their own Runtime/evidence-acquisition semantics. Canonicalization is shared output infrastructure, not a new Runtime rung or a new `runtime_variant`.

## 3. Validation gates

Before formal reruns, the implementation passed:

- focused regression: `100 passed, 2 skipped`;
- full repository regression: `371 passed, 2 skipped, 30 subtests passed`;
- formal `eval doctor` for all four new matrices: PASS.

The new formal conditions were:

- `l1-minimax-m3-canonicalized-development-v1`
- `l2-minimax-m3-canonicalized-development-v1`
- `oracle-minimax-m3-canonicalized-development-v1`
- `l4-minimax-m3-canonicalized-development-v1`

All use `triage-suite-v1`, 20 Cases, 3 repeats per Case, MiniMax-M3, and the same new output-resolution contract.

## 4. Three-layer experiment design

The result must be read in three layers.

### Layer A — historical baseline generation

The original L1/L2/Oracle/L4 runs remain immutable. They did not use the new canonicalizer.

| Condition | Execution | Failure Type Exact | Evidence Hit | Required Fields | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 | 100.00% | 76.67% | 51.38% | 96.67% | 96.67% |
| L2 | 100.00% | 85.00% | 55.57% | 99.58% | 90.00% |
| Oracle | 100.00% | 85.00% | 89.29% | 100.00% | 100.00% |
| L4 | 98.33% | 88.33% | 65.51% | 96.67% | 81.36% |

Historical Run IDs:

- L1: `de1809aa-3506-4e04-843b-099f4be00df4`
- L2: `82372eec-204f-4223-b87e-0f26a9ae3fb5`
- Oracle: `388dc6a6-6483-4e11-9b4a-5c935929bd5a`
- L4: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`

### Layer B — zero-model-cost historical offline replay

For each historical scored Sample, the preserved raw `candidate_document` was replayed through the new canonicalizer and the unchanged scorer. Historical `execution_failed` Samples were preserved unchanged. Results were then re-aggregated through the formal Sample → Case → Suite path.

A mandatory self-check first re-scored the historical raw candidate without canonicalization. All four conditions reproduced the stored historical Protocol and metric aggregates exactly. This establishes that the replay path itself did not introduce scoring drift.

### Layer C — fresh canonicalized formal generation

All four conditions were then generated again under the shared `development-v2` output contract using `20 Cases × 3 repeats`.

This layer tests real hosted execution under the new behavior. It does **not** isolate the canonicalizer causally because the model/provider generated new outputs.

## 5. Offline replay result — causal isolation

### 5.1 Summary

| Condition | Protocol before | Protocol after | Evidence before | Evidence after | Changed Samples | Unknown IDs before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 | 96.67% | 96.67% | 51.38% | 51.38% | 0 | 0 → 0 |
| L2 | 90.00% | **95.00%** | 55.57% | **59.46%** | 3 | 6 → 2 |
| Oracle | 100.00% | 100.00% | 89.29% | 89.29% | 0 | 0 → 0 |
| L4 | 81.36% | **96.61%** | 65.51% | **75.88%** | 9 | 12 → 0 |

Failure Type Exact Match was unchanged in every condition. Required Fields Completeness was also unchanged. That is the expected signature of a representation-normalization layer rather than a diagnosis repair layer.

### 5.2 L4 causal effect

Historical L4 contained 59 scored Samples and 11 protocol-invalid Samples. Offline replay changed 9 candidates and recovered all 9 of those Samples:

- Protocol Validity: `48/59 = 81.36%` → `57/59 = 96.61%` (**+15.25 percentage points**)
- Evidence Hit Rate: `65.51%` → `75.88%` (**+10.37 percentage points**)
- `unknown_evidence_id`: `12` → `0`
- duplicate Evidence references: `1` → `0`
- Failure Type Exact Match: `88.33%` → `88.33%`

Recovered L4 Samples:

- `bugswarm-traccar-170287308#repeat-0`
- `bugswarm-apache-struts-190697114#repeat-0`
- `bugswarm-apache-struts-190697114#repeat-2`
- `bugswarm-spring-hateoas-232784946#repeat-0`
- `bugswarm-spring-hateoas-232784946#repeat-1`
- `bugswarm-spring-hateoas-232784946#repeat-2`
- `bugswarm-traccar-166900445#repeat-1`
- `bugswarm-blueflood-80881330#repeat-2`
- `odrepair-dubbo-737f7a7e#repeat-0`

The earlier diagnostic ceiling of `56/59 = 94.92%` considered only unknown-ID recovery. The actual replay reached `57/59` because stable deduplication also recovered the duplicate-only `spring-hateoas#repeat-1` Sample.

### 5.3 L2 causal effect

L2 also contained the same class of mechanical report-realization failure:

- Protocol Validity: `90.00%` → `95.00%` (**+5.00 percentage points**)
- Evidence Hit Rate: `55.57%` → `59.46%` (**+3.89 percentage points**)
- unknown Evidence IDs: `6` → `2`
- Failure Type Exact Match remained `85.00%`

Three invalid Samples were recovered.

This is important because it confirms that the defect is not L4-specific. Shared output infrastructure is the correct scope.

### 5.4 L1 and Oracle controls

Historical L1 and Oracle had no candidate changed by the canonicalizer. Their replay metrics were exactly unchanged.

This is a useful negative control: the resolver does not perturb reports that already use valid frozen coordinates.

## 6. Fresh formal generation

### 6.1 Run identity and execution

| Condition | Run ID | Scored / Planned | Status |
| --- | --- | ---: | --- |
| L1 | `5dd0f286-ae66-4374-a935-bc6d53e15742` | 59 / 60 | `completed_with_sample_failures` |
| L2 | `345b08a2-1a9a-4b7e-be19-4c17721786a9` | 58 / 60 | `completed_with_sample_failures` |
| Oracle | `023d5960-c450-42e1-a516-a874106673f4` | 60 / 60 | `completed` |
| L4 | `d6fee1ba-ddd2-4ed3-ae2f-625603de5fef` | 60 / 60 | `completed` |

Execution failures were preserved rather than silently re-run:

- L1: `bugswarm-sonar-php-206164136#repeat-0` → `model_provider_timeout @ model_provider`
- L2: `github-osquery-issue-7718#repeat-1` and `#repeat-2` → `model_provider_timeout @ evidence_analysis`
- Oracle: none
- L4: none

The L1/L2 failures hit the frozen 600-second request-timeout boundary. They are formal execution observations, not repaired/missing benchmark rows.

### 6.2 Fresh metrics

| Condition | Execution | Failure Type Exact | Evidence Hit | Required Fields | Protocol Validity | Canonicalization changed | Unknown IDs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 | 98.33% | 80.00% | 52.16% | 99.79% | 96.61% | 1 | 4 |
| L2 | 96.67% | 83.33% | 54.15% | 98.33% | **98.28%** | 4 | 0 |
| Oracle | 100.00% | 83.33% | 85.40% | 96.67% | 96.67% | 0 | 0 |
| L4 | 100.00% | 81.67% | **71.83%** | 99.58% | **93.33%** | 4 | 2 |

Fresh L4 remained materially above the historical L4 generation on the two dimensions most directly affected by the historical realization defect:

- Protocol Validity: `81.36%` → `93.33%` (**+11.98 pp**)
- Evidence Hit Rate: `65.51%` → `71.83%` (**+6.32 pp**)

Fresh L2 Protocol Validity rose from historical `90.00%` to `98.28%`.

These directional results are consistent with the replay result, but their exact deltas must not be attributed solely to canonicalization.

## 7. Why fresh-generation deltas are not causal estimates

The fresh Oracle run is the cleanest demonstration of regeneration variance:

```text
canonicalization_changed_samples = 0
```

but its metrics still moved from the historical generation:

- Failure Type Exact: `85.00%` → `83.33%`
- Evidence Hit: `89.29%` → `85.40%`
- Required Fields: `100.00%` → `96.67%`
- Protocol Validity: `100.00%` → `96.67%`

Its two invalid Samples were `invalid_report_type`: the provider/model returned a JSON string containing report text rather than a JSON object. Canonicalization did not touch either output.

Therefore:

> Historical baseline → fresh canonicalized generation = canonicalization + new model/provider sample realization + execution variance.

The causal claim must come from offline replay, where the model candidate is held fixed.

## 8. Residual invalid reports confirm the resolver boundary

Fresh L4 had four protocol-invalid Samples after canonicalization:

| Sample | Error | Interpretation |
| --- | --- | --- |
| `bugswarm-apache-struts-190697114#repeat-0` | `unknown_evidence_id` | Source identity used `struts-messages_en-properties`; the frozen source identity differs. Repair would require guessing a source-name typo. |
| `bugswarm-byte-buddy-149441998#repeat-1` | `unknown_evidence_id` | Source prefix `byte-buddy-dep-dep-pom-xml` does not exist. Repair would require guessing the intended source. |
| `bugswarm-nukkit-94403868#repeat-2` | `missing_required_field` | Non-evidence report error; resolver must not touch it. |
| `idflakies-cukes-http-b483e1a8#repeat-1` | `missing_required_field` | Non-evidence report error; resolver must not touch it. |

The two remaining unknown IDs are deliberately unresolved. Adding `_ ↔ -`, duplicate path-segment deletion, edit distance, basename guessing, nearest-ID selection, or an LLM correction pass would change the component from deterministic coordinate normalization into fuzzy semantic/report repair.

That behavior is out of scope for V1.

## 9. Broad-range expansion and metric limitation

A fresh L1 Struts Sample authored this reference:

```text
log:raw-log:lines-2001-20718
```

Under the frozen overlap rule, the reference deterministically spans every real Canonical Evidence unit from line 2001 through 20718. The candidate therefore changed from `5` raw references to `192` resolved references.

The resolver is behaving correctly according to its contract. However, this exposes a separate scorer limitation:

- Report Evidence Hit is recall-oriented;
- it rewards matching Required Evidence;
- it does not currently penalize citing a very broad number of otherwise-valid Evidence IDs.

A future Evidence Precision / Citation Specificity metric may be warranted if broad over-citation becomes material. That should be an evaluator/scorer evolution with its own experiment. It should **not** be implemented by adding arbitrary width thresholds or heuristics to the canonicalizer.

## 10. Interpretation

The combined evidence supports the following conclusions.

### 10.1 The implementation solves a real mechanical failure mode

The strongest result is the L4 offline replay: 9 historical protocol-invalid Samples become valid, all 12 historical unknown Evidence IDs disappear, the duplicate-only failure is recovered, and taxonomy remains unchanged.

This is direct evidence that part of the historical Oracle↔L4 gap was report representation rather than diagnosis/evidence acquisition.

### 10.2 The behavior belongs at the shared output boundary

L2 also benefits, while L1/Oracle historical outputs are unchanged. The problem is not specific to ReAct control or Tool Policy.

### 10.3 The resolver has a defensible non-semantic boundary

Fresh residual invalid reports show that the implementation does not cross into fuzzy repair. If source identity itself is wrong and the intended source cannot be derived from exact frozen coordinates, normal validation still fails.

### 10.4 Fresh generation confirms operational usefulness but also shows model variance

Fresh L4 Protocol/Evidence remained substantially above the historical L4 generation, but taxonomy and other metrics moved independently. Oracle changed despite zero canonicalization activity. Fresh-generation deltas must therefore be described as operational comparison results, not single-variable causal uplift.

## 11. Decision

`canonical-line-range-normalization-v1` is accepted as the shared Evidence Reference Canonicalization baseline for the current L1/L2/Oracle/L4 comparison generation.

Issue #59 is considered engineering- and experiment-complete once this milestone record is merged.

No further resolver expansion is justified by the current evidence. In particular, do not add fuzzy source correction, semantic Evidence selection, hidden Ground Truth access, or L4-only provenance gates to this version.

The next independent Runtime experiment is L4 **batch + parallel ToolCalls**, motivated by the historical `26` rejected multi-ToolCall IDs and repeated prompt traffic. It must remain a separate treatment so quality and efficiency effects can be measured without conflating them with citation normalization.

## 12. Artifact policy

The complete generated formal `evaluation.json` / `evaluation.md` bundles remain under ignored `.devagentops/...` paths by repository policy. This repository intentionally does not commit every generated run artifact.

For this selected milestone, the committed machine-readable snapshot preserves the Run IDs, fingerprints, aggregate metrics, replay results, execution failures, protocol-invalid details, and the interpretation boundary needed to audit the conclusion:

- [`evidence-reference-canonicalization-results-2026-08-19.json`](evidence-reference-canonicalization-results-2026-08-19.json)

Historical baseline milestone files remain immutable and must not be edited to make them appear to have used the new behavior.
