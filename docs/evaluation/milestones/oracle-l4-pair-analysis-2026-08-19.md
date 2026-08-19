# Oracle ↔ L4 Pair Analysis Findings — 2026-08-19

## Overview

This document records the Human / AI review of the first real Oracle ↔ L4 Pair Analyzer output for `triage-suite-v1` using MiniMax-M3.

The Pair Analyzer itself performs only deterministic alignment, aggregation, gap calculation, and evidence packaging. The causal interpretations in this document were made after reviewing the generated `pair-analysis.md` across all 15 detailed-review Cases.

This is a diagnostic analysis milestone. It is not a new Runtime result, not a new scorer, and not a replacement for the frozen L4 V1 baseline.

## Pair identity

- Oracle run: `388dc6a6-6483-4e11-9b4a-5c935929bd5a`
- L4 run: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`
- Suite: `triage-suite-v1` version `1`
- Model: `MiniMax-M3`
- Gap convention: `Oracle - L4`
- Primary comparison unit: Case aggregate
- Repeat indexes are not treated as paired Oracle/L4 samples

The generated Pair Analyzer output covered all 20 Cases and expanded 15 Cases for detailed review.

## Suite realization gap

| Metric | Oracle | L4 | Gap |
|---|---:|---:|---:|
| Failure Type Exact Match | `0.8500` | `0.8833` | `-0.0333` |
| Evidence Hit Rate | `0.8929` | `0.6551` | `+0.2377` |
| Protocol Validity | `1.0000` | `0.8136` | `+0.1864` |
| Required Fields Completeness | `1.0000` | `0.9667` | `+0.0333` |
| Execution Coverage | `1.0000` | `0.9833` | `+0.0167` |

The suite-level result is therefore not a generic "Oracle is better" outcome.

L4 slightly exceeds Oracle on taxonomy exact match while remaining substantially behind on Evidence Hit and protocol validity. The largest current realization gaps are therefore evidence/report realization rather than raw taxonomy classification.

## Protocol failure concentration

Among the `59` scored L4 Samples:

- protocol-valid Samples: `48`
- protocol-invalid Samples: `11`
- protocol validity: `81.36%`

The invalid Samples break down as:

- `8/11` Samples with one or more `unknown_evidence_id` errors
- `2/11` Samples with `invalid_report_type`
- `1/11` Sample with `duplicate_evidence_reference`

If an idealized coordinate-assistance treatment removed only the eight unknown-ID failures while changing nothing else, protocol validity would have an upper-bound counterfactual of:

```text
56 / 59 = 94.92%
```

This is not a forecast for L4.1. It only shows that Canonical Evidence coordinate failures are large enough to justify one isolated ablation.

## Human / AI badcase findings

The detailed review shows four materially different failure mechanisms. These are review interpretations, not persisted Pair Analyzer labels.

### 1. Canonical coordinate / final-report mapping failures

Several Cases show a clean pattern:

```text
Agent inspected the relevant physical content
  -> diagnosis was substantially correct
  -> final report invented or malformed a Canonical Evidence ID
  -> protocol validity and/or Evidence Hit collapsed
