# N17 — github-node-issue-61762 — REJECTED case record

> **FINAL DISPOSITION: `REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.**
> **N17 is NOT a Formal Suite member and must never be frozen as one.**
> Retained solely as review history, a rejection record, and a **negative calibration example**.
> The fourth `timeout_or_flaky_failure` slot is **unfilled**.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** `FAIL`.
**Human Review:** `COMPLETED WITH REJECTION`. Not pending; not approved; not awaiting freeze.
**Failure type:** `timeout_or_flaky_failure` (unrelated to the rejection).
**Fingerprint:** `3f0f80d8fcf25cda9e2422c2cd926cbef2ce55b593f7b71da72e2fa2c51b2f1e` (`provisional-pre-freeze`, rejected package).

Draft lineage: `3839fc54…` (source-chain BLOCKER) → `f5e1447b…` (source chain repaired, siblings wrongly excluded as leakage) → `7ec5090c…` (siblings restored, Required set corrected, revision identity corrected) → `3f0f80d8…` (this record: rejection state).

## Why this Case was rejected — and why that is not a defect

The rejection is **not** because the Case is unreal, because Ground Truth is wrong, because provenance is unfixable, or because schema/validation failed. After repair, N17 is an authentic, source-faithful, causally valid Case that passes every structural check.

It was rejected for exactly one reason: the real failing-era repository already contained a natural same-family sibling test whose contemporaneous comment and implementation hand over the restart synchronization mechanism, the flaky-race explanation, and the recommended synchronization pattern. An ordinary Agent searching `BREAK_MESSAGE`, `restart`, or `flaky` from the raw failure finds it in one hop. Pipeline, Retrieval and ReAct would therefore converge along the same lexical/search path, and the evidence-acquisition differentiation the Formal Suite exists to measure would not appear.

**Real environment makes the Case too easy → replace the Case. Never hide authentic contemporaneous information to manufacture benchmark difficulty.** That is the governing principle and the reason this package was repaired honestly and then rejected rather than quietly trimmed back into difficulty.

## Methodological value — negative calibration example

N17 establishes, on a real Case rather than in the abstract:

> **`scientifically valid` ≠ `useful formal benchmark case`.**

Formal Case admission therefore needs at least two layers:

- **Layer 1 — Scientific Validity:** authentic historical failure, source-faithful provenance, exact/recoverable revision identity, valid causal chain, Ground Truth supported by Agent-visible evidence, no future-artifact leakage or curator bias, fair Runtime treatment.
- **Layer 2 — Runtime Discriminative Value:** enough real investigation complexity that the Case can separate Pipeline, Retrieval, ReAct and Oracle instead of collapsing them onto one shortcut.

It also documents a specific, reusable **failure mode**:

> The real failure-era repository already contains a same-family sibling fix carrying strong causal or remedial guidance → obvious failure-derived search finds it in one hop → the acquisition gap collapses → the Case is unsuitable as a Formal Runtime benchmark, however authentic it is.

This is a systematic hazard for `timeout_or_flaky_failure` candidates in particular, because flaky tests are fixed in batches across a test family, so a still-broken victim's snapshot frequently contains a fixed, commented sibling. **The check belongs in Candidate Discovery, before package construction** — discovering it after a full package has been built, as happened here, is the expensive path. The screening procedure is recorded in `BULK-DRAFT-REVIEW.md`.

## Human decisions recorded

| Question | Decision |
|---|---|
| Formal Suite disposition | `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`; N17 excluded from the Formal Suite |
| Sibling membership | `INCLUDE` both — contemporaneous repository knowledge is not leakage; only future fix / passing revision / curator-only research is excluded |
| Answer-neutral scope rule incl. clause (e) | Accepted in principle, **deliberately not frozen** into methodology or an ADR yet; to be validated against N16, N01 and further real Cases first |
| Executed-revision representation limitation | Accepted; Schema V2 unchanged; recorded as a future improvement candidate (`executed_revision` / `revision_identity_note` or equivalent); must not block Issue #15 |
| `repo:test-common-debugger-js:lines-0001-0100` | Demoted to Optional on the removal test, not on preference |
| `test/common/index.js` | Retained; rationale is real dependency tracing and platform-timeout semantics, not workspace inflation |
| `case_id` rename to `github-node-22532700362` | **Not performed.** The rename is sound in principle, but N17 will not enter the Formal Suite, so identity churn on a rejected draft is unwarranted. The current identity is kept for review history; the replacement candidate will use its own real source identity. |
| Taxonomy | `timeout_or_flaky_failure`, `acceptable_failure_types: []`; unrelated to the rejection |

## Retained technical record

Everything below is preserved because the source-chain repair and the measurement-value analysis are the durable output of this review.

### 1. Repair history

**First Human Review — source-chain BLOCKER.** The original draft combined three unrelated histories: a 5-line console excerpt from the body of issue #61762 that **names no test file** (its own build links point at run `21828756273`, whose failing test was `test-debugger-restart-message.js`); a repository and Ground Truth built around `test-debugger-exceptions.js`; and revision `3163d8aaf4df…`, verified upstream as `test: avoid initial-break wait in restart-message`, committed **2026-05-13**, touching only `test/parallel/test-debugger-restart-message.js` — the restart-message *fix* state three months *after* the failure. The whole chain was replaced with one verified failure and every derived layer rebuilt.

**Second Human Review — two corrections.** Executed-revision precision was overstated (§2), and the two restart sibling tests had been wrongly excluded as leakage (§4). Both fixed; the second correction produced the rejection.

### 2. Revision identity

Recovery of the actual executed revision was attempted and **failed**. Every GitHub primary-metadata route reports only the pull-request head:

| Route | Result |
|---|---|
| `actions/runs/22532700362` → `head_sha`, `head_commit.id` | `3c08a48c…` (PR head) |
| same → `head_commit.tree_id` | `afce3e8ea54a…` — the tree of `3c08a48c…`, not of a merge |
| `check-runs/65274588187` → `head_sha` | `3c08a48c…` |
| `commits/3c08a48c…/check-suites` → `head_sha`, `after` | `3c08a48c…` for all 20 suites |
| `git ls-remote refs/pull/65153/merge` | `929712c2e0bd…` — regenerated for current head `2cbfe5ba…`; the historical merge commit is gone |

The workflow uses `actions/checkout` with no explicit `ref:`, so a `pull_request` event checks out `refs/pull/65153/merge`. Therefore:

- **Actual executed revision:** GitHub ephemeral pull-request merge revision (`refs/pull/65153/merge`); **exact historical merge SHA no longer recoverable**.
- **Recoverable repository revision** (declared in `repository-manifest.json`): `3c08a48c24c39ad4dee6d95c5c800246f300525e`, the run head commit.
- **Relationship:** all frozen Physical Universe repository members are independently proven **byte-equivalent** to the actual executed merge state.

Proof: `3c08a48c…` changes only `deps/googletest/**` (none a member); its parent `6964b539806e…` landed on `main` at committer date `2026-02-28T14:40:38Z`; the run started `2026-03-01T00:54:32Z`; and **no commit touching any of the 11 declared members has a committer date inside that gap**. The two era commits that do touch members, `76ba280051…` and `4f04a36bba…`, were confirmed **ancestors** of `3c08a48c…` (compare API: `status: ahead`, `behind_by: 0`). Author dates are unreliable here because Node.js rebases on land.

Corroboration: every annotation stack frame resolves to exactly the expected construct in the frozen bytes — `debugger.js:92` the `timeoutErr` line, `:67` the `new Promise` in `waitFor`, `:178` `.waitFor(BREAK_MESSAGE)` in `stepCommand`, `test-debugger-exceptions.js:41` `await cli.stepCommand('r')`; the observed `connecting to …` resolves to `inspect.js:222`.

**`3c08a48c…` must not be read as the executed revision.**

**Representation limitation (accepted, not worked around).** `repository-manifest.json` schema `1` has a single revision slot and the loader rejects unknown fields, so the executed-versus-recoverable distinction cannot be machine-readable without changing Schema V2 — which was **not** modified. The honest in-schema representation used is: declare the recoverable commit in `exact_revision` with `revision_kind: "git_commit"`, and carry the distinction in `provenance.source_url_or_construction_note` (free text, inside the Case fingerprint, outside `PublicCaseView`). ADR 0126 already scopes `exact_revision` as proving source rather than asserting byte identity with a particular tree. Future improvement candidate for the Schema owner: an optional `executed_revision` block or `revision_identity_note`. Any Case built from a `pull_request`-triggered run with a default checkout has this shape.

### 3. Authenticity and provenance

| Fact | Value |
|---|---|
| Run | `22532700362`, workflow `Test macOS`, event `pull_request` |
| Job / check run | `65274588187`, job `test-macOS`, `failure`, completed `2026-03-01T01:56:34Z` |
| Failure annotation | `annotation_level: failure`, `path: test/parallel/test-debugger-exceptions.js` |
| Full job log | **not retrievable**, HTTP `410`, retention expired, not reconstructed |

`raw.log` is the verbatim annotation message, **27 lines / 1,649 bytes**. It names the victim twice inside its own body — stack frame `test/parallel/test-debugger-exceptions.js:41:17` and the trailing `Command:` line — so no curator framing was needed to establish victim identity. No ANSI, CR or other control bytes were present; the sole transformation is one appended trailing newline.

### 4. Physical Evidence Universe and the sibling decision

**Answer-neutral workspace scope rule** (stated before any content judgement, applied uniformly):

> A file belongs to the bounded natural investigation workspace if a reader of the failure observation who does **not** know the answer would reach it by (a) being named in the observation, (b) following the project-internal `require`/data-dependency closure of an observation-named file, (c) opening the owning implementation module of the subsystem whose output the observation quotes, (d) opening the configuration of the failing job, or (e) listing or searching the test family the failing test belongs to.

Clause (e) governs the siblings, and they are **INCLUDED**. The earlier exclusion was withdrawn: it rested on a narrower rule formulated *after* reading their content, which the same packet already violated by including the workflow file and the debugger implementation (neither is in any dependency closure). A rule invented after seeing content, shaped to remove precisely the most helpful content, is not answer-neutral. These files are also not future artifacts — not PR #62055, not a passing revision, not curator-only — but contemporaneous repository truth.

**What the siblings contain.** Commit `4f04a36bba7f…` "test: avoid flaky debugger restart waits" landed **2026-02-27, two days before the run**, and is an ancestor of the executed revision:

- `test-debugger-restart-message.js:27-34` — `stepCommand('restart')` → `command('restart')` + `waitFor(/Debugger attached\./)` + `waitForPrompt()`, carrying `// For \`restart\`, sync on attach/prompt instead of BREAK_MESSAGE to avoid flaky races.` and a link to issue #61762.
- `test-debugger-run-after-quit-restart.js:60` — `stepCommand('restart')` → `command('restart')`, no comment.

The victim was missed by that sweep and still used `stepCommand('r')` at lines 30, 41 and 49; PR #62055 completed the migration in May.

**Membership — 11 members / 3,638 lines / 108,082 bytes at `3c08a48c…`**

| Path | Lines | Clause | Derivation from the observation |
|---|---:|---|---|
| `test/parallel/test-debugger-exceptions.js` | 58 | (a) | Annotation path and stack frame `:41`. |
| `test/common/debugger.js` | 190 | (a) | Named by three of four stack frames. |
| `test/parallel/test-debugger-restart-message.js` | 43 | (e) | Restart sibling in the failing test's family. |
| `test/parallel/test-debugger-run-after-quit-restart.js` | 85 | (e) | Restart sibling in the failing test's family. |
| `test/fixtures/debugger/exceptions.js` | 10 | (b) | Data dependency via `fixtures.path('debugger','exceptions.js')`. |
| `test/common/fixtures.js` | 60 | (b) | `require('../common/fixtures')` in the victim. |
| `test/common/index.js` | 1,106 | (b) | `require('../common')` at victim `:2` and `debugger.js:2`; supplies `platformTimeout` (`:308`), `isMacOS` (`:181`), `isWindows` (`:176`) that `debugger.js:10-15` uses to produce the observed `Timeout (15000)`, plus `skipIfInspectorDisabled` and `mustCall`. Real dependency tracing, not workspace inflation. |
| `lib/internal/debugger/inspect.js` | 363 | (c) | Prints the observed `connecting to …` (`:222`). |
| `lib/internal/debugger/inspect_client.js` | 354 | (c) | Websocket transport that would carry a lost or late event. |
| `lib/internal/debugger/inspect_repl.js` | 1,227 | (c) | `get restart()` (`:972`), the `debug>` prompt, and `Debugger.on('paused')` (`:893`) printing the break header (`:920`). |
| `.github/workflows/test-macos.yml` | 142 | (d) | Failing job configuration; the only artifact explaining the `dir%20with $unusual"chars?'åß∂ƒ©∆¬…\`` directory in every observed path, plus the macOS runner and flaky-retry settings. |

Including the complete `lib/internal/debugger/` module is a fairness requirement, not padding: with only the test and helper present, the test-level diagnosis would be the only conclusion the workspace could support, making Ground Truth unfalsifiable by construction.

**Leakage boundary — only future artifacts excluded, verified by scan of all 12 frozen artifacts:** PR #62055 merge `9de9b9f88e5d…` and head `6dca87336071…` absent; post-run restart-message fix `3163d8aaf4df…` absent; fix diff, passing revision and curator research absent. The contemporaneous markers `61762`, `instead of BREAK_MESSAGE` and `avoid flaky races` appear in exactly one file, `test-debugger-restart-message.js`, **by design** — they were in the repository when the failure happened.

### 5. Independent causal chain (Physical Artifacts only; PR #62055 not consulted)

1. The annotation times out after 15,000 ms waiting for the pattern `debugger.js:5-8` builds as `BREAK_MESSAGE`; `debugger.js:10-15` shows 15,000 ms is the Windows/macOS `platformTimeout` branch.
2. The failing frame is `test-debugger-exceptions.js:41`, `await cli.stepCommand('r')`, the restart in the `breakOnUncaught` section; lines 30, 41 and 49 all restart this way.
3. `debugger.js:175-180`: `stepCommand` calls `writeLine(input, true)` then `waitFor(BREAK_MESSAGE).then(() => waitForPrompt())`; `writeLine` with `flush = true` (`:159-168`) clears the captured buffer before writing.
4. `waitFor` (`:59-108`) arms one fixed `setTimeout(TIMEOUT)` at call time and resolves only if post-flush accumulated output matches.
5. The captured output shows the restart fully succeeding inside that window — old session ends (`Debugger ending on ws://…:62933`), new one starts (`…:62936`), CLI reconnects (`connecting to … < Debugger attached.`), command acknowledged (`debug>  ok`), prompt returns (`debug> `) — while the expected break line never appears.
6. `debugger.js` shows the alternatives not used for this step: `command()` (`:170-173`) waits for the prompt only; `waitForInitialBreak()` (`:115-122`) waits for the break separately, and the victim already calls it on the next line, `:42`.

Supported conclusion: the restart step synchronizes on the break message alone, in one fixed window opened before the restart begins, so it depends on debugger output timing and fails intermittently on macOS.

Deliberately **not** concluded: why the break line was absent. Never emitted, emitted before the wait was armed, and delivered late are all consistent with this evidence; upstream leaves the macOS event/output delivery behaviour unresolved. `expected-answer.json` states this limit explicitly.

### 6. Evidence Ground Truth

**Required (3):** `log:raw-log:lines-0001-0027`, `repo:test-parallel-test-debugger-exceptions-js:lines-0001-0058`, `repo:test-common-debugger-js:lines-0101-0190`.

**Optional (6):** `repo:test-common-debugger-js:lines-0001-0100`, `repo:test-fixtures-debugger-exceptions-js:lines-0001-0010`, `repo:lib-internal-debugger-inspect-repl-js:lines-0901-1000`, `repo:github-workflows-test-macos-yml:lines-0101-0142`, `repo:test-parallel-test-debugger-restart-message-js:lines-0001-0043`, `repo:test-parallel-test-debugger-run-after-quit-restart-js:lines-0001-0085`. The two siblings are listed rather than omitted so their corroborating force is visible instead of hidden.

**Removal test on `repo:test-common-debugger-js:lines-0001-0100` → demoted to Optional.** Run element by element against the narrowed Expected Diagnosis with only `raw.log` + victim + `debugger.js:0101-0190` remaining:

| Diagnosis element | Derivable without `0001-0100`? | Source |
|---|---|---|
| timed out after 15,000 ms | Yes | `raw.log` prints `Timeout (15000)` |
| at the restart step, line 41 | Yes | `raw.log` stack frame + victim `:41` |
| waiting for a break message | Yes | `raw.log` prints the expanded pattern; `debugger.js:178` shows `.waitFor(BREAK_MESSAGE)` |
| restart, reconnect, `ok`, prompt all completed | Yes | `raw.log` captured output |
| the step flushes output then writes the command | Yes | `writeLine` `:159-168`, **inside `0101-0190`** |
| the wait is a single fixed window | Yes | the annotation's `Timeout (15000) while waiting for …` raised from `waitFor` demonstrates it behaviourally |
| macOS attribution | Yes | runner path in `raw.log`; `runs-on: macos-15` in the workflow file |
| remediation: acknowledge restart and prompt, then wait for the break | Yes | `command()` `:170-173` and `waitForInitialBreak()` `:115-122`, both **inside `0101-0190`** |

The unique content of `0001-0100` is the `BREAK_MESSAGE` definition (duplicated verbatim by `raw.log`), the `platformTimeout` branch (value in `raw.log`, platform corroborated twice elsewhere), and `waitFor`'s implementation (behaviour demonstrated by the observation). No irreplaceable causal fact is lost.

Remaining inclusion-minimality: remove the log unit and there is no observation; remove the victim unit and the restart step and callsite are unknown; remove `0101-0190` and there is no evidence this step waits on the break message rather than the prompt, nor that `command()`/`waitForInitialBreak()` are the alternatives.

### 7. Runtime Discriminative Value — the analysis behind the rejection

| Metric | Rejected draft 1 | Siblings hidden | **Final** | B04 baseline |
|---|---:|---:|---:|---:|
| Physical repo files | 3 | 9 | **11** | 6 |
| Physical repo lines / bytes | 258 / 7,119 | 3,510 / 104,527 | **3,638 / 108,082** | 3,050 / 118,229 |
| Raw artifact lines / bytes | 5 / 355 | 27 / 1,649 | **27 / 1,649** | 619 / 38,662 |
| Total physical lines / bytes | 263 / 7,474 | 3,537 / 106,176 | **3,665 / 109,731** | 3,669 / 156,891 |
| Canonical units | 5 | 41 | **43** (1 log + 42 repo) | 44 |
| Required units | 3 | 4 | **3** | 2 |
| Required / total | 60.0 % | 9.8 % | **7.0 %** | 4.5 % |
| Required + Optional / total | 60.0 % | 17.1 % | **20.9 %** | 9.1 % |
| Units in files with no Required evidence | 40 % | 90.2 % | **90.7 %** (39/43) | — |

**The counts are healthy. The counts are not the binding constraint** — which is itself a calibration lesson: no numeric threshold would have caught this.

**The shortcut test decided it.** `list_files` returns **11 files**, three of them debugger tests, so any adaptive runtime opens all three. Searches taken directly from the failure observation:

| Query, all derived from `raw.log` | Files hit |
|---|---|
| `BREAK_MESSAGE` — printed verbatim in the annotation's error message | **2**: `test/common/debugger.js`, **`test-debugger-restart-message.js`** |
| `flaky` — the obvious query for an intermittent timeout | **2**: **`test-debugger-restart-message.js`**, `.github/workflows/test-macos.yml` |
| `restart` — the failing operation | **4**, including **`test-debugger-restart-message.js`** |

Any one of those single searches surfaces a 43-line file whose comment states the mechanism, the reason, the remediation pattern, and the tracking issue — supplying `root_cause` and `recommended_action`, two of the three scored diagnosis fields, while `failure_type` is already implied by `Timeout` plus the workflow's `FLAKY_TESTS: keep_retrying`. That file is also a **single dense canonical unit** saturated with the query terms, so it ranks highly under essentially any fixed top-k or embedding scheme. The 5-hop causal chain in §5 becomes optional rather than necessary.

There is also a **measurement pathology**: an Agent that does the right engineering thing — find the prior fix in the family and reason by analogy — cites a file that is Optional, not Required, so it can score a correct diagnosis with weak Report Evidence Hit. That penalises good behaviour.

Neither enlarging nor shrinking the universe repairs this. Enlarging does not defeat `grep`: adding all 33 debugger tests still leaves `flaky` and `BREAK_MESSAGE` as two- or three-hit queries. Shrinking means hiding contemporaneous truth.

### 8. Canonicalization (provisional)

Fixed-100 windows, start at line 1, contiguous, non-overlapping, final unit may be shorter, IDs from source path and line range only. Coverage verified per artifact: **3,665 / 3,665 lines, no gaps, no overlaps**, every unit hash resolving from the frozen bytes.

Two `N=100` boundary observations worth carrying into the `N ∈ {50, 100, 200}` comparison even though the Case is rejected: `inspect_repl.js` splits one causal fact across units `0801-0900` and `0901-1000` (the `Debugger.on('paused')` handler opens at `:893`, its break-header `print` lands at `:920`); and the `debugger.js` pair `0001-0100` / `0101-0190` splits one helper's semantics across two units, which is what made the §6 removal test non-obvious.

### 9. Validation at rejection

- Schema V2 loader: PASS; declared fingerprint equals calculated (`3f0f80d8…`).
- Repository manifest membership, sizes, SHA-256, path safety, no symlinks, no undeclared files: PASS (11 members).
- Canonical coverage 3,665/3,665 lines, gap-free, overlap-free, exact resolved hashes: PASS.
- Required/Optional referential integrity and disjointness, Expected Answer schema: PASS.
- `PublicCaseView` exposes only `case_id`, `case_schema_version`, `case_fingerprint`, `raw_log_path`, `repository_root`, `forbidden_actions`; no evaluator or provenance leakage: PASS.
- Future fix/passing artifact scan over all 12 frozen artifacts: no hits.
- Secret scan: one benign match, `inspect_client.js:59` `WebSocket secret mismatch: …`, the inspector's handshake key-validation message.
- All 20 case directories load; **B04 fingerprint unchanged at `89a8f9a08f0dcb26…`**.
- `pytest tests/test_issue_22_case_schema_v2.py tests/test_issue_6_evaluation_suite.py tests/test_issue_14_structured_report_scoring.py` → `126 passed`.

The package remains loader-valid **so that this rejection record stays inspectable**. Validity is not admission.

### 10. Scope boundary

Only the N17 package, this record, and the N17 material in `BULK-DRAFT-REVIEW.md` were changed across the whole repair-and-rejection sequence. B04, every other Case, the suite manifest, runtime code, Schema V2, and the Canonicalization Profile documents were not touched. No replay, no historical environment reconstruction, no synthetic log, no Suite Manifest, no Suite fingerprint, no methodology or ADR change, no replacement candidate construction.
