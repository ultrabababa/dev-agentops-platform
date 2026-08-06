import json
import shutil
from pathlib import Path

import pytest

from devagentops.cli import main
from devagentops.evaluation_suite import (
    EvaluationSuiteError,
    calculate_case_fingerprint,
    load_case_package,
)
from devagentops.scoring import evaluate_case_report
from devagentops.structured_report import (
    MIN_RECOMMENDED_ACTION_NON_WHITESPACE_CHARS,
)


FIXTURE_CASE_ROOT = (
    Path(__file__).parent
    / "fixtures/evaluation/cases/constructed-assertion-001"
)
FIXTURE_CASE = FIXTURE_CASE_ROOT / "case.json"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, document) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy_case(tmp_path: Path) -> Path:
    destination = tmp_path / "case-package"
    shutil.copytree(FIXTURE_CASE_ROOT, destination)
    return destination / "case.json"


def _refresh_case_fingerprint(case_path: Path) -> None:
    document = _read_json(case_path)
    document["case_fingerprint"] = calculate_case_fingerprint(case_path)
    _write_json(case_path, document)


def _valid_report(**overrides):
    report = {
        "schema_version": "1",
        "case_id": "constructed-assertion-001",
        "classification_status": "classified",
        "failure_type": "test_assertion_failure",
        "summary": "The calculation result contradicts the asserted total.",
        "root_cause": "The implementation multiplies values instead of adding them.",
        "recommended_action": "Review calculate_total and restore the required addition behavior.",
        "confidence": 0.95,
        "evidence_references": [
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "repo:calculate-total"},
        ],
    }
    report.update(overrides)
    return report


def _error_codes(result) -> list[str]:
    return [error.code for error in result.validation.errors]


def test_exact_report_returns_explicit_per_case_metric_vector():
    result = evaluate_case_report(_valid_report(), load_case_package(FIXTURE_CASE))

    assert result.validation.valid is True
    assert result.structured_report is not None
    assert result.quality_metrics.as_dict() == {
        "failure_type_exact_match": 1.0,
        "failure_type_reviewed_acceptable_match": 0.0,
        "report_evidence_hit_rate": 1.0,
        "required_fields_completeness": 1.0,
    }
    assert result.evidence_diagnostics.as_dict() == {
        "required_evidence_count": 2,
        "matched_required_evidence_count": 2,
        "unknown_evidence_count": 0,
        "duplicate_evidence_reference_count": 0,
    }


def test_reviewed_acceptable_match_is_separate_and_mutually_exclusive(
    tmp_path: Path,
):
    case_path = _copy_case(tmp_path)
    expected_path = case_path.parent / "expected-answer.json"
    expected = _read_json(expected_path)
    expected["acceptable_failure_types"] = ["config_or_environment_failure"]
    _write_json(expected_path, expected)
    _refresh_case_fingerprint(case_path)

    report = _valid_report(failure_type="config_or_environment_failure")
    result = evaluate_case_report(report, load_case_package(case_path))

    assert result.quality_metrics.failure_type_exact_match == 0.0
    assert result.quality_metrics.failure_type_reviewed_acceptable_match == 1.0


def test_expected_answer_rejects_primary_as_reviewed_acceptable(tmp_path: Path):
    case_path = _copy_case(tmp_path)
    expected_path = case_path.parent / "expected-answer.json"
    expected = _read_json(expected_path)
    expected["acceptable_failure_types"] = [expected["primary_failure_type"]]
    _write_json(expected_path, expected)

    with pytest.raises(
        EvaluationSuiteError,
        match="primary_failure_type must not appear in acceptable_failure_types",
    ):
        calculate_case_fingerprint(case_path)


def test_inconclusive_without_failure_type_is_valid_and_normalizes_to_none():
    report = _valid_report(classification_status="inconclusive")
    del report["failure_type"]

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is True
    assert result.structured_report is not None
    assert result.structured_report.failure_type is None
    assert result.quality_metrics.failure_type_exact_match == 0.0
    assert result.quality_metrics.failure_type_reviewed_acceptable_match == 0.0
    assert result.quality_metrics.required_fields_completeness == 1.0


@pytest.mark.parametrize(
    ("report", "expected_code"),
    [
        (
            _valid_report(classification_status="classified", failure_type=None),
            "null_failure_type_for_classified",
        ),
        (
            _valid_report(
                classification_status="inconclusive",
                failure_type="test_assertion_failure",
            ),
            "failure_type_not_allowed_for_inconclusive",
        ),
    ],
)
def test_classification_status_and_failure_type_condition_rules(report, expected_code):
    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert expected_code in _error_codes(result)
    assert result.quality_metrics.failure_type_exact_match == 0.0
    assert result.quality_metrics.failure_type_reviewed_acceptable_match == 0.0