```

Strong examples:

- `bugswarm-traccar-170287308`
  - all three L4 repeats selected the correct taxonomy and reconstructed the decoder-regex failure;
  - repeat `0` cited the invented log span `log:raw-log:lines-2300-2632` and became protocol-invalid;
  - repeats using valid Canonical IDs achieved full Evidence Hit.

- `bugswarm-apache-struts-190697114`
  - all three repeats correctly diagnosed the `to large` versus `too large` assertion mismatch;
  - repeats `0` and `2` invented non-canonical log spans and became protocol-invalid;
  - the core diagnosis was already correct before the final citation failure.

- `bugswarm-spring-hateoas-232784946`
  - all three repeats correctly identified the Spring 5 / Jackson 2.8.5 incompatibility;
  - all three reports were protocol-invalid: two from unknown Evidence IDs and one from a duplicate citation;
  - this is the strongest concentration of final-report realization loss in one Case.

- `bugswarm-traccar-166900445`
  - two repeats were fully correct;
  - the remaining repeat still identified the placeholder SMTP credential mechanism but cited an invented raw-log coordinate and became protocol-invalid.

- `bugswarm-blueflood-80881330`
  - one repeat was an invalid outer report type;
  - one repeat correctly identified the `metrics` versus `graphite_event` mapping mismatch but invented a repository Evidence ID;
  - the successful repeat shows the diagnosis can be realized under the baseline when the citation is valid.

- `odrepair-dubbo-737f7a7e`
  - L4 reconstructed the stale RpcContext / AsyncContext pollution chain strongly across repeats;
  - one otherwise strong repeat lost protocol validity because it invented a repository coordinate.

These Cases provide direct evidence that part of the Oracle-L4 gap is not evidence acquisition or causal reasoning. It is failure to serialize already-observed evidence back into the exact frozen Canonical coordinate vocabulary.

### 2. Investigation-depth / evidence-acquisition failures

Other Cases do not support a coordinate-only explanation.

- `bugswarm-retrofit-113047638`
  - L4 repeatedly recognized that `ProtoRequestBodyConverter.convert(null)` was not reached;
  - it generally stopped before reconstructing the full lazy-execution chain through `MethodHandler -> OkHttpCall.createRawCall -> RequestFactory.create -> execute/enqueue`;
  - the missing evidence is primarily investigation depth, not final coordinate mapping.

- `bugswarm-sonar-php-206164136`
  - shallow repeats stopped at the symptom that TESTS measures were not persisted;
  - the strongest repeat continued through `PhpUnitService` / `PhpUnitTestFileReport` into the fixture XML and found that `Monkey.php` was absent from the report paths;
  - the repeat-level improvement tracks deeper investigation rather than a citation-format fix.

These Cases should not be used as evidence that Canonical coordinate assistance solves the whole realization gap. They point toward later Retrieval / investigation-strategy work.

### 3. Evidence-selection gaps after broadly correct diagnosis

Several Cases show correct or near-correct causal diagnosis with protocol-valid reports, but weaker coverage of the frozen Required Evidence set.

Examples include:

- `github-tan-cli-30459137058`
- `bugswarm-cola-12505170926`
- `idflakies-cukes-http-b483e1a8`

In these Cases, simply making physical-span-to-coordinate mapping easier may not recover all Evidence Hit gap. The Agent must still decide which observed evidence is important enough to cite.

### 4. Genuine causal-reasoning failures

`odrepair-remoting-abf0455a` remains the cleanest reasoning bottleneck.

Oracle and L4 both achieved `0/3` taxonomy exact match. Protocol was valid throughout, and Oracle already supplied the reviewed evidence directly. Neither condition reliably reconstructed the frozen causal chain:

```text
polluter test
  -> invalid regex override during ClassFilter static initialization
  -> class initialization becomes poisoned in the JVM
  -> later victim test observes the failure
```

This Case should not motivate more citation assistance, planner machinery, or extra tools. It demonstrates a reasoning limitation that remains even after relevant evidence is available.

## Adaptive investigation can add real value

The comparison also contains clear negative-gap Cases where L4 outperforms Oracle.

### `github-osquery-issue-7718`

- Oracle taxonomy exact match: `0/3`
- L4 taxonomy exact match: `3/3`
- Evidence Hit: equal at the Case aggregate
- Protocol: fully valid in both conditions

L4 autonomously discovered the startup-readiness race:

```text
test pre-creates pidfile
  -> pidfile existence is used as readiness
  -> readiness check can pass before SIGINT handler installation
  -> SIGINT arrives too early
  -> default signal termination returns -2
