# Issue #15 Schema V2 bulk pre-freeze draft review

**Bulk construction status:** 19 packages — **every package reviewed and dispositioned; 0 `DRAFT_READY`, 0 awaiting disposition.** B01 / B02 / B06 / B08 / N01 / N07 / N09 / N11 / N18 / N20 `HUMAN REVIEW PASS` (pre-freeze, 10 Cases); B05 / B09 / B16 / N10 / N12 / N13 / N16 / N17 / N22 `REJECTED` (9 Cases). B04 is the unchanged Human-reviewed Schema V2 calibration reference, **provisionally retained** as one `lint_or_type_failure` Formal candidate for discovery planning.
**Original 19-candidate disposition:** 18 constructed; N06 `REPLACED` because its committed iDFlakies record has no Agent-visible exception/stack/failure detail.
**Human Review status:** **all 19 packages reviewed and dispositioned; the existing-draft Human Review phase is CLOSED.** **`test_assertion_failure` is fully resolved**: B02 `PASS` (`ADEQUATE`) and B01 `PASS` (`BORDERLINE-ADEQUATE`); N12 `REJECTED` (`REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`, Layer 1 `PASS`) and N22 `REJECTED` (`UNDERDETERMINED_GT_AND_LOW_DISCRIMINATIVE_VALUE`). **N22 is the one rejection whose Layer 1 is NOT recorded as a clean `PASS`**: the frozen evidence proves only that the implementation emits `contentType` while the fixtures expect `ContentType`, and does not establish which side is stale or regressed, so its Ground Truth direction is underdetermined. N22 was not salvaged. **`lint_or_type_failure` is fully resolved**: N07 `PASS` (`ADEQUATE`) and N09 `PASS` (`BORDERLINE-ADEQUATE`) alongside the B04 Human-reviewed Schema V2 calibration reference; B05 `REJECTED` with Layer 1 `PASS`. **Nothing here is frozen** — `Canonicalization Profile v1` is unfrozen and no Suite Manifest exists. **`dependency_or_install_failure` is fully resolved**: B06 `PASS` (`ADEQUATE`) and N20 `PASS` (`ADEQUATE — lower end`); B09 and N13 `REJECTED` for low discriminative value, both with Layer 1 `PASS`. **N20 has passed package-content Human Review**: Layer 1 `PASS` with the executed merge revision recovered and verified, Layer 2 `ADEQUATE — lower end`. **`config_or_environment_failure` is fully resolved**: N11 `PASS` (`BORDERLINE-ADEQUATE`) and B08 `PASS` (`LOW`, admitted as a deliberate low-difficulty anchor); B16 and N10 `REJECTED` for low and trivial discriminative value, with Layer 1 `PASS` in both cases. **B08 has completed full Human Review**: Layer 1 `PASS` after reversing four non-secret replacements, Layer 2 **`LOW`**; its disposition is a portfolio decision, not a validity one. **N01, N11 and N18 have passed package-content Human Review** (Runtime Discriminative Value `ADEQUATE — lower end`, `BORDERLINE-ADEQUATE` and `BORDERLINE-ADEQUATE`); those are review passes, not Formal Freezes. **N01 and N18 have passed package-content Human Review** (Runtime Discriminative Value `ADEQUATE — lower end` and `BORDERLINE-ADEQUATE` respectively); those are review passes, not Formal Freezes. **N18 has passed package-content Human Review** with Runtime Discriminative Value `BORDERLINE-ADEQUATE`; that is a review PASS, not a Formal Freeze. **N17 is `REJECTED` (`REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`) and N16 is `REJECTED` (`INVALID_FAILURE_ARTIFACT_AND_LOW_DISCRIMINATIVE_VALUE`); neither is a Formal Suite member.** B04 remains the unchanged Human-reviewed calibration baseline at fingerprint `89a8f9a08f0dcb26…`.
**Final replacement backlog — 9 slots, all five categories resolved:** `timeout_or_flaky_failure: 2` (N17, N16), `config_or_environment_failure: 2` (B16, N10), `dependency_or_install_failure: 2` (B09, N13), `lint_or_type_failure: 1` (B05), `test_assertion_failure: 2` (N12, N22) — **9 confirmed, final**. 10 of 20 slots are filled by Human-reviewed Cases; the `lint_or_type_failure` count of 1 assumes **B04 is provisionally retained** as one candidate of that type for planning purposes. That provisional retention is **not** a Canonicalization Profile v1 freeze, **not** a Suite Manifest freeze, and **not** a Formal Suite freeze. The full taxonomy shortfall is now known, so targeted discovery proceeds as **one combined round covering all 9 slots**, not category by category.

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

### Provenance note: a `pull_request` job log may record its own executed merge SHA

N20 adds a third variant to the revision-identity problem, and the best one. On a `pull_request` event `actions/checkout`
takes the ephemeral merge ref, so the run's `head_sha` is the pull-request head rather than what executed. In N17 that merge
SHA was unrecoverable. In N20 **the job log records it directly** — the `git fetch`, the `git checkout` and a
`HEAD is now at <sha> Merge <head> into <base>` line — and the commit was still addressable, so the executed revision could be
declared and every member verified against the merge tree.

