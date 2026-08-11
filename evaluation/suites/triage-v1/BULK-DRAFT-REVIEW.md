# Issue #15 Schema V2 bulk pre-freeze draft review

**Bulk construction status:** 19 packages — 13 `DRAFT_READY`, N01, N11 and N18 `HUMAN REVIEW PASS` (pre-freeze), B08 `REVIEWED` awaiting a portfolio decision, plus N17 and N16 `REJECTED`.
**Original 19-candidate disposition:** 18 constructed; N06 `REPLACED` because its committed iDFlakies record has no Agent-visible exception/stack/failure detail.
**Human Review status:** `PENDING` for the 13 `DRAFT_READY` packages. **B08 has completed full Human Review**: Layer 1 `PASS` after reversing four non-secret replacements, Layer 2 **`LOW`**; its disposition is a portfolio decision, not a validity one. **N01, N11 and N18 have passed package-content Human Review** (Runtime Discriminative Value `ADEQUATE — lower end`, `BORDERLINE-ADEQUATE` and `BORDERLINE-ADEQUATE`); those are review passes, not Formal Freezes. **N01 and N18 have passed package-content Human Review** (Runtime Discriminative Value `ADEQUATE — lower end` and `BORDERLINE-ADEQUATE` respectively); those are review passes, not Formal Freezes. **N18 has passed package-content Human Review** with Runtime Discriminative Value `BORDERLINE-ADEQUATE`; that is a review PASS, not a Formal Freeze. **N17 is `REJECTED` (`REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`) and N16 is `REJECTED` (`INVALID_FAILURE_ARTIFACT_AND_LOW_DISCRIMINATIVE_VALUE`); neither is a Formal Suite member.** B04 remains the unchanged Human-reviewed calibration baseline at fingerprint `89a8f9a08f0dcb26…`.
**Unfilled Formal Suite slots:** `timeout_or_flaky_failure: 2` (N17 and N16). N01 and N18 have both passed Human Review, so 2 of the 4 slots are filled and the confirmed shortfall is **2**. All four candidates in this type are now resolved.

These packages are not Human-frozen, final, or a Formal Suite. Schema V2 currently requires the literal loader value `curation.review_status = human_reviewed`; each new `case.json.reviewed_by` explicitly scopes that marker to the already completed Candidate Selection and Source Artifact Eligibility gates and states that package-content Human Review remains pending. The Bulk Review Ledger is the authoritative draft-state record.

Durable intent: source identity, Physical Artifacts, exact/relevant revisions, causal semantics, taxonomy, and Expected Diagnosis semantics. Disposable pre-freeze layer: Canonical boundaries, Evidence IDs, Required/Optional ID mapping, and Case fingerprint.

## Two-layer admission requirement

Formal Case admission is now reviewed in two layers, applied to N17 first:

- **Layer 1 — Scientific Validity:** authentic historical failure, source-faithful provenance, exact executed revision, valid causal chain, Ground Truth supported by Agent-visible evidence, no leakage or curator bias, fair Runtime treatment.
- **Layer 2 — Runtime Discriminative Value:** enough real investigation complexity that a simple Runtime cannot approach Oracle merely because the curator shrank the search space, and enough measurement value for Retrieval, ReAct, planning, tool use, context selection, and verification.

The Physical Evidence Universe is a **bounded natural investigation workspace**; Required Evidence is the **inclusion-minimal sufficient** subset. The gap between them is the space in which Runtime capability is measured. Neither shrinking the Universe toward the known answer nor padding it with synthetic distractors is permitted; membership follows the plausible natural investigation neighbourhood visible from the failure observation.

Two corollaries, both established by the N17 review:

- **Membership is decided by an answer-neutral scope rule, never by how helpful a file turns out to be.** A file belongs to the workspace if a reader who does not know the answer would reach it by being named in the observation, by the project-internal dependency closure of an observation-named file, by opening the owning implementation module of the subsystem whose output the observation quotes, by opening the failing job's configuration, or by listing/searching the failing test's own family. Excluding a member because it leaks the diagnosis is curator manipulation in the harder direction and is forbidden. Only *future* artifacts — the fix, the passing revision, later PRs, curator research — stay out.
- **If authentic contemporaneous content makes a Case easy, replace the Case; do not hide the content.** The verdict is then `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`, which records insufficient measurement value, not a false or defective source.

