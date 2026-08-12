# N11 — bugswarm-testng-64757057 — Human Review PASS record

> **PACKAGE-CONTENT HUMAN REVIEW: `PASS`.** N11 is retained in the Formal Suite candidate set.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and the coordinates and fingerprint remain `provisional-pre-freeze`.

**Layer 1 — Scientific Validity:** `PASS` after reversing a curator allowlist extraction (§2).
**Layer 2 — Runtime Discriminative Value:** **`BORDERLINE-ADEQUATE`** — deliberate; must not be rewritten upward (§9).
**Failure type:** `config_or_environment_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `6dd132fd5604fce4ebdaf475c777bfc4ca57a940ae2befd8e26e502276841b69` (`provisional-pre-freeze`; supersedes `a0543dff…`).

The headline finding is that the draft's `gradle/publishing.gradle` retained **32 of 171 lines** — 81 % of the file was deleted to remove one line containing a credential. That is curator pruning of the investigation workspace, and it has been reversed.

## 1. Authenticity and provenance

| Fact | Value |
|---|---|
| Source | `https://www.bugswarm.org/artifact-logs/64757057/raw/` |
| Exact revision | `dc1efd4c626362bb469813229fb5b48b660f1bf3` (testng-team/testng) |
| `raw.log` | 1,204 lines / 69,731 bytes |
| Sanitization verified | `strip_ANSI(upstream)` = 69,731 B == frozen **byte-for-byte** (upstream 70,469 B, 199 ESC) |

The ANSI-removal claim is now **fully verified** for this package rather than inferred from pipeline similarity.

**One provenance detail the draft did not record, and which looks like a mismatch until resolved.** `.travis.yml:9` declares `script: "./compile-with-gradle.sh"`, and that script contains `./gradlew clean createVersion compileJava`. But the log shows `$ ./gradlew assemble` and `The command "eval ./gradlew assemble" failed`. These are consistent: the log places that command inside `travis_fold:start:install`, i.e. it is Travis's **default install step** for a Gradle project. `.travis.yml` declares no `install:`, so Travis supplied `./gradlew assemble`, it failed, and the declared `script:` phase never ran. Now recorded in `provenance`.

## 2. The allowlist extraction — reversed

The draft declared:

> *"Applied the Human-approved strict allowlist: retained only the contiguous signing/task-graph section from exact revision lines 60-91; excluded unrelated publishing credentials and service configuration entirely."*

Upstream is **171 lines**. The draft kept lines 60-91 and discarded 137. What was removed:

| Upstream lines | Content | Actually secret? | Investigation-relevant? |
|---|---|---|---|
| 1-39 | imports, build timestamps, `maven-publish` + bintray plugins, jar manifest, first `publishing {}` block | no | yes |
| 40-41 | `properties.load(project.rootProject.file('local.properties'))` | no | **yes — the only thing that explains `touch local.properties`** |
| 43-58 | `bintray {}` reading `bintray.user` / `bintray.apikey` | read from file, not hardcoded | yes — competing hypothesis |
| 60-91 | **retained** — javadoc/jar tasks, `artifacts {}`, `signing {}` | — | — |
| **96** | `authentication(userName: '3rszImfP', password: 'uAOidhWfey…')` | **yes — a real hardcoded credential** | yes |
| 92-103 | `uploadArchives {}` — the publish path `configurations.archives` feeds | no (apart from line 96) | yes |
| 105-154 | artifactory buildscript and config, credentials from env/properties | no | yes — competing hypothesis |
| 156-171 | second `apply plugin: 'maven-publish'`, group, `publishing {}` | no | yes |

**Exactly one line contained a secret. 137 lines were deleted to remove it.**

### Why this is not acceptable