**Check the job log for the checkout lines before concluding a merge SHA is lost.** Where it is recoverable, declare it and
record the pull-request head as a fallback, since the frozen members are normally byte-identical at both and the ephemeral ref
may later be garbage-collected.

### Portfolio policy for low-value Cases

Human decision, recorded at ledger level only and deliberately **not** promoted to the methodology or an ADR:

- **`LOW` is not automatically disallowed** when the Case serves an explicit, stated portfolio role. A suite in which every
  Case is hard cannot distinguish a weak runtime from a broken one, so one clean, unambiguous easy Case per failure type has
  diagnostic value at the bottom of the range. B08 is admitted on exactly that basis, and its role travels with it: it is
  admitted **because** it is easy, and must never be described as discriminating.
- **`LOW` Cases are not required per taxonomy.** One suite-level easy anchor is enough, and B08 already serves that role, so a
  category must not retain a `LOW` Case merely to preserve its count. B09 and N13 were rejected on exactly this basis.
- **`TRIVIAL` should generally not occupy an equal-weight Formal slot.** Where the observation essentially states the
  complete diagnosis, an equal-weight slot buys nothing. N10 is rejected on this basis.
- **Layer 1 and Layer 2 are independent axes.** B16 and N10 are both rejected with Layer 1 `PASS`: authentic, byte-identical
  to their exact revisions, correctly diagnosed, and worth nothing as benchmarks. Every rejection record must say which axis
  failed, so a later reader never mistakes a measurement-value rejection for a provenance defect.

### Category finding: `test_assertion_failure` is graded by how much the assertion message discloses

All four reviewed. The variable is not the failure class but **how much of the comparison the test framework prints**.

| Case | Layer 2 | Required | What the observation discloses | What the source must supply |
|---|---|---:|---|---|
| B02 | **`ADEQUATE`** | 3 (1.3 %) | **only the test name**, one of 1,680; assertion message suppressed; the expected string occurs **zero** times in the log | **both sides of the comparison**, and a one-character `to`/`too` difference |
| B01 | `BORDERLINE-ADEQUATE` | 3 (8.1 %) | the mismatch, but the actual value is an opaque `Position@285fb753` | whether producing a `Position` is correct — the oracle-versus-product judgement |
| N12 | `LOW` | 2 (15.4 %) | **both sides in full**; difference is one visible `u` prefix | nothing the observation withholds |
| N22 | `LOW` | 3 (21.4 %) | **both key spellings**, so the mismatch is visible | only which side emits which |

**Dispositions:** B02 `PASS`, B01 `PASS`, N12 `REJECTED` (Layer 1 `PASS`), N22 `REJECTED` (Layer 1 **not** a clean `PASS` — see below).

An assertion failure is only discriminative when the framework **withholds** part of the comparison. Where JUnit or pytest
prints expected and actual in full, the Case collapses to reading a diff. B02 is discriminative precisely because Maven's
terminal summary names the failing test and nothing else.

Required share is again anti-correlated with difficulty: B02 has the **lowest** share in the entire suite at 1.3 % and is the
hardest, while N22 has the highest of this group at 21.4 % and is `LOW`.

### Hazard: Ground Truth underdetermination (found in N22)

A Ground Truth may assert a **direction** — which side of a mismatch is wrong — that the Physical Universe cannot decide.
N22's frozen evidence proves only that the implementation emits `contentType` while the fixtures expect `ContentType`; it does
not establish whether the implementation changed the contract key or regressed it, so the claim that the oracle is stale is
underdetermined. Two-sided contract mismatches drawn from **sibling histories** are the characteristic setting.

**Removal-testing the Required set does not catch this.** Every Required unit can be genuinely necessary while the claim they
jointly support still overreaches. The check is separate: *does the Required set entail the direction the Expected Answer
asserts, or only the symmetric mismatch?*

This is the only rejection in the suite whose **Layer 1 is not recorded as a clean `PASS`**. All eight others — B05, B09, B16,
N10, N12, N13, N16(artifact), N17 — are distinguished from it, and B05, B09, B16, N10, N12 and N13 in particular were rejected
on measurement value alone with Layer 1 `PASS`.

### The single best difficulty predictor, across all five categories

Every category finding above reduces to the same variable: **how much of the causal mechanism the observation and its tooling
have already told the Agent.** Config/environment skews easy because CI logs name the missing thing; dependency splits sharply
on whether the terminal symptom equals the root cause; lint/type is graded by how much the analyzer explains; assertion is
graded by how much of the comparison the framework prints.

This is therefore the **primary screening question at Candidate Discovery**, applied before any package construction:

> *How much of the causal mechanism has the observation/tooling already told the Agent?*

**Log size, repository size, file count, unit count and Required share are diagnostics only, never difficulty proxies.** The
suite now contradicts them three times over: B02 has the lowest Required share in the suite (1.3 %) and is the hardest Case;
N22 has the highest of its group (21.4 %) and is `LOW`.

### Replacement construction round 1 — C2, A1, D2 built

The first three candidates, chosen because their open questions could materially change admission, are constructed as
Schema V2 packages and reviewed. Records: `reviews/c2-blueflood-review.md`, `reviews/a1-retrofit-review.md`,
`reviews/d2-nukkit-review.md`. **None is a Formal Freeze and Formal Suite membership is not frozen.**

