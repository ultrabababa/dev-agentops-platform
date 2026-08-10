# N12 — bugswarm-django-coupons-89457805 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `test_assertion_failure`
**Fingerprint:** `df3f7d3d61de07601414651ac769e68532b8552e2470f5b0b03601a3132296a0` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/89457805/raw/ ; upstream exact/relevant revision: https://github.com/byteweaver/django-coupons/commit/4776a4e472e3a14cf475e95f0e146fc3f79b50eb
- Attribution/license note: BSD-3-Clause upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `4776a4e472e3a14cf475e95f0e146fc3f79b50eb` with 7 bounded investigation files:

- `.travis.yml`
- `coupons/forms.py`
- `coupons/models.py`
- `coupons/tests/test_use_cases.py`
- `requirements.txt`
- `setup.py`
- `tox.ini`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: One Django coupon test fails on a Unicode-marked ValidationError representation while 24 sibling tests pass.
- Root cause: The test compares a stringified form-error payload whose Python 2 representation exposes a Unicode prefix. The assertion is coupled to representation details instead of the semantic form.errors mapping.
- Primary type: `test_assertion_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Assert the semantic form.errors structure rather than a stringified ValidationError representation.

## Evidence Ground Truth draft

- Required (2): `log:raw-log:lines-0301-0400`, `repo:coupons-tests-test-use-cases-py:lines-0001-0078`
- Optional (1): `repo:coupons-forms-py:lines-0001-0061`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Low-medium: the representation mismatch is visible, while semantic-vs-string diagnosis still requires the test source.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