This rule is accepted in principle but **deliberately not frozen** into the methodology or an ADR yet. It must be validated against N16, N01 and further real Cases before being generalized from a single observation.

Each review records a `Runtime Discriminative Value` verdict of `ADEQUATE`, `LOW`, `TRIVIAL`, or `BLOCKED`, together with the diagnostic counts behind it **and a shortcut test**: the searches a reader would derive directly from the failure observation, and what those searches return. Counts alone are not decisive — N17 was rejected with entirely healthy counts (43 units, 7.0 % Required, 90.7 % of units in files holding no Required evidence), because one observation-derived search reaches a contemporaneous comment stating the mechanism. **No numeric threshold is frozen**; a suite-wide policy will be written into the methodology after N16, N01 and further real Case reviews.

### N17 and N16 as negative calibration examples

N17 is retained in the tree as review history, a rejection record, and a **negative calibration example**. It establishes on a real Case that:

> **`scientifically valid` ≠ `useful formal benchmark case`.**

and documents the specific failure mode:

> The real failure-era repository already contains a same-family sibling fix carrying strong causal or remedial guidance → obvious failure-derived search finds it in one hop → the acquisition gap collapses → the Case is unsuitable as a Formal Runtime benchmark, however authentic it is.

N16 records a **different and independent** failure mode, and the two must not be collapsed:

> The Agent-visible raw failure artifact was never a failure observation — it was the fix author's post-hoc
> description quoted from the fix PR body → pre-localized, adjacent to the stated root cause and remedy, and
> with no surviving authentic artifact to replace it → Layer 1 fails and cannot be repaired.

| | N17 | N16 |
|---|---|---|
| Layer 1 | `PASS` after repair | **`FAIL / BLOCKED`, unrepairable** |
| Layer 2 | `FAIL` | `LOW` |
| Salvageable? | Yes — an authentic Check Run annotation survived | No — job log expired, only a generic exit-code annotation remains |

Full records: `reviews/n17-review.md`, `reviews/n16-review.md`.

### Provenance category: undeterminable exact failing revision + deterministic failure-era snapshot

Suite-level Human decision, established by N18 and available to any later Case with the same shape. A Formal Case may be
admitted when its exact failing revision can never be recovered, but it must not be dressed up as an exact-revision Case.
Requirements:

1. an authentic dated failure artifact;
2. the exact failing revision is genuinely unrecoverable, with the reason stated;
3. a deterministic failure-era repository snapshot;
4. that snapshot is at or before the failure observation — **never** a later pre-fix commit chosen for proximity to the fix;
5. per-member history checked around the failure era for every causally relevant Physical Universe member;
6. members that drifted after the observation are refrozen to failure-era bytes by preference;
7. Ground Truth relies only on facts already stable in the failure era;
8. provenance states all three of *actual failing revision*, *recoverable failure-era snapshot*, and *relationship / confidence*;
9. the snapshot is **never** called the exact failing revision.

**The snapshot-selection rule is deterministic; it is not a probability claim.** "Latest suitable upstream default-branch
commit at or before the failure-observation timestamp" must never be read as "probably the commit the reporter actually ran".
Its correct meaning is narrower: the snapshot is a legitimate failure-era state in time, the frozen bytes come exactly from
that commit, the causally relevant facts are compatible with the authentic observation, and exact-executed-state confidence
remains unattainable. Reviews must keep *failure-era snapshot confidence* and *exact executed revision confidence* distinct.

`repository-manifest.json.exact_revision` under this category means **the exact upstream revision of the frozen repository
bytes**, not the exact executed revision of the failure. Read that way the field carries no factual error, and provenance
must still state `actual failing revision = undeterminable` alongside the snapshot's role.