| Case | Slot | Layer 1 | Layer 2 | Open question outcome |
|---|---|---|---|---|
| `bugswarm-blueflood-80881330` | `config_or_environment_failure` | `PASS` | **`ADEQUATE`** | Resolved for the Case — `events_mapping.json` is a repository file |
| `bugswarm-retrofit-113047638` | `test_assertion_failure` | `PASS` | **`ADEQUATE — lower end`** | Branch-name leak preserved; assessed weak and partly misleading |
| `bugswarm-nukkit-94403868` | `dependency_or_install_failure` | `PASS` | **`BORDERLINE-ADEQUATE`** | Dependency established from the manifests; **rating lowered from the screening estimate** |

Three findings worth carrying into the remaining six:

- **A screening estimate is not a review verdict.** D2 was screened `ADEQUATE` on an absence-based inference over the
  log's download list. Once the manifest work was done, the honest rating fell to `BORDERLINE-ADEQUATE`, because the
  compiler quotes the offending imports into the log and one 29-line build file completes the diagnosis. The rating was
  lowered rather than the package adjusted to protect it.
- **Compiler and analyzer output quotes source lines back into the log.** Any candidate whose tooling echoes the
  offending source text will tend to fail a strict removal test for that source file. This generalises the B16 finding
  from Java stack traces to javac diagnostics, and it should be applied at screening for the remaining candidates.
- **Direction-settling units are now selected deliberately.** In both C2 and A1 a Required unit exists solely to
  determine which side of a mismatch is wrong. This is the standing countermeasure to the N22 hazard, and it is what
  separates a Required set that establishes a mismatch from one that entails the Expected Answer.

### Targeted Candidate Discovery round: candidate ledger produced

One combined discovery round covering all 9 slots has been run and recorded in
[`REPLACEMENT-CANDIDATES.md`](REPLACEMENT-CANDIDATES.md). **23 candidates screened: 9 `KEEP`, 10 `RESERVE`, 4 `REJECT`.**
No Case Package was constructed and no candidate is admitted.

Two reusable discovery findings:

- **BugSwarm hosts a raw log for only about 45 % of its artifacts.** The dataset lists 6,566 artifacts, but the
  `artifact-logs/<job_id>/raw/` endpoint returns 404 for the majority. Candidate-pool size must be estimated from
  *fetchable logs*, not from artifact count.
- **GitHub Actions `pull_request` jobs record their own executed merge SHA**, as `* [new ref] <sha> -> pull/<n>/merge`
  and `HEAD is now at <short> Merge <head> into <base>`. Every PR candidate screened this round had a recoverable and
  upstream-verifiable executed revision, so a `pull_request` origin is **not** by itself a provenance defect. This
  generalises the N20 finding.

### Existing-draft Human Review phase: CLOSED

All 19 packages are reviewed and dispositioned — **10 `HUMAN REVIEW PASS`, 9 `REJECTED`**. Nothing is frozen. The next phase is
**one targeted Candidate Discovery round covering all 9 replacement slots at once**, not five per-category rounds, with Runtime
Discriminative Value screened **before** package construction rather than after.

### Category finding: `lint_or_type_failure` is graded by how much the tool explains

All four reviewed, with B04 as the calibration reference.

| Case | Layer 2 | Required | What the tool output gives | What the source must add |
|---|---|---:|---|---|
| N07 | **`ADEQUATE`** | 3 | *only* `Cannot infer type argument 1 of "retry_on_error"` — location, no mechanism | **everything**, across two files that must be read together |
| N09 | `BORDERLINE-ADEQUATE` | 2 | file, line, class, method, rule ID and a plain-English rule statement | the *intent* — a reflective cross-version shim — which decides narrow-versus-suppress |
| B04 | *(baseline, `PASS`)* | 2 | `Redundant 'public' modifier` at file:line:col | **why** it is redundant: the private nested enclosing class |
| B05 | `LOW` | 2 | *"apparent infinite recursive loop"* plus method, signature, file and line | almost nothing — one glance confirms the self-call |

**The discriminating variable is how much of the mechanism the analyzer already prints.** A tool that names a rule but not a
reason leaves real work; a tool that describes the defect in plain English leaves only confirmation. B05 sits at the bottom
because FindBugs' message *is* the diagnosis, and N07 at the top because mypy asserts a failure without any explanation.

**Difficulty here depends mainly on how much mechanism the analyzer already explains.** Log size, file count and Required
share are diagnostics only and must not be used as difficulty proxies: N09 has the largest log of the group at 8,149 lines
with 545 `error` matches and the lowest Required share at 1.8 %, yet rates below N07, whose log is a third the size.

### Category finding: `dependency_or_install_failure` splits sharply

All four candidates reviewed. Unlike the config/environment group, this category is **not** uniformly easy — it splits into
two clearly different shapes.

