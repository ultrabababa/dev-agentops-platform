# N10 — bugswarm-traccar-170953503 — REJECTED case record

> **FINAL DISPOSITION: `REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.**
> **N10 is NOT a Formal Suite member.** Retained only as a rejection record.
> **Layer 1 remains `PASS`** — `raw.log` is byte-exact against upstream and every member is byte-identical to the exact revision. It was not rejected for any defect.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`TRIVIAL`** — the observation essentially states the complete diagnosis.
**Failure type:** `config_or_environment_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `619b08a62991c9d34d58e0c1ebae752dd5cd14a8196311bb6899b109e46ac83d` (`provisional-pre-freeze`; supersedes `62de4f9f…`).

## 1. Authenticity, provenance, sanitization

Source `bugswarm.org/artifact-logs/170953503/raw/`; exact revision `64e149b69750fdc6f150a18e39a3df1ba76ccc24` (traccar/traccar). `raw.log` 464 lines / 18,168 bytes.

- **`raw.log` verified byte-exact**: `strip_ANSI(upstream)` = 18,168 bytes == frozen, an exact match rather than a prefix. The upstream artifact is small enough to fetch whole.
- **All 3 repository members byte-identical** to the exact revision.

No Layer 1 defect. Cleanest provenance of the four config/environment Cases alongside B16.

## 2. Independent causal chain

```
raw.log:421  Submodule 'traccar-web' (git@github.com:tananaev/traccar-web.git) registered for path 'traccar-web'
raw.log:425  Permission denied (publickey).
raw.log:427  fatal: Could not read from remote repository.
raw.log:431  Clone of 'git@github.com:tananaev/traccar-web.git' into submodule path 'traccar-web' failed
             … retried 3 of 3, then "failed and exited with 1"
```

`.gitmodules` declares `url = git@github.com:tananaev/traccar-web.git` — SSH transport — and the Travis checkout has no matching private key. `.travis.yml` is three lines (`language: java`, `jdk: openjdk7`) and provides no key material. The Expected Answer is accurate.

## 3. Required Evidence — corrected from 2 to 1

`.gitmodules` is **three lines**, and its entire causal content is the submodule URL. **The log prints that exact URL verbatim, twice** (`:421`, `:431`), alongside `Permission denied (publickey)`.

A strict removal test therefore fails for the repository unit: remove `.gitmodules` and the log still supplies the submodule name, the SSH URL, the transport, the authentication failure mode, and the three retries. It adds only `path = traccar-web`, which the log also states (`registered for path 'traccar-web'`).

**Required is now 1** (`log:raw-log:lines-0401-0464`); `.gitmodules` and `.travis.yml` are Optional.

## 4. Runtime Discriminative Value — `TRIVIAL`

| Metric | Value |
|---|---:|
| Repository files / lines | 3 / 261 |
| `raw.log` | 464 lines / 18,168 bytes |
| Canonical units | 10 (5 log + 5 repo) |
| Required / Optional | **1** / 2 |

**The complete diagnosis is contained in a single log unit.** The log names the failing command, prints the offending URL verbatim, states the authentication mode that failed, and shows three identical retries. The only inference required is that `git@github.com:` denotes SSH and that a public CI checkout carries no deploy key — one step of ordinary domain knowledge. The recommended action (use HTTPS or a relative submodule URL) is the standard remedy.

The repository contributes **nothing necessary**, and the largest member, `pom.xml` at 245 lines, is unrelated to the failure. The log is 464 lines, so even localisation is cheap.

**Rating `TRIVIAL`.** This is the first `TRIVIAL` recorded in the suite. It is not a defect — the Case is authentic, correctly built and correctly diagnosed. There is simply nothing to investigate: the CI log states the problem and the answer in adjacent lines.

Under the Measurement-Value Screening rule, a candidate that looks `TRIVIAL` should be dropped before package construction. N10 was constructed before that rule existed.

## 5. Scope boundary

Only this record, the N10 Required-Evidence correction and the N10 ledger row were changed. No Physical Artifact was modified.

## 6. Final disposition

**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Layer 1 stays `PASS`; the package is impeccable on provenance and fidelity. The rejection follows the recorded principle that **`TRIVIAL` should generally not occupy an equal-weight Formal slot**: the log prints the offending SSH URL verbatim beside `Permission denied (publickey)`, Required is a single log unit, and the repository contributes nothing at all.

N10 is the clearest demonstration in the suite that Layer 1 and Layer 2 are independent axes — a Case can be flawless and still be worth nothing as a benchmark.
