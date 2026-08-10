# N22 — bugswarm-pytest-jira-xray-13013454823 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `test_assertion_failure`
**Fingerprint:** `ca97bbe4bb5aecbc76f8352b2c0b73dd25c2441dc122a9391e9907d70176e9c3` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/13013454823/raw/ ; upstream exact/relevant revision: https://github.com/fundakol/pytest-jira-xray/commit/019244aa79f9adc182ee138955cc50efe37df9b6
- Attribution/license note: Apache-2.0 upstream repository; public BugSwarm historical failed-job attribution. Passing revision is a sibling from a common base, not a direct child fix.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `019244aa79f9adc182ee138955cc50efe37df9b6` with 6 bounded investigation files:

- `pyproject.toml`
- `requirements-tests.txt`
- `setup.cfg`
- `src/pytest_xray/evidence.py`
- `tests/conftest.py`
- `tests/test_xray_plugin.py`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: A nested Jira/Xray evidence payload assertion differs only in the casing of the content-type key.
- Root cause: The implementation emits contentType, but the expected fixtures on the failing branch still use ContentType. A contract-key change left the test oracle stale.
- Primary type: `test_assertion_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Synchronize the expected evidence fixtures with the implementation's contentType key and review sibling fixtures for the same stale casing.

## Evidence Ground Truth draft

- Required (3): `log:raw-log:lines-0301-0400`, `repo:src-pytest-xray-evidence-py:lines-0001-0037`, `repo:tests-test-xray-plugin-py:lines-0101-0200`
- Optional (0): none
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Medium: failing and passing revisions are sibling histories; the package correctly uses only the failing branch, but provenance must not be narrated as a direct child fix.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
