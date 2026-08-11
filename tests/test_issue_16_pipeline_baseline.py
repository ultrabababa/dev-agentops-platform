import json
import shutil
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import devagentops.evaluation_run as evaluation_run
from devagentops.cli import main
from devagentops.evaluation_artifacts import EvaluationArtifactError
from devagentops.evaluation_suite import (
    calculate_case_fingerprint,
    calculate_suite_fingerprint,
)
from devagentops.storage import StorageError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "evaluation"


def _write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_pipeline_matrix(path: Path) -> None:
    _write_json(
        path,
        {
            "matrix_id": "issue-16-tracer-bullet",
            "matrix_version": "1",
            "schema_version": "1",
            "conditions": [
                {
                    "id": "pipeline-baseline-tiny-v1",
                    "type": "anchor",
                    "runtime_variant": "pipeline_baseline",
                    "suite": "tiny-loader-fixture-v2",
                    "evaluation_method": "triage-method-v1",
                    "model": {
                        "applicability": "not_applicable",
                        "reason": "deterministic_pipeline_uses_no_model",
                    },
                    "components": {},
                    "budgets": {
                        "applicability": "not_applicable",
                        "reason": "fixed_pipeline_has_no_agent_or_model_budget",
                    },
                    "repeats": 1,
                }
            ],
        },
    )


def _eval_run_command(
    *,
    matrix: Path,
    suite: Path,
    database: Path,
    artifacts_dir: Path,
) -> list[str]:
    return [
        "eval",
        "run",
        "--matrix",
        str(matrix),
        "--registry",
        str(PROJECT_ROOT / "components" / "registry.json"),
        "--suite",
        str(suite),
        "--condition",
        "pipeline-baseline-tiny-v1",
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts_dir),
    ]


def _refresh_fixture_fingerprints(evaluation_root: Path) -> None:
    case_path = (
        evaluation_root / "cases" / "constructed-assertion-001" / "case.json"
    )
    case_document = json.loads(case_path.read_text(encoding="utf-8"))
    case_document["case_fingerprint"] = calculate_case_fingerprint(case_path)
    _write_json(case_path, case_document)

    suite_path = evaluation_root / "tiny-suite.json"
    suite_document = json.loads(suite_path.read_text(encoding="utf-8"))
    suite_document["suite_fingerprint"] = calculate_suite_fingerprint(suite_path)
    _write_json(suite_path, suite_document)


def _assert_failed_run(
    database_path: Path,
    *,
    failure_code: str,
    expected_events: list[str],
) -> None:
    with sqlite3.connect(database_path) as connection:
        run = connection.execute(
            "SELECT run_id, status, failure_code FROM evaluation_runs"
        ).fetchone()
        assert run[1:] == ("failed", failure_code)
        event_types = [
            row[0]
            for row in connection.execute(
                "SELECT event_type FROM evaluation_trace_events "
                "WHERE run_id = ? ORDER BY sequence",
                (run[0],),
            )
        ]
        assert event_types == expected_events
        assert "run_completed" not in event_types
        assert connection.execute("SELECT COUNT(*) FROM evaluation_reports").fetchone()[
            0
        ] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone()[0] == 0


def test_eval_run_stops_at_formal_doctor_without_creating_outputs(
    tmp_path: Path,
    capsys,
) -> None:
    evaluation_root = tmp_path / "evaluation"
    shutil.copytree(FIXTURE_ROOT, evaluation_root)
    suite_path = evaluation_root / "tiny-suite.json"
    raw_log_path = (
        evaluation_root
        / "cases"
        / "constructed-assertion-001"
        / "physical-artifacts"
        / "raw.log"
    )
    raw_log_path.write_text(
        raw_log_path.read_text(encoding="utf-8") + "fingerprint drift\n",
        encoding="utf-8",
    )
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=suite_path,
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error": "invalid Offline Case package",
        "code": "invalid_case_manifest",
    }
    assert not database_path.exists()
    assert not artifacts_dir.exists()


