# D1 — bugswarm-spring-hateoas-232784946 — construction and Human Review record

> **FINAL DISPOSITION: `HUMAN REVIEW PASS`.** Layer 1 `PASS`, Layer 2 **`ADEQUATE`**.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `dependency_or_install_failure`, `acceptable_failure_types: []`. **Slot:** the second `dependency_or_install_failure` replacement.
**Fingerprint:** `2553f3dc639d72f27ef1fccdf4553aa6b03cf28e61e775b1bceb0958fc65a995` (supersedes `573e8780…` after the Required promotion in §3).

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/232784946/raw/`. **Exact executed revision** `d68700231eb1d8afaf27328cc5d576a71e966a2a`, verified upstream; committer date `2017-05-16T11:13:52Z` matches BugSwarm exactly. Travis push job on `master`, one entry of a four-profile matrix.

`raw.log` 312,626 bytes / 4,824 lines. ANSI/CR normalisation only. All **4 members byte-identical**.

## 2. Independent causal chain
1. `raw.log:870` — `export PROFILE=spring5-next`; `:909` — `mvn clean dependency:list test -P${PROFILE} -Dsort`.
2. `pom.xml:113-124` — the `spring5-next` profile overrides **only** `spring.version` to `5.0.0.BUILD-SNAPSHOT`.
3. `pom.xml:75` — `jackson.version` is a single top-level property, `2.8.5`, shared by every profile. No profile overrides it.
4. `raw.log:2634-2636` — `dependency:list` confirms `jackson-databind:jar:2.8.5:compile` resolved successfully. Nothing is missing or unresolvable.
5. `raw.log:2758-2781` — `BeanInstantiationException` → `NoClassDefFoundError: com/fasterxml/jackson/databind/exc/InvalidDefinitionException` → `ClassNotFoundException`, thrown while Spring 5 constructs `AllEncompassingFormHttpMessageConverter` inside `RequestMappingHandlerAdapter`. That class arrived in Jackson 2.9.
6. Every test context that builds that bean fails: **32 failures across otherwise unrelated test classes**, spanning `EnableHypermediaSupportIntegrationTest`, `TraversonTest`, `TypeReferencesIntegrationTest` and others.

## 3. Required Evidence — 5 units, removal-tested
| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-2701-2800` | The observation and the missing class | Remove: no failure |
| `log:raw-log:lines-0801-0900` | That the executed profile is `spring5-next` | Remove: four candidate profiles remain, so the Spring version is undetermined |
| `repo:pom-xml:lines-0001-0100` | `jackson.version` = 2.8.5 | Remove: the Jackson version is unknown |
| `repo:pom-xml:lines-0101-0200` | That `spring5-next` bumps Spring and **not** Jackson | Remove: the root cause — a partial profile override — cannot be stated |
| `log:raw-log:lines-2601-2700` | That `jackson-databind:jar:2.8.5:compile` **resolved successfully** | Remove: "the artifact is missing or could not be resolved" survives, and the Expected Answer's explicit distinction between version incompatibility and a missing dependency is no longer entailed |

The fifth unit was promoted from Optional at Human review precisely because the Ground Truth draws that distinction. Three units remain Optional, including `.travis.yml`'s matrix.

## 4. Shortcut and leakage review
`jackson.version` occurs zero times in the log. `InvalidDefinitionException` occurs 122 times — the observation is loud about the *symptom* and silent about the *cause*. The competing hypothesis "Jackson is missing or unresolvable" is authentic and is refuted from inside the log by `dependency:list`, which is why that unit is retained as Optional rather than discarded. Answer-prose scan clean.

## 5. Runtime Discriminative Value — `ADEQUATE`
66 units (49 log + 17 repo), Required 4, 4 files / 40,362 bytes. The terminal symptom — 32 broken Spring contexts — is maximally distant from the root cause, a single property not overridden in one profile. The diagnosis requires identifying which matrix entry ran, reading a profile override, knowing which Jackson release introduced the class, and scoping the fix so the Spring 4.3 profiles are not disturbed.

## 6. Disposition — decided
**`HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. One Required promotion applied at Human review (§3); the rating is unchanged. Not a Formal Freeze; Formal Suite membership is not frozen.
