# F1 — bugswarm-lucene-27509200564 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE`** · constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`. **Slot:** the first of two `timeout_or_flaky_failure` replacements.
**Fingerprint:** `96321f0921bf091d685a5dd646a3885cd57b268caa3e329dee5ba0e3f92d9b05`.

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/27509200564/raw/`. GitHub Actions `pull_request` job for PR 13574. The log records its executed revision — `* [new ref] 556b838b09c2de3d64d1ba5afb4dcf99bc4014c6 -> pull/13574/merge` and `HEAD is now at 556b838 Merge f33b3285… into 5e52b809…` — and that **merge revision is verified upstream** (committer date `2024-07-16T13:00:51Z`).

`raw.log` 80,325 bytes / 973 lines. ANSI/CR normalisation only. All **6 members byte-identical**.

## 2. Why this one is genuinely nondeterministic
The nondeterminism is **visible in the artifacts**, not merely asserted by dataset metadata:
- The log carries `at __randomizedtesting.SeedInfo.seed([6603B3B1AF668E36:8EBB33E82E62C25D]:0)` — the failure is seed-parameterised.
- `MockDirectoryWrapper.openInput:815` calls `LuceneTestCase.newIOContext(randomState, context)`, **replacing the caller's context with a randomly chosen one** before the check at `:817`.

That is the difference between this Case and the two flaky candidates that were rejected during this round — see `reviews/flaky-slot-2-record.md`.

## 3. Independent causal chain
1. `raw.log:805-810` — `TestOverviewImpl > testGetIndexFormat FAILED` with `RuntimeException: MockDirectoryWrapper: opening segments file [segments_1] with a non-READONCE context[IOContext[context=FLUSH, …]]`, thrown at `MockDirectoryWrapper.openInput:818` from `IndexUtils$2.doBody:344`.
2. `IndexUtils.java:337-344` — `getIndexFormat` opens the segments file with `IOContext.DEFAULT`.
3. `MockDirectoryWrapper.java:815-824` — the context is first randomised, then any segments-file read whose context is not exactly `IOContext.READONCE` is rejected. This guard is what PR 13574 (`more_readonce`) tightens.
4. `LuceneTestCase.newIOContext:1782` — returns a randomly selected context, so `DEFAULT` becomes `FLUSH` or another value on some seeds and a permitted one on others.
5. The observed context is `FLUSH`, so the guard fires. On other seeds it does not, and the job passes.

## 4. Required Evidence — 4 units, removal-tested
| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0801-0900` | The observation, the rejected context, and the seed | Remove: no failure and no nondeterminism marker |
| `repo:indexutils-java:lines-0301-0400` | That the caller passes `IOContext.DEFAULT` | Remove: the offending call site is unknown |
| `repo:mockdirectorywrapper-java:lines-0801-0900` | The READONCE guard and the randomisation immediately before it | Remove: the rule being violated is unknown |
| `repo:lucenetestcase-java:lines-1701-1800` | That `newIOContext` genuinely randomises | Remove: the failure looks deterministic, so the **taxonomy assignment itself** loses support |

The fourth unit is what entails the `timeout_or_flaky_failure` classification, not merely the mechanism. Four Optional, including the test and an unrelated errorprone warning region.

## 5. Shortcut and leakage review
`newIOContext`, `IOContext.DEFAULT` and `randomState` occur **zero times in the log**. `READONCE` occurs twice, inside the exception message. A genuine distractor precedes the failure: an errorprone `RethrowReflectiveOperationExceptionAsLinkageError` warning in an unrelated benchmark module. Answer-prose: `TODO`, `HACK`, `workaround` and `should be` all occur in the two large test-framework files; they are ordinary maintenance comments in 4,382 lines of authentic framework code and none concerns the READONCE rule.

## 6. Runtime Discriminative Value — `ADEQUATE`
66 units (10 log + 56 repo), Required 4, 6 files / 192,289 bytes. The observation names a rule violation but not the rule, not the caller's intent and not the source of the nondeterminism. Establishing that this is a flaky failure rather than a deterministic one is itself an inference step requiring a third file.

## 7. Disposition
**Recommended `HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not a Formal Freeze.
