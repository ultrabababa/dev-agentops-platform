# B02 — bugswarm-apache-struts-190697114 — full Human Review record

> **FINAL DISPOSITION: `HUMAN REVIEW PASS`.** Layer 1 `PASS`, Layer 2 **`ADEQUATE`**.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is not frozen, no Suite Manifest exists, Formal Suite membership is not frozen, and all coordinates and the fingerprint remain `provisional-pre-freeze`.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`ADEQUATE`** — the strongest disclosure profile in the suite.
**Failure type:** `test_assertion_failure`.
**Fingerprint:** `fee5ba44a1272c3b64cfb4e41e9dffa8103f7e6b3fbe641c6a7b12ff1812c38f` (`provisional-pre-freeze`; supersedes `99b0ef1e…`).

## Layer 1
Exact revision `880c4c2d33f67c28a834a44da5a2523b858601b3` (apache/struts). `raw.log` **verified byte-exact** (1,954,490 → 1,953,762 == frozen) — the largest artifact in the suite at 20,718 lines. All **6 members byte-identical**. Nothing to repair.

## Causal chain
`raw.log:20651-20654` is the entire failure disclosure: `Failed tests: testAcceptFileWithMaxSize … (FileUploadInterceptorTest)` and `Tests run: 1680, Failures: 1`. The test oracle expects the misspelled prefix `The file is to large`; the English upload message the failing revision produces says `The file is too large`. Product message and assertion text are out of sync.

## Shortcut analysis — the strongest disclosure profile in the suite
- **The terminal summary suppresses the assertion message.** No expected value, no actual value, no comparison — only the test name.
- **`file is to large` occurs ZERO times in the log**, and only in `FileUploadInterceptorTest.java`. Both sides of the comparison must be recovered from source.
- `file is too large` occurs **once**, at `:19692`, roughly 960 lines earlier, inside an unrelated `WARN` line emitted by a *passing* test.
- One failure among **1,680 tests**; the log also carries several stack traces from tests that did not fail.
- The discriminating detail is a **one-character** spelling difference between `to` and `too`.

## Layer 2 — `ADEQUATE`
235 units (208 log + 27 repo), Required 3 (**1.3 %**, lowest in the suite), 6 files / 2,411 repository lines. Localisation is genuinely hard, the assertion detail is absent from the observation, and the oracle-versus-product judgement must be made entirely from source. Strongest of the assertion group.

## Final disposition
**`HUMAN REVIEW PASS`** — admitted as a `test_assertion_failure` Formal candidate, pre-freeze. Layer 1 `PASS`; Layer 2 **`ADEQUATE`**, the strongest of the assertion group and the strongest disclosure profile in the suite.

This is a **review pass, not a Formal Freeze**: `Canonicalization Profile v1` is unfrozen, calibration has not started, no Suite Manifest exists, and Formal Suite membership is not frozen.

## Scope boundary
Only this record, the B02 `case.json` curation status and fingerprint, and the B02 ledger material were changed. No Physical Artifact was modified.
