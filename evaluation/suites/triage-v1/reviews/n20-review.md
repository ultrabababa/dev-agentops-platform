# N20 — github-tan-cli-30459137058 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `dependency_or_install_failure`
**Fingerprint:** `4d6e25ab8a20c9017cdaa479c071177bd9f80e06e5bd5bcc55bfaa5431490332` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://github.com/alplabai/tan-cli/actions/runs/30459137058 ; upstream exact/relevant revision: https://github.com/alplabai/tan-cli/commit/3043521c5ef278d79d34045bdb2116e81e9c661d
- Attribution/license note: Apache-2.0 upstream repository; public GitHub Actions run attribution.
- raw.log: Complete historical first-blink GitHub Actions job log from run 30459137058.

## Physical repository universe

Exact/relevant revision `3043521c5ef278d79d34045bdb2116e81e9c661d` with 4 bounded investigation files:

- `.github/workflows/parity.yml`
- `Cargo.toml`
- `README.md`
- `install.sh`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: The first-blink job fails to build hidapi because libudev.h is absent, then later surfaces misleading elftools import errors from the incomplete environment.
- Root cause: The clean Linux runner prerequisite list omits libudev development headers required by hidapi. Bootstrap continues after the failed requirements install, causing downstream missing-module symptoms.
- Primary type: `dependency_or_install_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Install the libudev development package before bootstrap and fail fast when requirements installation leaves the environment incomplete.

## Evidence Ground Truth draft

- Required (2): `log:raw-log:lines-0901-1000`, `repo:github-workflows-parity-yml:lines-0601-0700`
- Optional (1): `log:raw-log:lines-3301-3400`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: High: the first causal native-build error is far from the terminal symptom, and the pinned SDK supplies part of the install behavior outside the allowed repository universe.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
