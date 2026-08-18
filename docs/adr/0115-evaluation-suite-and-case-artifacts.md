# Evaluation Suite and Case Artifacts

## Status

Accepted and implemented for `triage-suite-v1`.

## Context

Evaluation scores are meaningful only when the Case set, Physical Artifacts, Canonical coordinates, Ground Truth and scoring-relevant identities are stable.

## Decision

V1 uses an explicit immutable Formal Suite manifest. The first Suite is now frozen as:

```text
triage-suite-v1
= 20 Offline Case Schema V2 packages
= 5 Failure Types × 4 Cases each
= equal case weighting
```

Suite membership is manifest-driven; formal loading does not discover Cases by directory scan.

Every Formal Case uses Schema V2:

```text
case.json
physical-artifacts/
canonical-evidence/
evaluator/
```

Physical Artifacts contain the raw log and bounded exact-revision repository snapshot. Canonical Evidence contains answer-neutral source coordinates. `evaluator/required-evidence.json` and `evaluator/expected-answer.json` separately hold Evidence and Diagnosis Ground Truth.

Case/Suite fingerprints freeze the scoring-relevant package state. Runtime tools, retrieval configuration and Agent behavior are Treatment variables and must not rewrite the frozen Case identity.

## Current state

Earlier “roughly 20 Cases”, Schema V1 log-chunk/repository-evidence wording, B04 calibration-only status and “Canonicalization Profile still to be frozen” are superseded for the active V1 Suite.

Current Formal foundation includes:

- 20 frozen V2 Cases;
- frozen Canonicalization Profile v1;
- Human-reviewed provenance/sanitization/Required Evidence/Expected Answer;
- preserved L1/L2/Oracle MiniMax-M3 20×3 milestones over the frozen Suite.

## Alternatives Considered

- Large benchmark first: slows review before infrastructure stabilizes.
- Directory scanning: allows draft/temp files to alter formal identity.
- Re-chunking or reading current working tree during formal runs: introduces drift.
- Keep Schema V1 after physical/canonical/evaluator conflation was known: undermines evidence-acquisition experiments.

## Consequences

Formal comparisons can hold the evaluation world fixed while varying Runtime/Treatment behavior. Any change to frozen Case content, Canonical coordinates or Ground Truth requires a new Case/Suite identity rather than an in-place edit.

## Implementation Notes

- `eval doctor` verifies Matrix/component/Suite/Case/fingerprint integrity before model calls;
- Suite fingerprint composes explicit manifest data and verified Case fingerprints;
- provenance and sanitization review state are part of formal eligibility;
- L4 uses the same frozen Suite and scorer; it must not create new Cases or re-curate Ground Truth as part of Issue #52.

## Consolidates

Micro ADRs: `0024`, `0025`, `0026`, `0061`, `0062`, `0080`, `0081`, `0082`, `0083`, `0084`, `0085`, `0086`, `0087`, `0088`, `0089`, `0090`.

## Refined By

- ADR 0125 — Evidence Universe/access;
- ADR 0126 — Schema V2 physical/canonical/evaluator split;
- ADR 0128 — L4 condition-specific visibility.
