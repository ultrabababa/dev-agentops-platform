# V1 Failure Type Taxonomy and Offline Case Policy

## Status

Accepted for V1.

## Scope

V1 covers CI/Test Failure Triage and reporting only. A triage run classifies the failure, cites evidence, explains the likely root cause, and recommends the next action. It does not edit code, rerun CI, create pull requests, deploy, or perform other remediation actions.

## Failure Type Taxonomy

| Failure type ID                 | Display name                  | Definition                                                                                                                                            | Examples                                                                                                       | Do not use for                                                                                   |
| ------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `test_assertion_failure`        | Test Assertion Failure        | A test completed and failed because expected behavior did not match observed behavior.                                                                | Unit, integration, or snapshot assertion mismatch; expected exception was not raised.                          | Static checks, dependency installation, missing configuration, or intermittent timeouts.         |
| `lint_or_type_failure`          | Lint or Type Failure          | Static analysis rejected source formatting, lint rules, or type correctness before product behavior was executed.                                     | TypeScript type error; Python type checker failure; formatter or linter rule violation.                        | Runtime test assertions or package installation failures.                                        |
| `dependency_or_install_failure` | Dependency or Install Failure | The job failed because dependencies were missing, incompatible, unavailable, or incorrectly installed.                                                | Package resolver conflict; missing lockfile entry; native package build failure; registry package unavailable. | Invalid application configuration or missing secrets after dependencies install successfully.    |
| `config_or_environment_failure` | Config or Environment Failure | Required configuration, environment variables, secrets, paths, service endpoints, or runtime settings were missing, invalid, or inconsistent.         | Missing env var; invalid config file; wrong working directory; unavailable configured test service.            | Dependency resolution problems or nondeterministic test timing.                                  |
| `timeout_or_flaky_failure`      | Timeout or Flaky Failure      | The failure is characterized by nondeterminism, excessive duration, race behavior, or intermittent behavior without a stable product-code root cause. | Test timeout; retry passes; order-dependent test; race-prone async wait.                                       | Stable assertion failures, static failures, dependency failures, or deterministic config errors. |

## Mapping to Structured Reports and Expected Answers

When populated, the `structured_triage_report.failure_type` field must use one of the V1 failure type IDs from the taxonomy table. The report can explain nuance in root cause, recommended action, confidence, and evidence fields, but it must not invent additional failure type values.

The `expected_answer.primary_failure_type` field stores the single preferred V1 failure type ID for scoring failure type exact accuracy. The `expected_answer.acceptable_failure_types` field may list rare reviewer-approved alternatives for ambiguous cases; these alternatives are not synonyms and should be used only when the case evidence reasonably supports more than one taxonomy category.

In Offline Case Schema V2, `evaluator/required-evidence.json` is the sole Evidence Ground Truth and its `required_evidence_ids` must identify a Human-reviewed Minimal Sufficient Evidence Set. `evaluator/expected-answer.json` remains Diagnosis Ground Truth and must not duplicate the evidence selection. The complete required set contains the source facts needed to derive the Expected Diagnosis under the fixed diagnosis contract, while removing any item makes at least one necessary fact or disambiguation unavailable. Required Evidence must resolve through Canonical Evidence source spans to source-faithful Physical Artifacts and must not encode the Failure Type, Root Cause, Fix, Tool Path, scorer label, or curator reasoning as evaluator-authored annotations. This principle strengthens Case review; it does not add Oracle execution or Gap Analysis to the Formal Suite curation scope. The V2-only Loader enforces this artifact split and no longer accepts Schema V1.

## Classification and Causal Analysis

The V1 Failure Type is a stable evaluation category, not a complete causal model. A Structured Triage Report should keep the classification separate from the stage where the failure surfaced and from the causal explanation:

| Field | Question answered | Example |
| --- | --- | --- |
| `failure_stage` | Where did the failure surface? | `test_collection` |
| `symptom` | What externally observable failure occurred? | `pytest collection failed` |
| `immediate_cause` | What directly caused the failing command or step? | `application module import failed` |
| `root_cause` | Why did the immediate cause exist? | `a required package was absent from the project dependencies` |
| `triggering_change` | What change introduced or exposed the root cause, when supported by evidence? | `the dependency was removed from pyproject.toml` |
| `failure_type` | Which stable V1 evaluation category best describes the case? | `dependency_or_install_failure` |