Representation limitation, accepted and not worked around: `repository-manifest.json` has a single revision slot and the
loader rejects unknown fields, so the distinction lives in `provenance` free text and no validator can enforce it. Schema V2
is unchanged. Two independent instances now exist — N17's unrecoverable ephemeral PR merge SHA and N18's undeterminable
failing revision — which is recorded as a future improvement candidate (`revision_role`, `executed_revision`,
`revision_identity_note` or equivalent) for the Schema owner. It must not block Issue #15. This category is deliberately **not** yet written into the
methodology or an ADR.

### Calibration finding: Evidence Hit does not measure candidate elimination

Established by the N01 review and recorded for later, once Runtimes exist. N01's two restored sibling test classes are
deliberately **neither Required nor Optional**: their value is that an Agent must open and eliminate them as plausible
polluters, and they are never cited in a correct diagnosis.

Retrieval Evidence Hit and Report Evidence Hit both measure **positive supporting evidence acquisition** — whether the
Runtime reached and cited the facts that support the answer. Neither measures **negative evidence work**, i.e. ruling out
competing candidates. In N01 seven candidate polluters must be eliminated, yet a Runtime that eliminates them thoroughly
scores identically to one that guesses the polluter correctly first try.

Recorded as a calibration/review finding only. The scorer, Schema V2, the methodology and the ADRs are **not** changed.
Signal to watch: if ReAct demonstrably performs better candidate elimination than Retrieval but the Evidence Hit gap stays
flat, the metric is missing this dimension of investigation quality.

### Sanitization technique rule: replace, do not excise

Established by the N11 review. When a Physical Artifact contains a real secret, the correct treatment is **typed-placeholder
replacement preserving file extent, structure and line coordinates** — the technique already used by
`bugswarm-traccar-166900445` (`[SANITIZED_SMTP_USERNAME]` and similar).

Deleting surrounding content is **not** acceptable. N11's draft removed 137 of 171 lines of `gradle/publishing.gradle` to
strip one credential line, which pruned several competing hypotheses, left a log line (`touch local.properties`)
unexplainable from the workspace, and — worst — presented the excerpt as a complete file, numbered from line 1, with no
disclosure that it was truncated. Reversed.

A sanitization transformation must never reduce the Agent-visible investigation workspace beyond the secret itself, and a
truncated artifact must never be presented as complete.

**Corollary from B08 — replace only what is actually protected.** Before replacing a literal, confirm it is genuinely a secret, personal datum, private hostname or internal URL. B08's draft had replaced `SMTP_USERNAME = "username"`, `SMTP_PASSWORD = "password"`, a public AWS SES endpoint and a public project role address. None was protected content, all four were causally load-bearing, and `[SANITIZED_SMTP_HOST]` is unresolvable, so the sanitized source predicted a name-resolution failure instead of the 535 the log records — the artifact contradicted its own observation. Replacing a non-secret is worse than leaving it: it removes evidence *and* asserts something false.

**Human decision:** N11's earlier "Human-approved strict allowlist" is explicitly **superseded** by this rule. The rule is kept
at ledger level as an operational convention and is deliberately **not** promoted to the methodology or an ADR yet.

### Measurement-Value Screening — run during Candidate Discovery, before construction

N17's cost was that this was discovered only after a complete package had been built and repaired twice. Screen candidates against their real failure-era repository **before** committing to package construction:

0. **Is the raw failure artifact from the failure side at all?** It must be a CI job log, a Check Run failure
   annotation, or a failure-reporting issue body. **Never** narrative text from a fix PR, a fix commit message,
   or a post-mortem write-up, however verbatim the quotation: such text is authored after the diagnosis is
   known, arrives pre-localized, and usually sits in the same paragraph as the root cause and the fix. If a
   candidate's only surviving failure text lives in a fix PR, check whether an authentic failure-side artifact
   still exists; if none does, drop the candidate here rather than constructing a package. (N16 rule.)
