import json
import sqlite3
from pathlib import Path

import devagentops.evaluation.debug as evaluation_debug
import pytest
from devagentops.cli import main
from devagentops.evaluation.preflight import run_formal_eval_doctor
from devagentops.evaluation.suite import load_evaluation_suite
from devagentops.providers.siliconflow_v1 import ModelProviderError, ModelResponse, TokenCount


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = PROJECT_ROOT / "components" / "registry.json"
SUITE = PROJECT_ROOT / "evaluation" / "suites" / "triage-v1" / "suite.json"
TINY_SUITE = PROJECT_ROOT / "tests" / "fixtures" / "evaluation" / "tiny-suite.json"
REPOSITORY_DEBUG_MATRIX = (
    PROJECT_ROOT / "evaluation" / "matrices" / "l1-case-subset-debug-v1.json"
)
FIRST_FROZEN_CASE_IDS = [
    "bugswarm-traccar-170287308",
    "bugswarm-apache-struts-190697114",
]


class SequenceProvider:
    def __init__(self, documents: list[dict]) -> None:
        self._documents = iter(documents)
        self.requests = []

    def count_input_tokens(self, request):
        return TokenCount(
            input_tokens=1000,
            method="deterministic_fake_tokenizer_v1",
        )

    def complete(self, request):
        self.requests.append(request)
        return ModelResponse(
            visible_output=json.dumps(next(self._documents)),
            provider_request_id=f"fake-request-{len(self.requests)}",
            returned_model="Qwen/Qwen3.5-4B",
            usage={"prompt_tokens": 1000, "completion_tokens": 120},
            finish_reason="stop",
            latency_ms=7,
        )


class FailFirstProvider(SequenceProvider):
    def complete(self, request):
        self.requests.append(request)
        if len(self.requests) == 1:
            raise ModelProviderError(
                "qualification provider rate limited the request",
                code="model_provider_rate_limited",
                http_status=429,
            )
        return ModelResponse(
            visible_output=json.dumps(next(self._documents)),
            provider_request_id="fake-request-2",
            returned_model="Qwen/Qwen3.5-4B",
            usage={"prompt_tokens": 1000, "completion_tokens": 120},
            finish_reason="stop",
            latency_ms=7,
        )


class FirstContextInfeasibleProvider(SequenceProvider):
    def __init__(self, documents: list[dict]) -> None:
        super().__init__(documents)
        self.count_calls = 0

    def count_input_tokens(self, request):
        self.count_calls += 1
        return TokenCount(
            input_tokens=262144 if self.count_calls == 1 else 1000,
            method="deterministic_fake_tokenizer_v1",
        )


class AlwaysFailProvider(SequenceProvider):
    def complete(self, request):
        self.requests.append(request)
        raise ModelProviderError(
            "qualification provider unavailable",
            code="model_provider_unavailable",
        )


