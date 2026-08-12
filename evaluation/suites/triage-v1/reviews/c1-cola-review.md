# C1 — bugswarm-cola-12505170926 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE`** · constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `config_or_environment_failure`, `acceptable_failure_types: []`. **Slot:** the second `config_or_environment_failure` replacement.
**Fingerprint:** `c6c9be3613608a106784720411307a876e25d9633934fcef6e03cc813237fef1`.

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/12505170926/raw/`. **Exact executed revision** `1e0c1306bd98d454c1bd5f23888f6162969115b8` (alibaba/COLA), verified upstream; committer date `2023-04-04T11:05:20Z` matches BugSwarm exactly. GitHub Actions **push** job (`pr = -1`), so no merge-revision ambiguity.

`raw.log` 528,624 bytes / 4,259 lines. ANSI/CR normalisation only. All **8 members byte-identical**.

## 2. The observation discloses no configuration at all
This is the decisive property. In 4,259 lines the log contains **zero** occurrences of `jdbc:mysql`, `chargeDB`, `localhost:3306`, `MYSQL_SERVER` or `ddl-auto`. What it shows is a four-layer Spring cascade: `Failed to load ApplicationContext` → `UnsatisfiedDependencyException` → `BeanCreationException … 'dataSource'` → `DataSourceBeanCreationException` with `ConnectException: Connection refused`. Seven tests error; none reaches an assertion.

This is the opposite of the profile that sank N10, where the log printed the offending endpoint verbatim beside the error.

## 3. Independent causal chain
1. `ChargeServiceTest` is `@RunWith(SpringRunner.class) @ContextConfiguration(classes = Application.class)` and `ChargeRecordRepoTest` is `@SpringBootTest`; both boot the full context.
2. `application.yml` declares `jdbc:mysql://${MYSQL_SERVER:localhost}:${MYSQL_PORT:3306}/${MYSQL_DB_NAME:chargeDB}` with `jpa.hibernate.ddl-auto: update`, so Hibernate connects during context startup.
3. `.github/workflows/ci.yaml` runs only `./mvnw -V --no-transfer-progress clean install` across an OS × JDK matrix. It declares **no `services:` block** and no `MYSQL_*` environment overrides.
4. The connection is refused, `dataSource` creation fails, the context cannot load, and all tests in those classes error.

## 4. Required Evidence — 5 units, removal-tested
| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-1801-1900` | The observation and the context-load failure | Remove: no failure |
| `log:raw-log:lines-1901-2000` | The `dataSource` bean chain and `Connection refused` | Remove: the failing bean is unknown |
| `repo:application-yml:lines-0001-0015` | The MySQL endpoint and `ddl-auto: update` | Remove: what is being connected to, and why at startup, is unknown |
| `repo:ci-yaml:lines-0001-0026` | That the job provisions no database | Remove: "the MySQL service was temporarily down" survives, **inverting** the fix |
| `repo:chargeservicetest-java:lines-0001-0100` | That the test boots the full application context | Remove: the link from a unit test to a production data source is missing |

Five Optional, including `application-test.yml` and `PropertyTest`.

## 5. Shortcut and leakage review
No configuration token appears in the log, so the entire configuration side must come from the repository. A real competing hypothesis is present and authentic: `application-test.yml` exists and `PropertyTest` activates it with `@ActiveProfiles("test")`, while the two failing classes do not — inviting "the test profile was not activated" as the fix. That reading is wrong, because `application-test.yml` hard-codes the same `localhost:3306` endpoint; refuting it requires reading the file rather than just noticing the annotation. Answer-prose scan clean.

## 6. Runtime Discriminative Value — `ADEQUATE`
52 units (43 log + 9 repo), Required 5, 8 files. The chain from symptom to cause crosses four exception layers and then leaves the log entirely. The strongest `config_or_environment_failure` candidate found in the whole discovery round, and the category's recurring weakness — logs that name the missing thing — does not apply here.

## 7. Disposition
**Recommended `HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not a Formal Freeze.