1. Does the authentic failure observation already expose the root cause or the recommended action directly?
2. Does a sibling in the same test / module / failure family already carry an almost-direct historical fix?
3. Do obvious failure-derived queries — error tokens, the failing operation, test / function / module names, and natural keywords such as `flaky`, `timeout`, `race`, `restart`, `intermittent`, `sporadic`, issue numbers — hit an answer-bearing file in one hop?
4. Is simple `grep` or filename search already sufficient to reach the diagnosis?
5. Does the Case still require multi-step navigation, hypothesis formation, evidence composition, and competing-hypothesis discrimination?
6. Does the natural investigation workspace contain enough genuine search space?
7. Does a shortcut exist that the curator cannot legitimately remove?
8. If the artifact comes from a research benchmark, does that benchmark publish its own answer key
   alongside the record? iDFlakies ships `idfProjectsMinimizer.csv` (minimized polluter) and
   `idfProjectsFixer.csv` (fix outcome) in the same repository as the detection records. Such files are
   curator-only and must never enter the Physical Universe. (N01 rule.)

If a candidate already looks `LOW` or `TRIVIAL` at this stage, drop it before paying full Case Package construction cost. **Never make a candidate harder by hiding contemporaneous information.**

All three remaining `timeout_or_flaky_failure` candidates have now been screened this way. N16 was dropped on item 0; N18 passed screening and then full review; N01 remains queued. Every future candidate must be screened before construction.

## Construction ledger

