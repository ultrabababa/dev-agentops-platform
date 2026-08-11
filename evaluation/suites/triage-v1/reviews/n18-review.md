# N18 — github-osquery-issue-7718 — Human Review PASS record

> **PACKAGE-CONTENT HUMAN REVIEW: `PASS`.** N18 is retained in the Formal Suite candidate set.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and the Canonical coordinates and Case fingerprint remain `provisional-pre-freeze`.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`BORDERLINE-ADEQUATE`** — this rating is deliberate and must not be rewritten as `ADEQUATE`, `STRONG` or `HARD` (§12).
**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `5bba62cbf454764e247b64cb7a373036e857c75110973f00d496cd461449b743` (`provisional-pre-freeze`; lineage `d7cbe643…` → `4f81ac26…` → this record).

N18 is a **medium-difficulty Case with a genuine capability gradient**, not a high-difficulty evidence-acquisition Case. Victim localization is easy and the core insight is fairly local, but a complete, defensible diagnosis still requires the Python test, project-specific `retcode` semantics, the C++ daemon startup ordering, competing-hypothesis elimination, and cross-file/cross-language evidence composition.

## 1. Failure-era snapshot and its selection basis

**Anchor:** issue osquery/osquery#7718 filed **2022-08-08T16:19:02Z** by `Smjert`, title `test_osqueryd.py test_daemon_sigint flaky test`, label `flaky test`, zero comments, closed 2022-12-17 by the fix.

