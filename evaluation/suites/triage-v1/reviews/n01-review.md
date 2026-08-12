# N01 — idflakies-cukes-http-b483e1a8 — Human Review PASS record

> **PACKAGE-CONTENT HUMAN REVIEW: `PASS`.** N01 is retained in the Formal Suite candidate set.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and the coordinates and fingerprint remain `provisional-pre-freeze`.

**Layer 1 — Scientific Validity:** `PASS` after the Physical Universe repair applied in this review.
**Layer 2 — Runtime Discriminative Value:** **`ADEQUATE — lower end`** — this rating is deliberate and must not be rewritten as `STRONG`, `HARD` or `HIGH-DIFFICULTY` (§9).
**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `6465db63f1d2dc0ab64eb469dfa5c95d5749304228b7e666e0fc6e0e15b6ea43` (`provisional-pre-freeze`; lineage `fdbba293…` → `1c5e2460…` → this record).

N01 is the **strongest** of the four `timeout_or_flaky_failure` candidates reviewed. Its decisive property is that the failure observation contains **no token at all** pointing to the shared-state machinery: reaching `SingletonObjectFactory` and `GlobalWorld` requires reading the victim's test file and following a reference, which observation-keyed retrieval cannot shortcut.

## 1. Authenticity and provenance — the strongest of the four

`raw.log` is **byte-identical (1,935 bytes)** to the complete committed file `UT-SE-Research/iDFlakies/scripts/flaky-lists-files/cukes-http`. That file contains exactly this one detection record and nothing else, so the artifact is **complete, not excerpted**.

**The exact executed revision is known, not inferred.** `scripts/idfProjects1.csv` carries the header `#Project,SHA,module,expectedFlakyTests` and the row:

```
https://github.com/ctco/cukes,b483e1a8f261b80a66291a42fc455256b0b5059c,cukes-http,1
```

so iDFlakies checked out and executed exactly this pinned SHA. The apparent four-and-a-half-year gap between the upstream commit date (2018-11-06) and the record's `testRunId` timestamps (`1688181858373` / `1688181866086` = 2023-07-01T03:24:18Z / 03:24:26Z) is expected and consistent: the benchmark runs pinned revisions, not repository HEAD.

**N01 therefore needs no failure-era-snapshot category.** Unlike N17 (unrecoverable ephemeral merge SHA) and N18 (undeterminable failing revision), this is a genuine exact-executed-revision Case, and `repository-manifest.json.exact_revision` carries its ordinary meaning with no caveat.

### Record semantics

`name` is the victim; `intended` is a run order whose `result` is `PASS`; `revealed` is a run order whose `result` is `FAILURE`, listing the tests executed before the victim; `type: OD` means order-dependent. The revealed order contains six `EndsWithRegexpTest` methods followed by one `HttpAssertionFacadeImplTest` method — **seven candidate polluters**.

The record carries **no exception, no stack trace and no assertion output**. Per the review directive this is not automatically disqualifying: order-dependent triage legitimately rests on run orders plus source-state reasoning. It does mean the *failure mode* is derived rather than observed — see §6 and the field-by-field check in §13.

### Curator-only material correctly excluded

The same iDFlakies repository publishes its own answer key: `scripts/idfProjectsMinimizer.csv` names the minimized polluter for this exact victim, and `scripts/idfProjectsFixer.csv` records the iFixFlakies outcome. Neither is in the Physical Universe, and neither may ever enter it. Recorded as a standing rule for any future iDFlakies-sourced Case.

## 2. The Layer 1 defect that was repaired

The draft Physical Universe contained **one** of the three test classes the observation names:

| Observation-named class | Was in workspace | Now |
|---|---|---|
| `lv.ctco.cukes.http.facade.HttpAssertionFacadeImplTest` | yes | yes |
| `lv.ctco.cukes.http.matchers.EndsWithRegexpTest` | **no** | **restored** |
| `lv.ctco.cukes.http.logging.HttpLoggingPluginTest` | **no** | **restored** |

That was a curator-derived search-space reduction of the most damaging kind: the only test class retained was the one containing **both** the victim and the true polluter, so the curator had already eliminated all seven competing candidates on the Agent's behalf. Restoring them under scope clause (a) is mandatory, and it is what turns polluter identification into genuine discrimination work.

## 3. Physical Universe — final, 15 members

