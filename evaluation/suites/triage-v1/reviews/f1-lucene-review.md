# F1 — bugswarm-lucene-27509200564 — construction and Human Review record

> **REVISED after Human review.** Layer 1 `PASS` · Layer 2 `ADEQUATE` · **awaiting Human disposition; not yet a Human PASS.**
> The original Ground Truth named the wrong source of nondeterminism and has been corrected (§2, §3).
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`. **Slot:** the first of two `timeout_or_flaky_failure` replacements.
**Fingerprint:** `c0b86d8dedeb449cb2ce765f288de0bc7e03b10cf2702f3937196d1af43c0b60` (supersedes `96321f09…`; `OverviewTestBase.java` added as a member and Required Evidence rebuilt).

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/27509200564/raw/`. GitHub Actions `pull_request` job for PR 13574. The log records its executed revision — `* [new ref] 556b838b09c2de3d64d1ba5afb4dcf99bc4014c6 -> pull/13574/merge` and `HEAD is now at 556b838 Merge f33b3285… into 5e52b809…` — and that **merge revision is verified upstream** (committer date `2024-07-16T13:00:51Z`).

`raw.log` 80,325 bytes / 973 lines. ANSI/CR normalisation only. All **6 members byte-identical**.

## 2. Correction — the original mechanism was wrong

The first construction claimed the intermittency came from `LuceneTestCase.newIOContext(randomState, context)`
randomising the caller's context. **That is incorrect.** Reading the method at the exact revision:

```java
public static IOContext newIOContext(Random random, IOContext oldContext) {
  if (oldContext == IOContext.READONCE) return oldContext;   // preserves, never manufactures
  ...
  switch (random.nextInt(3)) {                                // DEFAULT | MergeInfo | FlushInfo
```

with the source's own comment: *"Make a totally random IOContext, except READONCE which has semantic implications."*
`newIOContext` therefore **never returns READONCE** for a caller passing `IOContext.DEFAULT`. Once
`MockDirectoryWrapper` is in use, the segments-file guard fires on **every** seed. The randomisation there changes only
*which* non-READONCE context is reported in the message — the log shows `FLUSH` — not whether the check trips.

The seed-dependent branch is one level up, in **wrapper selection**, exactly as the Human review indicated.

## 3. Independent causal chain — corrected

1. `raw.log:805-810` — `TestOverviewImpl > testGetIndexFormat FAILED` with `RuntimeException: MockDirectoryWrapper:
   opening segments file [segments_1] with a non-READONCE context[IOContext[context=FLUSH, …]]`, thrown at
   `MockDirectoryWrapper.openInput:818` from `IndexUtils$2.doBody:344`, alongside
   `at __randomizedtesting.SeedInfo.seed([6603B3B1AF668E36:8EBB33E82E62C25D]:0)`.
2. `TestOverviewImpl extends OverviewTestBase`; `OverviewTestBase.setUp:51` builds the directory under test with
   `dir = newFSDirectory(indexDir)`.
3. `LuceneTestCase.newFSDirectory(Path)` → `newFSDirectory(f, FSLockFactory.getDefault())` → **`newFSDirectory(f, lf,
   rarely())`** at `:1354`. The third argument is the `bare` flag, and it is the only seed-dependent input on this path.
4. `LuceneTestCase.wrapDirectory:1408-1428` — when `bare` is true it returns a **`RawDirectoryWrapper`**; otherwise it
   returns a **`MockDirectoryWrapper`**. The `NRTCachingDirectory` branch above it is skipped here because
   `filesystem == true`.
5. `LuceneTestCase.rarely:836-841` — `int p = TEST_NIGHTLY ? 5 : 1; … int min = 100 - Math.min(p, 20); return
   random.nextInt(100) >= min;`. With `TEST_NIGHTLY` false and the default multiplier this is `nextInt(100) >= 99`, i.e.
   **about one seed in a hundred**.
6. `IndexUtils.getIndexFormat:337-344` opens the segments file with `IOContext.DEFAULT`.
7. `MockDirectoryWrapper.openInput:815-824` randomises the context — never to READONCE — and then rejects any
   segments-file read whose context is not READONCE.

