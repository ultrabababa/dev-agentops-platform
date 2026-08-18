# Structured Report and Evidence Contract

## Status

Accepted and implemented.

## Context

Evaluation requires reports that can be validated, scored, and reviewed deterministically. Natural-language evidence descriptions are not enough to measure whether the system found and cited the expected facts.

## Decision

Structured Triage Report V1 is a versioned product/evaluation contract outside the Component Registry. Reports cite stable Canonical Evidence IDs through `evidence_references`.

Offline Case Schema V2 separates Ground Truth:

```text
evaluator/required-evidence.json
= Evidence Ground Truth

 evaluator/expected-answer.json
= Diagnosis Ground Truth
```

Required/Optional Evidence IDs are **not** stored in Expected Answer. Evidence Hit Rate compares final report citations against hidden Required Evidence IDs through the deterministic scorer.

Invalid/unknown Evidence IDs remain protocol/evidence-validation failures rather than being repaired.

## L4 citation refinement

ADR 0128 keeps the existing report/scorer contract unchanged. To let L4 cite valid IDs without a hidden Runtime mapping helper, the complete answer-neutral Canonical coordinate vocabulary may be disclosed in L4's initial model-visible input.

This does not expose Evidence Ground Truth: the model is not told which IDs are Required/Optional, and physical content remains tool-acquired.

Thus L4 badcase analysis can distinguish:

```text
physical fact not found
vs
fact found but Canonical ID not cited
vs
correct ID cited but diagnosis wrong
```

## Consequences

- report validation/scoring remains deterministic across L1/L2/L4/Oracle;
- Case Ground Truth remains hidden and separated by responsibility;
- L4 does not require scorer changes or an automatic source-span-to-ID annotator;
- unknown citations remain measurable model/report failures.

## Implementation Notes

- report schema/version is recorded in formal identities where applicable;
- canonical Evidence IDs come from frozen Case packages;
- current Formal Case Physical Universe does not include Project Knowledge; future independently versioned knowledge treatments must preserve provenance if they ever introduce report-citable evidence;
- public diagnostics expose only non-leaking aggregate/count information; hidden Required IDs and missed Required IDs stay evaluator-only;
- report invalidity is a scored capability outcome when the model had a valid execution opportunity, not automatically an infrastructure failure.

## Consolidates

Micro ADRs: `0102`, `0103`, `0104`, `0105`, `0106`, `0107`, `0108`.

## Refined By

- ADR 0126 — Ground Truth split and Canonical source coordinates;
- ADR 0128 — L4 citation-vocabulary visibility and terminal semantics.
