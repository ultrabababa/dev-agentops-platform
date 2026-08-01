import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_DOC = ROOT / "docs" / "evaluation" / "v1-failure-type-taxonomy-and-case-policy.md"
EXPECTED_FAILURE_TYPES = {
    "test_assertion_failure": "Test Assertion Failure",
    "lint_or_type_failure": "Lint or Type Failure",
    "dependency_or_install_failure": "Dependency or Install Failure",
    "config_or_environment_failure": "Config or Environment Failure",
    "timeout_or_flaky_failure": "Timeout or Flaky Failure",
}


class Issue2DocumentationTest(unittest.TestCase):
    def test_v1_failure_type_taxonomy_documents_accepted_ids_and_names(self):
        markdown = POLICY_DOC.read_text(encoding="utf-8")

        for failure_type_id, display_name in EXPECTED_FAILURE_TYPES.items():
            with self.subTest(failure_type_id=failure_type_id):
                self.assertRegex(
                    markdown,
                    rf"\|\s*`{re.escape(failure_type_id)}`\s*\|\s*{re.escape(display_name)}\s*\|",
                )

    def test_failure_type_mapping_documents_report_and_expected_answer_fields(self):
        markdown = POLICY_DOC.read_text(encoding="utf-8")

        required_fields = [
            "structured_triage_report.failure_type",
            "expected_answer.primary_failure_type",
            "expected_answer.acceptable_failure_types",
        ]

        self.assertIn("## Mapping to Structured Reports and Expected Answers", markdown)
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", markdown)

    def test_classification_is_separated_from_failure_stage_and_causal_analysis(self):
        markdown = POLICY_DOC.read_text(encoding="utf-8")

        required_concepts = [
            "## Classification and Causal Analysis",
            "`failure_stage`",
            "`symptom`",
            "`immediate_cause`",
            "`root_cause`",
            "`triggering_change`",
            "`classification_status`",
            "`inconclusive`",
        ]

        for concept in required_concepts:
            with self.subTest(concept=concept):
                self.assertIn(concept, markdown)

        self.assertIn("not V1 Failure Type values", markdown)
        self.assertIn("must not be represented as a Failure Type", markdown)

    def test_offline_case_policy_documents_source_rules_and_manifest_metadata(self):
        markdown = POLICY_DOC.read_text(encoding="utf-8")

        required_manifest_fields = [
            "case_id",
            "case_schema_version",
            "source_type",
            "source_url_or_construction_note",
            "license_or_permission",
            "created_by",
            "reviewed_by",
            "sanitization_status",
            "case_fingerprint",
        ]

        self.assertIn("## Offline Case Provenance and Sanitization Policy", markdown)
        self.assertIn("`constructed`", markdown)
        self.assertIn("`public_permitted_source`", markdown)
        for field in required_manifest_fields:
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", markdown)

    def test_initial_balanced_suite_target_documents_counts_by_failure_type(self):
        markdown = POLICY_DOC.read_text(encoding="utf-8")

        self.assertIn("## Initial Balanced Suite Composition Target", markdown)
        self.assertIn("Total target: 20 offline cases", markdown)
        for failure_type_id in EXPECTED_FAILURE_TYPES:
            with self.subTest(failure_type_id=failure_type_id):
                self.assertRegex(
                    markdown,
                    rf"\|\s*`{re.escape(failure_type_id)}`\s*\|\s*4\s*\|",
                )


if __name__ == "__main__":
    unittest.main()