**1,544 repository lines / 52,881 bytes**, plus `raw.log` 37 lines / 1,935 bytes. Total physical: **1,581 lines / 54,816 bytes**.

| Member | Lines | Clause | Why an investigator reaches it |
|---|---:|---|---|
| `…/facade/HttpAssertionFacadeImplTest.java` | 198 | (a) | Victim and one candidate polluter; obtains `world` from the singleton factory |
| `…/matchers/EndsWithRegexpTest.java` | 41 | (a) | Six candidate polluters in the revealed order |
| `…/logging/HttpLoggingPluginTest.java` | 76 | (a) | Named in the intended order; mentions `GlobalWorldFacade` and `CukesOptions` |
| `…/core/internal/di/SingletonObjectFactory.java` | 96 | (c) | JVM-wide static instance holder — why state is shared at all |
| `…/core/internal/context/GlobalWorld.java` | 80 | (c) | `@Singleton`, `ConcurrentHashMap` built once, `put` mutates, no per-test reset |
| `…/core/internal/context/GlobalWorldFacade.java` | 62 | (b) | The facade the tests actually call; exposes `reconstruct()` |
| `…/core/CukesOptions.java` | 38 | (b) | Defines the option keys statically imported by the tests |
| `…/core/internal/matchers/EndsWithRegexp.java` | 28 | (b) | Subject of an observation-named test; needed to close its elimination |
| `…/http/logging/HttpLoggingPlugin.java` | 145 | (b) | Subject of an observation-named test; needed to confirm it never writes the world |
| `…/http/facade/HttpAssertionFacadeImpl.java` | 230 | (c) | Reads `MAX_SIZE` / `DISPLAY_BODY` from the world on the assertion path |
| `…/http/matchers/StatusCodeMatcher.java` | 47 | (c) | Selects the full-body versus truncated assertion text |
| `…/http/CustomMatchers.java` | 48 | (b) | Imported by the victim test |
| `pom.xml` | 326 | (d) | Declares surefire `forkCount=1`/`reuseForks=false` — inside `pluginManagement` |
| `cukes-http/pom.xml` | 42 | (d) | Does **not** declare surefire, so the parent config is inert |
| `cukes-core/pom.xml` | 87 | (d) | Same, for the core module |

Nothing was added for volume and nothing was removed for difficulty. The three poms earn their place: JVM sharing is exactly what decides whether cross-class pollution is even possible (§7).

## 4. Independent causal chain

Derived from Physical Artifacts before consulting any fix or the benchmark's answer key.

1. **Observation.** Victim `shouldReturnBodyWhenEnabledAndNoMax` passes in the intended order and fails in the revealed order; `type: OD`. Seven tests precede it in the failing order.
2. **Shared instance.** `HttpAssertionFacadeImplTest:30` initialises `objectFactory = SingletonObjectFactory.instance()` as a **field**, so every JUnit test instance re-runs it; `SingletonObjectFactory:89-95` returns a JVM-wide `InstanceHolder.INSTANCE`. All test instances therefore share one factory.
3. **Shared state.** `HttpAssertionFacadeImplTest:34` resolves `GlobalWorldFacade` from that factory; `GlobalWorld:20` is `@Singleton`, its `context` is a `ConcurrentHashMap` created once in `reconstruct()` (`@Inject`, `:24-43`), and `put` (`:45-47`) mutates it. **No test resets it** — the workspace's only `@Before` is `HttpLoggingPluginTest`'s mock setup.
4. **Write.** `HttpAssertionFacadeImplTest:136` — the preceding test `shouldNotReturnBodyWhenEnabledButLongerThanMaxSize` does `world.put(ASSERTS_STATUS_CODE_MAX_SIZE, "5")` and never clears it.
5. **Omission.** The victim (`:77-98`) sets only `world.put(ASSERTS_STATUS_CODE_DISPLAY_BODY, "true")`; it never sets or clears `MAX_SIZE`, and expects the full-body assertion text. Every other test in the class sets both keys.
6. **Effect.** The class's own sibling tests establish the mapping: with `MAX_SIZE=100` (`:65`) the expectation is `with body:\n"""…"""`; with `MAX_SIZE=5` (`:136`) it is `with body <exceeding max size to show>`. So a leaked `MAX_SIZE=5` gives the victim the truncated text where it expects the full body.
7. **Mechanism (corroboration).** `HttpAssertionFacadeImpl:83-92` reads both keys from the world and passes `maxSize` to `StatusCodeMatcher`; `StatusCodeMatcher:33-36` branches `maxSize != null && size > maxSize` to the truncated text.
8. **Elimination.** `EndsWithRegexpTest` is a stateless matcher test and `EndsWithRegexp` a pure static factory — neither touches the world. `HttpLoggingPluginTest` injects a Mockito `@Mock GlobalWorldFacade`, and `HttpLoggingPlugin` receives its world by constructor injection and only **reads** it (`:45`, `:78`, `:111`), never writes. All seven cross-class candidates are eliminable, but only by reading source.