| Case | Layer 2 | Required | Required share | Shape |
|---|---|---:|---:|---|
| B06 | **`ADEQUATE`** | 4 | 3.4 % | Misleading 196-error fan-out, unstated domain decode (`major.minor 52` = Java 8), ~6,700 lines cause-to-terminal, static-init line explains the fan-out |
| N20 | `ADEQUATE — lower end` | 3 | 5.9 % | Misleading terminal symptom, absence inference, 2,325 lines cause-to-terminal; partly leaked by a workflow comment |
| N13 | `LOW` | 5 | 9.1 % | Absence inference against a 2-line manifest |
| B09 | `LOW` | 4 | 23.5 % | Absence inference against a 3-line manifest |

**The discriminating variable is whether the missing dependency produces a *misleading* failure.** B09 and N13 both name the
missing module, its file and its line, so only a trivial absence check remains. B06 and N20 both bury the real cause thousands
of lines behind a symptom that points somewhere else, and B06 additionally requires a domain fact the artifacts never state.

Note also that a low Required share does **not** by itself indicate difficulty: N13's 9.1 % comes from one unrelated 144 KB
file, while B09's 23.5 % — the highest in the suite — sits on a genuinely small workspace. Both are `LOW`.

### Category finding: `config_or_environment_failure` skews easy

All four candidates in this category have now been fully reviewed, and the pattern is consistent enough to record.

| Case | Layer 1 | Layer 2 | Required | Required share | Why |
|---|---|---|---:|---:|---|
| N11 | `PASS` | `BORDERLINE-ADEQUATE` | 3 | 15.8 % | Needs a cross-file `apply from:` link and knowledge that Gradle synthesises the failing task name |
| B08 | `PASS` | `LOW` | 2 | 6.1 % | One grep, log names the victim, one 59-line file explains it |
| B16 | `PASS` | `LOW` | **1** | 1.8 % | The Java stack names application file+line and test file+line; repository adds nothing necessary |
| N10 | `PASS` | **`TRIVIAL`** | **1** | 10.0 % | The log prints the offending SSH URL verbatim beside `Permission denied (publickey)` |

**The structural reason is that configuration and environment failures announce themselves.** A missing display, an SSH
transport mismatch, a rejected SMTP credential and an absent signing identity all produce CI output that names both the
symptom and the condition, and on the JVM a stack trace additionally supplies file and line for the application frame. Three
of the four Cases have a Required set of one or two units, and **two have Required = the log alone**, meaning the repository
contributes no necessary fact at all.