- **It pruned competing hypotheses.** A credential-shaped CI failure has several plausible credential-related explanations in this file — the `local.properties` load, bintray keys, artifactory keys, the Sonatype upload block. The extraction left `signing {}` as very nearly the only thing in the file, so the Agent could not reach a wrong answer because the wrong answers had been deleted.
- **It broke an explainable observation.** `raw.log:371` shows `$ touch local.properties`. In the pruned workspace nothing reads `local.properties`, so the question "why does this build need that file?" had no answer inside the Physical Universe. Restoring line 41 answers it.
- **The artifact did not disclose that it was an excerpt.** The frozen file began at upstream line 60 and was numbered from 1, with canonical unit `lines-0001-0032`. Nothing visible to the Agent indicated truncation, so it read as a complete file. That is misleading, not merely reduced.
- **It was not semantics-preserving as a build script.** The retained fragment keeps `artifacts { archives … }` and `signing { sign configurations.archives }` but drops `uploadArchives`, `maven-publish`, bintray and artifactory. As a Gradle script it no longer represents what Gradle evaluated.
- **A better technique was already the suite precedent.** `bugswarm-traccar-166900445` handles real credentials by replacing literals with typed placeholders (`[SANITIZED_SMTP_USERNAME]` and similar) while preserving file structure. That is what ADR 0126 means by semantics-preserving sanitization.

### Remediation applied

`gradle/publishing.gradle` restored to its full exact-revision extent, with **only** the two credential literals on line 96 replaced:

```
96|  authentication(userName: '[SANITIZED_SONATYPE_USERNAME]', password: '[SANITIZED_SONATYPE_PASSWORD]')
```

All 171 lines retained at their original line numbers; no other byte changed; the secret is gone (scan for `3rszImfP` / `uAOidhWfey` across all artifacts: no hits). File extent, structure, task graph and line coordinates are preserved.

## 3. Physical Universe — final, 4 members

Repository **312 lines / 7,247 bytes**; `raw.log` 1,204 lines / 69,731 bytes. Total physical **1,516 lines / 76,978 bytes**.

| Member | Lines | Clause | Why an investigator reaches it |
|---|---:|---|---|
| `gradle/publishing.gradle` | 171 | (c) | Defines `signing { sign configurations.archives }`, the publish paths, and `javadoc { failOnError false }` |
| `build.gradle` | 130 | (b) | `:35 apply from: 'gradle/publishing.gradle'` — what makes signing apply to every build |
| `.travis.yml` | 10 | (d) | The CI environment: no signing setup, `before_install: touch local.properties`, declared `script:` |
| `compile-with-gradle.sh` | 1 | (b) | **Added.** Named by `.travis.yml:9`; its contents (`./gradlew clean createVersion compileJava`) show the declared script is *not* what ran, closing the "what actually executed?" question |

## 4. Independent causal chain

1. `raw.log:1121`, `:1152`, `:1183` — `:signArchives FAILED` on all three Travis retries, each followed by `Execution failed for task ':signArchives'. > Cannot perform signing task ':signArchives' because it has no configured signatory`.
2. The failing command is `./gradlew assemble` inside `travis_fold:start:install` — Travis's default install step, not the declared `script:`.
3. `build.gradle:35` applies `gradle/publishing.gradle` to the build unconditionally.
4. `publishing.gradle:88-90` — `signing { sign configurations.archives }` with no guard, combined with `artifacts { archives jar; archives javadocJar; archives sourcesJar }` at `:82-86`, puts `signArchives` into the task graph of an ordinary `assemble`.
5. `.travis.yml` provides no signing identity — no keys, no `signing.*` properties, only `touch local.properties`.
6. Gradle's signing plugin therefore reaches `signArchives` with no signatory and fails deterministically — three retries, three identical failures.

**Task-name gap worth noting:** neither `signArchives` nor `signatory` appears anywhere in the repository. Both are synthesised by Gradle's signing plugin from `sign configurations.archives`. The Agent cannot lexically match the failing task name to source; it must know the plugin's naming convention.

## 5. Failure Type

