# B09 — bugswarm-f90nml-118661876 — REJECTED case record

**Layer 1 — Scientific Validity:** `PASS`. **Layer 2 — Runtime Discriminative Value:** **`LOW`**.
**Status:** **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Not a Formal Suite member; retained only as a rejection record. **Layer 1 remains `PASS`** — it was not rejected for any defect.
**Failure type:** `dependency_or_install_failure`. **Fingerprint:** `2e0bd13e1bcb706be1be61bdebfb0024bc0d3d06982d949358303f380902a2a2`.

## 1. Layer 1
Source `bugswarm.org/artifact-logs/118661876/raw/`; exact revision `a654e03ebf8660b24aa56180a331fb76e79a73f7` (marshallward/f90nml). `raw.log` **verified byte-exact** (upstream 34,093 B / 405 ESC → 32,725 B == frozen). All **5 members byte-identical** to the exact revision. No curator pruning; no transformation beyond ANSI removal. Nothing to repair.

## 2. Causal chain
`raw.log:667-670` — `Traceback … File "test_f90nml.py", line 9, in <module> / import numpy / ImportError: No module named numpy`; `:663` wraps it as `coverage.misc.ExceptionDuringRun`. `.travis.yml:11-14` installs only `ordereddict` (2.6 only) and `pip install .`; `:15-17` runs `cd test` then `pip install -r requirements_test.txt`; that file declares `coverage` and `coveralls` — **no numpy**. `test/test_f90nml.py:9` imports it unconditionally.

## 3. Required Evidence — corrected 3 → 4
Added `repo:test-requirements-test-txt:lines-0001-0003`. The Ground Truth asserts *"the failing revision's test dependency set does not declare/install it"*, and that file — installed by `.travis.yml:17` — is the only evidence for the omission. The other three pass removal tests: the log carries the ImportError, `.travis.yml` carries the install path, and the test unit carries the import site.

## 4. Shortcut analysis
`numpy` appears in the repository **only at the import site** (`test/test_f90nml.py`), never in a declaration file, so the diagnosis rests on **absence** — the same pattern as N20. But the log names the module, the file *and* the line; the log is 676 lines / 7 units; `requirements_test.txt` is 3 lines. Two greps and a 3-line file complete the diagnosis. No answer-prose in the workspace.

## 5. Layer 2 — `LOW`
17 units, Required 4 (**23.5 %**, the highest ratio in the suite), 5 files / 22,150 repository bytes. The absence inference is genuine but cheap: the declaration file is three lines long, so noticing what is missing costs nothing. There is no fan-out, no competing hypothesis, and no domain-knowledge step. Comparable to B08.

## 6. Final disposition

**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Layer 1 stays `PASS`; the package is authentic, byte-exact and correctly diagnosed. The rejection is purely about measurement value: the diagnosis is intrinsically shallow, because the log names the missing module, its file and its line, leaving only a trivial check against a two- or three-line declaration file.

**`LOW` Cases are not required per taxonomy.** B08 already serves the suite-level easy anchor, so this Case was not retained merely to preserve the category count.