**Selected snapshot:** `3d26714fc113cef9e79fde0ae1fd52e1d5ba6f2c` — *Add core to the type column description of osquery_extensions schema (#7716)*, committer date **2022-08-08T15:52:27Z**, i.e. **27 minutes before** the issue was filed.

Selection was deterministic, not judgemental: the latest `osquery/osquery` **master** commit at or before the failure-observation timestamp. Note the default branch is `master`, not `main` — querying `main` returns HTTP 404, which is what masked this check in the first review. osquery squash-merges, so author and committer dates coincide throughout this window and the ordering is unambiguous.

The superseded selection `aaf2853071c6` (*docs: Update the list of pages (#7866)*, 2022-12-06) is rejected: it is four months after the observation and was chosen only for being pre-fix relative to the later fix. Under the provenance category below, proximity to a fix is never a valid basis for snapshot selection.

## 2. How the actual failing revision is represented

Three-part representation, recorded verbatim in `case.json.provenance`:

| Field | Value |
|---|---|
| **Actual failing revision** | **UNDETERMINABLE.** The issue body is a bare unittest traceback recording no run, build, job, branch or commit reference, and the issue carries no comments. No anchor to an executed revision exists anywhere in the public record. This is a *permanent absence of an anchor*, not an expired-retention problem, so unlike N17 it cannot be recovered by any route. |
| **Recoverable failure-era snapshot** | `3d26714fc113cef9e79fde0ae1fd52e1d5ba6f2c` |
| **Relationship / confidence** | The snapshot is at or before the observation, so every frozen member is repository state a reader of that failure could have inspected at the time. Per-member history was checked around the anchor. Confidence that these are *failure-era* bytes is high; confidence that they are the *exact executed* bytes is unattainable and is claimed nowhere in the package. |

Per-member history at the anchor:

| Member | Last preceding change | Failure-era bytes vs previous December freeze |
|---|---|---|
| `tools/tests/test_osqueryd.py` | `0e130a865f96` 2022-08-01 *Improve Pidfile handling (#7304)* | identical |
| `tools/tests/test_base.py` | `e06610a83b1f` 2022-04-25 | identical |
| `osquery/core/init.cpp` | pre-`d02fcd6970f8` state | **refrozen — 885 → 875 lines** |

**`3d26714f…` is never called the exact failing revision anywhere in this package.**

## 3. init.cpp refreeze (R2)

`osquery/core/init.cpp` was refrozen to its failure-era state, reversing `d02fcd6970f8` (*Add a mechanism to reduce memory retained on Linux (#7502)*, committer date 2022-08-09T01:10:55Z — roughly **nine hours after** the observation). I diffed the two versions: the change is a single additive block after line 127, a Linux-only `malloc_trim_threshold` FLAG declaration. It is semantically inert for this failure but shifted every later line by ten.

Causal coordinates therefore move, and the failure-era numbers are the ones now frozen:

| Fact | December freeze | Failure-era freeze |
|---|---:|---:|
| `std::signal(SIGTERM/SIGINT/SIGUSR1, signalHandler)` | 378-380 | **368-370** |
| `Pidfile::create(pidfile_path)` | 486 | **476** |
| `signalHandler` body | ~192-206 | **182-196** |

Ordering is preserved: handler installation precedes pidfile creation in both. Manifest hash and size, canonical units, line coordinates, content hashes and the Case fingerprint were all recomputed.

## 4. Physical Universe — final members

**3 members, 1,924 lines / 59,885 bytes**, plus `raw.log` 9 lines / 508 bytes. Total physical: **1,933 lines / 60,393 bytes**.

| Member | Lines | Bytes | Scope clause | Justification from the observation |
|---|---:|---:|---|---|
| `tools/tests/test_osqueryd.py` | 314 | 10,183 | (a) | The only file the traceback names, at `:153` and `:141`; holds the victim, the helper, and 12 sibling `DaemonTests` methods |
| `tools/tests/test_base.py` | 735 | 24,385 | (b) | Imported by the victim; supplies `ProcessGenerator`, `expectTrue`, and the `retcode` attribute the failing assertion reads |
| `osquery/core/init.cpp` | 875 | 25,317 | (c) | Owning implementation of the daemon whose exit code the failing assertion checks; contains signal-handler installation and pidfile creation |

### CMakeLists.txt — EXCLUDED (R6)

Applying the test directly: would an investigator who does not know the answer enter this file *because of this failure*? No.

- **No direct dependency** — nothing in the test imports or reads it.
- **No failure-specific build or runtime configuration relation** — its only failure-adjacent content is generic wiring: `if(OSQUERY_BUILD_TESTS)`, `enable_testing()`, `findPythonExecutablePath()`, `add_subdirectory("tests")`, googletest. Nothing about the daemon, the pidfile, signals, or this test.
- **No platform/config relation implicated by the observation** — the traceback is a pure Python `unittest` assertion failure on a subprocess exit code. There is no build error, no missing binary, no configuration symptom pointing at the build system. The test ran to completion and failed an assertion.

It contributed 211 lines / 3 canonical units of pure mass, which is exactly the "workspace size / distractor mass" rationale that is forbidden. **Removed.**

## 5. Independent causal chain

Reconstructed from the revised Physical Artifacts only. The upstream fix was consulted **afterwards**, as curator-only confirmation, and was not used to derive any of this.

1. `raw.log`: `test_daemon_sigint` fails at `test_osqueryd.py:153` → `daemon_sigint_test_helper:141` → `self.assertEqual(daemon.retcode, 0)` → `AssertionError: -2 != 0`.
2. `test_osqueryd.py:151` — `test_daemon_sigint` calls `Path(pidfile_path).touch()`, **pre-creating** the pidfile, then hands that path to the helper at `:153`.
3. `test_osqueryd.py:129-135` — the helper waits on `test_base.expectTrue(pidfile_exists)`, documented `# Wait for the pidfile to exist. / # This means the signal handler has been installed.` Because the file already exists, this wait returns immediately.
4. `test_osqueryd.py:138` — `os.kill(daemon.pid, signal.SIGINT)` is therefore sent without any real guarantee about daemon startup progress.
5. `init.cpp:368-370` — the daemon installs `std::signal(SIGTERM/SIGINT/SIGUSR1, signalHandler)` during `Initializer` startup. `init.cpp:476` — `Pidfile::create(pidfile_path)` runs later. So **handler installation precedes pidfile creation**: a *daemon-created* pidfile would be a sound readiness proxy, and the pre-`touch()` is what destroys that guarantee.
6. `test_base.py:264` — `self.retcode = -1 if self.proc is None else self.proc.poll()`. A negative `poll()` result means the child was terminated by signal `-N`, so `-2` is SIGINT delivered under the **default disposition**, i.e. before the handler existed. `test_base.py:240` sets `self.retcode = -1` as a not-started sentinel, so the sign convention must be read from the code rather than guessed.
7. Optional corroboration `init.cpp:182-196` — a *handled* SIGINT reaches `Initializer::requestShutdown(rc)` with `rc` unchanged from success, which is why the handled path yields exit 0.

**Curator-only confirmation (consulted after the above):** fix `7734da437375` (#7888) removes exactly `Path(pidfile_path).touch()` and its following assert, replacing them with removal of any leftover pidfile. The independent reconstruction matches the upstream fix.

## 6. Expected Answer — final wording

`primary_failure_type`: `timeout_or_flaky_failure`. `acceptable_failure_types`: `[]`. Re-derived from the revised Physical-only analysis; no genuine taxonomy ambiguity appeared. Nondeterministic signal-versus-startup timing with no stable product defect; nothing is missing or invalid, so `config_or_environment_failure` does not apply; the assertion is the surface, not the cause, and the taxonomy routes intermittent timing away from `test_assertion_failure`.

- **summary** — "test_daemon_sigint intermittently observes a raw SIGINT termination reported as exit -2 instead of the daemon's handled clean exit 0."
- **root_cause** — "The test pre-creates the pidfile that its own readiness wait then polls, so that wait can return before the daemon has installed its SIGINT handler. In the daemon's real startup the SIGINT handler is installed earlier than the pidfile is created, so a daemon-created pidfile would be a valid readiness signal; pre-creating the file removes that guarantee. When the signal arrives first the default disposition terminates the process and the test wrapper reports the negative exit code -2 rather than the handled clean exit 0."
- **recommended_action** — "Do not pre-create the readiness pidfile; clear any stale pidfile and wait for the daemon-created readiness signal before sending SIGINT."

The narrow scope is preserved. The one substantive change is that the ordering claim is now stated explicitly, because Required Evidence now contains the evidence for it; previously the wording presupposed an ordering that no Required item established.

## 7. Required and Optional Evidence — final

**Required (5):**

| ID | Fact it carries |
|---|---|
| `log:raw-log:lines-0001-0009` | The failure observation: victim, helper, failing assertion, `-2 != 0` |
| `repo:tools-tests-test-osqueryd-py:lines-0101-0200` | `touch()` at `:151`; readiness wait and its documented intent at `:129-135`; `os.kill(SIGINT)` at `:138`; the assertion at `:141` |
| `repo:tools-tests-test-base-py:lines-0201-0300` | `retcode` origin `proc.poll()` at `:264` and the `-1` sentinel at `:240` — the sign convention licensing "-2 = unhandled signal" |
| `repo:osquery-core-init-cpp:lines-0301-0400` | Handler installation at `:368-370` |
| `repo:osquery-core-init-cpp:lines-0401-0500` | `Pidfile::create` at `:476` |

**Optional (2):** `repo:osquery-core-init-cpp:lines-0101-0200` (the `signalHandler` body, why a handled SIGINT yields 0) and `repo:tools-tests-test-osqueryd-py:lines-0001-0100` (the sibling `DaemonTests` methods as natural neighbourhood context).

## 8. init.cpp removal test

Set by causal necessity alone. The earlier packet's reasoning — that promotion would improve cross-language measurement — is **withdrawn as an invalid basis**; benchmark difficulty must not decide Required Evidence.

Decomposing as directed:

- **A. `raw.log` + `test_osqueryd.py` establish:** the pidfile is pre-touched; the readiness wait can therefore return immediately; the observed failure is `-2`.
- **B. `test_base.py` establishes:** `retcode` comes from `proc.poll()`; a negative value means termination by signal.
- **C. `init.cpp` uniquely establishes:** the daemon's real startup ordering — the SIGINT handler is installed (`:368-370`) *before* the pidfile is created (`:476`) — hence a daemon-created pidfile genuinely is a meaningful readiness proxy.

Removing `init.cpp` entirely leaves two competing hypotheses **unexcludable**, and they imply different recommended actions:

1. *The daemon never installs a SIGINT handler at all* — then the test's expectation of exit 0 is simply wrong and the remedy is to fix the expectation, not the setup.
2. *The daemon creates the pidfile before installing the handler* — then the readiness proxy was never valid, and the remedy is to replace the readiness signal, not to stop pre-creating it.

Without `init.cpp` the only support for the ordering is the test's own comment at `:130`, which is the test's assertion *about* the implementation, not evidence of it. Since the Expected Answer asserts both "before the daemon has installed its SIGINT handler" and "a daemon-created pidfile would be a valid readiness signal", and since `recommended_action` tells the reader to rely on the daemon-created signal, **both `init.cpp` units are necessary**:

- remove `lines-0301-0400` → no evidence the daemon installs a handler at all → hypothesis 1 survives → **necessary**.
- remove `lines-0401-0500` → no evidence the daemon-created pidfile postdates handler installation → hypothesis 2 survives and `recommended_action` is unsupported → **necessary**.

Both promoted to Required on removal proof.

Coordinate note: this one causal fact spans **two adjacent canonical units** at `N=100`. A calibration observation, not a defect.

## 9. test_base.py removal test

The Expected Answer depends on `retcode` sign semantics twice: `summary` calls `-2` a "raw SIGINT termination", and `root_cause` attributes it to "the default disposition".

`daemon.retcode` is an attribute of a project-specific wrapper class. Nothing in `raw.log` or `test_osqueryd.py` defines it. Two facts make the unit necessary rather than corroborating:

1. `test_base.py:264` is the only place establishing that `retcode` is `proc.poll()`, which is what licenses the negative-value-means-signal convention.
2. `test_base.py:240` sets `self.retcode = -1` as a *not-started sentinel*. A workspace containing a negative sentinel actively punishes guessing that any negative value encodes a signal number; the reader must consult the code to distinguish `-1` (never started) from `-2` (killed by signal 2).

Removing the unit leaves `-2` an uninterpreted magic number and the "default disposition" claim unsupported. **Required by causal necessity**, not as corroboration.

## 10. Sanitization correction (R3) and the schema representation question

**Sanitization is now `reviewed_no_changes` with no declared transformations.** I compared byte-for-byte against the issue body: the fenced block is 508 bytes with nine CRLF terminators, while the previous artifact was 507 bytes because the **final** CRLF had been normalized to LF — the single differing byte was at offset 506. The artifact has been restored to full byte fidelity, so nothing needs declaring. The previous description, *"Removed ANSI/control noise only"*, was wrong twice over: no ANSI or control bytes were ever present, and eight CR bytes were retained rather than removed.

### Schema representation — limitation, not a blocker

`repository-manifest.json` schema `1` has one revision slot and the loader rejects unknown fields, so the executed-versus-recoverable distinction cannot be machine-readable without changing Schema V2. Schema V2 was **not** modified and no unknown field was added.

Most honest representation available, and the one used:

- `manifest.upstream_repository.exact_revision` = `3d26714fc113cef9e79fde0ae1fd52e1d5ba6f2c`, `revision_kind: "git_commit"`. The frozen bytes *are* exactly this commit's bytes, so the field's own contract holds.
- `provenance.source_url_or_construction_note` opens with the literal category label `PROVENANCE CATEGORY: undeterminable exact failing revision + recoverable failure-era snapshot`, states in the first sentence that the manifest value **must NOT be read as the actual failing revision**, then gives the three-part representation, the per-member history, and the superseded selection.

**Is putting a non-failing revision in a slot named `exact_revision` semantically acceptable?** My judgement: yes, narrowly — the field is named `exact_revision`, not `exact_failing_revision`, and ADR 0126 scopes it as declaring the revision the frozen bytes came from rather than asserting any executed state. So this is not a misuse and **not a schema blocker**.

The residual limitation is real and worth recording: nothing machine-readable distinguishes the two, so a downstream tool or a reader who sees only the manifest will misread it, and the safeguard is prose that a validator cannot enforce. There are now **two independent instances** — N17's unrecoverable ephemeral merge SHA and N18's undeterminable failing revision — which strengthens the case for an optional `executed_revision` / `revision_identity_note` field. Recorded as a future improvement candidate for the Schema owner; deliberately not actioned, and it must not block Issue #15.

## 11. Shortcut and competing-hypothesis analysis (R5)

Re-run against the revised artifacts. Workspace is **3 files**; `list_files` returns `osquery/core/init.cpp`, `tools/tests/test_base.py`, `tools/tests/test_osqueryd.py`.

| Query from the observation | Files hit |
|---|---|
| `test_daemon_sigint`, `daemon_sigint_test_helper`, `signal handler` | 1 — `test_osqueryd.py` |
| `pidfile`, `retcode`, `SIGINT` | **3 — all members** |
| `flaky` | **0** |

**Answer-prose scan: clean.** No `flaky`, `intermittent`, `leftover`, no `7718`/`7095`/`7888`, no fix content. The two apparent `race` hits are false positives from `g-race-fully` (`init.cpp:189`) and `t-race-back` (`test_base.py:694`). **The workspace contains no prose stating the mechanism, the defect, or a remedy** — categorically unlike N17 and N16.

Answering the four questions directly:

**1. Is opening the traceback-named region enough for the complete diagnosis?** **No — this is the substantive change from the pre-revision state.** Before, the single Required repository unit self-contained both halves of the contradiction and the whole Expected Diagnosis followed from it. Now the diagnosis provably needs 4 artifacts and 5 windows: the ordering claim requires two non-adjacent windows of an 875-line C++ file, and the `-2` interpretation requires `test_base.py`. Honestly stated: the *core insight* ("the pre-touch defeats the readiness wait") is still reachable from one unit, so a **partial** answer stays cheap; the **complete, scored** answer is not.

**2. Without init.cpp, is only a hypothesis possible?** Confirmed — see §8. Both competing hypotheses survive, and they imply different recommended actions.

**3. Is real Python test → helper → C++ init composition needed?** Yes: 4 artifacts, 5 windows, two of them non-adjacent inside the C++ file, spanning two languages.

**4. What is the contemporaneous comment `# This means the signal handler has been installed.`?** None of the three options cleanly. **It is accurate contextual documentation of intent that is load-bearing for the diagnosis but does not state the defect.**

I am correcting my own screening claim here. In screening I called it a *misleading competing hypothesis the Agent must overturn*. That was wrong: `init.cpp:368-370` versus `:476` shows the contract is **true** for the daemon. It is not misleading. Nor is it an answer shortcut — it names no flake, no race, no mechanism, no remedy. It documents what the wait is for, which the reader needs in order to see that `touch()` defeats it. It originates in the earlier fix `2daa85f2` (2021-05-10, *Fix flaky test test_daemon_sigint by waiting for pidfile (#7095)*), is contemporaneous, and must not be hidden.

## 12. Runtime Discriminative Value — `BORDERLINE-ADEQUATE`

| Metric | December draft | **Failure-era revision** | B04 baseline |
|---|---:|---:|---:|
| Physical repo files | 4 | **3** | 6 |
| Physical repository | 2,145 l / 66,719 B | **1,924 l / 59,885 B** | 3,050 l / 118,229 B |
| Raw failure artifact | 9 l / 507 B | **9 l / 508 B** | 619 l / 38,662 B |
| Canonical units | 25 | **22** (1 log + 21 repo) | 44 |
| Required | 2 (8.0 %) | **5 (22.7 %)** | 2 (4.5 %) |
| Optional | 1 | **2** | 2 |
| Artifacts holding Required evidence | 2 of 5 | **4 of 4** | — |
| Units in files holding no Required evidence | 20/25 (80 %) | **0/22 (0 %)** | — |

Two metrics moved sharply and both need honest reading rather than a headline. Required rose to 22.7 % and the zero-Required-file share fell to 0 % — but neither indicates a worse Case. The 80 % figure was inflated by `CMakeLists.txt`, a file with no Required evidence that had no business in the workspace; removing it was required by the scope rule. What matters is dispersion, and dispersion improved: 17 of 22 units are non-Required, including **6 of 9** `init.cpp` units and **7 of 8** `test_base.py` units, so both large files retain real intra-file search space. The pre-revision 8 % Required ratio was the misleading number, because that single unit was sufficient on its own.

**Genuinely measured:** cross-file and cross-language evidence composition; two competing hypotheses that only the C++ file closes, with *different* remedies attached; a sign-convention inference actively booby-trapped by a `-1` sentinel; twelve authentic sibling test methods; and zero answer-bearing prose anywhere in the workspace.

**Reservations, stated rather than buried:**

1. Victim localization is free — the traceback names the file and both line numbers. Authentic and not repairable without damaging the artifact.
2. A partial diagnosis remains cheap. An Agent reading only the traceback-named unit can reach "the test pre-creates its own readiness file", which is most of the insight even though it cannot support the stated remedy.
3. The workspace is small in absolute terms: 3 files, 1,933 lines — roughly half of B04's 3,669.

**Expected separation — a pre-runtime *hypothesis*, not a validated result.** No Runtime exists yet and nothing here has been experimentally tested. Recorded so it can later be checked against real runs:

| Condition | Expectation |
|---|---|
| Fixed Pipeline | **likely partial** — should retrieve the SIGINT-bearing `init.cpp` window from the observation's own tokens, but unlikely to assemble the second ordering window plus the `poll()` window |
| Retrieval | **better evidence acquisition, may still miss the complete composition** — stronger on the first hop, still weak on the second |
| ReAct | **more likely to complete competing-hypothesis elimination and the full diagnosis** — can read the test, form the hypothesis, then deliberately verify the ordering in C++ |

That is a real gradient rather than a collapse, but it must be treated as a prediction to falsify, not as evidence.

**Rating: `BORDERLINE-ADEQUATE`.** Recorded with both sides intact and deliberately not raised. Strengths: authentic competing hypotheses with different remedies, Python ↔ C++ composition, project-specific `retcode` interpretation, startup-order verification, and a complete diagnosis requiring several artifacts and windows. Weaknesses: the traceback localizes the victim directly, the core insight is fairly discoverable from `test_osqueryd.py` alone, a simple Pipeline may produce a partial diagnosis, and the workspace is modest in absolute size. It is the strongest `timeout_or_flaky_failure` candidate, which is not the same as a strong Case.

## 13. Validation

- Schema V2 loader PASS; declared fingerprint equals calculated (`5bba62cb…`).
- Manifest membership, sizes, SHA-256, path safety, no symlinks, no undeclared files: PASS (3 members).
- Canonical coverage **1,933 / 1,933 lines**, gap-free, overlap-free, exact resolved hashes: PASS.
- Required/Optional referential integrity and disjointness, Expected Answer schema: PASS.
- `raw.log` byte-identical to the issue-body fenced block (508 bytes, 9 CRLF): PASS.
- All 3 members byte-identical to the declared failure-era snapshot: PASS.
- `PublicCaseView` exposes only `case_id`, `case_schema_version`, `case_fingerprint`, `raw_log_path`, `repository_root`, `forbidden_actions`; no evaluator, provenance or snapshot leakage: PASS.
- Future fix/passing artifact scan over all 4 frozen artifacts: no hits.
- All 20 case directories load with consistent fingerprints; **B04 `89a8f9a0…`, N17 `3f0f80d8…`, N16 `80345301…` all unchanged**.
- Scope: only the N18 package, this record and the N18 material in the Bulk Ledger were changed.
- `pytest tests/test_issue_22_case_schema_v2.py tests/test_issue_6_evaluation_suite.py tests/test_issue_14_structured_report_scoring.py` → `126 passed`.

## 14. Final Human Review status

| Layer | Outcome |
|---|---|
| Scientific / package-content Human Review | **`PASS`** |
| Runtime Discriminative Value | **`BORDERLINE-ADEQUATE`** |
| Formal Suite Freeze | **`NOT YET`** |

Freeze is withheld for reasons unrelated to this Case: `Canonicalization Profile v1` is not frozen, no Suite Manifest exists, and the Canonical coordinates and Case fingerprint remain `provisional-pre-freeze` and may be mechanically rebuilt once the Profile is settled. Physical Artifacts, provenance, causal semantics, taxonomy and Expected Diagnosis semantics are the durable layer and are unaffected by that rebuild.

R1–R6 were all applied and accepted: failure-era snapshot selected deterministically (R1), `init.cpp` refrozen to failure-era bytes (R2), sanitization corrected to full byte fidelity (R3), Required set rebuilt on removal proof (R4), shortcut analysis re-run (R5), `CMakeLists.txt` removed (R6).

Both representation items were put to Human Review and **accepted**:

1. **Provenance category** `undeterminable exact failing revision + deterministic failure-era snapshot` — accepted for this package and available to any later Case of the same shape. The snapshot-selection rule is deterministic, but it must **not** be read as "probably the commit the reporter actually ran". Its correct meaning is: the snapshot is a legitimate failure-era state in time, the frozen bytes come exactly from that commit, the causally relevant facts are compatible with the authentic observation, and exact-executed-state confidence remains unattainable. *Failure-era snapshot confidence* and *exact executed revision confidence* stay distinct.
2. **Schema representation** — `repository-manifest.json.exact_revision` is read as *the exact upstream revision of the frozen repository bytes*, not as *the exact executed revision of the failure*. Under that reading the field carries no factual error. Schema V2 is unchanged this round; a future improvement candidate (`revision_role`, `executed_revision`, `revision_identity_note` or equivalent) is recorded for the Schema owner and must not block Issue #15.

## 15. Scope boundary

Only the N18 package, this record, and the N18 material in `BULK-DRAFT-REVIEW.md` were changed. Methodology documents, ADRs, Schema V2, B04, N01, every other Case, the suite manifest and runtime code were not touched. No replay, no environment reconstruction, no synthetic log, no Suite Manifest, no Suite fingerprint, and no replacement-candidate discovery.