**Curator-only confirmation, consulted afterwards:** iDFlakies' own `idfProjectsMinimizer.csv` names `shouldNotReturnBodyWhenEnabledButLongerThanMaxSize` as the minimized polluter. The independent reconstruction matches.

## 5. Failure Type

`timeout_or_flaky_failure`, `acceptable_failure_types: []`. The V1 taxonomy lists "order-dependent test" explicitly under this type. Not `test_assertion_failure`: an assertion is the surface, but the taxonomy routes order-dependence away from that class and there is no stable product defect — the same code passes in the intended order. Not `config_or_environment_failure`: nothing is missing or invalid.

## 6. Expected Answer verdict

Each claim was checked against *authentic observation + revised Physical Universe*, and the wording was tightened where the previous draft outran its evidence.

| Claim | Support |
|---|---|
| Passes in intended order, fails in revealed order, order-dependent | `raw.log` directly |
| Tests share one JVM-wide configuration map | `SingletonObjectFactory:89-95` + `GlobalWorld:20-27` + test `:30-34` |
| Map is built once and never reset between tests | `GlobalWorld:24-43`; no `@Before`/`@After` reset in any test class |
| Preceding test writes `MAX_SIZE=5` and never clears it | test `:136` |
| Victim never sets or clears that key | test `:77-98` |
| The leaked limit replaces the expected full-body text with the truncated form | the class's own sibling expectations at `:65-73` versus `:136-142` |

The previous draft's phrase *"the assertion formatter reuses leaked state"* was flagged in screening as a possible over-claim. On the revised universe it is in fact **supported** — `StatusCodeMatcher` is that formatter and does receive the leaked limit — but it is supported by Optional evidence, not by the Required set, and it describes an implementation detail the record never shows. The final wording therefore attributes the effect to the sibling tests' own expectations, which is the Required-set-supported form, and leaves the facade/matcher mechanism as corroboration.

**One honest limitation to record:** the record reports only `result: FAILURE`. The specific failure mode is **derived** from run order plus repository state, never observed. That is legitimate for order-dependent triage, but a reviewer should know the Ground Truth asserts a mechanism the artifact itself does not display.

## 7. Required and Optional Evidence

**Required (5):**

| ID | Necessary fact |
|---|---|
| `log:raw-log:lines-0001-0037` | Victim identity, intended PASS order, revealed FAILURE order, `OD` classification |
| `repo:…httpassertionfacadeimpltest-java:lines-0001-0100` | Singleton acquisition at `:30-34`; the victim at `:77-98` setting only `DISPLAY_BODY`; the `MAX_SIZE=100` sibling expectation at `:51-74` |
| `repo:…httpassertionfacadeimpltest-java:lines-0101-0198` | The polluting write `MAX_SIZE="5"` at `:136` and its truncated-text expectation |
| `repo:…internal-di-singletonobjectfactory-java:lines-0001-0096` | JVM-wide static instance holder — without it, per-instance factories would mean no leakage |
| `repo:…internal-context-globalworld-java:lines-0001-0080` | `@Singleton`, map built once, `put` mutates, no reset — without it, the value could plausibly be rebuilt per test |

**Optional (4):** `…globalworldfacade-java:lines-0001-0062` (the facade the tests call, and the `reconstruct()` remedy), `…httpassertionfacadeimpl-java:lines-0001-0100` (reads the leaked key), `…statuscodematcher-java:lines-0001-0047` (the truncation branch), `repo:cukes-http-pom-xml:lines-0001-0042` (module declares no surefire, so the parent fork policy is inert).

### Removal tests