This is a property of the failure class, not of the curation. It should inform how many slots this category deserves and
what a replacement candidate would have to look like — plausibly one where the environment condition is *implicit*, for
example a silent misconfiguration producing a downstream symptom rather than a named exception.

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
| B01 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/170287308/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 **`BORDERLINE-ADEQUATE`**) | `4216e038468184a58e9fa10cb9eaff28450de743` | complete BugSwarm failed log, verified byte-exact | 6 | 3263 / 292121 | 37 | 3 / 1 | The sample matches the supported Upro pattern and follows the normal Position construction path, while the test still calls verifyNothing. | traced public source; all 6 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `BORDERLINE-ADEQUATE`: the actual value is an opaque `Position@285fb753`, so oracle-versus-product must be decided from the decoder's supported-pattern path. | **`PASS`**; Formal Suite membership **not frozen** |
| B02 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/190697114/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 **`ADEQUATE`**) | `880c4c2d33f67c28a834a44da5a2523b858601b3` | complete BugSwarm failed log, 20718 lines, verified byte-exact | 6 | 23129 / 2049094 | 235 | 3 / 1 | The oracle expects the misspelled 'The file is to large' while the product message says 'The file is too large'. | traced public source; all 6 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `ADEQUATE`: the terminal summary names only the test out of 1,680 and suppresses the assertion message; the expected string occurs ZERO times in the log. Strongest disclosure profile in the suite. | **`PASS`**; Formal Suite membership **not frozen** |
| N12 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/89457805/raw/ | **`REJECTED`** — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE` (Layer 1 `PASS`; Layer 2 **`LOW`**) | `4776a4e472e3a14cf475e95f0e146fc3f79b50eb` | complete BugSwarm failed log, verified byte-exact | 7 | 809 / 30445 | 13 | 2 / 1 | The test stringifies the form-error payload, so a Python 2 u-prefix breaks a text comparison. | traced public source; all 7 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `LOW`: the log prints both sides in full and the difference is one visible character. | **`REJECTED`**; not a Formal Suite member |
| N22 | `test_assertion_failure` | https://www.bugswarm.org/artifact-logs/13013454823/raw/ | **`REJECTED`** — `UNDERDETERMINED_GT_AND_LOW_DISCRIMINATIVE_VALUE` (Layer 1 **not a clean `PASS`**: GT direction underdetermined; Layer 2 **`LOW`**) | `019244aa79f9adc182ee138955cc50efe37df9b6` | complete BugSwarm failed log, verified byte-exact | 6 | 913 / 49498 | 14 | 3 / 0 | evidence.py emits contentType while the fixtures expect ContentType. | traced public source; all 6 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `LOW`: both spellings appear in the log so the mismatch is visible there. **GT concern**: the artifacts do not determine whether the oracle is stale or the implementation regressed the key casing. | **`REJECTED`**; not a Formal Suite member |
| B05 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/86922674/raw/ | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`**; Layer 1 remains `PASS` | `25f732d6280b3033dc6f5d7fcf70f5de5e7abf64` | complete BugSwarm failed log, verified byte-exact | 4 | 4920 / 494595 | 52 | 2 / 1 | fetchServiceToUpstreamInfoMap is declared once and calls itself unconditionally at line 238 with no base case, so FindBugs reports an apparent infinite recursive loop. | traced public source; all 4 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `LOW`: the log names the bug class in plain English plus method, file and line; the source only confirms. GT corrected - there is no overload. | **`REJECTED`**; retained as a rejection record |
| N07 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/237548392/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `ADEQUATE`) | `ec1efc4f95a9ee2abca72e9cef4304a19eb5366f` | complete BugSwarm failed log, verified byte-exact | 5 | 4022 / 288898 | 44 | 3 / 0 | retry_on_error is generic in _T over Callable[[], _T], but the call site passes a side-effect-only lambda returning None, so type argument 1 cannot be inferred. | traced public source; all 5 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `ADEQUATE`: the log is a bare one-line assertion with no mechanism; the explanation lives entirely in two source files that must be read together. Strongest of the lint group. | **`PASS`**; Formal Suite membership **not frozen** |
| N09 | `lint_or_type_failure` | https://www.bugswarm.org/artifact-logs/149441998/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `BORDERLINE-ADEQUATE`) | `2431dfb0c85e883a6389b04583a49dc80b61eeb9` | complete BugSwarm failed log, 8149 lines, verified byte-exact | 4 | 10617 / 646957 | 109 | 2 / 0 | A reflective Java 9 module probe is wrapped in catch (Exception ignored) with no analyzer-recognised justification, producing REC_CATCH_EXCEPTION. | traced public source; all 4 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `BORDERLINE-ADEQUATE`: the log states the violation completely, but only the source reveals the catch guards a deliberate cross-version shim, which is what decides narrow-versus-suppress. | **`PASS`**; Formal Suite membership **not frozen** |
| B06 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/221926468/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `ADEQUATE`) | `15f3258905e964ab3b23d9c11fde4a1946ef10b0` | complete BugSwarm failed log, 10452 lines, verified byte-exact | 5 | 11291 / 983498 | 116 | 4 / 2 | async-http-client 2.0.31 is a Java 8 class file and the job runs OpenJDK 7; Context.java line 159 holds it in a class-load-time static, so 196 of 237 unrelated tests error. | traced public source; all 5 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `ADEQUATE`: misleading 196-error fan-out, an unstated domain decode (major.minor 52 = Java 8), ~6,700 lines between cause and terminal message, and a static-init line that no log grep suggests. | **`PASS`**; **NOT a Formal Freeze** |
| B09 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/118661876/raw/ | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`**; Layer 1 remains `PASS` | `a654e03ebf8660b24aa56180a331fb76e79a73f7` | complete BugSwarm failed log, verified byte-exact | 5 | 1318 / 54875 | 17 | 4 / 1 | test_f90nml.py imports numpy at line 9, but the test dependency set installed by .travis.yml declares only coverage and coveralls. | traced public source; all 5 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `LOW`: absence inference is real but the declaration file is 3 lines and the log names module, file and line. Required 4/17 = 23.5 %, the highest ratio in the suite. | **`REJECTED`**; retained as a rejection record |
| N13 | `dependency_or_install_failure` | https://www.bugswarm.org/artifact-logs/113213406/raw/ | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`**; Layer 1 remains `PASS` | `2b7fc2f824696a408d6c857fb98bab593c4def41` | complete BugSwarm failed log, verified byte-exact | 6 | 5100 / 220461 | 55 | 5 / 1 | data.py imports tinydb inside the TinyDB adapter, but requirements.txt declares only pymongo and redis. | traced public source; all 6 members byte-identical | ANSI-only, byte-exact verified | Layer 2 `LOW`: the low Required share reflects one 144 KB unrelated file rather than search difficulty; the manifest is 2 lines. | **`REJECTED`**; retained as a rejection record |
| N20 | `dependency_or_install_failure` | https://github.com/alplabai/tan-cli/actions/runs/30459137058 | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `ADEQUATE — lower end`) | **executed merge revision `5bf4972f4e5931912654c24bed473296ae9a25eb`** (refs/pull/215/merge, recorded in raw.log:125, still addressable, members byte-identical to it); PR head `3043521c…` is the robust fallback | Complete GitHub Actions job log, verified byte-exact against strip_ANSI(upstream) | 4 | 4928 / 407910 | 51 | 3 / 1 | The host-deps prerequisite list omits libudev development headers required by hidapi; bootstrap warns and continues, so the real cause surfaces 2,325 lines later as misleading elftools import errors. | executed merge revision recovered and verified — the first in the suite | ANSI-only, byte-exact verified | Layer 2 `ADEQUATE — lower end`: the log tail actively misleads and the diagnosis rests on absence (`libudev` has zero repository hits), but a workflow comment leaks the warns-and-continues mechanism. | **`PASS`**; **NOT a Formal Freeze** |
| B08 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/166900445/raw/ | **`HUMAN REVIEW PASS`** — admitted as a **deliberate low-difficulty anchor** (pre-freeze; Layer 1 `PASS`, Layer 2 `LOW`) | `18d39ff2412b9aced899915d0187f21eb25f49b6` | complete BugSwarm failed log | 4 | 2945 / 268909 | 33 | 2 / 1 | An environment-dependent integration test runs in the ordinary suite and opens an authenticated SMTP connection to a public AWS SES endpoint using the placeholder credentials committed in the test source, so the service rejects it with 535. | traced public source | **four replacements REVERSED** — only the personal email is redacted; username, password, host and FROM restored | **Layer 2 `LOW`**: one grep locates the failure, the log names the victim, and one 59-line file explains it. No cross-file composition, no competing hypothesis. Intrinsically shallow, not mishandled. | **`PASS`** — low-difficulty anchor; **NOT a Formal Freeze** |
| B16 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/138584081/raw/ | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`**; Layer 1 remains `PASS` | `3a90292cacebbd8dbdb7228a36ca89c0f6a9940f` | complete BugSwarm failed log, 4617 lines | 5 | 5133 / 564171 | 55 | **1** / 4 | MacroHelperTest exercises a modal JOptionPane path on a headless CI worker with no X11 DISPLAY. | traced public source; all 5 members byte-identical | ANSI-only, prefix-verified | **Layer 2 `LOW`**: Required corrected 3 -> 1 because the Java stack names the application file+line and the test file+line, so the repository adds no necessary fact. Required share 1.8 %. | **`REJECTED`**; retained as a rejection record |
| N10 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/170953503/raw/ | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`**; Layer 1 remains `PASS` | `64e149b69750fdc6f150a18e39a3df1ba76ccc24` | complete BugSwarm failed log, 464 lines, raw.log verified byte-exact | 3 | 725 / 27746 | 10 | **1** / 2 | The submodule URL uses the SSH git@github.com transport and the keyless CI checkout has no matching private key. | traced public source; all 3 members byte-identical | ANSI-only, byte-exact verified | **Layer 2 `TRIVIAL`**: the log prints the offending SSH URL verbatim twice next to `Permission denied (publickey)`; the 3-line .gitmodules adds nothing, so Required is the log alone. | **`REJECTED`**; retained as a rejection record |
| N11 | `config_or_environment_failure` | https://www.bugswarm.org/artifact-logs/64757057/raw/ | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS` after reversing an allowlist extraction, Layer 2 `BORDERLINE-ADEQUATE`) | `dc1efd4c626362bb469813229fb5b48b660f1bf3` | complete BugSwarm failed log, verified byte-exact against strip_ANSI(upstream) | 4 | 1516 / 76978 | 19 | 3 / 3 | The build applies the publishing script to every build and that script signs the archives configuration unconditionally rather than only on a publish/upload path. CI supplies no signing identity, so signArchives enters an ordinary assemble task graph and fails with no configured signatory. | traced public source; Travis default-install step recorded | **allowlist extraction REVERSED** — publishing.gradle restored to full 171 lines with only the line-96 credential replaced by typed placeholders | Layer 2 `BORDERLINE-ADEQUATE`: 101 authentic javadoc `error:` distractor lines and a task name absent from source, but the log states both the failing task and its reason. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N01 | `timeout_or_flaky_failure` | https://github.com/UT-SE-Research/iDFlakies/blob/master/scripts/flaky-lists-files/cukes-http (complete committed record); pinned-SHA list scripts/idfProjects1.csv | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS` after Physical Universe repair, Layer 2 `ADEQUATE — lower end`) | `b483e1a8f261b80a66291a42fc455256b0b5059c` — **exact executed revision**, pinned by iDFlakies `idfProjects1.csv`, not inferred | Byte-identical complete iDFlakies record, 37 lines / 1935 bytes; no exception, stack or assertion output | 15 | 1581 / 54816 | 23 | 5 / 4 | Each test instance takes its world from a JVM-wide SingletonObjectFactory and so shares one @Singleton GlobalWorld whose map is built once and never reset. The preceding test writes ASSERTS_STATUS_CODE_MAX_SIZE=5 and never clears it; the victim enables body display without setting or clearing that key, so it inherits the leaked limit and its expected full-body assertion text is replaced by the truncated form. | exact executed revision, benchmark-pinned | `reviewed_no_changes` — byte-identical to upstream | Layer 2 `ADEQUATE`: seven authentic competing polluters restored, and the observation names no state-machinery token, so two Required units are unreachable by observation-keyed retrieval. Weakness: victim and true polluter share one file. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N16 | `timeout_or_flaky_failure` | https://github.com/gptme/gptme/pull/1968 (fix PR); historical run https://github.com/gptme/gptme/actions/runs/23841222952 | **`REJECTED` — `INVALID_FAILURE_ARTIFACT_AND_LOW_DISCRIMINATIVE_VALUE`; not a Formal Suite member** | `f48de363aa956caae8789a9b751d7631fd44fe3c` (real run head, pre-fix) | **Not an authentic failure observation:** one sentence quoted from the body of merged fix PR #1968. Job log HTTP 410; only surviving Check Run annotation is a generic `.github` exit-code failure with no test-level detail, so salvage is impossible. | 4 | 2752 / 92050 | 30 | 3 / 0 | (as drafted) The implementation publishes the subagent in the shared list before starting its background thread, while the test treats list growth as completion and immediately indexes mock_create_thread.call_args. | fix-PR narrative, not failure-side artifact | transcription of fix-PR prose; earlier ANSI-removal claim was false | Layer 1 FAIL/BLOCKED and unrepairable. Layer 2 LOW: `api.py:417-419` comments state the race mechanism and same-file sibling tests already show the join remediation. | `REJECTED`; retained as negative calibration example |
| N18 | `timeout_or_flaky_failure` | https://github.com/osquery/osquery/issues/7718 (failure-reporting issue); curator-only fix https://github.com/osquery/osquery/pull/7888 | **`HUMAN REVIEW PASS`** (pre-freeze; Layer 1 `PASS`, Layer 2 `BORDERLINE-ADEQUATE`) | **failure-era snapshot** `3d26714fc113cef9e79fde0ae1fd52e1d5ba6f2c` (2022-08-08T15:52:27Z, 27 min before the issue); **actual failing revision UNDETERMINABLE** — the issue records no run/build/job/branch/commit anchor | Byte-identical fenced traceback from the issue body, 9 lines / 508 bytes, all nine CRLF retained | 3 | 1933 / 60393 | 22 | 5 / 2 | The test pre-creates the pidfile its own readiness wait polls, so the wait can return before the daemon installs its SIGINT handler. In real startup the handler precedes pidfile creation, so a daemon-created pidfile would be a valid readiness signal; the test's own `touch()` breaks that contract. The default disposition then yields -2 instead of the handled 0. | undeterminable failing revision + deterministic failure-era snapshot | `reviewed_no_changes` — full byte fidelity | Layer 2 `BORDERLINE-ADEQUATE`: complete diagnosis needs 4 artifacts / 5 windows across two languages with no answer-bearing prose present, but victim localization is free and a partial answer is cheap. | **`PASS`** — package-content Human Review complete; **NOT a Formal Freeze** |
| N17 | `timeout_or_flaky_failure` | Actions run https://github.com/nodejs/node/actions/runs/22532700362/job/65274588187 ; related tracking issue https://github.com/nodejs/node/issues/61762 ; curator-only causal PR https://github.com/nodejs/node/pull/62055 | **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`; not a Formal Suite member** | executed: ephemeral `refs/pull/65153/merge`, merge SHA unrecoverable; recoverable byte-equivalent: `3c08a48c24c39ad4dee6d95c5c800246f300525e` | Verbatim GitHub Check Run failure annotation for `test/parallel/test-debugger-exceptions.js`; full Actions job log expired (HTTP 410) and was not reconstructed. | 11 | 3665 / 109731 | 43 | 3 / 6 | The restart step synchronizes only on the break message, inside one fixed window opened before the restart begins, so it depends on debugger output timing and fails intermittently on macOS. Why the break line was absent is deliberately left unresolved. | verified upstream primary sources | trailing newline only | Layer 1 PASS. Layer 2 FAIL: the contemporaneous repository already contained a commented fix for this exact flake pattern in a sibling of the victim, so one observation-derived search yields root cause and recommended action. | `REJECTED`; retained as negative calibration example |

