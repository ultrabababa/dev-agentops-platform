# Issue #15 — targeted replacement Candidate Discovery ledger

**Status: candidate ledger only. No Case Package was constructed, no Physical Artifact was frozen, and no
candidate is admitted.** Every entry below is a *screening* judgement made from the authentic failure log plus
upstream revision verification. Nothing here is a Human Review PASS, a Formal Freeze, or Formal Suite membership.
`Canonicalization Profile v1` remains unfrozen and no Suite Manifest exists.

**Scope of this round.** One combined round covering all **9** replacement slots left by the closed 19-package bulk
review — `timeout_or_flaky_failure: 2`, `config_or_environment_failure: 2`, `dependency_or_install_failure: 2`,
`lint_or_type_failure: 1`, `test_assertion_failure: 2` — rather than five per-category rounds. The
`lint_or_type_failure` count of 1 assumes **B04 is provisionally retained** as one candidate of that type for planning.

## 1. Search performed

**Source priority 1 — BugSwarm (first pool, not a constraint).** The full public artifact dataset was enumerated from
`http://www.api.bugswarm.org/v1/artifacts` — **6,566 artifacts**. After excluding the 12 repositories already used by the
suite, **5,617** remained across **730** repositories. Artifacts were tagged by metadata into four screening pools
(analyzer invoked in CI config; `classification.build` ∈ {Yes, Partial}; `classification.test` = Yes; and
`reproducibility_status = Flaky` or `stability` below full), giving **1,894** tagged candidates across **394** repositories.

Raw logs were then fetched from `https://www.bugswarm.org/artifact-logs/<job_id>/raw/`. **Only about 45 % of artifacts
host a raw log**; the rest return HTTP 404. **741 authentic logs** were retrieved and screened. That 404 rate is a
property of the BugSwarm log host, not of the candidates, and it is the main reason the pool is narrower than the
artifact count suggests.

**Sources 2 and 3 were not needed to fill the slots.** BugSwarm yielded at least one defensible candidate for every
category, so no GitHub-issue or benchmark-record candidates are proposed in this round. Two categories are nevertheless
thin on *quality* rather than count — see §4.

## 2. Screening method

The primary question was applied before any construction cost, as recorded in the Bulk Review Ledger:

> *How much of the causal mechanism has the observation and its tooling already told the Agent?*

Concretely, each log was reduced to its terminal failure disclosure, and candidates were ranked by **how much the
observation withholds**. For assertion candidates this was measured directly: the surefire `Failed tests:` block was
stripped of test signatures and line references, and the residual message length counted. Three logs in the whole pool
disclose **zero** message characters.

Counts (log size, repository size, unit count, Required share) were **not** used as difficulty proxies. They appear below
only as diagnostics.

**No candidate was made harder.** Nothing was pruned, and no distractor was added. Where the natural workspace makes a
candidate easy, the candidate is rejected rather than trimmed.

## 3. Provenance verification

Every candidate's revision was checked against the GitHub API. **All 16 verified**: the commit exists, and its committer
date matches the BugSwarm `committed_at` to the second in every case.

For `pull_request` jobs the executed revision is the ephemeral merge commit, not the PR head — the N20 lesson. **Every
GitHub Actions PR candidate records its own executed merge SHA in the log**, e.g.

```
* [new ref]   b8ceb2891371446741daf16ce1f56f7615cdaf79 -> pull/3182/merge
HEAD is now at b8ceb28 Merge e2c57cbd3c9679473f0f2721bd51b1464da988a4 into 67cfdb21bc33192d4464aafa05fa80dcd91f8561
```

and that merge revision is still resolvable upstream. Provenance quality for those candidates is therefore
**recovered-and-verified executed merge revision**, the same category N20 was admitted under. Travis push-job candidates
have a directly verified **exact executed revision**.

## 4. Candidate ledger

Ratings are **preliminary** Runtime Discriminative Value, assigned from the observation and the upstream revision only.
No Physical Universe has been assembled, so no Required Evidence removal test has been run and no rating is final.

