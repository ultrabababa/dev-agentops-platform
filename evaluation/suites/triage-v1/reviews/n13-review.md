# N13 — bugswarm-appier-113213406 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `dependency_or_install_failure`
**Fingerprint:** `da37b25bbcd12acefcbc706e23988bc04a5685732961328b65acb1b0483212ca` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/113213406/raw/ ; upstream exact/relevant revision: https://github.com/hivesolutions/appier/commit/2b7fc2f824696a408d6c857fb98bab593c4def41
- Attribution/license note: Apache-2.0 upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `2b7fc2f824696a408d6c857fb98bab593c4def41` with 6 bounded investigation files:

- `.travis.yml`
- `requirements.txt`
- `setup.py`
- `src/appier/base.py`
- `src/appier/data.py`
- `src/appier/test/model.py`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: The ADAPTER=tiny CI job reaches six model-test errors because TinyDB is not installed.
- Root cause: The tiny adapter path imports tinydb, but the failing revision's dependency manifest omits that package. The CI matrix validly selects the path; the package declaration is incomplete.
- Primary type: `dependency_or_install_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Add TinyDB to the installation requirements used by the tiny adapter job and keep the matrix selection unchanged.

## Evidence Ground Truth draft

- Required (4): `log:raw-log:lines-0901-1000`, `repo:travis-yml:lines-0001-0031`, `repo:src-appier-data-py:lines-0001-0100`, `repo:src-appier-base-py:lines-0501-0600`
- Optional (1): `log:raw-log:lines-1001-1056`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Medium: dependency absence is established by combining matrix selection, import site, and the bounded requirements file.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
