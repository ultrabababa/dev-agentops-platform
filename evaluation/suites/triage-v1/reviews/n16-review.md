# N16 — github-gptme-pr-1968 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `timeout_or_flaky_failure`
**Fingerprint:** `8b1f851c8181dbe4016b86595492315a6fdde049f813fc0e53c945d2772eaf1d` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://github.com/gptme/gptme/pull/1968; failed job https://github.com/gptme/gptme/actions/runs/23841222952/job/69497065608 ; upstream exact/relevant revision: https://github.com/gptme/gptme/commit/f48de363aa956caae8789a9b751d7631fd44fe3c
- Attribution/license note: MIT upstream repository; public GitHub PR failure excerpt and failed-job metadata attribution.
- raw.log: One verbatim failure sentence preserved in upstream PR #1968; expired Actions output was not reconstructed.

## Physical repository universe

Exact/relevant revision `f48de363aa956caae8789a9b751d7631fd44fe3c` with 4 bounded investigation files:

- `gptme/tools/subagent/api.py`
- `pyproject.toml`
- `tests/conftest.py`
- `tests/test_tools_subagent.py`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: A subagent test intermittently reads mock call metadata before the background thread has populated it.
- Root cause: The implementation publishes the subagent in the shared list before starting its background thread, while the test treats list growth as completion and immediately indexes mock_create_thread.call_args. Scheduler interleaving can leave call_args as None.
- Primary type: `timeout_or_flaky_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Synchronize the test with completion of the spawned subagent thread before inspecting mock call arguments.

## Evidence Ground Truth draft

- Required (3): `log:raw-log:lines-0001-0001`, `repo:tests-test-tools-subagent-py:lines-0801-0900`, `repo:gptme-tools-subagent-api-py:lines-0301-0400`
- Optional (0): none
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: High: the Actions log expired; raw.log is a 1-line verbatim PR-preserved failure observation, so Agent-visible failure context is unusually thin.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