### `test_assertion_failure` — 2 slots

| | Source · job | Revision provenance | Observation discloses | Causal hypothesis | Prelim. RDV | Rec. |
|---|---|---|---|---|---|---|
| **A1** | BugSwarm `square/retrofit` job `113047638`, Travis push, 2,386 lines / 146,352 B, 307 tests, 1 failure | **exact executed revision** `323ffc8f00b19dba98873e77a77c25ec7f89f56c`, verified | **Only the test name.** `Failed tests:   serializeNullThrows(retrofit2.converter.protobuf.ProtoConverterFactoryTest)` — measured **zero** message characters | Retrofit began passing `null` through to converters; the protobuf converter's expected-throw oracle no longer sees a throw. Oracle-versus-product is genuinely open | **ADEQUATE** | **KEEP** |
| **A2** | BugSwarm `SonarSource/sonar-php` job `206164136`, Travis push, 1,692 lines / 111,598 B, 696 tests, 1 failure | **exact executed revision** `ebf7b1f2cade1ef88a5bc3f3563ce490a94ee374`, verified | `java.lang.AssertionError: Expecting actual not to be null` at `PHPSensorTest.java:419` — AssertJ names **neither which value nor why**. Sole disclosure in the log | The sensor's SonarLint branch leaves unset something the test asserts non-null; which side is wrong requires the sensor source | **ADEQUATE** | **KEEP** |
| A3 | `google/auto` job `393700005` | merge revision `b4483253…`, verified | Surefire truncates to `(..)`, **but** a full expected-versus-actual AST diff appears earlier (`javax.annotation.Generated` vs `javax.annotation.processing.Generated`) | JDK 9+ moved the `@Generated` annotation | LOW–MEDIUM | RESERVE |
| A4 | `spring-projects/spring-hateoas` job `78347612` | `9d35670e…`, verified | Message elided to `(..)`; 291 tests | serialization drift | MEDIUM | RESERVE — BugSwarm marks it `Flaky` 4/5, a taxonomy conflict for an assertion slot |
| — | `zarr-developers/zarr-python` job `28094803829` | — | Prints the full diff: `{'separator': '/'} != {'separator': '.'}` | — | LOW | **REJECT** at screening — the N12 profile exactly |

### `lint_or_type_failure` — 1 slot

| | Source · job | Revision provenance | Observation discloses | Causal hypothesis | Prelim. RDV | Rec. |
|---|---|---|---|---|---|---|
| **L1** | BugSwarm `PyGithub/PyGithub` job `36442425251`, GH Actions PR 3182, 674 lines / 51,954 B | **executed merge revision** `b8ceb2891371446741daf16ce1f56f7615cdaf79`, recorded in-log and verified | `github/Requester.py:924:13: error: "object" has no attribute "raise_for_status"  [attr-defined]` · `Found 1 error in 1 file (checked 291 source files)`. mypy states the violation and **nothing about why the type is `object`** | A value reaches line 924 with an over-broad static type; recovering *where* that type is introduced needs the annotation chain, not the error | **ADEQUATE** | **KEEP** |
| L2 | `PyGithub/PyGithub` job `34636499466`, PR 3095 | executed merge revision `fe504355…`, in-log and verified | `"Organization" has no attribute "attach_security_config"` (and `detach_…`) at `Repository.py:4232`/`:4238` | The PR calls methods never added to `Organization` — an **absence-based inference** across two files | ADEQUATE | RESERVE — strong alternate to L1 |
| L3 | `open-telemetry/opentelemetry-python` job `35720302870`, PR 4361 | merge revision `75b14e47…`, verified | Three related mypy errors including `Non-overlapping equality check (left operand type: "str", …)` | A new advisory union type is compared against `str` | MEDIUM | RESERVE |
| — | `joyent/java-manta` checkstyle jobs (many) | — | `You have 77 Checkstyle violations`, each violation itemised above it | — | LOW | **REJECT** at screening |

### `dependency_or_install_failure` — 2 slots