| Case | Failure Type | Candidate source | Disposition | Exact/relevant revision | Raw failure artifact | Repo files | Physical lines / bytes | Canonical units | Req / Opt | Root-cause summary | Provenance | Sanitization | Scientific risk | Human Review |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| B01 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/170287308/raw/ | `DRAFT_READY` | `4216e038468184a58e9fa10cb9eaff28450de743` | complete BugSwarm failed log | 6 | 3263 / 292121 | 37 | 3 / 1 | The sample matches the supported Upro packet pattern and follows the normal Position construction path, while the test still calls verifyNothing. The test oracle is stale for a valid decoded sample. | traced public source | ANSI/control-only normalization | Low: causal path is compact, but the full log and six-file snapshot still require localization. | `PENDING` |
| B02 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/190697114/raw/ | `DRAFT_READY` | `880c4c2d33f67c28a834a44da5a2523b858601b3` | complete BugSwarm failed log | 6 | 23129 / 2049094 | 235 | 3 / 1 | The test oracle expects the misspelled prefix 'The file is to large', while the English upload message produced by the failing revision says 'The file is too large'. The product message and assertion text are out of sync. | traced public source | ANSI/control-only normalization | Medium: a very large authentic log contains many fatal/error distractors; the terminal summary names the victim but suppresses the assertion message. | `PENDING` |
| N12 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/89457805/raw/ | `DRAFT_READY` | `4776a4e472e3a14cf475e95f0e146fc3f79b50eb` | complete BugSwarm failed log | 7 | 809 / 30445 | 13 | 2 / 1 | The test compares a stringified form-error payload whose Python 2 representation exposes a Unicode prefix. The assertion is coupled to representation details instead of the semantic form.errors mapping. | traced public source | ANSI/control-only normalization | Low-medium: the representation mismatch is visible, while semantic-vs-string diagnosis still requires the test source. | `PENDING` |
| N22 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/13013454823/raw/ | `DRAFT_READY` | `019244aa79f9adc182ee138955cc50efe37df9b6` | complete BugSwarm failed log | 6 | 913 / 49498 | 14 | 3 / 0 | The implementation emits contentType, but the expected fixtures on the failing branch still use ContentType. A contract-key change left the test oracle stale. | traced public source | ANSI/control-only normalization | Medium: failing and passing revisions are sibling histories; the package correctly uses only the failing branch, but provenance must not be narrated as a direct child fix. | `PENDING` |
| B05 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/86922674/raw/ | `DRAFT_READY` | `25f732d6280b3033dc6f5d7fcf70f5de5e7abf64` | complete BugSwarm failed log | 4 | 4920 / 494595 | 52 | 2 / 1 | The collection overload recursively calls itself without reducing to a different overload or base case, so static analysis detects an infinite-recursion path. | traced public source | ANSI/control-only normalization | Low-medium: FindBugs names the recursive method directly; repository search is still required to confirm the missing base/delegation path. | `PENDING` |
| N07 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/237548392/raw/ | `DRAFT_READY` | `ec1efc4f95a9ee2abca72e9cef4304a19eb5366f` | complete BugSwarm failed log | 5 | 4022 / 288898 | 44 | 3 / 0 | retry_on_error promises to return the callback's generic result, but callers use side-effect-only lambdas whose return contract provides no useful type argument. The helper signature is over-general for its use. | traced public source | ANSI/control-only normalization | Medium: the checker points at a call site, and diagnosis requires relating it to the generic helper contract. | `PENDING` |
| N09 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/149441998/raw/ | `DRAFT_READY` | `2431dfb0c85e883a6389b04583a49dc80b61eeb9` | complete BugSwarm failed log | 4 | 10617 / 646957 | 109 | 2 / 0 | The reflective compatibility fallback intentionally catches a broad Exception, but the source provides no analyzer-recognized justification, producing REC_CATCH_EXCEPTION. | traced public source | ANSI/control-only normalization | Medium: the finding is late and precise, but deciding between narrowing and justified suppression requires understanding the reflective fallback. | `PENDING` |
| B06 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/221926468/raw/ | `DRAFT_READY` | `15f3258905e964ab3b23d9c11fde4a1946ef10b0` | complete BugSwarm failed log | 5 | 11291 / 983498 | 116 | 3 / 2 | The project resolves async-http-client 2.0.31, whose class file is Java 8 major version 52, while the CI job runs OpenJDK 7. The incompatible dependency poisons shared initialization. | traced public source | ANSI/control-only normalization | Low-medium: class-version semantics are strong; fan-out volume and JDK/dependency cross-artifact reasoning provide the main difficulty. | `PENDING` |
| B09 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/118661876/raw/ | `DRAFT_READY` | `a654e03ebf8660b24aa56180a331fb76e79a73f7` | complete BugSwarm failed log | 5 | 1318 / 54875 | 17 | 3 / 1 | The selected test path imports NumPy, but the failing revision's test dependency set does not declare/install it, so collection/execution fails with ImportError. | traced public source | ANSI/control-only normalization | Medium: missing-package causality partly relies on manifest absence, which is less direct than a positive declaration. | `PENDING` |
| N13 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/113213406/raw/ | `DRAFT_READY` | `2b7fc2f824696a408d6c857fb98bab593c4def41` | complete BugSwarm failed log | 6 | 5100 / 220461 | 55 | 4 / 1 | The tiny adapter path imports tinydb, but the failing revision's dependency manifest omits that package. The CI matrix validly selects the path; the package declaration is incomplete. | traced public source | ANSI/control-only normalization | Medium: dependency absence is established by combining matrix selection, import site, and the bounded requirements file. | `PENDING` |
| N20 | `dependency_or_install_failure` | https://github.com/alplabai/tan-cli/actions/runs/30459137058 | `DRAFT_READY` | `3043521c5ef278d79d34045bdb2116e81e9c661d` | Complete historical first-blink GitHub Actions job log from run 30459137058. | 4 | 4928 / 407910 | 51 | 2 / 1 | The clean Linux runner prerequisite list omits libudev development headers required by hidapi. Bootstrap continues after the failed requirements install, causing downstream missing-module symptoms. | traced public source | ANSI/control-only normalization | High: the first causal native-build error is far from the terminal symptom, and the pinned SDK supplies part of the install behavior outside the allowed repository universe. | `PENDING` |
| B08 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/166900445/raw/ | `REVIEWED`; Layer 1 `PASS` after reversing four non-secret replacements, **Layer 2 `LOW`**; disposition is a portfolio decision | `18d39ff2412b9aced899915d0187f21eb25f49b6` | complete BugSwarm failed log | 4 | 2945 / 268909 | 33 | 2 / 1 | An environment-dependent integration test runs in the ordinary suite and opens an authenticated SMTP connection to a public AWS SES endpoint using the placeholder credentials committed in the test source, so the service rejects it with 535. | traced public source | **four replacements REVERSED** — only the personal email is redacted; username, password, host and FROM restored | **Layer 2 `LOW`**: one grep locates the failure, the log names the victim, and one 59-line file explains it. No cross-file composition, no competing hypothesis. Intrinsically shallow, not mishandled. | `PENDING RE-REVIEW` |
| B16 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/138584081/raw/ | `DRAFT_READY` | `3a90292cacebbd8dbdb7228a36ca89c0f6a9940f` | complete BugSwarm failed log | 5 | 5133 / 564171 | 55 | 3 / 1 | MacroHelperTest invokes a JOptionPane path in an environment without a graphical display. The test's GUI requirement is incompatible with the headless CI runtime. | traced public source | ANSI/control-only normalization | Low: HeadlessException and JOptionPane call path are direct; the main value is environment-vs-test classification. | `PENDING` |
| N10 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/170953503/raw/ | `DRAFT_READY` | `64e149b69750fdc6f150a18e39a3df1ba76ccc24` | complete BugSwarm failed log | 3 | 725 / 27746 | 10 | 2 / 0 | The submodule URL uses the SSH git@github.com transport, but the keyless CI checkout environment has no matching private key. The repository transport configuration is incompatible with CI. | traced public source | ANSI/control-only normalization | Low: the log and .gitmodules form a clean cross-artifact diagnosis. | `PENDING` |
| N11 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/64757057/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS` after reversing an allowlist extraction, Layer 2 `BORDERLINE-ADEQUATE`) | `dc1efd4c626362bb469813229fb5b48b660f1bf3` | complete BugSwarm failed log, verified byte-exact against strip_ANSI(upstream) | 4 | 1516 / 76978 | 19 | 3 / 3 | The build applies the publishing script to every build and that script signs the archives configuration unconditionally rather than only on a publish/upload path. CI supplies no signing identity, so signArchives enters an ordinary assemble task graph and fails with no configured signatory. | traced public source; Travis default-install step recorded | **allowlist extraction REVERSED** — publishing.gradle restored to full 171 lines with only the line-96 credential replaced by typed placeholders | Layer 2 `BORDERLINE-ADEQUATE`: 101 authentic javadoc `error:` distractor lines and a task name absent from source, but the log states both the failing task and its reason. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N01 | `timeout_or_flaky_failure` | https://github.com/UT-SE-Research/iDFlakies/blob/master/scripts/flaky-lists-files/cukes-http (complete committed record); pinned-SHA list scripts/idfProjects1.csv | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS` after Physical Universe repair, Layer 2 `ADEQUATE — lower end`) | `b483e1a8f261b80a66291a42fc455256b0b5059c` — **exact executed revision**, pinned by iDFlakies `idfProjects1.csv`, not inferred | Byte-identical complete iDFlakies record, 37 lines / 1935 bytes; no exception, stack or assertion output | 15 | 1581 / 54816 | 23 | 5 / 4 | Each test instance takes its world from a JVM-wide SingletonObjectFactory and so shares one @Singleton GlobalWorld whose map is built once and never reset. The preceding test writes ASSERTS_STATUS_CODE_MAX_SIZE=5 and never clears it; the victim enables body display without setting or clearing that key, so it inherits the leaked limit and its expected full-body assertion text is replaced by the truncated form. | exact executed revision, benchmark-pinned | `reviewed_no_changes` — byte-identical to upstream | Layer 2 `ADEQUATE`: seven authentic competing polluters restored, and the observation names no state-machinery token, so two Required units are unreachable by observation-keyed retrieval. Weakness: victim and true polluter share one file. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N16 | `timeout_or_flaky_failure` | https://github.com/gptme/gptme/pull/1968 (fix PR); historical run https://github.com/gptme/gptme/actions/runs/23841222952 | **`REJECTED` — `INVALID_FAILURE_ARTIFACT_AND_LOW_DISCRIMINATIVE_VALUE`; not a Formal Suite member** | `f48de363aa956caae8789a9b751d7631fd44fe3c` (real run head, pre-fix) | **Not an authentic failure observation:** one sentence quoted from the body of merged fix PR #1968. Job log HTTP 410; only surviving Check Run annotation is a generic `.github` exit-code failure with no test-level detail, so salvage is impossible. | 4 | 2752 / 92050 | 30 | 3 / 0 | (as drafted) The implementation publishes the subagent in the shared list before starting its background thread, while the test treats list growth as completion and immediately indexes mock_create_thread.call_args. | fix-PR narrative, not failure-side artifact | transcription of fix-PR prose; earlier ANSI-removal claim was false | Layer 1 FAIL/BLOCKED and unrepairable. Layer 2 LOW: `api.py:417-419` comments state the race mechanism and same-file sibling tests already show the join remediation. | `REJECTED`; retained as negative calibration example |
| N18 | `timeout_or_flaky_failure` | https://github.com/osquery/osquery/issues/7718 (failure-reporting issue); curator-only fix https://github.com/osquery/osquery/pull/7888 | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `BORDERLINE-ADEQUATE`) | **failure-era snapshot** `3d26714fc113cef9e79fde0ae1fd52e1d5ba6f2c` (2022-08-08T15:52:27Z, 27 min before the issue); **actual failing revision UNDETERMINABLE** — the issue records no run/build/job/branch/commit anchor | Byte-identical fenced traceback from the issue body, 9 lines / 508 bytes, all nine CRLF retained | 3 | 1933 / 60393 | 22 | 5 / 2 | The test pre-creates the pidfile its own readiness wait polls, so the wait can return before the daemon installs its SIGINT handler. In real startup the handler precedes pidfile creation, so a daemon-created pidfile would be a valid readiness signal; the test's own `touch()` breaks that contract. The default disposition then yields -2 instead of the handled 0. | undeterminable failing revision + deterministic failure-era snapshot | `reviewed_no_changes` — full byte fidelity | Layer 2 `BORDERLINE-ADEQUATE`: complete diagnosis needs 4 artifacts / 5 windows across two languages with no answer-bearing prose present, but victim localization is free and a partial answer is cheap. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N17 | `timeout_or_flaky_failure` | Actions run https://github.com/nodejs/node/actions/runs/22532700362/job/65274588187 ; related tracking issue https://github.com/nodejs/node/issues/61762 ; curator-only causal PR https://github.com/nodejs/node/pull/62055 | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`; not a Formal Suite member** | executed: ephemeral `refs/pull/65153/merge`, merge SHA unrecoverable; recoverable byte-equivalent: `3c08a48c24c39ad4dee6d95c5c800246f300525e` | Verbatim GitHub Check Run failure annotation for `test/parallel/test-debugger-exceptions.js`; full Actions job log expired (HTTP 410) and was not reconstructed. | 11 | 3665 / 109731 | 43 | 3 / 6 | The restart step synchronizes only on the break message, inside one fixed window opened before the restart begins, so it depends on debugger output timing and fails intermittently on macOS. Why the break line was absent is deliberately left unresolved. | verified upstream primary sources | trailing newline only | Layer 1 PASS. Layer 2 FAIL: the contemporaneous repository already contained a commented fix for this exact flake pattern in a sibling of the victim, so one observation-derived search yields root cause and recommended action. | `REJECTED`; retained as negative calibration example |