def _write_debug_matrix(path: Path, *, suite_id: str = "triage-suite-v1") -> None:
    path.write_text(
        json.dumps(
            {
                "matrix_id": "issue-35-l1-debug",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "l1-case-subset-debug-v1",
                        "type": "candidate",
                        "runtime_variant": "full_context_one_shot",
                        "suite": suite_id,
                        "evaluation_method": "triage-method-v1",
                        "model": {
                            "provider": "siliconflow",
                            "model": "Qwen/Qwen3.5-4B",
                        },
                        "components": {
                            "prompt": "structured-triage-task-contract-v1"
                        },
                        "budgets": {
                            "context_limit_tokens": 262144,
                            "max_output_tokens": 1024,
                        },
                        "repeats": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _valid_report(suite_case) -> dict:
    return {
        "schema_version": "1",
        "case_id": suite_case.case_id,
        "classification_status": "classified",
        "failure_type": suite_case.package.expected_answer.primary_failure_type,
        "summary": "The selected Case failed in its recorded CI execution.",
        "root_cause": "The available evidence identifies the recorded failure cause.",
        "recommended_action": "Apply the evidence-supported correction and rerun CI.",
        "confidence": 0.8,
        "evidence_references": [
            {"evidence_id": suite_case.package.evidence_ids[0]}
        ],
    }


def _debug_args(
    matrix: Path,
    database: Path,
    artifacts: Path,
    case_ids: list[str],
    *,
    suite: Path = SUITE,
) -> list[str]:
    args = [
        "eval",
        "debug",
        "--matrix",
        str(matrix),
        "--registry",
        str(REGISTRY),
        "--suite",
        str(suite),
        "--condition",
        "l1-case-subset-debug-v1",
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts),
    ]
    for case_id in case_ids:
        args.extend(("--case", case_id))
    return args


def test_debug_runs_selected_cases_in_suite_order_and_publishes_results(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    suite = load_evaluation_suite(SUITE)
    selected = list(suite.cases[:2])
    provider = SequenceProvider([_valid_report(case) for case in selected])
    monkeypatch.setattr(
        evaluation_debug,
        "create_model_provider",
        lambda: provider,
    )
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            [selected[1].case_id, selected[0].case_id],
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    assert len(provider.requests) == 2
    for request, suite_case in zip(provider.requests, selected, strict=True):
        prompt_text = request.messages[0]["content"]
        assert '"expected_answer"' not in prompt_text
        assert '"required_evidence_ids"' not in prompt_text
        assert "evaluator/expected-answer.json" not in prompt_text
        assert "evaluator/required-evidence.json" not in prompt_text
        assert suite_case.package.expected_answer.summary not in prompt_text
        assert suite_case.package.expected_answer.root_cause not in prompt_text
        assert suite_case.package.expected_answer.recommended_action not in prompt_text
    output = json.loads(captured.out)
    assert output["status"] == "completed"
    assert output["selected_case_ids"] == [case.case_id for case in selected]
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert artifact["status"] == "completed"
    assert artifact["manifest"]["run_kind"] == "case_subset_debug"
    assert artifact["manifest"]["case_selection"] == {
        "mode": "explicit_subset",
        "case_ids": [case.case_id for case in selected],
    }
    assert [result["case_id"] for result in artifact["case_results"]] == [
        case.case_id for case in selected
    ]
    assert [
        event["case_id"]
        for event in artifact["trace"]
        if event["event_type"] == "case_started"
    ] == [case.case_id for case in selected]
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, runtime_variant FROM evaluation_runs"
        ).fetchone() == ("completed", "full_context_one_shot")
        assert connection.execute(
            "SELECT case_id FROM evaluation_reports ORDER BY rowid"
        ).fetchall() == [(case.case_id,) for case in selected]
        assert connection.execute(
            "SELECT case_id FROM evaluation_case_scores ORDER BY rowid"
        ).fetchall() == [(case.case_id,) for case in selected]


def test_repository_l1_debug_condition_passes_complete_doctor() -> None:
    preflight = run_formal_eval_doctor(
        REPOSITORY_DEBUG_MATRIX,
        REGISTRY,
        SUITE,
    )

    assert preflight.matrix.matrix_id == "l1-case-subset-debug"
    assert preflight.suite.suite_id == "triage-suite-v1"
    assert [
        condition.effective_condition["runtime_variant"]
        for condition in preflight.matrix.conditions
    ] == ["full_context_one_shot"]


def test_debug_completes_doctor_before_provider_or_outputs(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path, suite_id="not-the-loaded-suite")
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    provider_factory_called = False

    def unexpected_provider():
        nonlocal provider_factory_called
        provider_factory_called = True
        raise AssertionError("provider must not be created before doctor succeeds")

    monkeypatch.setattr(evaluation_debug, "create_model_provider", unexpected_provider)

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            ["constructed-assertion-001"],
            suite=TINY_SUITE,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert provider_factory_called is False
    assert not database_path.exists()
    assert not artifacts_dir.exists()


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("runtime_variant", "fixed_model_workflow", "unsupported_debug_runtime_variant"),
        ("repeats", 2, "unsupported_debug_repeat_count"),
    ],
)
def test_debug_rejects_non_l1_or_repeated_condition_before_side_effects(
    tmp_path: Path,
    monkeypatch,
    capsys,
    field: str,
    value,
    expected_code: str,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path, suite_id="tiny-loader-fixture-v2")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["conditions"][0][field] = value
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    def unexpected_provider():
        raise AssertionError("provider must not be created for invalid condition")

    monkeypatch.setattr(evaluation_debug, "create_model_provider", unexpected_provider)

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            ["constructed-assertion-001"],
            suite=TINY_SUITE,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err)["code"] == expected_code
    assert not database_path.exists()
    assert not artifacts_dir.exists()