- **`SingletonObjectFactory` — Required.** Remove it and `@Singleton` alone proves only "one per injector". Since each JUnit test method builds a new test instance, without the JVM-wide static holder each instance could obtain a fresh injector and a fresh world, and no leakage would follow. The necessary fact is lost.
- **`GlobalWorld` — Required.** Remove it and there is no evidence the map survives rather than being rebuilt, and no evidence that no reset hook exists. The leakage claim collapses to a correlation.
- **Both victim-file units — Required.** The first carries the singleton acquisition and the victim's omission; the second carries the polluting write. Neither substitutes for the other.
- **`HttpAssertionFacadeImpl` and `StatusCodeMatcher` — Optional, deliberately.** I initially expected these to be Required, but the removal test fails: the victim's class already demonstrates empirically that `MAX_SIZE=5` yields the truncated expectation and `MAX_SIZE=100` the full-body one. The diagnosis therefore stands without the implementation. Marking them Required would have inflated the set for mechanism detail the Required evidence already implies — the same error corrected in the N18 review.
- **The two sibling test classes — neither Required nor Optional.** Their role is to be *searched and eliminated*, not cited. The positive evidence identifies the polluter without them; their elimination is confirmatory. They belong in the Physical Universe as authentic competing candidates, which is precisely why omitting them was a defect.

## 8. Contemporaneous shortcut analysis

**Answer-prose scan over all 15 members is clean.** No occurrence of `flaky`, `flakiness`, `intermittent`, `order-depend`, `pollut`, `leak`, `shared state` or `idflakies` anywhere. No prior sibling fix, no remediation comment, no issue reference. This is categorically unlike N17 and N16.

Two authentic near-miss distractors survive and are valuable rather than harmful:

- `HttpLoggingPluginTest:47` holds the workspace's **only** `@Before`, so a superficial reader may take it for state cleanup; it sets up a Mockito mock.
- `HttpLoggingPlugin:51` calls `config.reset()`, which resets the RestAssured configuration, not the world.

**Search behaviour from the observation:**

| Query | Files hit |
|---|---|
| victim / polluter method names | 1 — the victim's test file |
| `EndsWithRegexpTest`, `HttpLoggingPluginTest` | 1 each |
| `MAX_SIZE` | 3 |
| `GlobalWorld` | **6**, including both distractors |
| `world.put` | 3 — and notably *not* `HttpLoggingPlugin`, since it only reads |

**The decisive property:** the observation contains **no token whatsoever** naming `GlobalWorld`, `SingletonObjectFactory`, `MAX_SIZE` or any state concept. It names only test method identifiers. Two of the five Required units therefore live in files that **cannot be reached by any query derived from the observation** — they are reachable only by opening the victim's test file and following `SingletonObjectFactory.instance()` at line 30. That is a genuine second hop that observation-keyed retrieval cannot shortcut.

**An authentic Maven-semantics trap.** The root `pom.xml:170-178` declares surefire with `forkCount=1` and `reuseForks=false` — but inside `<pluginManagement>` (`:158-180`), and **neither `cukes-http/pom.xml` nor `cukes-core/pom.xml` declares the plugin**, so that configuration is inert and surefire defaults (`reuseForks=true`, one JVM per module) apply. A superficial reader concludes cross-class pollution is impossible and wrongly eliminates all seven candidates; a careful reader checks the module poms. This is upstream reality, not curator construction.

## 9. Runtime Discriminative Value — `ADEQUATE` (lower end)

| Metric | Draft | **Revised** | N18 | B04 |
|---|---:|---:|---:|---:|
| Physical repo files | 10 | **15** | 3 | 6 |
| Physical total | 1,243 l / 43,677 B | **1,581 l / 54,816 B** | 1,933 l / 60,393 B | 3,669 l / 156,891 B |
| Raw artifact | 37 l / 1,935 B | **37 l / 1,935 B** | 9 l / 508 B | 619 l / 38,662 B |
| Canonical units | 17 | **23** | 22 | 44 |
| Required | 4 (23.5 %) | **5 (21.7 %)** | 5 (22.7 %) | 2 (4.5 %) |
| Optional | 0 | **4** | 2 | 2 |
| Required spread over | 3 of 11 artifacts | **4 of 16 artifacts** | 4 of 4 | — |
| Units in files with no Required evidence | 10/17 (59 %) | **18/23 (78 %)** | 0/22 | — |

