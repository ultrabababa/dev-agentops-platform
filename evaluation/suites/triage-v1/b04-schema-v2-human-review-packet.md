# B04 Schema V2 Human Review Packet

## Review status

`B04 Schema V2 calibration package = HUMAN REVIEW PASS`

- Case: `bugswarm-checkstyle-77722324`
- Failure Type: `lint_or_type_failure`
- Branch: `codex/issue-15-b04-schema-v2`
- Base: `origin/main` at `69c9b8b75c3ff613cae0def30f11fa9451726d4a`
- Human-reviewed calibration-baseline Case fingerprint: `89a8f9a08f0dcb263733b21e85b5355b43dfe4cbf817a3130548379e13fc3bd7`
- Final Suite Manifest/fingerprint: not created
- Suite directory: `evaluation/suites/triage-v1/`, where `triage-v1` means the first Formal Triage Evaluation Suite, not Offline Case Schema V1

This fingerprint is the loader-verified Human-reviewed calibration baseline. It is not a final Formal Suite fingerprint: `Canonicalization Profile v1` is not frozen, and a later Profile decision may mechanically regenerate Canonical coordinates, dependent Evidence IDs, and the Case fingerprint while leaving Physical Artifacts and Ground Truth semantics unchanged.

Suite version, Suite Manifest schema, Offline Case schema, artifact schemas, and Structured Report schema are independent version namespaces. Therefore the Case envelope and Expected Answer remain V2 while repository manifest, Canonical Evidence and Evidence Ground Truth artifacts correctly remain at their own V1 schemas.

## 1. Provenance and causal verification

- Benchmark artifact: BugSwarm `checkstyle-checkstyle-77722324`, historical failed job `77722324`.
- Raw source: `https://www.bugswarm.org/artifact-logs/77722324/raw/`.
- Upstream repository: `https://github.com/checkstyle/checkstyle`.
- Exact failing revision: `da6ebe6de41b7a5afc6f6746ff0c2382c2a4be0f`.
- BugSwarm release 1.3.1 records the artifact as active and Reproducible 5/5.
- Curator-only passing child: `1e7ae5866daead0d81be2bfcf7febbd1ca0fcbd8`; it removes only `public` from the `FieldFrame` constructor. The passing commit and diff are not present in the package.

The real log shows Maven `ant-phase-verify`, Checkstyle running on 687 files, one `Redundant 'public' modifier` finding at `EqualsAvoidNullCheck.java:489:9`, and the resulting one-error build failure. Tests were skipped, and earlier dependency metadata warnings did not terminate the build.

## 2. Physical Artifact Universe

### raw.log

- Full historical failed log retained: 619 lines.
- Original: 39,422 bytes; SHA-256 `c6a0b792dd547ae69aa7d2267b3cf35b634ead62aae8591f894189aee90edbdd`.
- Frozen normalized artifact: 38,662 bytes; SHA-256 `7b2f3c09d2c8af3f4f88be69f486895987c25e1059f8560c8daed821571d5da9`.
- Transformation: removed 206 ANSI CSI escape bytes; no line was removed, reordered, rewritten, or added.
- No failure-window trimming and no synthetic output.

### Repository snapshot

All six files are complete and byte-identical to the exact failing revision:

| Path | Bytes | SHA-256 | Investigation role |
|---|---:|---|---|
| `.travis.yml` | 11,985 | `a7306394…00023` | Real Checkstyle job, JDK and Maven command |
| `pom.xml` | 62,843 | `c337e534…b8cb` | Maven verify to Ant execution wiring |
| `config/ant-phase-verify.xml` | 2,055 | `e6480610…e1c12` | Checkstyle invocation, fileset and fatal property |
| `config/checkstyle_checks.xml` | 12,654 | `d02f7a94…839ed` | Real enabled checker configuration |
| `src/main/java/.../EqualsAvoidNullCheck.java` | 20,086 | `3f8af792…9d9ee` | Complete source named by the failure |
| `src/test/java/.../EqualsAvoidNullCheckTest.java` | 8,606 | `9dba5616…e9d9` | Natural paired test investigation path |