def test_completeness_uses_eight_content_groups_without_rechecking_correctness():
    report = _valid_report(
        schema_version="999",
        failure_type="invented_failure_type",
        confidence=2.0,
        recommended_action="not empty",
        evidence_references=[{"evidence_id": "fake:evidence"}],
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert result.quality_metrics.required_fields_completeness == 1.0
    assert result.quality_metrics.failure_type_exact_match == 0.0
    assert result.quality_metrics.report_evidence_hit_rate == 0.0
    assert {
        "unknown_schema_version",
        "invalid_failure_type",
        "recommended_action_too_short",
        "confidence_out_of_range",
        "unknown_evidence_id",
    } <= set(_error_codes(result))


def test_missing_required_content_reduces_only_its_fixed_completeness_group():
    report = _valid_report(summary="   ")

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert result.quality_metrics.required_fields_completeness == 7 / 8
    assert result.quality_metrics.failure_type_exact_match == 1.0
    assert result.quality_metrics.report_evidence_hit_rate == 1.0


def test_unknown_schema_and_unknown_top_level_field_are_agent_report_failures():
    report = _valid_report(schema_version="2", unexpected="value")

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert _error_codes(result) == [
        "unknown_schema_version",
        "unknown_report_field",
    ]
    assert result.quality_metrics.failure_type_exact_match == 1.0
    assert result.quality_metrics.required_fields_completeness == 1.0


def test_case_id_mismatch_zeroes_case_dependent_metrics_but_not_completeness():
    result = evaluate_case_report(
        _valid_report(case_id="case-002"), load_case_package(FIXTURE_CASE)
    )

    assert result.validation.as_dict()["errors"][0] == {
        "code": "case_id_mismatch",
        "field": "case_id",
        "message": "Report case ID does not match the evaluated case",
        "expected": "constructed-assertion-001",
        "actual": "case-002",
    }
    assert result.quality_metrics.as_dict() == {
        "failure_type_exact_match": 0.0,
        "failure_type_reviewed_acceptable_match": 0.0,
        "report_evidence_hit_rate": 0.0,
        "required_fields_completeness": 1.0,
    }


def test_hallucinated_evidence_hard_zeroes_hit_but_keeps_count_diagnostics():
    report = _valid_report(
        evidence_references=[
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "fake:evidence"},
        ]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert result.quality_metrics.report_evidence_hit_rate == 0.0
    assert result.quality_metrics.required_fields_completeness == 1.0
    assert result.evidence_diagnostics.as_dict() == {
        "required_evidence_count": 2,
        "matched_required_evidence_count": 1,
        "unknown_evidence_count": 1,
        "duplicate_evidence_reference_count": 0,
    }
    error = next(
        error.as_dict()
        for error in result.validation.errors
        if error.code == "unknown_evidence_id"
    )
    assert error == {
        "code": "unknown_evidence_id",
        "field": "evidence_references[1].evidence_id",
        "actual": "fake:evidence",
        "message": "Evidence ID does not exist in the evaluated case",
    }


def test_duplicate_evidence_is_invalid_but_deduplicated_without_hard_zero():
    report = _valid_report(
        evidence_references=[
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "repo:calculate-total"},
        ]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert result.quality_metrics.report_evidence_hit_rate == 1.0
    assert result.evidence_diagnostics.matched_required_evidence_count == 2
    assert result.evidence_diagnostics.duplicate_evidence_reference_count == 1


def test_unknown_evidence_count_means_distinct_unknown_ids():
    report = _valid_report(
        evidence_references=[
            {"evidence_id": "fake:evidence"},
            {"evidence_id": "fake:evidence"},
        ]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert result.quality_metrics.report_evidence_hit_rate == 0.0
    assert result.evidence_diagnostics.unknown_evidence_count == 1
    assert result.evidence_diagnostics.duplicate_evidence_reference_count == 1


def test_optional_evidence_is_not_in_the_required_hit_denominator():
    report = _valid_report(
        evidence_references=[
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "repo:calculate-total"},
        ]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is True
    assert result.quality_metrics.report_evidence_hit_rate == 1.0
    assert result.evidence_diagnostics.required_evidence_count == 2


def test_partial_required_evidence_produces_fractional_hit():
    report = _valid_report(
        evidence_references=[{"evidence_id": "log:assertion-mismatch"}]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is True
    assert result.quality_metrics.report_evidence_hit_rate == 0.5


@pytest.mark.parametrize(
    ("references", "expected_code", "expected_hit"),
    [
        (
            ["log:assertion-mismatch"],
            "invalid_evidence_reference_type",
            0.0,
        ),
        (
            [
                {
                    "evidence_id": "log:assertion-mismatch",
                    "source_type": "log",
                }
            ],
            "unknown_evidence_reference_field",
            0.5,
        ),
    ],
)
def test_evidence_reference_shape_errors_preserve_parseable_diagnostics(
    references, expected_code, expected_hit
):
    result = evaluate_case_report(
        _valid_report(evidence_references=references),
        load_case_package(FIXTURE_CASE),
    )

    assert result.validation.valid is False
    assert expected_code in _error_codes(result)
    assert result.quality_metrics.report_evidence_hit_rate == expected_hit


def test_damaged_evidence_entry_does_not_erase_complete_required_evidence_hit():
    report = _valid_report(
        evidence_references=[
            {"evidence_id": "log:assertion-mismatch"},
            "damaged-reference",
            {"evidence_id": "repo:calculate-total"},
        ]
    )

    result = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    assert result.validation.valid is False
    assert "invalid_evidence_reference_type" in _error_codes(result)
    assert result.quality_metrics.report_evidence_hit_rate == 1.0
    assert result.evidence_diagnostics.matched_required_evidence_count == 2


@pytest.mark.parametrize(
    "confidence", [-0.01, 1.01, True, float("nan"), float("inf")]
)
def test_confidence_contract_rejects_bounds_and_boolean(confidence):
    result = evaluate_case_report(
        _valid_report(confidence=confidence), load_case_package(FIXTURE_CASE)
    )

    assert result.validation.valid is False
    assert result.quality_metrics.failure_type_exact_match == 1.0


def test_extreme_integer_confidence_returns_validation_error_instead_of_crashing():
    result = evaluate_case_report(
        _valid_report(confidence=10**10000), load_case_package(FIXTURE_CASE)
    )

    assert result.validation.valid is False
    error = next(
        error for error in result.validation.errors if error.field == "confidence"
    )
    assert error.code == "confidence_out_of_range"
    assert result.quality_metrics.failure_type_exact_match == 1.0
    assert result.quality_metrics.required_fields_completeness == 1.0


@pytest.mark.parametrize("references", [None, {}, "evidence", []])
def test_evidence_reference_container_without_minimum_content_is_incomplete(
    references,
):
    result = evaluate_case_report(
        _valid_report(evidence_references=references),
        load_case_package(FIXTURE_CASE),
    )

    assert result.validation.valid is False
    assert result.quality_metrics.report_evidence_hit_rate == 0.0
    assert result.quality_metrics.required_fields_completeness == 7 / 8


def test_recommended_action_threshold_is_public_and_language_neutral():
    assert MIN_RECOMMENDED_ACTION_NON_WHITESPACE_CHARS == 12

    failing = evaluate_case_report(
        _valid_report(recommended_action="修复它"), load_case_package(FIXTURE_CASE)
    )
    passing = evaluate_case_report(
        _valid_report(recommended_action="检查依赖声明并恢复缺失的软件包版本"),
        load_case_package(FIXTURE_CASE),
    )

    assert "recommended_action_too_short" in _error_codes(failing)
    assert failing.quality_metrics.required_fields_completeness == 1.0
    assert passing.validation.valid is True


def test_report_top_level_non_object_is_scored_as_agent_output_failure():
    result = evaluate_case_report([], load_case_package(FIXTURE_CASE))

    assert result.validation.as_dict() == {
        "valid": False,
        "errors": [
            {
                "code": "invalid_report_type",
                "field": "$",
                "message": "Structured Triage Report must be a JSON object",
                "expected": "object",
                "actual": "array",
            }
        ],
    }
    assert result.quality_metrics.as_dict() == {
        "failure_type_exact_match": 0.0,
        "failure_type_reviewed_acceptable_match": 0.0,
        "report_evidence_hit_rate": 0.0,
        "required_fields_completeness": 0.0,
    }


def test_validation_error_order_is_stable():
    report = {
        "schema_version": "2",
        "case_id": "wrong-case",
        "classification_status": "unknown",
        "failure_type": 7,
        "summary": "",
        "root_cause": "Known root cause",
        "recommended_action": "short",
        "confidence": 2,
        "evidence_references": [
            {"evidence_id": "fake:evidence", "z": 1, "a": 2}
        ],
        "z_extra": True,
        "a_extra": True,
    }

    first = evaluate_case_report(report, load_case_package(FIXTURE_CASE))
    second = evaluate_case_report(report, load_case_package(FIXTURE_CASE))

    first_errors = first.validation.as_dict()["errors"]
    assert first_errors == second.validation.as_dict()["errors"]
    assert [(error["code"], error["field"]) for error in first_errors] == [
        ("unknown_schema_version", "schema_version"),
        ("case_id_mismatch", "case_id"),
        ("invalid_classification_status", "classification_status"),
        ("invalid_field_type", "failure_type"),
        ("empty_required_field", "summary"),
        ("recommended_action_too_short", "recommended_action"),
        ("confidence_out_of_range", "confidence"),
        ("unknown_evidence_id", "evidence_references[0].evidence_id"),
        ("unknown_evidence_reference_field", "evidence_references[0].a"),
        ("unknown_evidence_reference_field", "evidence_references[0].z"),
        ("unknown_report_field", "a_extra"),
        ("unknown_report_field", "z_extra"),
    ]


def test_expected_answer_refactor_preserves_fixture_fingerprint_and_public_shape():
    package = load_case_package(FIXTURE_CASE)
    declared = _read_json(FIXTURE_CASE)["case_fingerprint"]

    assert package.case_fingerprint == declared
    assert calculate_case_fingerprint(FIXTURE_CASE) == declared
    assert "expected_answer" not in package.as_dict()
    assert "expected_answer" not in json.dumps(package.as_dict())


def test_public_result_contains_only_issue_14_outputs_and_no_expected_labels():
    package = load_case_package(FIXTURE_CASE)
    report = _valid_report(failure_type="config_or_environment_failure")

    payload = evaluate_case_report(report, package).as_dict()
    encoded = json.dumps(payload, sort_keys=True)

    assert set(payload) == {
        "validation",
        "quality_metrics",
        "evidence_diagnostics",
    }
    for excluded in (
        "retrieval",
        "tool_path",
        "aggregation",
        "quality_gate",
        "leaderboard",
        "badcase",
        "primary_failure_type",
        "acceptable_failure_types",
        "required_evidence_ids",
        "optional_evidence_ids",
    ):
        assert excluded not in encoded
    assert package.expected_answer.summary not in encoded
    assert package.expected_answer.root_cause not in encoded
    assert package.expected_answer.recommended_action not in encoded


def test_cli_returns_zero_for_legal_json_contract_failures(tmp_path: Path, capsys):
    report_path = tmp_path / "report.json"
    _write_json(report_path, _valid_report(schema_version="2"))

    assert (
        main(
            [
                "eval",
                "score",
                "--case",
                str(FIXTURE_CASE),
                "--report",
                str(report_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["validation"]["valid"] is False
    assert payload["quality_metrics"]["failure_type_exact_match"] == 1.0


def test_cli_scores_legal_json_with_extreme_integer_confidence(tmp_path: Path, capsys):
    report_path = tmp_path / "report.json"
    encoded = json.dumps(_valid_report(confidence="EXTREME_INTEGER"))
    encoded = encoded.replace('"EXTREME_INTEGER"', "1" + "0" * 10000)
    report_path.write_text(encoded, encoding="utf-8")

    assert (
        main(
            [
                "eval",
                "score",
                "--case",
                str(FIXTURE_CASE),
                "--report",
                str(report_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    confidence_error = next(
        error
        for error in payload["validation"]["errors"]
        if error["field"] == "confidence"
    )
    assert confidence_error["code"] == "confidence_out_of_range"
    assert confidence_error["actual"] == {
        "type": "number",
        "significant_digits": 10001,
        "exponent": 0,
    }


@pytest.mark.parametrize("report_document", [[], "report", 7])
def test_cli_returns_zero_when_legal_json_top_level_is_not_object(
    report_document, tmp_path: Path, capsys
):
    report_path = tmp_path / "report.json"
    _write_json(report_path, report_document)

    assert (
        main(
            [
                "eval",
                "score",
                "--case",
                str(FIXTURE_CASE),
                "--report",
                str(report_path),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["validation"]["errors"][0]["code"] == "invalid_report_type"


@pytest.mark.parametrize("failure", ["missing_report", "invalid_json", "missing_case"])
def test_cli_returns_two_only_when_scoring_cannot_start(
    failure: str, tmp_path: Path, capsys
):
    report_path = tmp_path / "report.json"
    case_path = FIXTURE_CASE
    if failure == "missing_report":
        report_path = tmp_path / "missing.json"
    elif failure == "invalid_json":
        report_path.write_text("{not-json", encoding="utf-8")
    else:
        _write_json(report_path, _valid_report())
        case_path = tmp_path / "missing-case.json"

    assert (
        main(
            [
                "eval",
                "score",
                "--case",
                str(case_path),
                "--report",
                str(report_path),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]