**Strengths.** Seven authentic competing polluters across two additional classes, eliminable only by reading source. Two high-quality near-miss distractors. A forced two-file state-lifetime composition that the observation gives no lexical route to. A genuine Maven `pluginManagement` trap. A deliberately sparse observation that forces derivation rather than reading. Zero answer prose. Seventy-eight percent of units sit in files holding no Required evidence.

**Weaknesses.** The victim and the true polluter are in the same file, 45 lines apart, and the observation names both, so the correlation is reachable in roughly one file open. Their method names (`…AndNoMax` versus `…ButLongerThanMaxSize`) are semantically paired, which is authentic but strongly suggestive. Eliminating the other seven candidates is good practice but is not strictly forced by the scoring contract. The absolute workspace is modest.

**Expected separation — pre-runtime hypothesis, not a validated result.**

| Condition | Expectation |
|---|---|
| Fixed Pipeline | Likely retrieves the victim's test file from the observation's method names and reports the correlation, but has **no lexical route** to `SingletonObjectFactory` or `GlobalWorld`, so it should fail to establish leakage |
| Retrieval | Same ceiling for the same reason; better recall over the test classes, still blocked on the unnamed state machinery |
| ReAct | Can open the victim's file, follow `SingletonObjectFactory.instance()`, establish singleton lifetime, then sweep and eliminate the seven candidates — the full diagnosis |

**Rating `ADEQUATE`, lower end.** Placed one step above N18 on one concrete and checkable ground: N18's observation supplies `SIGINT`, `retcode` and `pidfile`, which lexically point into both of its non-victim Required files, whereas N01's observation supplies nothing that points at its state machinery. The remaining weaknesses are real and are why this is the lower end rather than a strong Case.

## 10. Canonicalization observations

Fixed-100, start at line 1, contiguous, non-overlapping, final unit may be shorter, IDs from source path and line range only. Coverage verified: **1,581 / 1,581 lines, no gaps, no overlaps**, all unit hashes resolving from frozen bytes. `provisional-pre-freeze`; to be rebuilt when the Profile is frozen. No boundary was moved to suit Required Evidence.

Calibration observations for the `N ∈ {50, 100, 200}` comparison:

- **Whole-file units dominate.** Twelve of fifteen members are shorter than 100 lines, so they each collapse to exactly one unit. At `N=100` this Case is effectively file-granular, which makes Evidence Hit coarse: citing `GlobalWorld` at all means citing all 80 lines. `N=50` would split `GlobalWorld` (80) and `SingletonObjectFactory` (96) and is worth comparing.
- **A load-bearing split.** The victim's test file (198 lines) is the one member that splits, and the split lands **between the victim and its polluter** — victim at `:77-98` in unit 1, polluter at `:136` in unit 2. Both are Required precisely because of that boundary. This is a clean instance of one causal comparison straddling a neutral boundary, alongside the N17 and N18 observations already recorded.

## 11. Severity findings

1. **Fixed — curator-derived search-space reduction (Layer 1, high).** Two of three observation-named test classes were absent, leaving only the class containing both victim and polluter. Restored.
2. **Fixed — false sanitization metadata.** The draft declared `reviewed_sanitized` with "Removed ANSI/control noise only"; `raw.log` is byte-identical to upstream with no control bytes and no transformation. Now `reviewed_no_changes` with zero transformations. This is the third package in which that boilerplate proved false, after N16 and N18.
3. **Fixed — imprecise provenance.** The draft cited only the source URL and revision. The pinned-SHA evidence establishing this as a genuine exact-executed-revision Case was not recorded; it now is.
4. **Recorded — derived failure mode.** The record shows no message, so the truncated-text mechanism is inferred from source and order. Legitimate for order-dependent triage, disclosed rather than smoothed over.
5. **Recorded — benchmark answer key adjacency.** iDFlakies publishes the minimized polluter and the fix outcome in sibling CSVs of the same repository. Excluded here; a standing rule for future iDFlakies-sourced Cases.

## 12. Validation