**So the outcome is:** on the rare seeds where `rarely()` returns true, a bare `RawDirectoryWrapper` is used, the guard
does not exist, and the test passes. On the great majority of seeds `MockDirectoryWrapper` is installed and the test
fails deterministically. The intermittency is real and seed-carried, but it is **strongly asymmetric** — failure is the
common outcome, not a 50/50 race (§7).

## 4. Required Evidence — 8 units, each removal-tested

`OverviewTestBase.java` was added to the Physical Universe at the exact revision; it is the file that links the failing
test to `newFSDirectory`, and without it the seed-dependent branch cannot be reached from the observation at all.

| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0801-0900` | The observation, the rejected context, and the seed line | Remove: no failure and no nondeterminism marker |
| `repo:overviewtestbase-java:lines-0001-0097` | That the directory under test comes from `newFSDirectory(indexDir)` | Remove: the chain from the test to wrapper selection is broken |
| `repo:lucenetestcase-java:lines-1301-1400` | That `newFSDirectory(f, lf)` passes `rarely()` as the `bare` flag | Remove: the seed-dependent input is unidentified |
| `repo:lucenetestcase-java:lines-1401-1500` | That `bare` selects `RawDirectoryWrapper` versus `MockDirectoryWrapper` | Remove: the consequence of the flag is unknown |
| `repo:lucenetestcase-java:lines-0801-0900` | `rarely()` = `nextInt(100) >= 99` | Remove: the direction of the asymmetry — usually fails, rarely passes — is not entailed |
| `repo:lucenetestcase-java:lines-1701-1800` | That `newIOContext` never manufactures READONCE | Remove: the refuted original hypothesis revives, and the failure looks like context randomisation |
| `repo:indexutils-java:lines-0301-0400` | That the caller passes `IOContext.DEFAULT` | Remove: the offending call site is unknown |
| `repo:mockdirectorywrapper-java:lines-0801-0900` | The READONCE guard on segments files | Remove: the rule being violated is unknown |

Two of these are direction-settling in the N22 sense: `lucenetestcase-java:lines-1701-1800` rules out the wrong
nondeterminism story, and `lucenetestcase-java:lines-0801-0900` establishes which outcome is the common one. Four units
remain Optional.

## 5. Shortcut and leakage review
`newIOContext`, `IOContext.DEFAULT` and `randomState` occur **zero times in the log**. `READONCE` occurs twice, inside the exception message. A genuine distractor precedes the failure: an errorprone `RethrowReflectiveOperationExceptionAsLinkageError` warning in an unrelated benchmark module. Answer-prose: `TODO`, `HACK`, `workaround` and `should be` all occur in the two large test-framework files; they are ordinary maintenance comments in 4,382 lines of authentic framework code and none concerns the READONCE rule.

## 6. Runtime Discriminative Value — `ADEQUATE`
67 units (10 log + 57 repo), Required 8, 7 files / 195,404 bytes. The observation names a rule violation but not the rule,
not the caller's intent, and not the source of the nondeterminism. Locating the seed-dependent branch requires three hops
through the test framework — `setUp` → `newFSDirectory` → `wrapDirectory` — and the most inviting wrong answer, that the
context randomiser is responsible, must be refuted from a fourth. The Case now measures precisely that refutation, since
the constructing reviewer got it wrong on the first pass and the evidence is what corrects it.

## 7. Open question for the Human — the taxonomy label

The corrected mechanism makes the intermittency **asymmetric**: roughly 99 seeds in 100 fail. There is also a stable
product-code cause — `IndexUtils.getIndexFormat` passes `IOContext.DEFAULT` where the framework now requires READONCE —
whereas the taxonomy describes `timeout_or_flaky_failure` as intermittent behaviour *"without a stable product-code root
cause"*. The nondeterminism is genuine, artifact-visible and carried by a documented randomiser, but it lives in the test
harness's wrapper selection rather than in a race in the product.

Recorded rather than resolved. `test_assertion_failure` is a poor fit — the failure is a framework `RuntimeException`,
not an assertion — so the realistic choices are to keep `timeout_or_flaky_failure`, or to keep it with
`acceptable_failure_types` widened. **No change was made to the label.**

## 8. Disposition
**`NEEDS REVISION` cleared; awaiting Human disposition.** Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not marked Human PASS, per
the instruction to report the repaired chain first. Not a Formal Freeze.
