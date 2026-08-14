from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import devagentops.evaluation.run_v2 as evaluation_run_v2
from devagentops.cli import main
from devagentops.evaluation.artifacts import EvaluationArtifactError
from devagentops.evaluation.execution import SampleResult
from devagentops.providers.contracts import CompletionObservation, ExactTokenCount


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATRIX = PROJECT_ROOT / "evaluation/matrices/l1-minimax-m3-development-v2.json"
REGISTRY = PROJECT_ROOT / "components/registry.json"
SUITE = PROJECT_ROOT / "evaluation/suites/triage-v1/suite.json"
CONDITION = "l1-minimax-m3-adaptive-development-v1"


class _FakeProvider:
    def __init__(self, provider_index: int) -> None:
        self.provider_index = provider_index
        self.complete_calls = 0

    def count_input_tokens(self, request):
        return ExactTokenCount(1000, "exact-fake-count")

    def complete(self, request):
        self.complete_calls += 1
        return CompletionObservation(
            visible_output="not-json-but-scored-protocol-invalid",
            reasoning_output="private-reasoning-must-not-persist",
            provider_request_id=f"request-{self.provider_index}",
            returned_model="MiniMax-M3",
            usage={"prompt_tokens": 1000, "completion_tokens": 10},
            finish_reason="stop",
            latency_ms=5,
        )