`config_or_environment_failure`, `acceptable_failure_types: []`. The CI environment lacks the signing identity and configuration that an unconditionally applied signing task requires — the taxonomy's "required configuration … secrets … or runtime settings were missing". Deliberately *not* narrowed to "a missing environment secret": the evidence supports only `no configured signatory`, and the defect is as much the unconditional application of signing as it is the absent identity. Not `timeout_or_flaky_failure`: it failed identically on all three retries. Not `dependency_or_install_failure`: dependencies resolved and the build reached `:jar`, `:javadoc`, `:sourcesJar` successfully.

## 6. Expected Answer

Retained in substance, sharpened to name the two facts the Required set now carries — that the publishing script is applied to *every* build, and that signing is unconditional rather than bound to a publish path.

- **summary** — "The Gradle build reaches the signArchives task and fails because no signatory is configured, even though this CI job only assembles artifacts and never publishes them."
- **root_cause** — "The build applies the publishing script to every build, and that script signs the archives configuration unconditionally rather than only on a publish or upload task path. The CI environment supplies no signing identity, so once signArchives enters the task graph of an ordinary assemble it fails with no configured signatory."
- **recommended_action** — "Make archive signing conditional on the upload or publish task path, or on the signing credentials being present, so that ordinary CI builds that only assemble artifacts do not depend on a signing identity."

Every claim is supported by the Required set; nothing asserts more than the artifacts show.

## 7. Required and Optional Evidence

**Required (3):**

| ID | Necessary fact |
|---|---|
| `log:raw-log:lines-1101-1200` | All three `:signArchives FAILED` occurrences and the `no configured signatory` diagnosis |
| `repo:gradle-publishing-gradle:lines-0001-0100` | `signing { sign configurations.archives }` (`:88-90`) with no guard; `artifacts { archives … }` (`:82-86`); also `javadoc { failOnError false }` (`:69`) |
| `repo:build-gradle:lines-0001-0100` | `:35 apply from: 'gradle/publishing.gradle'` — establishes "for ordinary builds" |

**Optional (3):** `repo:travis-yml:lines-0001-0010` (CI env supplies no signing identity), `repo:gradle-publishing-gradle:lines-0101-0171` (the `uploadArchives` publish path signing is actually meant for), `repo:compile-with-gradle-sh:lines-0001-0001` (the declared script that never ran).

### Removal tests

- **`build-gradle:0001-0100` — promoted to Required.** It was Optional in the draft. Without it there is no evidence the publishing script applies to ordinary builds; the Agent could reasonably conclude signing only applies under a publish profile, and the root cause's "for every build" clause is unsupported.
- **`gradle-publishing-gradle:0001-0100` — Required.** Contains the unguarded `signing` block. Removal leaves the log's message unexplained by any source.
- **`log:raw-log:lines-1101-1200` — Required.** The only place the failing task and reason appear.
- **`gradle-publishing-gradle:0101-0171` — Optional, deliberately.** It shows the `uploadArchives` path that signing is intended for, which supports the recommended action. But unit `0001-0100` already contains a `publishing {}` block and the bintray configuration, so a publish path is demonstrably present without it. Marking the second half Required would have inflated the set purely because restoring the file made more material available.

## 8. Contemporaneous shortcut analysis

**Answer-prose scan: clean.** No `flaky`, `workaround`, `TODO`, `FIXME`, or comment suggesting the signing block should be conditional.

| Query from the observation | Files hit |
|---|---|
| `signArchives`, `signatory` | **none** — Gradle-synthesised names, absent from source |
| `signing`, `archives`, `uploadArchives` | 1 — `gradle/publishing.gradle` |
| `bintray`, `artifactory`, `publish`, `password` | 2 — `build.gradle`, `gradle/publishing.gradle` |
| `local.properties` | 2 — `.travis.yml`, `gradle/publishing.gradle` |

