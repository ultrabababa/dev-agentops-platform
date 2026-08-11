# N20 — github-tan-cli-30459137058 — Human Review PASS record

> **PACKAGE-CONTENT HUMAN REVIEW: `PASS`.** N20 is retained in the Formal Suite candidate set.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and coordinates and fingerprint remain `provisional-pre-freeze`.

**Layer 1 — Scientific Validity:** `PASS` — and the strongest provenance in the suite (§1).
**Layer 2 — Runtime Discriminative Value:** **`ADEQUATE — lower end`** — deliberate; the workflow comment leaks the warns-and-continues mechanism but not the missing package, which is not enough to reduce the Case to `LOW`.
**Failure type:** `dependency_or_install_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `ec7dc5ae3c17db1c8275a41b801e8ea4ea14e412ed7ba6fed82779143fb48c7c` (`provisional-pre-freeze`; supersedes `4d6e25ab…`).

## 1. Provenance — the executed merge revision was recovered and verified

Run `30459137058`, workflow `parity`, job `first blink -- tan bootstrap -> init -> build` (id `90600330105`), event `pull_request`, conclusion `failure`. `raw.log` 3,492 lines / 336,408 bytes, **verified byte-exact**: `strip_ANSI(upstream job log)` (338,583 B, 398 ESC) equals the frozen artifact.

The draft declared `3043521c5ef278d79d34045bdb2116e81e9c661d`, the pull-request head. That is the same class of error as N17 — a `pull_request` event checks out the ephemeral merge ref, not the head. Here, however, **the log records the executed revision directly**:

```
:98   git fetch … origin +5bf4972f4e5931912654c24bed473296ae9a25eb:refs/remotes/pull/215/merge
:107  git checkout --progress --force refs/remotes/pull/215/merge
:125  HEAD is now at 5bf4972 Merge 3043521c5ef278d79d34045bdb2116e81e9c661d into 309ff63d4630d3b3a71a2e1cd6692f4ff13f4d01
```

`5bf4972f4e5931912654c24bed473296ae9a25eb` is **still addressable**, with parents `309ff63d4630` (base) and `3043521c5ef2` (head), and **all four frozen members are byte-identical to that merge tree**. `exact_revision` now declares it.

This makes N20 the **first Case in the suite with a fully recovered and verified executed merge revision** — strictly better than N17 (merge SHA lost) and N18 (no anchor at all). It is also robust: the members are *additionally* byte-identical at the head, so if the ephemeral ref is later garbage-collected the bytes stay verifiable, and the executed SHA is permanently recorded inside `raw.log`.

**External dependencies outside the Physical Universe**, recorded in the log rather than frozen: the pinned `alp-sdk` checkout (`:228`, `cdfe136`) and the Zephyr west workspace (`:815-824`, `1f6485ec`). The ledger flagged this as a risk. It is **not** a Layer 1 defect: the Zephyr requirements set that pulls in `hidapi` lives in that fetched workspace, but the diagnosis never needs it, because the log names both `hidapi` and the missing `libudev.h` directly.

## 2. Independent causal chain

1. `:955` `error: subprocess-exited-with-error`; `:957` `× Building wheel for hidapi (pyproject.toml) did not run successfully.`
2. `:986` **`hidapi/linux/hid.c:43:10: fatal error: libudev.h: No such file or directory`** → `:990` `error: command '/usr/bin/gcc' failed with exit code 1` → `:994` `ERROR: Failed building wheel for hidapi` → `:995` `error: failed-wheel-build-for-install`.
3. Context at `:955` is `bootstrap: Installing Zephyr Python requirements into the venv` — the install is driven by `tan bootstrap`.
4. Workflow `:602-608` — the `host deps` step installs `ninja-build device-tree-compiler gperf ca-certificates curl xz-utils pkg-config libusb-1.0-0-dev`. **`libudev-dev` is absent.**
5. Bootstrap warns and continues; the job runs ~2,300 more lines.
6. `:3311-3391` — `ModuleNotFoundError: No module named 'elftools'`, four times, then `:3404` `##[error]Process completed with exit code 1`.

The Expected Answer is accurate.

## 3. Required and Optional Evidence

**Required (3):** `log:raw-log:lines-0901-1000` (the `libudev.h` failure and the failed hidapi wheel) · `log:raw-log:lines-3301-3400` (the misleading `elftools` terminal symptom) · `repo:github-workflows-parity-yml:lines-0601-0700` (the `apt-get install` prerequisite list).

