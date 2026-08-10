# B02 — bugswarm-apache-struts-190697114 pre-freeze draft review

**Status:** `DRAFT_READY`; package-content Human Review `PENDING`
**Failure type:** `test_assertion_failure`
**Fingerprint:** `0335e68f104d4c83010afa9a009563e1c61abfd83cc795ca13a0f02d8947baac` (`provisional-pre-freeze`)

## Source and authentic failure observation

- Source: https://www.bugswarm.org/artifact-logs/190697114/raw/ ; upstream exact/relevant revision: https://github.com/apache/struts/commit/880c4c2d33f67c28a834a44da5a2523b858601b3
- Attribution/license note: Apache-2.0 upstream repository; public BugSwarm historical failed-job attribution.
- raw.log: Complete BugSwarm historical failed-job log with ANSI/control-only normalization.

## Physical repository universe

Exact/relevant revision `880c4c2d33f67c28a834a44da5a2523b858601b3` with 6 bounded investigation files:

- `core/pom.xml`
- `core/src/main/java/org/apache/struts2/interceptor/FileUploadInterceptor.java`
- `core/src/main/resources/org/apache/struts2/struts-messages.properties`
- `core/src/main/resources/org/apache/struts2/struts-messages_en.properties`
- `core/src/test/java/org/apache/struts2/interceptor/FileUploadInterceptorTest.java`
- `pom.xml`

The snapshot contains plausible build/test/config neighbors, not passing/fix artifacts or synthetic distractors.

## Causal chain and taxonomy

- Failure observation: The Struts core suite has one failing file-upload assertion amid many expected error-level test messages.
- Root cause: The test oracle expects the misspelled prefix 'The file is to large', while the English upload message produced by the failing revision says 'The file is too large'. The product message and assertion text are out of sync.
- Primary type: `test_assertion_failure` because the root cause, rather than only the surface stage, matches this V1 class.
- Recommended action: Synchronize the stale expected warning text with the actual English upload message and keep the unrelated parser/security-test errors as non-fatal test output.

## Evidence Ground Truth draft

- Required (3): `log:raw-log:lines-20601-20700`, `repo:core-src-test-java-org-apache-struts2-interceptor-fileuploadinterceptortest-java:lines-0201-0300`, `repo:core-src-main-resources-org-apache-struts2-struts-messages-en-properties:lines-0001-0044`
- Optional (1): `log:raw-log:lines-20501-20600`
- Rationale: Required IDs are the current inclusion-minimal cross-log/repository facts; helpful corroboration remains Optional. IDs are provisional and must be remapped after Profile v1 freeze.

## Leakage, sanitization, and ambiguity

- Passing/fix revisions and curator causal research are excluded from Physical Artifacts.
- PublicCaseView exposes no evaluator data; package validation includes exact hashes, membership, and references.
- Sanitization: Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation without changing failure semantics.
- Known scientific risk: Medium: a very large authentic log contains many fatal/error distractors; the terminal summary names the victim but suppresses the assertion message.
- Canonicalization: fixed 100-line, start-at-1, full-coverage windows are disposable `provisional-pre-freeze` coordinates, not a frozen Suite rule.