Repository total: 118,229 bytes. Physical evidence total is approximately 157 KB, bounded but materially broader than the Required Evidence subset.

## 3. Canonical Evidence design

Canonical JSON contains only stable IDs, physical source paths, 1-based inclusive line ranges, and exact resolved byte hashes. It contains no copied log/source text.

### Log units

Eleven source-structural units cover the complete retained log:

1. system information, lines 1–67
2. git clone and exact checkout, 68–362
3. job command/JDK setup, 363–400
4. Maven preamble and dependency warnings, 401–439
5. Maven generation stages, 440–504
6. Maven compilation, 505–529
7. Ant compilation phase, 530–542
8. test compilation, 543–554
9. skipped tests and package stages, 555–571
10. Checkstyle `ant-phase-verify` failure, 572–601
11. post-failure cache/final job result, 602–619

Only unit 10 is Required Evidence. Ten authentic log units are non-required investigation context.

### Repository units

All six Physical Repository files are now covered completely using a B04-local deterministic rule: start at line 1, use contiguous non-overlapping 100-line units, and allow only the final unit of each file to be shorter. No boundary depends on the failure line, fix, Required Evidence or curator judgment.

| File | Lines | Deterministic units |
|---|---:|---:|
| `.travis.yml` | 221 | 3 |
| `pom.xml` | 1,673 | 17 |
| `config/ant-phase-verify.xml` | 52 | 1 |
| `config/checkstyle_checks.xml` | 356 | 4 |
| `EqualsAvoidNullCheck.java` | 596 | 6 |
| `EqualsAvoidNullCheckTest.java` | 152 | 2 |
| **Total** | **3,050** | **33** |

Coverage validation confirms 3,050/3,050 lines covered with no gaps or overlaps. Every unit hash resolves from the exact frozen bytes. This 100-line rule is specific to B04 and is not a Formal Suite-wide chunk-size requirement.

## 4. Required Evidence Ground Truth

Required:

- `log:ci-lines-0572-0601:maven-antrun-verify`
- `repo:equals-avoid-null-check.java:lines-0401-0500`

Human-reviewed inclusion-minimality argument:

- Without the log unit, the repository shows a visibility pattern but does not establish the actual CI failure stage, checker finding, or fatal outcome.
- Without the deterministic repository unit, the log names a redundant modifier but does not expose the private nested-class context needed to explain why the modifier is redundant.

The Required set remains inclusion-minimal at Canonical Unit granularity: the log establishes the observed CI rejection, while the repository window supplies the source semantics needed for the causal explanation. Its cardinality and semantics are unchanged; only the curator-selected source span was replaced by the neutral 401–500 partition window.

Optional:

- `repo:ant-phase-verify.xml:lines-0001-0052`
- `repo:checkstyle-checks.xml:lines-0101-0200`

The remaining 29 repository units are not marked Required or Optional merely because they exist. They complete the neutral Canonical coordinate coverage over the same searchable Physical Repository Universe; they are not mandatory Runtime Retrieval chunks.

## 5. Diagnosis Ground Truth

- Primary: `lint_or_type_failure`
- Acceptable alternatives: none
- Summary: Maven verify fails in the Checkstyle-backed verify stage after one RedundantModifier violation.
- Root cause: private static nested `FieldFrame` declares a public constructor whose accessibility cannot meaningfully exceed the private enclosing class; the enabled static rule rejects the redundant modifier.
- Recommended action: align constructor visibility with the enclosing class and rerun Checkstyle verification.

Taxonomy checks:

- Not test assertion: tests are skipped.
- Not dependency/install: metadata warnings are nonfatal and compilation/package stages continue.
- Not config/environment: valid checker configuration runs and rejects real source semantics.
- Not timeout/flaky: artifact is recorded Reproducible 5/5.

