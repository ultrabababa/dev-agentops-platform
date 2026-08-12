# A2 — bugswarm-sonar-php-206164136 — construction and Human Review record

> **FINAL DISPOSITION: `HUMAN REVIEW PASS`.** Layer 1 `PASS`, Layer 2 **`ADEQUATE`**.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `test_assertion_failure`, `acceptable_failure_types: []`. **Slot:** the second `test_assertion_failure` replacement.
**Fingerprint:** `feb687cc8c09aeb0214eea1bf38d5b741e1dbfc55652c3d88b8217d1ba9eca87` (supersedes `403660d1…` after the Required promotions in §4).

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/206164136/raw/`. **Exact executed revision** `ebf7b1f2cade1ef88a5bc3f3563ce490a94ee374` (SonarSource/sonar-php), verified upstream; committer date `2017-02-28T12:43:38Z` matches BugSwarm exactly. Travis push job on branch `SONARPHP-684`.

`raw.log` 111,598 bytes / 1,691 lines. ANSI/CR normalisation only. All **9 members byte-identical**.

## 2. The observation withholds both sides
The entire disclosure is `java.lang.AssertionError: Expecting actual not to be null` at `PHPSensorTest.java:419`, one failure among 696 tests. AssertJ names neither the value nor the metric nor the file. `Expecting actual` occurs twice in the log and nothing else about the failure appears.

## 3. Independent causal chain
1. `PHPSensorTest.java:419` — `assertThat(context.measure(testFileKey, CoreMetrics.TESTS)).isNotNull();`, where `testFileKey` is `Monkey.php`, registered as `Type.TEST`.
2. `PHPSensor.execute` calls `processCoverage` only when `inSonarQube(context)` holds. The test has just set a **SonarQube** runtime, so the gate passes — the SonarLint gate this test is named for is **not** the cause.
3. `PhpUnitTestFileReport.saveTestMeasures:59-65` writes `CoreMetrics.TESTS` only when `getUnitTestInputFile` resolves a file, matching the **report's own path** against TEST-typed PHP files.
4. `phpunit-junit-report.xml` names `MegaAppTest.php` and `src/App2Test.php` … `src/AppTest.php`. **It contains no entry for `Monkey.php`.** No report object exists for that file, so no TESTS measure is ever produced.

## 4. Required Evidence — 9 units, removal-tested
| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-1501-1600` | The observation and the failing line | Remove: no failure |
| `repo:phpsensortest-java:lines-0401-0456` | The assertion, the metric, and that the subject is `Monkey.php` | Remove: the claim is unknown |
| `repo:phpunittestfilereport-java:lines-0001-0100` | That TESTS is written only for files the report names | Remove: the necessary condition is unknown |
| `repo:phpunit-junit-report-xml:lines-0001-0055` | That `Monkey.php` is absent from the report | Remove: the decisive absence cannot be established |
| `repo:phpsensor-java:lines-0101-0200` | That `inSonarQube` passes for a SonarQube runtime, and that `processCoverage` is the only route to the importer | Remove: the SonarLint gate survives as an explanation, **inverting** the diagnosis |
| `repo:phpsensortest-java:lines-0301-0400` | That the test sets `PHPUNIT_TESTS_REPORT_PATH_KEY` to `PhpTestUtils.PHPUNIT_REPORT_NAME` and registers `Monkey.php` as `Type.TEST` | Remove: neither the configured report nor the subject file is established |
| `repo:phptestutils-java:lines-0001-0057` | That `PHPUNIT_REPORT_NAME` resolves to `…/phpunit/sensor/phpunit-junit-report.xml` | Remove: the configured property cannot be tied to the fixture actually frozen |
| `repo:phpunitservice-java:lines-0001-0099` | That `parseReport(PHPUNIT_TESTS_REPORT_PATH_KEY, importer, "test", …)` drives the tests importer from that property | Remove: the property and the importer are not connected |
| `repo:phpunittestresultimporter-java:lines-0001-0044` | That one `PhpUnitTestFileReport` is produced per file the report names | Remove: "no entry therefore no report object therefore no measure" is not entailed |

Four units were promoted from Optional at Human review so the causal chain is closed end to end — configured report path → fixture → importer → per-file report → absent entry → no measure — rather than relying on units that were merely available. **The Physical Universe was not expanded**; every promoted unit was already a member. Two units remain Optional, including the coverage fixture, which *does* reference `Monkey.php` and is a genuine near-miss.

## 5. Shortcut and leakage review
`Monkey.php`, `CoreMetrics.TESTS` and `getUnitTestInputFile` occur **zero times in the log**. The test's own name — `should_disable_unnecessary_features_for_sonarlint` — actively misdirects toward the SonarLint gate, which is authentic and retained. The coverage fixture referencing `/Monkey.php` is a second authentic near-miss: it makes "the file is in the reports" superficially plausible. Answer-prose: the `TODO`/`should be` hits in `PHPSensor.java` are unrelated.

## 6. Runtime Discriminative Value — `ADEQUATE`
34 units (17 log + 17 repo), Required 5, 9 files. The observation supplies only "something was null". Diagnosis requires a four-hop trace from the assertion through the sensor gate, the importer and the report resolver, ending in an **absence-based inference** over a fixture, while refuting the explanation the test's own name suggests.

## 7. Disposition — decided
**`HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Four Required promotions applied at Human review (§4); the rating is unchanged. Not a Formal Freeze; Formal Suite membership is not frozen.
