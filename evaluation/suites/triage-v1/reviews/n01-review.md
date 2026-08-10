# N01 — idflakies-cukes-http-b483e1a8 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `timeout_or_flaky_failure`
**Fingerprint:** `fdbba293e06a32285b78acb3573fa40208d0722bf42ef2644f2cf151940bec74` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://github.com/UT-SE-Research/iDFlakies/blob/master/scripts/flaky-lists-files/cukes-http ; upstream exact/relevant revision: https://github.com/ctco/cukes/commit/b483e1a8f261b80a66291a42fc455256b0b5059c
- Attribution/license note: Apache-2.0 upstream repository; public iDFlakies committed benchmark-record attribution.
- raw.log: Complete 37-line committed iDFlakies JSON record; the separate original-order file remains curator-only.

## Physical repository universe

Exact/relevant revision `b483e1a8f261b80a66291a42fc455256b0b5059c` with 10 bounded investigation files:

- `cukes-core/pom.xml`
- `cukes-core/src/main/java/lv/ctco/cukes/core/CukesOptions.java`
- `cukes-core/src/main/java/lv/ctco/cukes/core/internal/context/GlobalWorld.java`
- `cukes-core/src/main/java/lv/ctco/cukes/core/internal/context/GlobalWorldFacade.java`
- `cukes-core/src/main/java/lv/ctco/cukes/core/internal/di/SingletonObjectFactory.java`
- `cukes-http/pom.xml`
- `cukes-http/src/main/java/lv/ctco/cukes/http/facade/HttpAssertionFacadeImpl.java`
- `cukes-http/src/main/java/lv/ctco/cukes/http/matchers/StatusCodeMatcher.java`
- `cukes-http/src/test/java/lv/ctco/cukes/http/facade/HttpAssertionFacadeImplTest.java`
- `pom.xml`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: The same HTTP assertion test passes in the intended run but fails after a max-size test in the revealed order.
- Root cause: The preceding test leaves ASSERTS_STATUS_CODE_MAX_SIZE=5 in singleton GlobalWorld state. The victim enables body display without resetting that key, so the assertion formatter reuses leaked state and the outcome depends on test order.
- Primary type: `timeout_or_flaky_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Reconstruct or clear GlobalWorld between tests, or make each test establish and clean up every configuration key it uses.

## Evidence Ground Truth draft

- Required (4): `log:raw-log:lines-0001-0037`, `repo:cukes-http-src-test-java-lv-ctco-cukes-http-facade-httpassertionfacadeimpltest-java:lines-0101-0198`, `repo:cukes-http-src-main-java-lv-ctco-cukes-http-facade-httpassertionfacadeimpl-java:lines-0001-0100`, `repo:cukes-core-src-main-java-lv-ctco-cukes-core-internal-context-globalworld-java:lines-0001-0080`
- Optional (0): none
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: High: the committed iDFlakies JSON is authentic and sufficient for order outcome, but it contains no stack trace; causal diagnosis depends heavily on repository state semantics.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