## 6. Explicitly excluded curator-only material

- Passing revision and fix diff
- Commit-derived root-cause explanation
- Candidate ledger and research notes
- Expected Answer from the Agent-visible workspace
- Required/Optional labels from PublicCaseView
- Project Knowledge
- Oracle pack
- Replay or historical environment reconstruction
- Synthetic noise or failure output

## 7. Public-source attribution

- BugSwarm artifact: `checkstyle-checkstyle-77722324`; historical failed job `77722324`.
- Public failure source: `https://www.bugswarm.org/artifact-logs/77722324/raw/`.
- Exact upstream Checkstyle revision: `da6ebe6de41b7a5afc6f6746ff0c2382c2a4be0f`.
- Upstream Checkstyle license family: LGPL-2.1-or-later.
- No replay or synthetic replacement was used.

## 8. Sanitization review

- ANSI CSI removal is the only transformation.
- Secret/private-key scan found no credential material.
- `.travis.yml` contains no encrypted `secure:` values.
- Public paths, worker metadata, revision SHA, tool versions, timestamps and dependency warnings remain intact.
- Root cause and diagnostic structure are unchanged.

## 9. Leakage review

- Canonical IDs describe source identity, location or build stage; none contains `root-cause`, `bad-public-modifier`, `fix`, `required`, or scorer terminology.
- Repository snapshot contains no passing/fix content.
- `PublicCaseView` exposes only case identity, schema, fingerprint, raw-log path, repository root and forbidden actions.
- Evaluator and provenance metadata remain outside PublicCaseView.

Residual review point: the raw log itself says `Redundant 'public' modifier`, as the authentic checker output should. Correct diagnosis still requires locating the fatal stage and connecting it to the private nested-class source semantics.

## 10. Validation evidence

- Source fidelity: normalized source log independently regenerated and byte-compared with packaged `raw.log`; PASS.
- Six repository files byte-compared with exact-revision downloads; PASS.
- Repository manifest membership/size/hash: loader verified.
- Repository Canonical coverage: 33 units, 3,050/3,050 lines, no gaps or overlaps.
- Canonical source ownership, line ranges and exact-byte hashes: independently checked and loader verified.
- Physical repository directories are read-only during review to prevent macOS `.DS_Store` metadata from re-entering the strict manifest universe; the six declared files and their bytes are unchanged.
- Required/Optional references and separation: loader verified.
- Declared Case fingerprint: loader verified.
- Focused tests: `126 passed in 0.58s`.

Focused test files:

- `tests/test_issue_22_case_schema_v2.py`
- `tests/test_issue_6_evaluation_suite.py`
- `tests/test_issue_14_structured_report_scoring.py`

No Suite Manifest exists, so suite-level `eval doctor` and Suite fingerprint remain intentionally deferred.

## 11. Human Review outcome and remaining calibration boundary

Human Review accepted the complete 619-line log, six-file Physical Repository Universe, 11 log units, 33 deterministic repository units, two-item inclusion-minimal Required Evidence, Optional Evidence, Diagnosis Ground Truth, ANSI-only sanitization, public-source attribution, and calibration-package review metadata.

`Canonicalization Profile v1` remains unfrozen. B04's repository `N=100` and 11-unit log segmentation are calibration observations, not final suite-wide parameters. If the Profile later selects different algorithms or parameters, only Canonical coordinates, dependent Evidence IDs, and fingerprint are mechanically rebuilt and revalidated; the accepted Physical Universe and Ground Truth semantics remain unchanged.

## 12. Scope boundary confirmation

- Only B04 was constructed.
- No other Formal Case was created or modified.
- Old Schema V1 drafts were not modified or migrated.
- No Suite Manifest or Suite fingerprint was created.
- No upstream project, replay, Docker image, historical environment or synthetic reproduction was executed.
- No Runtime, Retriever, Oracle or Agent code was implemented.
