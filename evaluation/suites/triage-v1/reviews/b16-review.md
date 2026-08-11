# B16 — bugswarm-ugs-138584081 — REJECTED case record

> **FINAL DISPOSITION: `REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.**
> **B16 is NOT a Formal Suite member.** Retained only as a rejection record.
> **Layer 1 remains `PASS`** — the package is authentic, byte-identical to its exact revision and correctly diagnosed. It was not rejected for any defect.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`LOW`** — the complete diagnosis is log-alone sufficient; the repository adds no necessary evidence.
**Failure type:** `config_or_environment_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `9d06d8fee747351d5acd0304798faeca7b7afd11460c6f7e9e25a878b3667653` (`provisional-pre-freeze`; supersedes `e06b8206…`).

## 1. Authenticity, provenance, sanitization

Source `bugswarm.org/artifact-logs/138584081/raw/`; exact revision `3a90292cacebbd8dbdb7228a36ca89c0f6a9940f` (winder/Universal-G-Code-Sender). `raw.log` 4,617 lines / 547,403 bytes — the largest log in the config/environment group.

- **All 5 repository members byte-identical** to the exact revision. No repository transformation was declared and none was made.
- **Sanitization:** the ANSI-removal boilerplate. Prefix-verified — the upstream endpoint caps responses near 64 KiB, and `strip_ANSI(upstream)` is a byte-exact prefix of the frozen artifact. Consistent, but not fully verifiable through that endpoint.

No Layer 1 defect found. This is the first of the four config/environment Cases with nothing to repair.

## 2. Independent causal chain

`raw.log:4420` runs `MacroHelperTest`; `:4423` reports `Tests run: 3, Failures: 0, Errors: 1 <<< FAILURE!`; `:4424-4438` gives the full stack:

```
java.awt.HeadlessException:
No X11 DISPLAY variable was set, but this program performed an operation which requires it.
  … at javax.swing.JOptionPane.showConfirmDialog(JOptionPane.java:757)
  at com.willwinder.universalgcodesender.MacroHelper.substituteValues(MacroHelper.java:110)
  at com.willwinder.universalgcodesender.MacroHelperTest.testSubstitutePrompt(MacroHelperTest.java:76)
```

`MacroHelper.java:110` is `JOptionPane.showConfirmDialog(null, myPanel, …)` inside the prompt-substitution branch; `MacroHelperTest.java:76` calls the real `substituteValues` with `{prompt|…}` tokens rather than stubbing the dialog. `.travis.yml` (13 lines) sets up `oraclejdk8` and codecov and provides **no xvfb or virtual display**.

The Expected Answer is accurate and appropriately scoped.

## 3. Required Evidence — corrected from 3 to 1

The draft declared three Required units: the log plus `MacroHelper.java:0101-0126` and `MacroHelperTest.java:0001-0080`. Both repository units **fail a strict removal test**:

- The log's stack already names `MacroHelper.substituteValues(MacroHelper.java:110)` — file *and* line — so "invokes a JOptionPane path" is established without opening the source.
- The log's stack already names `MacroHelperTest.testSubstitutePrompt(MacroHelperTest.java:76)` — file *and* line — so the victim is established without opening the test.
- The log states the environment reason verbatim: `No X11 DISPLAY variable was set`.

Every element of the Expected Diagnosis is therefore derivable from `raw.log` alone. **Required is now 1** (`log:raw-log:lines-4401-4500`); the two repository units and `.travis.yml` moved to Optional, joining the second log unit.

This is not a defect in the package — it is a property of a Java stack trace. But it is decisive for Layer 2.

## 4. Runtime Discriminative Value — `LOW`

| Metric | Value |
|---|---:|
| Repository files / lines | 5 / 516 |
| `raw.log` | 4,617 lines / 547,403 bytes |
| Canonical units | 55 (47 log + 8 repo) |
| Required / Optional | **1** / 4 |
| Required share | **1.8 %** |

**What it measures:** log localisation in the largest artifact of this group — 47 log units, one of which matters. That is genuine, and 1.8 % is the lowest Required share in the suite.

**Why that is not enough:** `HeadlessException` and `<<< FAILURE!` are highly distinctive single-grep tokens, and the stack then hands over the application file, the application line, the test file and the test line. The repository contributes zero necessary facts. There is no cross-file composition, no competing hypothesis, and no inference the stack does not already make.

**Rating `LOW`.** Slightly above N10 because the log is an order of magnitude larger and the repository at least documents the design choice — a modal GUI call inside a helper exercised by a plain unit test — even though nothing there is required.

## 5. Scope boundary

Only this record, the B16 Required-Evidence correction and the B16 ledger row were changed. No Physical Artifact was modified.

## 6. Final disposition

**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Layer 1 stays `PASS`: nothing about the provenance, artifacts, causal chain or Ground Truth is wrong, and no repair would change the outcome. The rejection is purely about measurement value — with Required corrected to a single log unit, the repository contributes nothing necessary, so the Case cannot measure evidence acquisition.

B08 was chosen over B16 for the category's low-difficulty anchor role because B08 at least requires opening a second file.
