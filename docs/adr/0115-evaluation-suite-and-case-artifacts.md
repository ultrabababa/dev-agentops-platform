# Evaluation Suite and Case Artifacts

## Status

Accepted.

## Context

Evaluation scores are meaningful only when the case set, expected answers, evidence artifacts, and scoring data are stable. V1 also needs small enough data to build quickly while covering the main CI/test failure types.

## Decision

V1 will start with a small balanced immutable evaluation suite of roughly 20 offline case packages. Suite manifests explicitly list cases and weights. Suite versions, case packages, expected answers, raw logs, preprocessed log chunks, repository evidence snapshots, and relevant fingerprints are frozen for formal evaluation.

## Alternatives Considered

- Start with a large benchmark. This would slow down labeling and badcase review before the eval loop is proven.
- Discover cases by scanning directories. This allows draft cases and temporary files to alter formal suites.
- Re-chunk logs or index the current working tree during evaluation. This makes results drift with preprocessing or local code changes.

## Consequences

Formal evaluation is repeatable and explainable. Case and suite changes create new versions, and anchor conditions can be rerun to explain score shifts.

## Implementation Notes

- V1 uses equal case weighting in the balanced suite.
- Expected answers freeze with suite versions.
- Case packages include case schema version, raw log, frozen log chunks, log chunk fingerprint, repository evidence snapshot, expected answer, forbidden actions, and case fingerprint.
- Suite fingerprint composes suite manifest data and case fingerprints.
- Formal evaluation validates the component, case, suite, and condition fingerprint chain before running.
- Provide `eval doctor` to validate configuration and fingerprints without calling the model.

## Consolidates

Micro ADRs: `0024`, `0025`, `0026`, `0061`, `0062`, `0080`, `0081`, `0082`, `0083`, `0084`, `0085`, `0086`, `0087`, `0088`, `0089`, `0090`.