def test_eval_run_executes_pipeline_scores_persists_and_writes_artifacts(
    tmp_path: Path,
    capsys,
) -> None:
    evaluation_root = tmp_path / "evaluation"
    shutil.copytree(FIXTURE_ROOT, evaluation_root)
    suite_path = evaluation_root / "tiny-suite.json"
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=suite_path,
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    output = json.loads(captured.out)
    assert output["status"] == "completed"
    assert output["condition_id"] == "pipeline-baseline-tiny-v1"
    run_id = output["run_id"]

    with sqlite3.connect(database_path) as connection:
        run = connection.execute(
            "SELECT status, condition_id, runtime_variant, suite_id "
            "FROM evaluation_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        assert run == (
            "completed",
            "pipeline-baseline-tiny-v1",
            "pipeline_baseline",
            "tiny-loader-fixture-v2",
        )
        manifest = json.loads(
            connection.execute(
                "SELECT manifest_json FROM evaluation_run_manifests WHERE run_id = ?",
                (run_id,),
            ).fetchone()[0]
        )
        event_types = [
            row[0]
            for row in connection.execute(
                "SELECT event_type FROM evaluation_trace_events "
                "WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            )
        ]
        report = json.loads(
            connection.execute(
                "SELECT report_json FROM evaluation_reports "
                "WHERE run_id = ? AND case_id = ?",
                (run_id, "constructed-assertion-001"),
            ).fetchone()[0]
        )
        metrics = json.loads(
            connection.execute(
                "SELECT metrics_json FROM evaluation_case_scores "
                "WHERE run_id = ? AND case_id = ?",
                (run_id, "constructed-assertion-001"),
            ).fetchone()[0]
        )

    assert manifest["run_kind"] == "tracer_bullet"
    assert manifest["runtime_variant"] == "pipeline_baseline"
    assert manifest["pipeline_version"] == "deterministic_pytest_assertion_v1"
    assert "canonical_run" not in manifest
    assert manifest["model_configuration"] == {
        "applicability": "not_applicable",
        "reason": "deterministic_pipeline_uses_no_model",
    }
    assert event_types == [
        "run_started",
        "case_started",
        "pipeline_started",
        "report_submitted",
        "evaluation_completed",
        "case_completed",
        "run_completed",
    ]
    assert report == {
        "case_id": "constructed-assertion-001",
        "classification_status": "classified",
        "confidence": 1.0,
        "evidence_references": [
            {"evidence_id": "log:assertion-mismatch"},
            {"evidence_id": "repo:calculate-total"},
            {"evidence_id": "repo:test-total"},
        ],
        "failure_type": "test_assertion_failure",
        "recommended_action": (
            "Change calculate_total to return left + right, then rerun the "
            "affected test."
        ),
        "root_cause": (
            "calculate_total returns left * right, so inputs 2 and 3 produce 6 "
            "while the test expects 5."
        ),
        "schema_version": "1",
        "summary": (
            "Pytest assertion failed: calculate_total(2, 3) produced 6 instead of 5."
        ),
    }
    assert metrics == {
        "failure_type_exact_match": 1.0,
        "failure_type_reviewed_acceptable_match": 0.0,
        "report_evidence_hit_rate": 1.0,
        "required_fields_completeness": 1.0,
    }

    json_path = Path(output["artifacts"]["json"])
    markdown_path = Path(output["artifacts"]["markdown"])
    assert json_path.is_file()
    assert markdown_path.is_file()
    artifact = json.loads(json_path.read_text(encoding="utf-8"))
    assert artifact["run_id"] == run_id
    assert artifact["manifest"] == manifest
    assert artifact["case_results"][0]["report"] == report
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# DevAgentOps Evaluation Tracer Bullet" in markdown
    assert "deterministic_pytest_assertion_v1" in markdown


def test_pipeline_output_is_deterministic_and_does_not_read_expected_answer_prose(
    tmp_path: Path,
    capsys,
) -> None:
    evaluation_root = tmp_path / "evaluation"
    shutil.copytree(FIXTURE_ROOT, evaluation_root)
    expected_answer_path = (
        evaluation_root
        / "cases"
        / "constructed-assertion-001"
        / "evaluator"
        / "expected-answer.json"
    )
    expected_answer = json.loads(expected_answer_path.read_text(encoding="utf-8"))
    leakage_sentinel = "EVALUATOR_ONLY_SENTINEL_MUST_NOT_REACH_PIPELINE"
    expected_answer["summary"] = leakage_sentinel
    expected_answer["root_cause"] = leakage_sentinel
    expected_answer["recommended_action"] = leakage_sentinel
    _write_json(expected_answer_path, expected_answer)
    _refresh_fixture_fingerprints(evaluation_root)

    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    outputs: list[dict] = []
    artifacts: list[dict] = []
    for run_number in (1, 2):
        exit_code = main(
            _eval_run_command(
                matrix=matrix_path,
                suite=evaluation_root / "tiny-suite.json",
                database=tmp_path / f"run-{run_number}.db",
                artifacts_dir=tmp_path / f"artifacts-{run_number}",
            )
        )
        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.err == ""
        output = json.loads(captured.out)
        outputs.append(output)
        artifacts.append(
            json.loads(Path(output["artifacts"]["json"]).read_text(encoding="utf-8"))
        )

    first_result = artifacts[0]["case_results"][0]
    second_result = artifacts[1]["case_results"][0]
    assert first_result == second_result
    assert leakage_sentinel not in json.dumps(first_result)
    assert artifacts[0]["manifest"]["pipeline_version"] == (
        "deterministic_pytest_assertion_v1"
    )
    assert outputs[0]["run_id"] != outputs[1]["run_id"]


def test_pipeline_failure_persists_failure_trace_without_success_outputs(
    tmp_path: Path,
    capsys,
) -> None:
    evaluation_root = tmp_path / "evaluation"
    shutil.copytree(FIXTURE_ROOT, evaluation_root)
    raw_log_path = (
        evaluation_root
        / "cases"
        / "constructed-assertion-001"
        / "physical-artifacts"
        / "raw.log"
    )
    original_test_status = (
        "tests/test_total.py F" + " " * 52 + "[100%]"
    )
    unsupported_test_status = (
        "tests/test_total.py ?" + " " * 52 + "[100%]"
    )
    raw_log = raw_log_path.read_text(encoding="utf-8").replace(
        original_test_status,
        unsupported_test_status,
    )
    raw_log_path.write_text(raw_log, encoding="utf-8")
    _refresh_fixture_fingerprints(evaluation_root)
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=evaluation_root / "tiny-suite.json",
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error": "deterministic pytest assertion rule did not match the frozen raw log",
        "code": "pipeline_baseline_failed",
    }
    with sqlite3.connect(database_path) as connection:
        run = connection.execute(
            "SELECT run_id, status, failure_code, failure_message "
            "FROM evaluation_runs"
        ).fetchone()
        assert run[1:] == (
            "failed",
            "pipeline_baseline_failed",
            "deterministic pytest assertion rule did not match the frozen raw log",
        )
        event_types = [
            row[0]
            for row in connection.execute(
                "SELECT event_type FROM evaluation_trace_events "
                "WHERE run_id = ? ORDER BY sequence",
                (run[0],),
            )
        ]
        assert event_types == [
            "run_started",
            "case_started",
            "pipeline_started",
            "failure",
        ]
        assert connection.execute("SELECT COUNT(*) FROM evaluation_reports").fetchone()[
            0
        ] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone()[0] == 0
    assert not artifacts_dir.exists()


