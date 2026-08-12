# N13 — bugswarm-appier-113213406 — REJECTED case record

**Layer 1 — Scientific Validity:** `PASS`. **Layer 2 — Runtime Discriminative Value:** **`LOW`**.
**Status:** **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Not a Formal Suite member; retained only as a rejection record. **Layer 1 remains `PASS`** — it was not rejected for any defect.
**Failure type:** `dependency_or_install_failure`. **Fingerprint:** `3e95a055fdf5804b581eb8fd7c180c4676211d16d65161ab5962071c7bbbdf99`.

## 1. Layer 1
Source `bugswarm.org/artifact-logs/113213406/raw/`; exact revision `2b7fc2f824696a408d6c857fb98bab593c4def41` (hivesolutions/appier). `raw.log` **verified byte-exact** (upstream 61,150 B → 59,116 B == frozen). All **6 members byte-identical**. Nothing to repair.

## 2. Causal chain
`raw.log:950-955` — `File ".../src/appier/data.py", line 85, in collection / … line 90, in get_db / import tinydb / ImportError: No module named 'tinydb'`, repeated four times. `requirements.txt` declares `pymongo` and `redis` — **no tinydb**. `data.py:90` imports it inside the TinyDB adapter's `get_db`; `base.py` selects the adapter; `.travis.yml` runs the matrix that reaches this path.

## 3. Required Evidence — corrected 4 → 5
Added `repo:requirements-txt:lines-0001-0002`. The Ground Truth asserts *"the failing revision's dependency manifest omits that package"*, and `requirements.txt` is the only evidence for that omission. The existing four pass removal tests.

## 4. Shortcut analysis
`tinydb` appears in the repository **only at the import site** (`src/appier/data.py`), never in a declaration — again the absence pattern. The log names the module, the file and two line numbers. `requirements.txt` is **two lines**. `src/appier/base.py` is 144 KB / 24 units of genuine distractor mass, which is why the Required share is low, but none of it is needed. No answer-prose in the workspace.

## 5. Layer 2 — `LOW`
55 units, Required 5 (**9.1 %**), 6 files / 161 KB. The low Required share reflects one very large unrelated file rather than real search difficulty: the essential diagnosis is the log plus a two-line manifest. The adapter-selection and matrix reasoning add a third hop but change no conclusion. Slightly above B09 on distractor mass, below B06 and N20 on everything else.

## 6. Final disposition

**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Layer 1 stays `PASS`; the package is authentic, byte-exact and correctly diagnosed. The rejection is purely about measurement value: the diagnosis is intrinsically shallow, because the log names the missing module, its file and its line, leaving only a trivial check against a two- or three-line declaration file.

**`LOW` Cases are not required per taxonomy.** B08 already serves the suite-level easy anchor, so this Case was not retained merely to preserve the category count.