| | Source · job | Revision provenance | Observation discloses | Causal hypothesis | Prelim. RDV | Rec. |
|---|---|---|---|---|---|---|
| **D1** | BugSwarm `spring-projects/spring-hateoas` job `232784946`, Travis push, 4,825 lines / 312,626 B, **32 failures of 314 tests** | **exact executed revision** `d68700231eb1d8afaf27328cc5d576a71e966a2a`, verified | 32 Spring context failures. The cause is four layers down: `BeanInstantiationException` → `NoClassDefFoundError: com/fasterxml/jackson/databind/exc/InvalidDefinitionException` → `ClassNotFoundException` | The resolved Jackson databind version predates `InvalidDefinitionException`. **Terminal symptom (32 broken beans) is nowhere near the root cause (one dependency version)** | **ADEQUATE** | **KEEP** |
| **D2** | BugSwarm `Nukkit/Nukkit` job `94403868`, Travis push, 719 lines / 30,823 B | **exact executed revision** `5a893db8c78d3f4b05a9a6d34c7da782ed537611`, verified | ~30 javac errors — `package org.iq80.leveldb does not exist`, `cannot find symbol: class DB` — and `Execution failed for task ':compileJava'`. **Nothing states a dependency problem** | A declared import has no corresponding dependency. The log's download list (gson, jansi, snakeyaml, jline — no leveldb) supports an **absence-based inference**; a compile error is a misleading downstream symptom | **ADEQUATE** | **KEEP** |
| D3 | `orbit/orbit` job `126506070` | exact revision `4808ea4905…`, verified | `package org.jgroups.util does not exist` in a test source — preceded by an unrelated `[ERROR] Invalid use of await …` that does **not** fail the build | Test-scoped dependency missing; the earlier ERROR is a genuine competing hypothesis to eliminate | ADEQUATE | RESERVE — close behind D2 |
| D4 | `pallets/quart` job `25205086955`, PR 341 | executed merge revision `8348af54…`, in-log and verified | `ImportError: cannot import name 'aiter' from 'builtins' (unknown location)`, ×20 collection errors; interpreter path shows 3.9.19 | `aiter` is a builtin only from Python 3.10 — a **domain-knowledge bridge** | BORDERLINE-ADEQUATE | RESERVE |
| D5 | `hhatto/autopep8` job `25505354328`, PR 747 | merge revision `0980c6e0…`, verified | `AttributeError: module 'tokenize' has no attribute 'FSTRING_START'`, 67 failures | `FSTRING_START` is Python 3.12+; the matrix runs older | BORDERLINE-ADEQUATE | RESERVE |
| D6 | `brettwooldridge/HikariCP` job `446093148`, PR 1265 | `943f09b60a…`, verified | 3 unrelated-looking failures; `AbstractMethodError` among the exceptions | Classic JDBC driver ABI mismatch presenting as scattered test failures | MEDIUM | RESERVE |
| — | `alibaba/spring-cloud-alibaba` job `16538071631` | — | `Non-resolvable parent POM … Could not find artifact` | — | LOW | **REJECT** — states the resolver failure plainly |

### `config_or_environment_failure` — 2 slots

