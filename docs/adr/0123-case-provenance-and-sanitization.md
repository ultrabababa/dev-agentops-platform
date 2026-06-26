# Case Provenance and Sanitization

## Status

Accepted.

## Context

V1 depends on offline case packages for repeatable evaluation and portfolio demonstration. If case artifacts come from unknown, private, or unsanitized sources, the evaluation suite becomes hard to trust, hard to publish, and risky to share.

## Decision

V1 offline cases must record case provenance and may use only deliberately constructed cases or cases from sources that are public and permitted for this use. Logs, repository evidence snapshots, project knowledge excerpts, and expected-answer artifacts must be reviewed and sanitized before entering a formal evaluation suite.

## Alternatives Considered

- Use raw production or private CI logs for realism. This creates avoidable privacy, secret leakage, and publication risks.
- Skip provenance until the dataset grows. Retrofitting source and permission history later is unreliable.

## Consequences

The V1 evaluation suite is safer to inspect, publish, and demo. Dataset creation requires a little more discipline, but that cost is small compared with discovering later that a case cannot be shared or contains sensitive data.

## Implementation Notes

- Case manifests should record provenance fields such as source type, source URL or construction note, license or permission status, author/reviewer, and sanitization status.
- Sanitization should cover secrets, tokens, personal data, private hostnames, private repository names, customer identifiers, and internal-only URLs.
- `eval doctor` should fail formal evaluation when a suite references cases without accepted provenance or sanitization metadata.
- Artificially constructed cases should be marked as constructed rather than pretending to be real production incidents.