Stage or symptom labels such as `BUILD_FAILURE` and `TEST_COLLECTION_FAILURE` are not V1 Failure Type values. A build or collection step can fail because of dependencies, configuration, static code problems, or other causes, so promoting these surface stages into the same flat enum would make labels overlap.

Uncertainty is also separate from failure classification. The report uses `classification_status` to state whether the available evidence supports a classification. When the evidence is insufficient, the report should use `inconclusive`; `UNKNOWN` must not be represented as a Failure Type. In that state, `failure_type` may be absent or null under the versioned Structured Triage Report Schema, and evaluation may score the classification as a miss without forcing an unsupported claim.

V1 does not freeze a separate `failure_stage` enum in this policy. The Structured Triage Report Schema may define stage values independently without changing the five-type suite distribution. New Failure Types should be introduced only through a new taxonomy and Evaluation Suite Version when reviewed formal badcases show that the existing categories are insufficient.

## Offline Case Provenance and Sanitization Policy

V1 formal evaluation uses Offline Case Packages only. A case can enter a formal suite when its `source_type` is one of:

- `constructed`: deliberately authored for DevAgentOps from synthetic repository snippets, synthetic logs, or public examples rewritten into a safe standalone case.
- `public_permitted_source`: derived from a public source whose license, terms, or explicit permission allow this use.

Raw production logs, private CI outputs, private repository snapshots, customer data, internal-only URLs, and copied third-party artifacts without permission are not accepted for V1 formal suites.

Formal Case construction must preserve an authentic, frozen, bounded-but-realistic Evidence Universe rather than reducing the Agent-visible corpus to the curator-known Required Evidence subset. Natural neighboring information and distractors are allowed and often necessary to measure evidence localization. Constructed Cases remain valid, but curators must not append synthetic irrelevant noise solely to manufacture difficulty. Detailed universe, canonical-unit, and runtime-access semantics are defined in [Formal Evaluation Methodology：Evidence Universe 与 Access Conditions](formal-evaluation-methodology.md).

For the first Formal Suite, that Evidence Universe contains only the complete or naturally bounded raw log and the bounded exact-revision repository snapshot declared by Schema V2. Project Knowledge remains a general or future independently controlled runtime/retrieval input, not a Case Physical Artifact. The five Batch-1 Schema V1 packages remain calibration drafts only and must not be Human-frozen or extended under V1. B04 has passed Schema V2 Human Review; calibrate and Human-freeze the shared `Canonicalization Profile v1` before scaling Formal Case construction.

Each offline case manifest must include:

| Manifest field | Requirement |
| --- | --- |
| `case_id` | Stable case identifier unique within the suite. |
| `case_schema_version` | Offline Case Schema version used by the package. |
| `source_type` | Either `constructed` or `public_permitted_source`. |
| `source_url_or_construction_note` | Public URL for permitted sources, or a concise construction note for constructed cases. |
| `license_or_permission` | License, terms, permission note, or `project_constructed` for constructed cases. |
| `created_by` | Person or agent that assembled the case package. |
| `reviewed_by` | Human reviewer that accepted the case for formal evaluation. |
| `sanitization_status` | Must be `reviewed_sanitized` before formal evaluation. |
| `case_fingerprint` | Stable content identity for the frozen case package. |

Sanitization review covers raw logs, the manifest-declared repository snapshot, Canonical Evidence coordinates, Evidence Ground Truth, and Expected Answers. Review must remove or replace secrets, tokens, personal data, private hostnames, private repository names, customer identifiers, and internal-only URLs.

## Initial Balanced Suite Composition Target

Total target: 20 offline cases.

This target is accepted as sufficient for the first evaluation foundation because it covers the five V1 core failure types evenly while keeping expected-answer review, evidence review, and badcase analysis small enough to complete before the full evaluation pipeline hardens.

| Failure type ID | Target case count | Initial coverage goal |
| --- | --- | --- |
| `test_assertion_failure` | 4 | Cover stable assertion mismatches across unit or integration-style tests. |
| `lint_or_type_failure` | 4 | Cover static rejection before runtime behavior is exercised. |
| `dependency_or_install_failure` | 4 | Cover resolver, install, and package availability failures. |
| `config_or_environment_failure` | 4 | Cover missing or invalid configuration, paths, env vars, and service settings. |
| `timeout_or_flaky_failure` | 4 | Cover nondeterministic, timing, retry, and timeout patterns. |

All V1 cases use equal case weighting in the initial suite. Expanding beyond 20 cases or changing the distribution should create a new Evaluation Suite Version rather than mutating the accepted V1 suite target.