| N06 | `timeout_or_flaky_failure` | iDFlakies WildFly naming record | `REPLACED` by N17 | `b19048b72669fc0e96665b1b125dc1fda21f5993` | Intended PASS plus revealed ERROR with empty revealed order; no exception/stack/output | — | — | — | — | Agent-visible failure evidence is insufficient without prohibited replay or invention. | traced public source | n/a | Source blocker is decisive. | replacement previously Human-approved |

## Failure-type outcome

- `test_assertion_failure`: **B02 and B01 `HUMAN REVIEW PASS`** (2 of 4 slots filled, pre-freeze); N12 `REJECTED` for low discriminative value with Layer 1 `PASS`, and N22 `REJECTED` for Ground Truth underdetermination plus low value. **Two slots unfilled.**
- `lint_or_type_failure`: **N07 and N09 `HUMAN REVIEW PASS`** alongside the unchanged **B04 Human-reviewed Schema V2 calibration reference, provisionally retained as one Formal candidate of this type for discovery planning** (3 of 4 slots accounted for, none frozen); B05 `REJECTED`. **One slot unfilled.**
- `dependency_or_install_failure`: **B06 and N20 `HUMAN REVIEW PASS`** (2 of 4 slots filled, pre-freeze); B09 and N13 `REJECTED`. **Two slots unfilled.**
- `config_or_environment_failure`: **N11 and B08 `HUMAN REVIEW PASS`** (2 of 4 slots filled, pre-freeze; B08 carries an explicit low-difficulty-anchor role); B16 and N10 `REJECTED`. **Two slots unfilled.**
- `timeout_or_flaky_failure`: **N01 and N18 `HUMAN REVIEW PASS`** (2 of 4 slots filled, both pre-freeze); N06 `REPLACED`, its replacement N17 `REJECTED` for low Runtime Discriminative Value, and N16 `REJECTED` for an invalid failure artifact plus low value. **Two slots are unfilled**, and a third would open if N01 fails.

