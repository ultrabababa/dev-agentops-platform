import json
import shutil
from pathlib import Path

import pytest

from devagentops.cli import main
from devagentops.component_registry import freeze_component
from devagentops.evaluation_suite import (
    EvaluationSuiteError,
    calculate_case_fingerprint,
    calculate_suite_fingerprint,
    load_evaluation_suite,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "evaluation"
FIXTURE_SUITE = FIXTURE_ROOT / "tiny-suite.json"
CASE_RELATIVE_PATH = Path("cases/constructed-assertion-001/case.json")


def _copy_fixture(tmp_path: Path) -> Path:
    destination = tmp_path / "evaluation"
    shutil.copytree(FIXTURE_ROOT, destination)
    return destination / "tiny-suite.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_matrix(path: Path, *, suite_id: str = "tiny-loader-fixture-v2") -> None:
    _write_json(
        path,
        {
            "matrix_id": "issue-6-test",
            "matrix_version": "1",
            "schema_version": "1",
            "conditions": [
                {
                    "id": "pipeline-anchor-v1",
                    "type": "anchor",
                    "runtime_variant": "pipeline",
                    "suite": suite_id,
                    "evaluation_method": "triage-method-v1",
                    "model": {"provider": "test", "name": "fake-model"},
                    "components": {"prompt": "triage-prompt-v1"},
                    "budgets": {"max_steps": 1, "max_tokens": 256},
                    "repeats": 1,
                }
            ],
        },
    )


def _write_registry(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "draft-prompt.json"
    _write_json(
        manifest_path,
        {
            "schema_version": "1",
            "component_type": "prompt",
            "behavior": {"template": "Diagnose {log}"},
        },
    )
    registry_path = tmp_path / "components" / "registry.json"
    freeze_component(manifest_path, registry_path, "triage-prompt-v1")
    return registry_path


def _formal_doctor_command(
    matrix_path: Path,
    registry_path: Path,
    suite_path: Path,
) -> list[str]:
    return [
        "eval",
        "doctor",
        "--matrix",
        str(matrix_path),
        "--registry",
        str(registry_path),
        "--suite",
        str(suite_path),
    ]


def test_loads_tiny_explicit_fixture_suite_without_directory_scanning(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    ignored = suite_path.parent / "cases" / "draft-invalid-case.json"
    ignored.write_text("not JSON", encoding="utf-8")

    suite = load_evaluation_suite(suite_path)

    assert suite.suite_id == "tiny-loader-fixture-v2"
    assert suite.suite_version == "2"
    assert len(suite.cases) == 1
    assert suite.cases[0].case_id == "constructed-assertion-001"
    assert suite.cases[0].weight == 1
    assert len(suite.cases[0].package.evidence_ids) == 3
    assert len(suite.cases[0].package.case_fingerprint) == 64
    assert len(suite.suite_fingerprint) == 64


def test_json_formatting_and_normalized_relative_paths_do_not_change_fingerprints(
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    original = load_evaluation_suite(suite_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    case_document["artifacts"]["raw_log"] = "./physical-artifacts/raw.log"
    _write_json(case_path, case_document)
    suite_document = _read_json(suite_path)
    suite_document["cases"][0]["manifest"] = (
        "./cases/constructed-assertion-001/case.json"
    )
    _write_json(suite_path, suite_document)
    evidence_path = case_path.parent / "physical-artifacts/repository-manifest.json"
    evidence_document = _read_json(evidence_path)
    evidence_document["files"][0]["path"] = "./tests/test_total.py"
    _write_json(evidence_path, evidence_document)
    for json_path in suite_path.parent.rglob("*.json"):
        document = _read_json(json_path)
        json_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=6),
            encoding="utf-8",
        )

    reformatted = load_evaluation_suite(suite_path)

    assert reformatted.cases[0].package.case_fingerprint == (
        original.cases[0].package.case_fingerprint
    )
    assert reformatted.suite_fingerprint == original.suite_fingerprint


def test_declared_case_and_suite_fingerprints_do_not_participate_in_own_calculation(
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    original = load_evaluation_suite(suite_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    case_document["case_fingerprint"] = "f" * 64
    _write_json(case_path, case_document)
    suite_document = _read_json(suite_path)
    suite_document["suite_fingerprint"] = "f" * 64
    _write_json(suite_path, suite_document)

    assert calculate_case_fingerprint(case_path) == (
        original.cases[0].package.case_fingerprint
    )
    case_document["case_fingerprint"] = original.cases[0].package.case_fingerprint
    _write_json(case_path, case_document)
    assert calculate_suite_fingerprint(suite_path) == original.suite_fingerprint


@pytest.mark.parametrize(
    ("relative_path", "mutate"),
    [
        (
            Path("cases/constructed-assertion-001/physical-artifacts/raw.log"),
            lambda text: text + "drift\n",
        ),
        (
            Path("cases/constructed-assertion-001/evaluator/expected-answer.json"),
            lambda document: {**document, "summary": "Changed scoring semantics."},
        ),
        (
            CASE_RELATIVE_PATH,
            lambda document: {
                **document,
                "forbidden_actions": [*document["forbidden_actions"], "run_tests"],
            },
        ),
        (
            CASE_RELATIVE_PATH,
            lambda document: {
                **document,
                "provenance": {
                    **document["provenance"],
                    "source_url_or_construction_note": "Changed construction provenance.",
                },
            },
        ),
    ],
)
def test_behavior_or_eligibility_changes_change_case_fingerprint(
    relative_path: Path,
    mutate,
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    original_fingerprint = calculate_case_fingerprint(case_path)
    target = suite_path.parent / relative_path
    if target.suffix == ".json":
        _write_json(target, mutate(_read_json(target)))
    else:
        target.write_text(mutate(target.read_text(encoding="utf-8")), encoding="utf-8")

    assert calculate_case_fingerprint(case_path) != original_fingerprint
    with pytest.raises(EvaluationSuiteError, match="fingerprint changed"):
        load_evaluation_suite(suite_path)


def test_suite_fingerprint_uses_recomputed_verified_case_fingerprint(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    original = load_evaluation_suite(suite_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    raw_log_path = case_path.parent / "physical-artifacts/raw.log"
    raw_log_path.write_text(
        raw_log_path.read_text(encoding="utf-8") + "changed input\n",
        encoding="utf-8",
    )
    case_document = _read_json(case_path)
    case_document["case_fingerprint"] = calculate_case_fingerprint(case_path)
    _write_json(case_path, case_document)

    changed_suite_fingerprint = calculate_suite_fingerprint(suite_path)

    assert changed_suite_fingerprint != original.suite_fingerprint
    with pytest.raises(EvaluationSuiteError, match="suite .* fingerprint changed"):
        load_evaluation_suite(suite_path)


@pytest.mark.parametrize("unsafe_path", ["../raw.log", "/tmp/raw.log", "..\\raw.log"])
def test_case_artifact_paths_reject_absolute_or_escape_paths(
    unsafe_path: str,
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    case_document["artifacts"]["raw_log"] = unsafe_path
    _write_json(case_path, case_document)

    with pytest.raises(EvaluationSuiteError, match="relative path|POSIX"):
        calculate_case_fingerprint(case_path)


@pytest.mark.parametrize(
    "unsafe_path", ["../outside-case.json", "/tmp/case.json", "..\\case.json"]
)
def test_suite_case_paths_reject_absolute_or_escape_paths(
    unsafe_path: str,
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    suite_document = _read_json(suite_path)
    suite_document["cases"][0]["manifest"] = unsafe_path
    _write_json(suite_path, suite_document)

    with pytest.raises(EvaluationSuiteError, match="relative path|POSIX"):
        calculate_suite_fingerprint(suite_path)


def test_case_artifact_symlink_cannot_escape_package(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    raw_log_path = case_path.parent / "physical-artifacts/raw.log"
    outside_log = tmp_path / "outside.log"
    outside_log.write_text("outside package", encoding="utf-8")
    raw_log_path.unlink()
    raw_log_path.symlink_to(outside_log)

    with pytest.raises(EvaluationSuiteError, match="outside its package"):
        calculate_case_fingerprint(case_path)


def test_loader_rejects_missing_provenance(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    del case_document["provenance"]
    _write_json(case_path, case_document)

    with pytest.raises(EvaluationSuiteError, match="provenance"):
        load_evaluation_suite(suite_path)


def test_loader_rejects_unsanitized_case(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    case_document["sanitization"]["status"] = "pending_review"
    _write_json(case_path, case_document)

    with pytest.raises(EvaluationSuiteError, match="sanitization has unsupported status"):
        load_evaluation_suite(suite_path)


def test_loader_rejects_invalid_evidence_reference(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    expected_path = (
        suite_path.parent
        / "cases/constructed-assertion-001/evaluator/required-evidence.json"
    )
    expected = _read_json(expected_path)
    expected["required_evidence_ids"].append("repo:missing")
    _write_json(expected_path, expected)

    with pytest.raises(EvaluationSuiteError, match="unknown Canonical Evidence ID"):
        load_evaluation_suite(suite_path)


def test_loader_rejects_duplicate_stable_evidence_ids_within_artifact(
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    evidence_path = (
        suite_path.parent
        / "cases/constructed-assertion-001/canonical-evidence/repository-units.json"
    )
    evidence = _read_json(evidence_path)
    evidence["units"][1]["evidence_id"] = evidence["units"][0]["evidence_id"]
    _write_json(evidence_path, evidence)

    with pytest.raises(EvaluationSuiteError, match="duplicate evidence IDs"):
        load_evaluation_suite(suite_path)


@pytest.mark.parametrize(
    ("target", "field", "message"),
    [
        ("suite", "schema_version", "unsupported suite schema version"),
        ("case", "case_schema_version", "unsupported Offline Case Schema version"),
        (
            "repository_manifest",
            "schema_version",
            "unsupported repository manifest schema version",
        ),
        (
            "log_units",
            "schema_version",
            "unsupported canonical log evidence schema version",
        ),
        (
            "repository_units",
            "schema_version",
            "unsupported canonical repo evidence schema version",
        ),
        (
            "required_evidence",
            "schema_version",
            "unsupported evidence ground truth schema version",
        ),
        (
            "expected",
            "schema_version",
            "unsupported expected answer schema version",
        ),
    ],
)
def test_loader_rejects_unknown_schema_versions(
    target: str,
    field: str,
    message: str,
    tmp_path: Path,
):
    suite_path = _copy_fixture(tmp_path)
    case_root = (suite_path.parent / CASE_RELATIVE_PATH).parent
    target_path = {
        "suite": suite_path,
        "case": suite_path.parent / CASE_RELATIVE_PATH,
        "repository_manifest": case_root / "physical-artifacts/repository-manifest.json",
        "log_units": case_root / "canonical-evidence/log-units.json",
        "repository_units": case_root / "canonical-evidence/repository-units.json",
        "required_evidence": case_root / "evaluator/required-evidence.json",
        "expected": case_root / "evaluator/expected-answer.json",
    }[target]
    document = _read_json(target_path)
    document[field] = "999"
    _write_json(target_path, document)

    with pytest.raises(EvaluationSuiteError, match=message):
        load_evaluation_suite(suite_path)


def test_suite_manifest_requires_explicit_case_weight(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    suite_document = _read_json(suite_path)
    del suite_document["cases"][0]["weight"]
    _write_json(suite_path, suite_document)

    with pytest.raises(EvaluationSuiteError, match="weight"):
        load_evaluation_suite(suite_path)


def test_loader_rejects_changed_case_or_suite_fingerprint(tmp_path: Path):
    suite_path = _copy_fixture(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH
    case_document = _read_json(case_path)
    case_document["case_fingerprint"] = "0" * 64
    _write_json(case_path, case_document)
    with pytest.raises(EvaluationSuiteError, match="case .* fingerprint changed"):
        load_evaluation_suite(suite_path)

    suite_path = _copy_fixture(tmp_path / "suite-drift")
    suite_document = _read_json(suite_path)
    suite_document["suite_fingerprint"] = "0" * 64
    _write_json(suite_path, suite_document)
    with pytest.raises(EvaluationSuiteError, match="suite .* fingerprint changed"):
        load_evaluation_suite(suite_path)


def test_eval_doctor_modes_are_explicit_and_mutually_exclusive(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "matrix.json"
    _write_matrix(matrix_path)
    registry_path = tmp_path / "unused-registry.json"

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2
    assert "requires both --registry and --suite" in json.loads(
        capsys.readouterr().err
    )["error"]

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--suite",
                str(FIXTURE_SUITE),
            ]
        )
        == 2
    )
    assert "requires both --registry and --suite" in json.loads(
        capsys.readouterr().err
    )["error"]

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
            ]
        )
        == 2
    )
    assert "requires both --registry and --suite" in json.loads(
        capsys.readouterr().err
    )["error"]

    assert (
        main(
            [
                "eval",
                "doctor",
                "--structural-only",
                "--matrix",
                str(matrix_path),
                "--suite",
                str(FIXTURE_SUITE),
            ]
        )
        == 2
    )
    assert "validates only the Evaluation Matrix" in json.loads(
        capsys.readouterr().err
    )["error"]

    assert (
        main(
            [
                "eval",
                "doctor",
                "--structural-only",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
                "--suite",
                str(FIXTURE_SUITE),
            ]
        )
        == 2
    )
    assert "validates only the Evaluation Matrix" in json.loads(
        capsys.readouterr().err
    )["error"]

    assert (
        main(
            [
                "eval",
                "doctor",
                "--structural-only",
                "--matrix",
                str(matrix_path),
            ]
        )
        == 0
    )
    structural = json.loads(capsys.readouterr().out)
    assert "evaluation_suite" not in structural
    assert "component_fingerprints" not in structural["conditions"][0]


def test_formal_eval_doctor_validates_matrix_components_suite_and_cases(
    tmp_path: Path,
    capsys,
):
    suite_path = _copy_fixture(tmp_path)
    matrix_path = tmp_path / "matrix.json"
    _write_matrix(matrix_path)
    registry_path = _write_registry(tmp_path)

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
                "--suite",
                str(suite_path),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["conditions"][0]["component_fingerprints"]["prompt"]
    assert payload["evaluation_suite"]["suite_id"] == "tiny-loader-fixture-v2"
    assert payload["evaluation_suite"]["cases"][0]["case_fingerprint"]


@pytest.mark.parametrize(
    "invalid_case",
    [
        "missing_provenance",
        "unsanitized",
        "invalid_evidence",
        "fingerprint_drift",
        "malformed_source_type",
        "malformed_primary_failure_type",
    ],
)
def test_formal_eval_doctor_returns_redacted_stable_errors_for_invalid_cases(
    invalid_case: str,
    tmp_path: Path,
    capsys,
):
    suite_path = _copy_fixture(tmp_path)
    matrix_path = tmp_path / "matrix.json"
    _write_matrix(matrix_path)
    registry_path = _write_registry(tmp_path)
    case_path = suite_path.parent / CASE_RELATIVE_PATH

    if invalid_case in {
        "missing_provenance",
        "unsanitized",
        "malformed_source_type",
    }:
        case_document = _read_json(case_path)
        if invalid_case == "missing_provenance":
            del case_document["provenance"]
        elif invalid_case == "unsanitized":
            case_document["sanitization"]["status"] = "pending_review"
        else:
            case_document["provenance"]["source_type"] = []
        _write_json(case_path, case_document)
    elif invalid_case in {"invalid_evidence", "malformed_primary_failure_type"}:
        expected_path = case_path.parent / (
            "evaluator/required-evidence.json"
            if invalid_case == "invalid_evidence"
            else "evaluator/expected-answer.json"
        )
        expected = _read_json(expected_path)
        if invalid_case == "invalid_evidence":
            expected["required_evidence_ids"].append("repo:missing")
        else:
            expected["primary_failure_type"] = {}
        _write_json(expected_path, expected)
    else:
        raw_log_path = case_path.parent / "physical-artifacts/raw.log"
        raw_log_path.write_text(
            raw_log_path.read_text(encoding="utf-8") + "drift\n",
            encoding="utf-8",
        )

    assert main(_formal_doctor_command(matrix_path, registry_path, suite_path)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error": "invalid Offline Case package",
        "code": "invalid_case_manifest",
    }


def test_formal_eval_doctor_rejects_matrix_suite_mismatch(tmp_path: Path, capsys):
    suite_path = _copy_fixture(tmp_path)
    matrix_path = tmp_path / "matrix.json"
    _write_matrix(matrix_path, suite_id="different-suite-v1")
    registry_path = _write_registry(tmp_path)

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
                "--suite",
                str(suite_path),
            ]
        )
        == 2
    )
    error = json.loads(capsys.readouterr().err)["error"]
    assert "different-suite-v1" in error
    assert "tiny-loader-fixture-v2" in error