- Schema V2 loader PASS; declared fingerprint equals calculated (`6465db63…`).
- Manifest membership, sizes, SHA-256, path safety, no symlinks, no undeclared files: PASS (15 members).
- Canonical coverage **1,581 / 1,581 lines**, gap-free, overlap-free, exact resolved hashes: PASS.
- Required/Optional referential integrity and disjointness, Expected Answer schema: PASS.
- `raw.log` byte-identical to the complete upstream iDFlakies record (1,935 bytes, LF-only): PASS.
- All 15 members byte-identical to the pinned executed revision: PASS.
- `PublicCaseView` exposes only case identity, schema, fingerprint, raw-log path, repository root and forbidden actions: PASS.
- Answer-prose and benchmark-answer-key scan over all 16 frozen artifacts: no hits.
- All 20 case directories load with consistent fingerprints; **B04 `89a8f9a0…`, N17 `3f0f80d8…`, N16 `80345301…`, N18 `5bba62cb…` all unchanged**.
- `pytest tests/test_issue_22_case_schema_v2.py tests/test_issue_6_evaluation_suite.py tests/test_issue_14_structured_report_scoring.py` → `126 passed`.

## 13. Expected Answer observed-versus-derived check

The iDFlakies record directly observes only: the victim's identity, the intended order with `result: PASS`, the revealed order with `result: FAILURE`, and the `OD` classification. It does **not** observe the assertion message, the returned body, any truncation, or the value of `MAX_SIZE` at failure time.

Field-by-field check of `evaluator/expected-answer.json`:

| Field | Verdict |
|---|---|
| `summary` | **Clean, no change.** Every clause is observed, and the classification is explicitly attributed to *the record*. No mechanism is asserted. |
| `root_cause` | **One minimal correction applied.** All source-derived clauses were already stated as facts about the code rather than about the artifact, and the forbidden pattern — claiming the log shows truncation — was absent throughout. The single clause worth tightening read *"as the sibling tests in the same class show, that limit replaces the full-body assertion text the victim expects with the truncated form"*, which could be read as narrating the failing run. It now reads *"and the sibling tests in the same class establish that such a limit yields the truncated assertion text rather than the full body the victim expects"* — attributing the mechanism to source and generalising *"such a limit"* rather than recounting the specific execution. |
| `recommended_action` | **Clean, no change.** Purely prescriptive; asserts nothing about what was observed. |

The epistemic boundary itself is recorded where it belongs — in `case.json.provenance`, which states that the record carries no exception, stack trace or assertion output and that the failure mode must therefore be derived from run orders plus repository state. It is deliberately **not** placed inside `expected-answer.json`, since that field is scored against Agent output and should carry the diagnosis, not commentary about evidence provenance.

## 14. Final Human Review status

| Layer | Outcome |
|---|---|
| Scientific / package-content Human Review | **`PASS`** |
| Runtime Discriminative Value | **`ADEQUATE — lower end`** |
| Formal Suite Freeze | **`NOT YET`** |

Freeze is withheld only because `Canonicalization Profile v1` is unfrozen and no Suite Manifest exists; the coordinates and fingerprint are `provisional-pre-freeze` and may be mechanically rebuilt. Physical Artifacts, provenance, causal semantics, taxonomy and Expected Diagnosis semantics are the durable layer.

N01 needs no further difficulty and no further Required Evidence.

## 15. Calibration finding — Evidence Hit does not measure candidate elimination

The two restored sibling test classes, `EndsWithRegexpTest` and `HttpLoggingPluginTest`, are deliberately **neither Required nor Optional**. Their value is that an Agent must open and eliminate them as plausible polluters; they are never cited in a correct diagnosis.

That exposes a gap in the current metric. Retrieval Evidence Hit and Report Evidence Hit both measure **positive supporting evidence acquisition** — did the Runtime reach and cite the facts that support the answer. Neither measures **negative evidence work**: ruling out competing candidates. In this Case seven candidate polluters must be eliminated, and a Runtime that does that thoroughly scores no differently from one that guesses the polluter correctly on the first try.

Recorded as a calibration/review finding only. The scorer, Schema V2, the methodology and the ADRs are **not** changed. The signal to watch once Runtimes exist: if ReAct demonstrably performs better candidate elimination than Retrieval but the Evidence Hit gap stays flat, the metric is missing this dimension of investigation quality.

## 16. Scope boundary

Only the N01 package, this record, and the N01 material in `BULK-DRAFT-REVIEW.md` were changed. N18, N16, N17, B04, every other Case, methodology documents, ADRs, Schema V2, the Canonicalization Profile documents, the suite manifest and runtime code were not touched. No replay, no environment reconstruction, no synthetic artifact, no Suite Manifest, no Suite fingerprint, and no replacement-candidate discovery.