@pytest.mark.parametrize(
    ("case_ids", "expected_code"),
    [
        ([], "empty_case_selection"),
        (
            ["constructed-assertion-001", "constructed-assertion-001"],
            "duplicate_case_selection",
        ),
        (["not-in-the-suite"], "unknown_case_selection"),
    ],
)
def test_debug_rejects_invalid_case_selection_before_side_effects(
    tmp_path: Path,
    monkeypatch,
    capsys,
    case_ids: list[str],
    expected_code: str,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path, suite_id="tiny-loader-fixture-v2")
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    def unexpected_provider():
        raise AssertionError("provider must not be created for invalid selection")

    monkeypatch.setattr(evaluation_debug, "create_model_provider", unexpected_provider)

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            case_ids,
            suite=TINY_SUITE,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err)["code"] == expected_code
    assert not database_path.exists()
    assert not artifacts_dir.exists()


def test_debug_scores_semantically_invalid_returned_report(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    case_id = "constructed-assertion-001"
    provider = SequenceProvider([{"schema_version": "1", "case_id": case_id}])
    monkeypatch.setattr(
        evaluation_debug,
        "create_model_provider",
        lambda: provider,
    )
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path, suite_id="tiny-loader-fixture-v2")
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            [case_id],
            suite=TINY_SUITE,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    output = json.loads(captured.out)
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    result = artifact["case_results"][0]
    assert result["case_id"] == case_id
    assert result["report"] is None
    assert result["validation"]["valid"] is False
    assert result["quality_metrics"]["required_fields_completeness"] < 1
    preview = artifact["metric_preview"]
    assert output["metric_preview"] == preview
    assert preview["status"] == "complete"
    assert preview["coverage"] == {
        "selected_case_count": 1,
        "scored_case_count": 1,
        "failed_case_count": 0,
        "selected_weight": 1,
        "scored_weight": 1,
        "failed_weight": 0,
        "complete": True,
    }
    assert preview["overall"]["metric_vector"] == result["quality_metrics"]
    assert preview["by_failure_type"] == [
        {
            "failure_type": "test_assertion_failure",
            "coverage": preview["coverage"],
            "metric_vector": result["quality_metrics"],
        }
    ]
    assert "composite_score" not in preview
    assert "quality_gate" not in preview
    markdown = Path(output["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert "## Metric Vector Preview" in markdown
    assert "### Overall" in markdown
    assert "### Failure Type `test_assertion_failure`" in markdown
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_runs"
        ).fetchone() == ("completed",)
        assert connection.execute(
            "SELECT valid FROM evaluation_reports"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone() == (1,)


def test_debug_continues_after_case_execution_failure_and_returns_non_success(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    provider = FailFirstProvider(
        [{"schema_version": "1", "case_id": FIRST_FROZEN_CASE_IDS[1]}]
    )
    monkeypatch.setattr(
        evaluation_debug,
        "create_model_provider",
        lambda: provider,
    )
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            FIRST_FROZEN_CASE_IDS,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 1, captured.err
    output = json.loads(captured.out)
    assert output["status"] == "completed_with_case_failures"
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert artifact["status"] == "completed_with_case_failures"
    assert [result["outcome"]["status"] for result in artifact["case_results"]] == [
        "execution_failed",
        "scored",
    ]
    assert artifact["case_results"][0]["quality_metrics"] is None
    assert artifact["case_results"][0]["outcome"]["failure_code"] == (
        "model_provider_rate_limited"
    )
    assert artifact["case_results"][1]["quality_metrics"] is not None
    preview = artifact["metric_preview"]
    assert output["metric_preview"] == preview
    assert preview["status"] == "incomplete"
    assert preview["coverage"] == {
        "selected_case_count": 2,
        "scored_case_count": 1,
        "failed_case_count": 1,
        "selected_weight": 2,
        "scored_weight": 1,
        "failed_weight": 1,
        "complete": False,
    }
    assert preview["overall"]["metric_vector"] == artifact["case_results"][1][
        "quality_metrics"
    ]
    assert "composite_score" not in preview
    assert "quality_gate" not in preview
    assert [
        event["case_id"]
        for event in artifact["trace"]
        if event["event_type"] == "case_started"
    ] == FIRST_FROZEN_CASE_IDS
    markdown = Path(output["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert all(case_id in markdown for case_id in FIRST_FROZEN_CASE_IDS)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT value FROM devagentops_metadata WHERE key = 'schema_version'"
        ).fetchone() == ("3",)
        assert connection.execute(
            "SELECT status FROM evaluation_runs"
        ).fetchone() == ("completed_with_case_failures",)
        assert connection.execute(
            "SELECT case_id, status, failure_code "
            "FROM evaluation_case_outcomes ORDER BY sequence"
        ).fetchall() == [
            (
                FIRST_FROZEN_CASE_IDS[0],
                "execution_failed",
                "model_provider_rate_limited",
            ),
            (FIRST_FROZEN_CASE_IDS[1], "scored", None),
        ]
        assert connection.execute(
            "SELECT case_id FROM evaluation_reports"
        ).fetchall() == [(FIRST_FROZEN_CASE_IDS[1],)]
        assert connection.execute(
            "SELECT case_id FROM evaluation_case_scores"
        ).fetchall() == [(FIRST_FROZEN_CASE_IDS[1],)]


def test_debug_context_infeasible_case_makes_no_model_call_and_continues(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    provider = FirstContextInfeasibleProvider(
        [{"schema_version": "1", "case_id": FIRST_FROZEN_CASE_IDS[1]}]
    )
    monkeypatch.setattr(
        evaluation_debug,
        "create_model_provider",
        lambda: provider,
    )
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            FIRST_FROZEN_CASE_IDS,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 1, captured.err
    assert provider.count_calls == 2
    assert len(provider.requests) == 1
    output = json.loads(captured.out)
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert [result["outcome"]["status"] for result in artifact["case_results"]] == [
        "execution_failed",
        "scored",
    ]
    assert artifact["case_results"][0]["outcome"] == {
        "status": "execution_failed",
        "failure_code": "l1_context_infeasible",
        "failure_stage": "context_feasibility",
        "failure_message": (
            "complete L1 request exceeds the frozen model context capability"
        ),
    }
    first_started_calls = [
        event
        for event in artifact["trace"]
        if event["event_type"] == "model_call_started"
        and event["case_id"] == FIRST_FROZEN_CASE_IDS[0]
    ]
    assert first_started_calls == []
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT case_id FROM evaluation_reports"
        ).fetchall() == [(FIRST_FROZEN_CASE_IDS[1],)]
        assert connection.execute(
            "SELECT case_id FROM evaluation_case_scores"
        ).fetchall() == [(FIRST_FROZEN_CASE_IDS[1],)]


def test_debug_all_execution_failures_publish_no_metric_vector(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    case_id = "constructed-assertion-001"
    provider = AlwaysFailProvider([])
    monkeypatch.setattr(
        evaluation_debug,
        "create_model_provider",
        lambda: provider,
    )
    matrix_path = tmp_path / "matrix.json"
    _write_debug_matrix(matrix_path, suite_id="tiny-loader-fixture-v2")
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(
        _debug_args(
            matrix_path,
            database_path,
            artifacts_dir,
            [case_id],
            suite=TINY_SUITE,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 1, captured.err
    output = json.loads(captured.out)
    preview = output["metric_preview"]
    assert preview["status"] == "incomplete"
    assert preview["coverage"]["scored_case_count"] == 0
    assert preview["coverage"]["failed_case_count"] == 1
    assert preview["overall"]["metric_vector"] is None
    assert preview["by_failure_type"][0]["metric_vector"] is None
    markdown = Path(output["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert "No scored Cases are available for this preview." in markdown
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_case_outcomes"
        ).fetchall() == [("execution_failed",)]
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_reports"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone() == (0,)