| | Source · job | Revision provenance | Observation discloses | Causal hypothesis | Prelim. RDV | Rec. |
|---|---|---|---|---|---|---|
| **C1** | BugSwarm `alibaba/COLA` job `12505170926`, GH Actions push (`pr = -1`), 4,260 lines / 528,624 B, 7 failures of 55 | **exact executed revision** `1e0c1306bd98d454c1bd5f23888f6162969115b8`, verified | A four-layer chain: `Failed to load ApplicationContext` → `UnsatisfiedDependencyException` → `BeanCreationException … 'dataSource'` → `DataSourceBeanCreationException` + `ConnectException: Connection refused`. **No line names a configuration file** | Test datasource configuration points at a database endpoint the CI job does not provide — an indirect misconfiguration surfacing as seven unrelated-looking test failures | **BORDERLINE-ADEQUATE** | **KEEP** |
| **C2** | BugSwarm `rackerlabs/blueflood` job `80881330`, Travis, 7,931 lines / 314,410 B, 2 errors of 293 | **exact executed revision** `3c1c16bc200b7d0b97b1dc0594d506b53aa51e0d`, verified | `EsSetupRuntimeException: Exception when executing request create index [index='events']` at `setUp:74`, with the stack inside `DocumentMapperParser.parse`, plus a cascading `tearDownClass:157 NullPointer` | The Elasticsearch index-**mapping resource** is invalid for the ES version, not a service that is down. Requires eliminating the readiness hypothesis — which BugSwarm itself endorses by labelling the artifact `Flaky` 4/5 — using the parser frame | **ADEQUATE**, conditional | **KEEP**, conditional on §5 |
| C3 | `haraldk/TwelveMonkeys` job `318828168` | exact revision `b8a540c0…`, verified | `FileNotFoundException: /Downloads/multi-foo.tiff` at `TIFFImageWriterTest.testWriteSequence:378` via `FileUtil.write` | A test writes to a path that exists only on a developer machine | MEDIUM — the offending path is printed verbatim | RESERVE |
| — | `sannies/mp4parser` job `86826291` | — | `FileNotFoundException: C:\dev\mp4parser\out.264` | Hardcoded Windows dev path in a test | LOW | **REJECT** — the N10 profile: the log prints the offending value verbatim beside the failure |

### `timeout_or_flaky_failure` — 2 slots

| | Source · job | Revision provenance | Observation discloses | Causal hypothesis | Prelim. RDV | Rec. |
|---|---|---|---|---|---|---|
| **F1** | BugSwarm `apache/lucene` job `27509200564`, GH Actions PR 13574, 974 lines / 80,323 B, 1 failure of 96, **stability 2/3** | **executed merge revision** `556b838b09c2de3d64d1ba5afb4dcf99bc4014c6`, recorded in-log and verified | `TestOverviewImpl > testGetIndexFormat FAILED` · `RuntimeException: MockDirectoryWrapper: opening segments file [segments_1] with a non-READONCE context[IOContext[context=FLUSH, …]]` · `__randomizedtesting.SeedInfo.seed([6603B3B1AF668E36:…])` | Luke's `IndexUtils` opens the segments file without a READONCE context while the PR tightens `MockDirectoryWrapper` enforcement; seed-dependent. Distractor: an unrelated errorprone `RethrowReflectiveOperationExceptionAsLinkageError` warning earlier | **ADEQUATE** | **KEEP** |
| **F2** | BugSwarm `orbit/orbit` job `361637862`, Travis PR 293, 6,551 lines / 573,520 B, 2 failures of 184, **stability 2/5** | **exact executed revision** `7f6f338f294aa776c6ec8121de8c6939e93a95b3`, verified | `CacheResponseTest.testMultipleInputs` and `testCacheFlushWithMultipleInputs`; `Values should be different. Actual: 2402940…`. Thousands of interleaved actor lifecycle lines as natural distractors | Actor response caching races actor deactivation — the log shows `Stage has 101 actors. The max actor count is set at 50 … deactivate 76 actors`. Genuine lifecycle/ordering reconstruction | **ADEQUATE** | **KEEP** |
| F3 | `ocpsoft/rewrite` job `118490282`, stability 3/4 | exact revision `fd31c04623…`, verified | `WebClassesFinderTest.testWebClassesFinder:72 » IllegalState Unable to load cla…` — **truncated mid-message**; 5,682 lines dominated by a full WildFly boot log | Deployment/classpath scanning under an Arquillian-managed container | MEDIUM–ADEQUATE | RESERVE |
| F4 | `brettwooldridge/HikariCP` job `446093148` | verified | Connection-pool initialisation tests | Pool lifecycle | MEDIUM | RESERVE — competes with D6 for its taxonomy |

## 5. Open questions to settle before construction

