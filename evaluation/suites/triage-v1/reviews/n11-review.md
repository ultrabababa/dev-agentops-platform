# N11 — bugswarm-testng-64757057 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `config_or_environment_failure`
**Fingerprint:** `a0543dffe89827676251f6ede4cdfc78d7529daba7125a6c6c173efb4f22b5e8` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/64757057/raw/ ; upstream exact/relevant revision: https://github.com/testng-team/testng/commit/dc1efd4c626362bb469813229fb5b48b660f1bf3
- Attribution/license note: Apache-2.0 upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `dc1efd4c626362bb469813229fb5b48b660f1bf3` with 3 bounded investigation files:

- `.travis.yml`
- `build.gradle`
- `gradle/publishing.gradle`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: Gradle reaches signArchives and fails because no signatory is configured, despite the CI job not publishing artifacts.
- Root cause: The publishing configuration makes archive signing unconditional for normal builds. A non-publishing CI environment has no signing identity, so the task graph fails at signArchives.
- Primary type: `config_or_environment_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Require archive signing only for the upload/publish task path and keep ordinary CI builds independent of signing credentials.

## Evidence Ground Truth draft

- Required (2): `log:raw-log:lines-1101-1200`, `repo:gradle-publishing-gradle:lines-0001-0032`
- Optional (1): `repo:build-gradle:lines-0001-0100`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Applied the Human-approved strict allowlist: retained only the contiguous signing/task-graph section from exact revision lines 60-91; excluded unrelated publishing credentials and service configuration entirely.
- Known scientific risk: High: strict allowlist extraction deliberately changes physical file extent; Human Review must confirm that the 32-line exact excerpt is sufficient and not misleading.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