**Optional (1):** `repo:github-workflows-parity-yml:lines-0501-0600`.

**Correction applied.** The draft had the terminal-symptom unit as Optional, but the Expected Answer's `summary` explicitly claims *"then later surfaces misleading elftools import errors from the incomplete environment"*. Without that unit the claim is unsupported, so it is **promoted to Required**. The other two pass removal tests directly: drop the first and the missing header is unknown; drop the workflow unit and the prerequisite omission cannot be established.

## 4. Shortcut analysis

| Probe | Result |
|---|---|
| Read the log tail | Node.js deprecation warnings and git cleanup — **not even the error** |
| Read the last error | `ModuleNotFoundError: No module named 'elftools'` — **actively misleading**, suggests a missing Python package |
| `grep libudev` | **2 hits in the log, ZERO in the repository** |
| `grep hidapi` | 11 log hits, 1 repo hit (a comment) |
| Cause-to-symptom distance | line 986 → line 3311 = **2,325 lines apart** in a 3,492-line log |

Two properties stand out, and both are rare in this suite:

- **The terminal symptom misleads.** The natural move — read the end — yields cleanup noise, and the last *error* points at a Python package that is not the problem. This is genuine first-error-versus-terminal-symptom discrimination.
- **The diagnosis rests on absence.** `libudev` appears **nowhere** in the repository. The answer is what is *missing* from the `apt-get install` list, so no repository grep can find it; the Agent must carry `libudev.h` from the log and notice its absence from the prerequisite list. No other reviewed Case requires absence-based inference.

### The leak

Workflow `:592-601` carries a substantial partial answer:

> *"pkg-config + libusb-1.0-0-dev are NOT decoration: this job's own second run proved `hidapi` builds from source inside bootstrap's Zephyr requirements install and fails without them … **bootstrap warns and continues by design, so the workspace looks complete and `tan init` dies later instead.**"*

That final sentence is essentially the second half of the Ground Truth. It hands over the warns-and-continues mechanism and the fact that the real death is later — which is one of the two discriminative properties.

It does **not** give away the missing package: `libudev` has zero repository hits. And it is contemporaneous, so under the standing rule it must not be hidden. Most of it (`:592-600`) sits in the non-Required unit `0501-0600`; only the trailing line falls inside the Required unit.

## 5. Runtime Discriminative Value — `ADEQUATE — lower end`

| Metric | Value |
|---|---:|
| Repository files | 4 |
| `raw.log` | 3,492 lines / 336,408 bytes |
| Canonical units | 51 (35 log + 16 repo) |
| Required / Optional | 3 / 1 |
| Required share | 5.9 % |
| Cause-to-symptom distance | 2,325 lines |

**Retained after the leak:** locating the real error in a 3,492-line log whose tail actively misleads, and the absence-based inference that `libudev-dev` is missing from the prerequisite list. Neither is greppable — the tail misleads, and the missing package appears nowhere in the repository.

**Lost to the leak:** the "why does the job continue and die later?" reasoning, which the workflow comment states outright.

**Rating `ADEQUATE — lower end`**, level with N01 and above N11. Placed there on the strength of the absence-inference and the 2,325-line separation, and held down from a clear `ADEQUATE` by the comment leak. This is the strongest `dependency_or_install_failure` structure seen so far, but the category has three further candidates still unreviewed.

## 6. Failure Type

`dependency_or_install_failure`, `[]`. A native build prerequisite is absent, so a required package fails to install — the taxonomy's "native package build failure". Not `config_or_environment_failure`: the CI configuration is present and valid, it is simply incomplete in one entry, and the failure surfaces as a package install failure. Not `timeout_or_flaky_failure`: deterministic.

## 7. Validation

Loader PASS; declared fingerprint equals calculated (`8c632706…`); 4 members byte-identical to the executed merge tree; `raw.log` byte-exact against `strip_ANSI(upstream)`; canonical coverage gap-free and overlap-free with exact hashes; `PublicCaseView` clean; all 20 cases load with consistent fingerprints; B04, N01, N11, N18, B08 unchanged; `126 passed`.

## 8. Scope boundary

Only the N20 package, this record and the N20 ledger row were changed. No Physical Artifact bytes were modified — only the declared revision, provenance, Required Evidence and status. No other Case, methodology document, ADR, Schema V2, Profile document, suite manifest or runtime code was touched. No replacement-candidate discovery.