| N06 | `timeout_or_flaky_failure` | iDFlakies WildFly naming record | `REPLACED` by N17 | `b19048b72669fc0e96665b1b125dc1fda21f5993` | Intended PASS plus revealed ERROR with empty revealed order; no exception/stack/output | — | — | — | — | Agent-visible failure evidence is insufficient without prohibited replay or invention. | traced public source | n/a | Source blocker is decisive. | replacement previously Human-approved |

## Failure-type outcome

- `test_assertion_failure`: B01, B02, N12, N22 — 4 drafts.
- `lint_or_type_failure`: B05, N07, N09 plus unchanged B04 — 3 new drafts.
- `dependency_or_install_failure`: B06, B09, N13, N20 — 4 drafts.
- `config_or_environment_failure`: B08, B16, N10, N11 — 4 drafts.
- `timeout_or_flaky_failure`: **N01 and N18 `HUMAN REVIEW PASS`** (2 of 4 slots filled, both pre-freeze); N06 `REPLACED`, its replacement N17 `REJECTED` for low Runtime Discriminative Value, and N16 `REJECTED` for an invalid failure artifact plus low value. **Two slots are unfilled**, and a third would open if N01 fails.

## Validation contract

Every new draft passed JSON parse, Schema V2 loader, declared/calculated fingerprint equality, exact repository membership/hashes/sizes, path safety, fixed-100 full coverage with no gaps/overlaps, canonical resolved hashes, Required/Optional referential integrity, Expected Answer schema, PublicCaseView leakage checks, targeted secret scans, and known fix/passing SHA scans. The shared fixed-100 audit is an explicit bulk-construction check; the generic loader does not itself enforce Profile compliance.