```

Oracle received the reviewed evidence but still focused on the visible signal-handler symptom. This is strong evidence that adaptive investigation itself can improve causal reconstruction.

### `odrepair-dubbo-737f7a7e`

L4 also exceeded Oracle on taxonomy aggregate (`2/3` exact versus `1/3`) while recovering the concrete stale thread-local / AsyncContext victim chain in detail.

These Cases argue against replacing L4 investigation with an Oracle-like evidence-delivery shortcut. The next change should preserve adaptive investigation and remove only a demonstrated realization defect.

## Decision: one narrow L4.1 ablation

Human / AI review verdict: **GO for one narrow development ablation.**

The proposed treatment is:

> Canonical Evidence Coordinate Assistance for physical evidence already observed by the Agent.

The experiment should preserve the L4 V1 baseline and change only the answer-neutral coordinate-assistance behavior.

It must not:

- expose Required Evidence labels;
- reveal which Canonical coordinates matter;
- expose Expected Answer or evaluator reasoning;
- silently repair the final report after generation;
- add planner, reflection, compaction, or a different model;
- change the frozen scorer or Case Ground Truth;
- change the investigation step budget merely to improve scores.

The empirical question is deliberately narrow:

> If L4 can deterministically recover the valid Canonical coordinate(s) corresponding to physical evidence it has actually inspected, do protocol validity and Evidence Hit improve without degrading taxonomy or changing investigation behavior?

## Development ablation scope

Before any new 20 × 3 formal run, use the six Cases that produced `unknown_evidence_id` failures in the L4 baseline:

```text
bugswarm-traccar-170287308
bugswarm-apache-struts-190697114
bugswarm-spring-hateoas-232784946
bugswarm-traccar-166900445
bugswarm-blueflood-80881330
odrepair-dubbo-737f7a7e
```

Recommended first experiment:

```text
6 Cases × 3 repeats = 18 Samples
```

The development ablation should be considered promising only if:

- unknown/invented Evidence IDs are materially reduced or eliminated;
- protocol validity improves accordingly;
- Evidence Hit improves where the baseline diagnosis had already located relevant physical content;
- taxonomy does not materially regress;
- no evaluator-only information is exposed;
- the new behavior has explicit Treatment / Component identity rather than being a hidden baseline repair.

If the 18-Sample development result does not show this pattern, stop the ablation rather than expanding the Runtime surface.

If it does, a full-Suite L4.1 formal comparison can then be justified.

## What remains outside L4.1

The Pair Analysis also establishes what should not be mixed into this ablation:

- `retrofit` / `sonar-php` style investigation-depth problems belong to later Retrieval or investigation-strategy experiments;
- evidence-selection gaps require separate analysis from coordinate validity;
- `odrepair-remoting-abf0455a` demonstrates a causal-reasoning limitation that coordinate assistance cannot solve;
- the single `pygithub` HTTP 529 sample remains an execution-reliability observation, not a diagnosis-quality failure.

Keeping these mechanisms separate is necessary to preserve interpretability of the next result.

## Conclusion

The Oracle ↔ L4 comparison does not support a single generic explanation for the realization gap.

The observed gap decomposes into at least:

```text
Canonical coordinate / report realization
Investigation depth / evidence acquisition
Evidence selection
Causal reasoning
Operational execution reliability
```

The most actionable next intervention is the first category because it is concentrated, directly observable in trajectories and validation errors, and can be changed without redesigning the L4 Runtime.

At the same time, negative-gap Cases such as `github-osquery-issue-7718` show that autonomous L4 investigation already contributes capability that the Oracle condition does not automatically realize.

Therefore the current direction is:

```text
preserve L4 V1 baseline
  -> run one Canonical-coordinate-assistance L4.1 development ablation
  -> decide from the 18-Sample evidence whether a full formal L4.1 run is warranted
  -> then move on rather than stacking unrelated Runtime features
```

## Related records

- [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../oracle-evidence-diagnostic-condition.md)
- [Oracle MiniMax-M3 Full-Suite Milestone](oracle-minimax-m3-full-suite-2026-08-15.md)
- [L4 MiniMax-M3 Full-Suite Milestone](l4-minimax-m3-full-suite-2026-08-19.md)
- [Formal Evaluation Methodology](../formal-evaluation-methodology.md)