## Validation contract

Every new draft passed JSON parse, Schema V2 loader, declared/calculated fingerprint equality, exact repository membership/hashes/sizes, path safety, fixed-100 full coverage with no gaps/overlaps, canonical resolved hashes, Required/Optional referential integrity, Expected Answer schema, PublicCaseView leakage checks, targeted secret scans, and known fix/passing SHA scans. The shared fixed-100 audit is an explicit bulk-construction check; the generic loader does not itself enforce Profile compliance.

Passing this contract establishes only that a package is structurally sound. The N17 BLOCKER passed every item above while combining three unrelated histories, and the finally repaired N17 passed every item and was still rejected for low measurement value. Structural validation must never be read as scientific validity, and neither implies Formal Suite admission. N17's fix/passing SHA scan list was extended to cover the restart-message fix `3163d8aa…`, the sibling-migration fix `4f04a36b…`, and both PR #62055 commits `9de9b9f8…` and `6dca8733…`.

## Human Review priority — scientific risk first

1. ~~N17~~, ~~N16~~ — **reviews closed, both `REJECTED`.** No further review needed. Replacement candidates must go through Measurement-Value Screening before construction.
2. ~~N18~~ — **review closed, `HUMAN REVIEW PASS`.** Layer 1 `PASS` after refreezing onto a failure-era snapshot; Layer 2 `BORDERLINE-ADEQUATE`, which must not be rewritten upward. Full record: `reviews/n18-review.md`.
3. ~~N01~~ — **review closed, `HUMAN REVIEW PASS`.** The two omitted observation-named test classes were restored under scope clause (a), turning polluter identification into genuine seven-candidate discrimination; Ground Truth was tightened to the Required-supported form and its observed-versus-derived wording verified. Layer 2 `ADEQUATE — lower end`, which must not be rewritten upward. Full record: `reviews/n01-review.md`.
4. ~~N11~~ — **review closed, `HUMAN REVIEW PASS`.** Its `gradle/publishing.gradle` allowlist extraction kept only 32 of 171 lines and has been reversed; the earlier "Human-approved" allowlist is explicitly superseded. Layer 2 `BORDERLINE-ADEQUATE`. See `reviews/n11-review.md`.
5. ~~N20~~ — **review closed, `HUMAN REVIEW PASS`.** The pinned-SDK concern is not a Layer 1 defect; the executed `refs/pull/215/merge` revision was recovered from raw.log and verified. Layer 2 `ADEQUATE — lower end`. See `reviews/n20-review.md`.
6. ~~B08~~, ~~B16~~, ~~N10~~ — **reviews closed.** B08 `PASS` as a deliberate low-difficulty anchor; B16 and N10 `REJECTED` for low/trivial discriminative value, both with Layer 1 `PASS`. See the per-Case packets.
7. ~~B09~~, ~~N13~~, ~~B06~~ — **reviews closed.** B06 `PASS` (`ADEQUATE`); B09 and N13 `REJECTED` for low discriminative value with Layer 1 `PASS`. Required sets were corrected in all three where the Ground Truth asserted a fact the Required set did not carry.
8. ~~B02~~, ~~N22~~ — **reviews closed.** B02 `PASS` (`ADEQUATE`); N22 `REJECTED` for Ground Truth underdetermination plus low value.
9. ~~B05~~, ~~N07~~, ~~N09~~ — **reviews closed.** N07 `PASS` (`ADEQUATE`) and N09 `PASS` (`BORDERLINE-ADEQUATE`); B05 `REJECTED` for low discriminative value with Layer 1 `PASS` and an accepted Ground Truth correction.
11. ~~B01~~, ~~B02~~, ~~N12~~, ~~N22~~ — **all reviewed and dispositioned. The `test_assertion_failure` category is resolved and the whole 19-package bulk review is CLOSED.** B02 and B01 `PASS`; N12 and N22 `REJECTED`. Next phase: one targeted Candidate Discovery round for all 9 replacement slots.

## Calibration inputs

- B01: sufficient real full-log + six-file Physical Universe; ready for calibration observation after this draft is accepted.
- B06: sufficient real full-log + five-file Physical Universe; ready for calibration observation after this draft is accepted.
- N01 (reviewed): complete committed JSON record + fifteen-file Physical Universe. Its non-log benchmark record remains the key Schema/attribution calibration stressor, and it adds two `N=100` observations — twelve of fifteen members are shorter than 100 lines and collapse to whole-file units, making Evidence Hit file-granular, while the one member that does split puts the victim and its polluter in different units.
- N17 (rejected, but its coordinate observations remain usable): contributes two concrete `N=100` boundary observations for the `N ∈ {50, 100, 200}` comparison — `inspect_repl.js` splits one `paused`-handler causal fact across units `0801-0900` and `0901-1000`, and the Required pair `debugger.js` `0001-0100` / `0101-0190` splits one helper's semantics across two units. Recorded as observations only; the Profile remains unfrozen and calibration has not started.

No Suite Manifest, Suite fingerprint, Runtime implementation, replay, historical environment reconstruction, or synthetic failure log was created. No methodology document or ADR was changed by the N17 review.