Passing this contract establishes only that a package is structurally sound. The N17 BLOCKER passed every item above while combining three unrelated histories, and the finally repaired N17 passed every item and was still rejected for low measurement value. Structural validation must never be read as scientific validity, and neither implies Formal Suite admission. N17's fix/passing SHA scan list was extended to cover the restart-message fix `3163d8aa…`, the sibling-migration fix `4f04a36b…`, and both PR #62055 commits `9de9b9f8…` and `6dca8733…`.

## Human Review priority — scientific risk first

1. ~~N17~~, ~~N16~~ — **reviews closed, both `REJECTED`.** No further review needed. Replacement candidates must go through Measurement-Value Screening before construction.
2. ~~N18~~ — **review closed, `HUMAN REVIEW PASS`.** Layer 1 `PASS` after refreezing onto a failure-era snapshot; Layer 2 `BORDERLINE-ADEQUATE`, which must not be rewritten upward. Full record: `reviews/n18-review.md`.
3. ~~N01~~ — **review closed, `HUMAN REVIEW PASS`.** The two omitted observation-named test classes were restored under scope clause (a), turning polluter identification into genuine seven-candidate discrimination; Ground Truth was tightened to the Required-supported form and its observed-versus-derived wording verified. Layer 2 `ADEQUATE — lower end`, which must not be rewritten upward. Full record: `reviews/n01-review.md`.
4. ~~N11~~ — **review closed, `HUMAN REVIEW PASS`.** Its `gradle/publishing.gradle` allowlist extraction kept only 32 of 171 lines and has been reversed; the earlier "Human-approved" allowlist is explicitly superseded. Layer 2 `BORDERLINE-ADEQUATE`. See `reviews/n11-review.md`.
5. N20: cross-repository pinned SDK behavior and first-error vs terminal-symptom causality.
6. ~~B08~~ — **full review complete, awaiting a portfolio decision.** Four of five replaced literals protected nothing and one made the frozen source contradict the log; reversed. Layer 2 `LOW`. See `reviews/b08-review.md`.
7. B02, N22, B09, N13: distractor/provenance/absence-evidence/partial-job nuances.
8. N07, N09, B06, B05, N12: moderate causal and Ground Truth review.
9. B01, B16, N10: lowest-risk direct causal chains.

## Calibration inputs

- B01: sufficient real full-log + six-file Physical Universe; ready for calibration observation after this draft is accepted.
- B06: sufficient real full-log + five-file Physical Universe; ready for calibration observation after this draft is accepted.
- N01 (reviewed): complete committed JSON record + fifteen-file Physical Universe. Its non-log benchmark record remains the key Schema/attribution calibration stressor, and it adds two `N=100` observations — twelve of fifteen members are shorter than 100 lines and collapse to whole-file units, making Evidence Hit file-granular, while the one member that does split puts the victim and its polluter in different units.
- N17 (rejected, but its coordinate observations remain usable): contributes two concrete `N=100` boundary observations for the `N ∈ {50, 100, 200}` comparison — `inspect_repl.js` splits one `paused`-handler causal fact across units `0801-0900` and `0901-1000`, and the Required pair `debugger.js` `0001-0100` / `0101-0190` splits one helper's semantics across two units. Recorded as observations only; the Profile remains unfrozen and calibration has not started.

No Suite Manifest, Suite fingerprint, Runtime implementation, replay, historical environment reconstruction, or synthetic failure log was created. No methodology document or ADR was changed by the N17 review.
