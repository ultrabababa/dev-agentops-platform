# N07 — bugswarm-mypy-237548392 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `lint_or_type_failure`
**Fingerprint:** `38d046472bb63fae3bf2f779aacd105ac643bfbed42c51bbadd590c226bdb4fe` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/237548392/raw/ ; upstream exact/relevant revision: https://github.com/python/mypy/commit/ec1efc4f95a9ee2abca72e9cef4304a19eb5366f
- Attribution/license note: MIT upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `ec1efc4f95a9ee2abca72e9cef4304a19eb5366f` with 5 bounded investigation files:

- `.travis.yml`
- `mypy/test/config.py`
- `mypy/test/helpers.py`
- `mypy/test/testcheck.py`
- `runtests.py`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: mypy rejects its own test package because it cannot infer the generic type argument of retry_on_error.
- Root cause: retry_on_error promises to return the callback's generic result, but callers use side-effect-only lambdas whose return contract provides no useful type argument. The helper signature is over-general for its use.
- Primary type: `lint_or_type_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Give retry_on_error a side-effect callback contract such as Callable[[], Any] returning None, consistent with the call sites.

## Evidence Ground Truth draft

- Required (3): `log:raw-log:lines-2801-2856`, `repo:mypy-test-helpers-py:lines-0201-0300`, `repo:mypy-test-testcheck-py:lines-0101-0200`
- Optional (0): none
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Medium: the checker points at a call site, and diagnosis requires relating it to the generic helper contract.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