def test_formal_cli_runs_full_suite_through_shared_engine_and_persists_aggregates(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    providers: list[_FakeProvider] = []

    def provider_factory(**kwargs):
        provider = _FakeProvider(len(providers))
        providers.append(provider)
        return provider

    monkeypatch.setattr(evaluation_run_v2, "create_minimax_provider", provider_factory)
    monkeypatch.setattr(evaluation_run_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_run_v2, "_git_dirty", lambda: False)
    database = tmp_path / "devagentops.db"
    artifacts = tmp_path / "artifacts"

    exit_code = main(
        [
            "eval",
            "run",
            "--matrix",
            str(MATRIX),
            "--registry",
            str(REGISTRY),
            "--suite",
            str(SUITE),
            "--condition",
            CONDITION,
            "--database",
            str(database),
            "--artifacts-dir",
            str(artifacts),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "Evaluation: 60 samples | concurrency=6" in captured.err
    assert captured.err.count("] scored ") == 60
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    markdown = Path(output["artifacts"]["markdown"]).read_text()
    assert output["status"] == "completed"
    assert len(providers) == 60
    assert all(provider.complete_calls == 1 for provider in providers)
    assert artifact["manifest"]["run_kind"] == "formal_full_suite"
    assert artifact["manifest"]["case_selection"]["mode"] == "full_suite"
    assert len(artifact["sample_results"]) == 60
    assert len(artifact["case_aggregates"]) == 20
    assert len(artifact["failure_type_aggregates"]) == 5
    assert artifact["suite_aggregate"]["total_case_count"] == 20
    assert artifact["suite_aggregate"]["protocol_invalid_sample_count"] == 60
    assert artifact["suite_aggregate"]["quality_status"] == "complete"
    assert output["fingerprints"]["treatment"] == (
        "1d6387a25f7722c30b36be82eaf5f7699550472a9b136db5964a783c3da758f4"
    )
    assert output["fingerprints"]["condition"] == (
        "c199208feb41748fd67095512871bcd406d108ed3444b98854adecf0aa1fcb2a"
    )
    assert output["fingerprints"]["execution_policy"] == (
        "c1f3aa8327a858befa9b77a8cc4bce80798c5c98a5125a0c31158ce109225e5b"
    )
    assert "L1 development-treatment milestone experiment" in markdown
    assert "not the final frozen L1-L4 benchmark" in markdown
    first_case = artifact["case_aggregates"][0]
    assert first_case["case_fingerprint"] in markdown
    assert "failure_type_exact_match" in markdown
    assert "Scored repeat indices: `[0, 1, 2]`" in markdown
    assert "Formal Evaluation: `false`" not in markdown
    assert "private-reasoning-must-not-persist" not in json.dumps(artifact)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_outcomes"
        ).fetchone() == (60,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_aggregates"
        ).fetchone() == (20,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_suite_aggregates"
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_failure_type_aggregates"
        ).fetchone() == (5,)


def test_invalid_formal_execution_policy_stops_before_provider_database_or_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    provider_calls = 0

    def forbidden_provider(**kwargs):
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("provider must not be created")

    monkeypatch.setattr(evaluation_run_v2, "create_minimax_provider", forbidden_provider)
    invalid_matrix = tmp_path / "invalid-matrix.json"
    matrix_document = json.loads(MATRIX.read_text(encoding="utf-8"))
    matrix_document["conditions"][0]["execution_policy"]["retry_count"] = 1
    invalid_matrix.write_text(json.dumps(matrix_document), encoding="utf-8")
    database = tmp_path / "must-not-exist.db"
    artifacts = tmp_path / "must-not-exist-artifacts"

    exit_code = main(
        [
            "eval",
            "run",
            "--matrix",
            str(invalid_matrix),
            "--registry",
            str(REGISTRY),
            "--suite",
            str(SUITE),
            "--condition",
            CONDITION,
            "--database",
            str(database),
            "--artifacts-dir",
            str(artifacts),
        ]
    )

    assert exit_code == 2
    assert provider_calls == 0
    assert not database.exists()
    assert not artifacts.exists()


def _synthetic_scored_result(sample) -> SampleResult:
    suite_case = sample.suite_case
    data = {
        "case_id": suite_case.case_id,
        "repeat_index": sample.identity.repeat_index,
        "sample_sequence": sample.identity.sample_sequence,
        "case_fingerprint": suite_case.package.case_fingerprint,
        "weight": suite_case.weight,
        "evaluation_failure_type": (
            suite_case.package.expected_answer.primary_failure_type
        ),
        "outcome": {"status": "scored"},
        "report": None,
        "validation": {"valid": False, "errors": ["synthetic-invalid"]},
        "quality_metrics": {
            "failure_type_exact_match": 0.0,
            "failure_type_reviewed_acceptable_match": 0.0,
            "report_evidence_hit_rate": 0.0,
            "required_fields_completeness": 0.0,
        },
        "evidence_diagnostics": {},
        "candidate_document": "synthetic-invalid",
        "visible_output": "synthetic-invalid",
        "provider_observation": {
            "provider_request_id": "synthetic",
            "returned_model": "MiniMax-M3",
            "usage": {},
            "finish_reason": "stop",
            "latency_ms": 1,
            "reasoning": {"present": False, "character_count": 0, "sha256": None},
        },
        "context_assessment": {
            "input_tokens": 1,
            "method": "synthetic",
            "exact": True,
            "context_window_tokens": 1000000,
            "reserved_completion_tokens": 65536,
        },
    }
    return SampleResult(sample.identity, "scored", data)


def test_artifact_failure_marks_run_failed_and_removes_samples_and_aggregates(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(evaluation_run_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_run_v2, "_git_dirty", lambda: False)
    monkeypatch.setattr(
        evaluation_run_v2,
        "execute_sample_plan",
        lambda planned, **kwargs: tuple(_synthetic_scored_result(item) for item in planned),
    )
    monkeypatch.setattr(
        evaluation_run_v2,
        "write_evaluation_artifacts",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            EvaluationArtifactError("synthetic artifact failure")
        ),
    )
    database = tmp_path / "devagentops.db"
    artifacts = tmp_path / "artifacts"

    exit_code = main(
        [
            "eval", "run",
            "--matrix", str(MATRIX),
            "--registry", str(REGISTRY),
            "--suite", str(SUITE),
            "--condition", CONDITION,
            "--database", str(database),
            "--artifacts-dir", str(artifacts),
        ]
    )

    assert exit_code == 2
    capsys.readouterr()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT status FROM evaluation_runs").fetchone() == (
            "failed",
        )
        for table in (
            "evaluation_sample_outcomes",
            "evaluation_sample_reports",
            "evaluation_sample_scores",
            "evaluation_case_aggregates",
            "evaluation_suite_aggregates",
            "evaluation_failure_type_aggregates",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (0,)


def test_programmer_error_is_run_level_failure_not_a_sample_outcome(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(evaluation_run_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_run_v2, "_git_dirty", lambda: False)

    def broken_engine(*args, **kwargs):
        raise RuntimeError("programmer bug")

    monkeypatch.setattr(evaluation_run_v2, "execute_sample_plan", broken_engine)
    database = tmp_path / "devagentops.db"
    artifacts = tmp_path / "artifacts"

    exit_code = main(
        [
            "eval", "run",
            "--matrix", str(MATRIX),
            "--registry", str(REGISTRY),
            "--suite", str(SUITE),
            "--condition", CONDITION,
            "--database", str(database),
            "--artifacts-dir", str(artifacts),
        ]
    )

    assert exit_code == 2
    capsys.readouterr()
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_runs"
        ).fetchone() == ("failed", "formal_execution_failed")
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_outcomes"
        ).fetchone() == (0,)
    assert not artifacts.exists()
