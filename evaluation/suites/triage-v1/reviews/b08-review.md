# B08 — bugswarm-traccar-166900445 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `config_or_environment_failure`
**Fingerprint:** `adf97c15a24b0d407ad9d6659b7e2ccaf4ed29f5e92300bce44575bb5748199a` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/166900445/raw/ ; upstream exact/relevant revision: https://github.com/traccar/traccar/commit/18d39ff2412b9aced899915d0187f21eb25f49b6
- Attribution/license note: Apache-2.0 upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `18d39ff2412b9aced899915d0187f21eb25f49b6` with 4 bounded investigation files:

- `.travis.yml`
- `pom.xml`
- `src/org/traccar/notification/NotificationMail.java`
- `test/org/traccar/notification/NotificiationMailTest.java`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: The ordinary CI test suite attempts an external SMTP connection and receives a 535 authentication rejection.
- Root cause: NotificiationMailTest is an environment-dependent integration test embedded in the normal suite and directly relies on external SMTP authentication values that are invalid for the historical CI run.
- Primary type: `config_or_environment_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Move the credential-dependent SMTP check to a separately managed integration test using injected secrets and a controlled test service; do not commit credentials.

## Evidence Ground Truth draft

- Required (2): `log:raw-log:lines-2401-2500`, `repo:test-org-traccar-notification-notificiationmailtest-java:lines-0001-0059`
- Optional (1): `repo:src-org-traccar-notification-notificationmail-java:lines-0001-0100`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Replaced the historical personal email address in the source header; production SMTP configuration structure is unchanged.
- Known scientific risk: Medium-high: external-service structure is preserved after sanitization, but literal endpoint/credential identity is intentionally unavailable.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