**Log-side discrimination is the real work.** The log carries **101 lines containing `error:`** — javadoc doclint errors from the `:javadoc` task — none of which is the failure. The genuine failure sits at lines 1121/1152/1183, deep in the tail. A naive reader latches onto the first hundred `error:` lines. Notably, the Required repository unit *also* explains why they are benign: `javadoc { failOnError false }` at `publishing.gradle:69`. That is a real "why didn't this fail the build?" reasoning step, answered by evidence the Agent must already have found.

**What the restoration changed.** In the pruned draft the repository step was nearly free: the 32-line file contained `signing {}` and essentially nothing else, so once the Agent opened it there was only one thing to see and no credential-related alternative to eliminate. After restoration the same file contains four credential- or publishing-related mechanisms, and the Agent must select the one the log actually names. The reversal is therefore both a validity fix and the main source of this Case's remaining measurement value.

## 9. Runtime Discriminative Value — `BORDERLINE-ADEQUATE`

| Metric | Draft | **Revised** |
|---|---:|---:|
| Physical repo files | 3 | **4** |
| Repository lines / bytes | 183 / 3,649 | **312 / 7,247** |
| `gradle/publishing.gradle` | 32 lines (81 % deleted) | **171 lines (full extent)** |
| Total physical | 1,387 l / 73,380 B | **1,516 l / 76,978 B** |
| Canonical units | 17 | **19** (13 log + 6 repo) |
| Required / Optional | 2 / 1 | **3 / 3** |
| Required share | 11.8 % | **15.8 %** |

**Strengths.** A 1,204-line log with 101 authentic `error:` distractor lines and only one of thirteen log units carrying Required evidence. The failing task name is absent from the repository, so the log-to-source link requires knowing Gradle's signing-plugin naming. Four restored credential/publishing mechanisms compete as explanations. The Travis default-install subtlety must be resolved to reconcile `.travis.yml` with the log. A cross-file link (`build.gradle:35`) is needed for the "every build" claim. The loudest distractor is explained by the Required evidence itself.

**Weaknesses.** The log states both the failing task and the reason — `Cannot perform signing task ':signArchives' because it has no configured signatory` — so the immediate cause is observed rather than derived, and the gap to the root cause is short: grep `signing`, find one file, find one unguarded three-line block. The repository is small at 312 lines across 4 files. Two of the three Required units are close to forced by the log text.

**Expected separation — pre-runtime hypothesis, not a validated result.** Fixed Pipeline should retrieve the tail log unit from the observation's own tokens and may produce a partial answer that stops at "no signatory configured"; it is less likely to reach `build.gradle:35`. Retrieval should reach `publishing.gradle` on `signing`. ReAct has headroom in the log-side discrimination — separating 101 benign `error:` lines from the real failure and explaining them via `failOnError false` — and in establishing the "every build" link.

**Rating `BORDERLINE-ADEQUATE`.** Below N01, roughly level with N18. Placed there because the observation names both the failing task and its reason, which neither N01 nor N18 does to the same degree. Before the reversal this Case would have rated `LOW`: the pruned file made the repository step nearly free.

## 10. Canonicalization observations

Fixed-100 rebuilt mechanically after membership changed. Coverage verified: **1,516 / 1,516 lines, no gaps, no overlaps**, all hashes resolving from frozen bytes. No boundary moved to suit Required Evidence.

Calibration notes: the log dominates the coordinate space, 13 of 19 units, so at `N=100` an Evidence Hit on the failure costs one unit out of thirteen — a favourable ratio for measuring log localisation. The restored `publishing.gradle` splits at line 100, placing `signing {}` (`:88-90`) and `uploadArchives {}` (`:92-103`) in **adjacent different units**; that boundary falls between the cause and the publish path it should have been bound to, which is a third instance of a causal comparison straddling a neutral `N=100` boundary, after N17, N18 and N01.

## 11. Severity findings