def test_invalid_pipeline_report_persists_failure_without_success_outputs(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr(
        evaluation_run,
        "evaluate_case_report",
        lambda *_args, **_kwargs: SimpleNamespace(structured_report=None),
    )

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=FIXTURE_ROOT / "tiny-suite.json",
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err) == {
        "error": "deterministic Pipeline Baseline produced an invalid report",
        "code": "invalid_pipeline_report",
    }
    _assert_failed_run(
        database_path,
        failure_code="invalid_pipeline_report",
        expected_events=[
            "run_started",
            "case_started",
            "pipeline_started",
            "report_submitted",
            "failure",
        ],
    )
    assert not artifacts_dir.exists()


def test_artifact_write_failure_replaces_completed_state_with_failure(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    def fail_artifact_write(*_args, **_kwargs):
        raise EvaluationArtifactError("injected artifact failure")

    monkeypatch.setattr(
        evaluation_run,
        "write_evaluation_artifacts",
        fail_artifact_write,
    )

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=FIXTURE_ROOT / "tiny-suite.json",
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err) == {
        "error": "injected artifact failure",
        "code": "artifact_write_failed",
    }
    _assert_failed_run(
        database_path,
        failure_code="artifact_write_failed",
        expected_events=[
            "run_started",
            "case_started",
            "pipeline_started",
            "report_submitted",
            "evaluation_completed",
            "case_completed",
            "failure",
        ],
    )
    assert not artifacts_dir.exists()


def test_complete_run_failure_is_persisted_before_artifact_publication(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_pipeline_matrix(matrix_path)
    database_path = tmp_path / "state" / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    artifact_writer_called = False

    def fail_completion(*_args, **_kwargs):
        raise StorageError("injected completion failure")

    def record_artifact_write(*_args, **_kwargs):
        nonlocal artifact_writer_called
        artifact_writer_called = True
        return {}

    monkeypatch.setattr(evaluation_run, "complete_run", fail_completion)
    monkeypatch.setattr(
        evaluation_run,
        "write_evaluation_artifacts",
        record_artifact_write,
    )

    exit_code = main(
        _eval_run_command(
            matrix=matrix_path,
            suite=FIXTURE_ROOT / "tiny-suite.json",
            database=database_path,
            artifacts_dir=artifacts_dir,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err) == {
        "error": "injected completion failure",
        "code": "run_finalization_failed",
    }
    assert artifact_writer_called is False
    _assert_failed_run(
        database_path,
        failure_code="run_finalization_failed",
        expected_events=[
            "run_started",
            "case_started",
            "pipeline_started",
            "report_submitted",
            "evaluation_completed",
            "case_completed",
            "failure",
        ],
    )
    assert not artifacts_dir.exists()