1. **C2 blueflood — is the ES mapping a repository file?** The rating assumes the index-mapping resource that
   `DocumentMapperParser` rejects lives in the repository and enters the Physical Universe under scope clause (d).
   If the mapping is supplied by the `elasticsearch-test` library rather than the project, the repository contributes
   nothing necessary and C2 collapses toward `LOW`. **Verify before construction.**
2. **F1 lucene — taxonomy judgement.** The failure is seed-dependent and intermittent (`stability 2/3`), which fits
   `timeout_or_flaky_failure`. It could also be argued as a test-infrastructure assertion. Recommend
   `timeout_or_flaky_failure` with `acceptable_failure_types: []`, but this is a judgement to confirm.
3. **A1 retrofit — a leak that cannot be removed.** The branch name `jw/pass-null-to-converters` appears twice in the
   authentic Travis output (`git clone --branch=…` and a cache filename). It names the triggering change. Under the
   standing rule this is contemporaneous real information and **must not be deleted**; it is a genuine shortcut risk to
   be recorded, and it is the main reason A1 might land below `ADEQUATE` on full review.
4. **C1 COLA — confirm the configuration artifact.** The chain ends at `Connection refused`; construction must confirm
   that the datasource endpoint is set by a repository configuration file rather than by a CI service block only.
5. **A2 sonar-php — branch `SONARPHP-684`** is a ticket identifier in the log. It is not answer-bearing inside the
   Physical Universe, but an external tracker lookup could shortcut it. Record, do not remove.

## 6. Round summary

**23 candidates screened to a disposition: 9 `KEEP`, 10 `RESERVE`, 4 `REJECT` at screening.** Every slot has at least one
`KEEP` and every category except `lint_or_type_failure` has at least one further reserve; `lint_or_type_failure` has two
reserves for its single slot.

**The two thin categories are the ones the closed review already flagged.** `config_or_environment_failure` remains the
hardest type to source well — CI logs for missing configuration tend to name the missing thing, which is exactly why B16
and N10 were rejected. C1 and C2 are proposed because their symptom chains are indirect, not because the category is
comfortable. If either fails §5 verification, the next round should go to **source priority 2 (GitHub historical
failures)** for that slot rather than settle for a `LOW` BugSwarm candidate — the recorded policy is that `LOW` cases are
not retained to preserve category count, and B08 already fills the suite-level easy-anchor role.

**Nothing is admitted, nothing is built, and no Physical Artifact exists for any candidate in this ledger.**

---

## Construction outcomes (appended after the two construction rounds)

**Eight of nine slots are filled.** Constructed and reviewed: C2 blueflood, A1 retrofit, D2 Nukkit (round 1, all three
`HUMAN REVIEW PASS`); C1 COLA, A2 sonar-php, L1 PyGithub, D1 spring-hateoas, F1 lucene (round 2, all five recommended
`PASS`). Per-Case records are in `reviews/`.

**Two screening estimates did not survive construction, in opposite directions:**

- **D2 Nukkit** was screened `ADEQUATE` and reviewed at `BORDERLINE-ADEQUATE`. javac quotes the offending imports into
  the log, so the named source file fails a strict removal test. Retained by Human decision.
- **F2 orbit** was screened `ADEQUATE` and **rejected before construction** as deterministic, together with its reserve
  **F3 ocpsoft/rewrite**. The `timeout_or_flaky_failure` entries in this ledger were screened partly on BugSwarm
  `reproducibility_status` and `stability`, which measure artifact reproduction variance rather than test-level
  nondeterminism. That screen is withdrawn; see `reviews/flaky-slot-2-record.md`.

**Reserves still standing and unused:** A3 google/auto, A4 spring-hateoas 78347612, L2 PyGithub 34636499466,
L3 opentelemetry-python, D3 orbit 126506070, D4 quart, D5 autopep8, D6 HikariCP, C3 TwelveMonkeys. **F4 HikariCP is
withdrawn as a flaky reserve** for the same reason as F2 and F3 — its recorded profile (`AbstractMethodError`) points at a
dependency ABI mismatch, not nondeterminism.