1. **Fixed — curator-pruned investigation workspace (Layer 1, high).** 137 of 171 lines of `gradle/publishing.gradle` deleted to remove one credential line, with no disclosure that the artifact was an excerpt, removing several competing hypotheses. Reversed via placeholder replacement.
2. **Fixed — missing CI-named member.** `compile-with-gradle.sh`, named by `.travis.yml:9`, was absent, leaving "what actually ran?" unanswerable from the workspace.
3. **Fixed — Required Evidence under-specified.** `build.gradle` was Optional despite carrying the only evidence for the "every build" clause of the root cause.
4. **Fixed — undocumented provenance subtlety.** The mismatch between `.travis.yml`'s `script:` and the log's `./gradlew assemble` is Travis's default install step; now recorded.
5. **Verified — sanitization claim.** `strip_ANSI(upstream) == frozen` byte-for-byte, so this package moves from "same-pipeline, unverified" to fully verified.

## 12. Validation

- Schema V2 loader PASS; declared fingerprint equals calculated (`6dd132fd…`).
- Manifest membership, sizes, SHA-256, path safety, no undeclared files: PASS (4 members).
- Canonical coverage **1,516 / 1,516 lines**, gap-free, overlap-free, exact resolved hashes: PASS.
- Required/Optional referential integrity and disjointness, Expected Answer schema: PASS.
- `raw.log` verified byte-exact against `strip_ANSI(upstream BugSwarm log)`: PASS.
- Hardcoded-credential scan across all artifacts: **no hits**.
- `PublicCaseView` exposes only case identity, schema, fingerprint, raw-log path, repository root and forbidden actions: PASS.
- All 20 case directories load with consistent fingerprints; **B04, N17, N16, N18, N01 fingerprints unchanged**.
- `pytest tests/test_issue_22_case_schema_v2.py tests/test_issue_6_evaluation_suite.py tests/test_issue_14_structured_report_scoring.py` → `126 passed`.

## 13. Ground Truth wording check

Checked before approval, against the rule that the Expected Answer must not over-narrow beyond what the failure evidence supports. The evidence directly supports `no configured signatory` and nothing stronger.

| Field | Result |
|---|---|
| `summary` | Clean — "fails because no signatory is configured", matching the log verbatim in substance. |
| `root_cause` | Clean — "The CI environment supplies no signing identity" combined with "signs the archives configuration unconditionally rather than only on a publish or upload task path". This is the intended calibre: the CI lacks the signing identity and configuration that an unconditionally applied signing task requires. |
| `recommended_action` | Clean — offers both remedies (bind signing to the publish path, or gate on the signing configuration being present). |

The terms `secret`, `environment secret`, `env var` and `environment variable` are **absent from all three fields**. No change was made; the wording was already at the correct calibre.

## 14. Final Human Review status

| Layer | Outcome |
|---|---|
| Scientific / package-content Human Review | **`PASS`** |
| Runtime Discriminative Value | **`BORDERLINE-ADEQUATE`** |
| Formal Suite Freeze | **`NOT YET`** |

Freeze is withheld only because `Canonicalization Profile v1` is unfrozen and no Suite Manifest exists.

Two Human decisions recorded:

1. **The earlier "Human-approved" allowlist extraction is explicitly superseded.** It deleted 81 % of a real file, pruned competing hypotheses, and presented a truncated artifact as complete, so it satisfies neither semantics-preservation nor the natural-workspace principle.
2. **The operational rule `replace, do not excise` is kept at ledger level.** Secrets are replaced in place with typed placeholders, preserving file structure, extent and line numbers. Deliberately **not** promoted to the methodology or an ADR yet.

## 14. Scope boundary

Only the N11 package, this record, and the N11 material in `BULK-DRAFT-REVIEW.md` were changed. B04, N01, N16, N17, N18, every other Case, methodology documents, ADRs, Schema V2, the Canonicalization Profile documents, the suite manifest and runtime code were not touched. No replay, no environment reconstruction, no synthetic artifact, no Suite Manifest, no Suite fingerprint, and no replacement-candidate discovery.
