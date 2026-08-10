# N18 — github-osquery-issue-7718 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `timeout_or_flaky_failure`
**Fingerprint:** `d7cbe643359ee488d56d1b2680170083f955eb2c1b7dcb2d0ec63c29edf843c6` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://github.com/osquery/osquery/issues/7718 ; upstream exact/relevant revision: https://github.com/osquery/osquery/commit/aaf2853071c61f54ea737cf938601959fd74f571
- Attribution/license note: Apache-2.0 OR GPL-2.0-only upstream repository; public GitHub issue traceback attribution.
- raw.log: Complete fenced traceback embedded in upstream issue #7718.

## Physical repository universe

Exact/relevant revision `aaf2853071c61f54ea737cf938601959fd74f571` with 4 bounded investigation files:

- `CMakeLists.txt`
- `osquery/core/init.cpp`
- `tools/tests/test_base.py`
- `tools/tests/test_osqueryd.py`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: test_daemon_sigint intermittently observes raw SIGINT exit -2 instead of the daemon's clean exit 0.
- Root cause: The test pre-creates the pidfile used as its readiness signal, so its wait can finish before the daemon installs the SIGINT handler. Signal timing then decides whether the default disposition kills the process.
- Primary type: `timeout_or_flaky_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Do not pre-create the readiness pidfile; clear stale state and wait for the daemon-created readiness signal before sending SIGINT.

## Evidence Ground Truth draft

- Required (2): `log:raw-log:lines-0001-0009`, `repo:tools-tests-test-osqueryd-py:lines-0101-0200`
- Optional (1): `repo:osquery-core-init-cpp:lines-0301-0400`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Medium-high: the issue preserves a complete traceback but not the full CI job; process exit semantics and readiness code carry the diagnosis.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
