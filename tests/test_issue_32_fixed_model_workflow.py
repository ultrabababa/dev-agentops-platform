import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path

import devagentops.evaluation.run as evaluation_run
import pytest
from devagentops.evaluation.components import load_component_manifest
from devagentops.cli import main
from devagentops.evaluation.suite import load_case_package
from devagentops.conditions.l2.fixed_workflow_v1 import (
    COMPLETE_RUNTIME_INPUT_SERIALIZER_FINGERPRINT,
    EVIDENCE_ANALYSIS_CONTROL,
    EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT,
    EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA,
    EVIDENCE_ANALYSIS_MEMO_SCHEMA_FINGERPRINT,
    HANDOFF_SERIALIZER_FINGERPRINT,
    REPORT_SYNTHESIS_CONTROL,
    REPORT_SYNTHESIS_CONTROL_FINGERPRINT,
    WORKFLOW_FINGERPRINT,
    FixedModelWorkflowError,
    run_fixed_model_workflow,
)
from devagentops.conditions.l1.full_context_v1 import (
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
)
from devagentops.providers.siliconflow_v1 import (
    ModelProviderError,
    ModelResponse,
    SiliconFlowProvider,
    TokenCount,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_TASK_CONTRACT = (
    PROJECT_ROOT
    / "components"
    / "frozen"
    / "prompt"
    / "structured-triage-task-contract-v1.json"
)
CASE_MANIFEST = (
    Path(__file__).parent
    / "fixtures"
    / "evaluation"
    / "cases"
    / "constructed-assertion-001"
    / "case.json"
)
REGISTRY = PROJECT_ROOT / "components" / "registry.json"
SUITE_MANIFEST = Path(__file__).parent / "fixtures" / "evaluation" / "tiny-suite.json"


class SequenceFakeProvider:
    def __init__(
        self,
        visible_outputs: list[str | Exception],
        input_tokens: list[int],
    ) -> None:
        self.visible_outputs = visible_outputs
        self.input_tokens = input_tokens
        self.counted_requests = []
        self.requests = []

    def count_input_tokens(self, request):
        self.counted_requests.append(request)
        return TokenCount(
            input_tokens=self.input_tokens[len(self.counted_requests) - 1],
            method="deterministic_fake_tokenizer_v1",
        )

    def complete(self, request):
        call_number = len(self.requests) + 1
        self.requests.append(request)
        visible_output = self.visible_outputs[call_number - 1]
        if isinstance(visible_output, Exception):
            raise visible_output
        return ModelResponse(
            visible_output=visible_output,
            provider_request_id=f"fake-request-{call_number}",
            returned_model="Qwen/Qwen3.5-4B",
            usage={"prompt_tokens": self.input_tokens[call_number - 1]},
            finish_reason="stop",
            latency_ms=call_number,
        )


def _write_l2_matrix(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "matrix_id": "issue-32-l2",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "l2-tiny-v1",
                        "type": "candidate",
                        "runtime_variant": "fixed_model_workflow",
                        "suite": "tiny-loader-fixture-v2",
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


def _l2_eval_args(matrix: Path, database: Path, artifacts: Path) -> list[str]:
    return [
        "eval",
        "run",
        "--matrix",
        str(matrix),
        "--registry",
        str(REGISTRY),
        "--suite",
        str(SUITE_MANIFEST),
        "--condition",
        "l2-tiny-v1",
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts),
    ]

def test_l2_executor_runs_exact_frozen_two_stage_workflow() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    memo = {
        "schema_version": "1",
        "case_id": package.case_id,
        "evidence_findings": [
            {
                "evidence_id": "log:assertion-mismatch",
                "finding": "The total assertion observed 6 instead of 5.",
            }
        ],
        "working_failure_type": "test_assertion_failure",
        "causal_hypothesis": "The implementation multiplies instead of adding.",
        "uncertainties": [],
    }
    report = {
        "schema_version": "1",
        "case_id": package.case_id,
        "classification_status": "classified",
        "failure_type": "test_assertion_failure",
        "summary": "The total assertion failed.",
        "root_cause": "The implementation multiplies instead of adding.",
        "recommended_action": "Change the implementation to addition and rerun the test.",
        "confidence": 0.99,
        "evidence_references": [{"evidence_id": "log:assertion-mismatch"}],
    }
    memo_output = json.dumps(memo, ensure_ascii=False)
    provider = SequenceFakeProvider(
        [memo_output, json.dumps(report)],
        [1200, 1400],
    )

    result = run_fixed_model_workflow(workspace, prompt, provider)

    assert result.candidate_document == report
    assert len(provider.requests) == 2
    stage_1, stage_2 = provider.requests
    assert stage_1.response_format == EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA
    assert stage_2.response_format == STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA
    assert stage_1.messages[0]["content"].endswith(EVIDENCE_ANALYSIS_CONTROL)
    assert stage_2.messages[0]["content"].endswith(REPORT_SYNTHESIS_CONTROL)
    assert (
        "\n\nRuntime execution control:\n\n" + EVIDENCE_ANALYSIS_CONTROL
        in stage_1.messages[0]["content"]
    )
    assert (
        "\n\nRuntime execution control:\n\n" + REPORT_SYNTHESIS_CONTROL
        in stage_2.messages[0]["content"]
    )
    assert result.complete_runtime_input.text in stage_1.messages[0]["content"]
    assert result.complete_runtime_input.text in stage_2.messages[0]["content"]
    handoff = json.loads(result.handoff.text)
    assert handoff["visible_output"] == memo_output
    assert handoff["visible_output_sha256"] == result.handoff.visible_output_sha256
    assert not result.handoff.text.endswith("\n")
    assert (
        result.complete_runtime_input.text
        + "\nCase-scoped intermediate artifact:\n"
        + result.handoff.text
        in stage_2.messages[0]["content"]
    )
    assert result.handoff.text in stage_2.messages[0]["content"]
    for request in provider.requests:
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
        assert request.enable_thinking is False
        assert request.temperature == 0
        assert request.max_tokens == 1024
        assert request.completions == 1
        assert request.stream is False
        assert request.tools is None
    real_counter = SiliconFlowProvider(api_key="not-used-for-counting")
    assert [
        real_counter.count_input_tokens(request).method
        for request in provider.requests
    ] == [
        "qwen3_5_4b_official_tokenizer_chat_template_v1",
        "qwen3_5_4b_official_tokenizer_chat_template_v1",
    ]


def test_eval_run_dispatches_l2_and_persists_fixed_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    memo = {
        "schema_version": "1",
        "case_id": "constructed-assertion-001",
        "evidence_findings": [
            {
                "evidence_id": "log:assertion-mismatch",
                "finding": "The total assertion observed 6 instead of 5.",
            }
        ],
        "working_failure_type": "test_assertion_failure",
        "causal_hypothesis": "The implementation multiplies instead of adding.",
        "uncertainties": [],
    }
    report = {
        "schema_version": "1",
        "case_id": "constructed-assertion-001",
        "classification_status": "classified",
        "failure_type": "test_assertion_failure",
        "summary": "The total assertion failed.",
        "root_cause": "The implementation multiplies instead of adding.",
        "recommended_action": "Change the implementation to addition and rerun the test.",
        "confidence": 0.99,
        "evidence_references": [{"evidence_id": "log:assertion-mismatch"}],
    }
    provider = SequenceFakeProvider(
        [json.dumps(memo), json.dumps(report)],
        [1200, 1400],
    )
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(_l2_eval_args(matrix_path, database_path, artifacts_dir))

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    output = json.loads(captured.out)
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    manifest = artifact["manifest"]
    assert manifest["runtime_variant"] == "fixed_model_workflow"
    assert "l1_execution" not in manifest
    assert manifest["l2_execution"]["workflow"]["version"] == (
        "fixed-model-workflow-v1"
    )
    assert manifest["l2_execution"]["workflow"]["ordered_stages"] == [
        "evidence_analysis",
        "report_synthesis",
    ]
    assert manifest["l2_execution"]["expected_model_calls_per_case"] == 2
    assert manifest["l2_execution"]["complete_runtime_input_serializer"][
        "fingerprint"
    ] == COMPLETE_RUNTIME_INPUT_SERIALIZER_FINGERPRINT
    assert manifest["l2_execution"]["condition_fingerprint_limitation"]
    events = artifact["trace"]
    assert [event["event_type"] for event in events].count(
        "l2_workflow_started"
    ) == 1
    assert [event["event_type"] for event in events].count(
        "l2_workflow_completed"
    ) == 1
    started = [event for event in events if event["event_type"] == "model_call_started"]
    completed = [
        event for event in events if event["event_type"] == "model_call_completed"
    ]
    assert [event["payload"]["stage_id"] for event in started] == [
        "evidence_analysis",
        "report_synthesis",
    ]
    assert [event["payload"]["logical_call_number"] for event in completed] == [1, 2]
    for event, request in zip(started, provider.requests, strict=True):
        canonical_request = json.dumps(
            request.provider_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        assert event["payload"]["message_content_sha256"] == event["payload"][
            "prompt_sha256"
        ]
        assert event["payload"]["request_sha256"] == hashlib.sha256(
            canonical_request.encode("utf-8")
        ).hexdigest()
    assert completed[0]["payload"]["visible_output"] == json.dumps(memo)
    assert completed[1]["payload"]["visible_output"] == json.dumps(report)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, runtime_variant FROM evaluation_runs"
        ).fetchone() == ("completed", "fixed_model_workflow")
        assert connection.execute(
            "SELECT valid FROM evaluation_reports"
        ).fetchone() == (1,)


@pytest.mark.parametrize(
    "memo_output",
    [
        "",
        "not-json",
        "{}",
        '{"schema_version":"1"}',
        "low quality output",
        "  \nΩ exact visible output\n ",
        json.dumps(
            {
                "schema_version": "1",
                "case_id": "constructed-assertion-001",
                "evidence_findings": [{"evidence_id": [], "finding": {}}],
                "working_failure_type": [],
                "causal_hypothesis": [],
                "uncertainties": {},
            }
        ),
    ],
)
def test_every_returned_stage_1_visible_string_reaches_stage_2(
    memo_output: str,
) -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    provider = SequenceFakeProvider([memo_output, "not-a-final-report"], [1000, 1100])

    result = run_fixed_model_workflow(workspace, prompt, provider)

    assert len(provider.requests) == 2
    assert result.candidate_document == "not-a-final-report"
    assert json.loads(result.handoff.text)["visible_output"] == memo_output
    assert result.handoff.visible_output_sha256 == hashlib.sha256(
        memo_output.encode("utf-8")
    ).hexdigest()
    assert result.handoff.text in provider.requests[1].messages[0]["content"]


def test_l2_context_preflight_is_independent_per_stage() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    stage_1_over = SequenceFakeProvider(
        ["unused"],
        [262144 - 1024 + 1],
    )

    with pytest.raises(FixedModelWorkflowError) as stage_1_error:
        run_fixed_model_workflow(workspace, prompt, stage_1_over)

    assert stage_1_error.value.code == "l2_context_infeasible"
    assert stage_1_error.value.stage_id == "evidence_analysis"
    assert stage_1_over.requests == []

    stage_2_over = SequenceFakeProvider(
        ["memo", "unused"],
        [1000, 262144 - 1024 + 1],
    )

    with pytest.raises(FixedModelWorkflowError) as stage_2_error:
        run_fixed_model_workflow(workspace, prompt, stage_2_over)

    assert stage_2_error.value.code == "l2_context_infeasible"
    assert stage_2_error.value.stage_id == "report_synthesis"
    assert len(stage_2_over.requests) == 1
    assert len(stage_2_over.counted_requests) == 2

    exact_boundary = SequenceFakeProvider(
        ["memo", "report"],
        [262144 - 1024, 262144 - 1024],
    )

    run_fixed_model_workflow(workspace, prompt, exact_boundary)

    assert len(exact_boundary.requests) == 2


def test_stage_1_validation_is_observational_for_wrong_case_and_evidence() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    memo = {
        "schema_version": "1",
        "case_id": "wrong-case",
        "evidence_findings": [
            {"evidence_id": "invented:id", "finding": "Unsupported finding."}
        ],
        "working_failure_type": "test_assertion_failure",
        "causal_hypothesis": "Unsupported hypothesis.",
        "uncertainties": [],
    }
    provider = SequenceFakeProvider([json.dumps(memo), "final"], [1000, 1100])

    result = run_fixed_model_workflow(workspace, prompt, provider)

    assert len(provider.requests) == 2
    assert result.evidence_analysis_observation == {
        "json_valid": True,
        "schema_valid": True,
        "case_id_matches": False,
        "evidence_ids_known": False,
    }


def test_l2_frozen_contract_fingerprints_are_stable() -> None:
    assert EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT == (
        "1ac29b23cab43ac5effe61db93b9ea161cfb2b20078b8402b15b01ed8048289f"
    )
    assert REPORT_SYNTHESIS_CONTROL_FINGERPRINT == (
        "f29ad9d115df462f884c4a8006234be55e4f4e18cc55b884d1da9a9085e68c8c"
    )
    assert EVIDENCE_ANALYSIS_MEMO_SCHEMA_FINGERPRINT == (
        "b865279bb0d5a5da41dc721e191f8b304717dddaa3e5dda80990856a0b91c915"
    )
    assert HANDOFF_SERIALIZER_FINGERPRINT == (
        "a8e182b2e66b2e505c610ed21c5b854b4595ac0e96aaa0ece0b21ff38c8f427f"
    )
    assert WORKFLOW_FINGERPRINT == (
        "57328e31a74b67b76676ab4952da0b53914f53fb29a227c1db19878706237807"
    )
    assert COMPLETE_RUNTIME_INPUT_SERIALIZER_FINGERPRINT == (
        "df710e02319c3b410b364bbc3ebcabe767f896316b2c66b809fb027d3c91ca11"
    )


@pytest.mark.parametrize(
    ("outputs", "input_tokens", "expected_stage", "attempted", "completed"),
    [
        (
            [
                ModelProviderError(
                    "SiliconFlow request failed with HTTP 429",
                    code="model_provider_rate_limited",
                    http_status=429,
                )
            ],
            [1000],
            "evidence_analysis",
            1,
            0,
        ),
        (
            [
                "memo",
                ModelProviderError(
                    "SiliconFlow request failed with HTTP 429",
                    code="model_provider_rate_limited",
                    http_status=429,
                ),
            ],
            [1000, 1100],
            "report_synthesis",
            2,
            1,
        ),
    ],
)
def test_l2_provider_failure_stops_at_fixed_stage_without_retry(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outputs: list[str | Exception],
    input_tokens: list[int],
    expected_stage: str,
    attempted: int,
    completed: int,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    provider = SequenceFakeProvider(outputs, input_tokens)
    secret = "l2-deterministic-secret-sentinel"
    monkeypatch.setenv("SILICONFLOW_API_KEY", secret)
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l2_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    error = json.loads(capsys.readouterr().err)
    assert exit_code == 2
    assert error["code"] == "model_provider_rate_limited"
    assert len(provider.requests) == attempted
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_runs"
        ).fetchone() == ("failed", "model_provider_rate_limited")
        assert connection.execute("SELECT COUNT(*) FROM evaluation_reports").fetchone() == (
            0,
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone() == (0,)
        payload = json.loads(
            connection.execute(
                "SELECT payload_json FROM evaluation_trace_events "
                "WHERE event_type = 'failure'"
            ).fetchone()[0]
        )
    assert payload["stage"] == expected_stage
    assert payload["attempted_logical_call_count"] == attempted
    assert payload["completed_logical_call_count"] == completed
    assert payload["http_status"] == 429
    artifact_path = next((tmp_path / "artifacts").glob("*/evaluation.json"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "failed"
    assert artifact["case_results"] == []
    assert artifact["failure"]["stage"] == expected_stage
    assert artifact["failure"]["payload"] == payload
    assert (artifact_path.parent / "evaluation.md").exists()
    secret_bytes = secret.encode("utf-8")
    assert secret_bytes not in artifact_path.read_bytes()
    assert secret_bytes not in (artifact_path.parent / "evaluation.md").read_bytes()
    assert secret_bytes not in database_path.read_bytes()


def test_stage_2_context_failure_persists_one_completed_call(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    provider = SequenceFakeProvider(
        ["memo", "unused"],
        [1000, 262144 - 1024 + 1],
    )
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l2_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err)["code"] == "l2_context_infeasible"
    assert len(provider.requests) == 1
    with sqlite3.connect(database_path) as connection:
        payload = json.loads(
            connection.execute(
                "SELECT payload_json FROM evaluation_trace_events "
                "WHERE event_type = 'failure'"
            ).fetchone()[0]
        )
        completed_events = connection.execute(
            "SELECT COUNT(*) FROM evaluation_trace_events "
            "WHERE event_type = 'model_call_completed'"
        ).fetchone()
    assert payload["stage"] == "report_synthesis"
    assert payload["attempted_logical_call_count"] == 1
    assert payload["completed_logical_call_count"] == 1
    assert payload["input_tokens"] == 262144 - 1024 + 1
    assert completed_events == (1,)
    artifact_path = next((tmp_path / "artifacts").glob("*/evaluation.json"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "failed"
    assert artifact["failure"]["stage"] == "report_synthesis"
    assert [
        event["event_type"] for event in artifact["trace"]
    ].count("model_call_completed") == 1
    assert artifact["case_results"] == []


def test_invalid_final_report_remains_completed_quality_observation(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    conflict = {
        "schema_version": "1",
        "case_id": "constructed-assertion-001",
        "classification_status": "inconclusive",
        "failure_type": "test_assertion_failure",
        "summary": "The available evidence is insufficient.",
        "root_cause": "The cause cannot be established.",
        "recommended_action": "Inspect more evidence.",
        "confidence": 0.2,
        "evidence_references": [{"evidence_id": "log:assertion-mismatch"}],
    }
    provider = SequenceFakeProvider(["", json.dumps(conflict)], [1000, 1100])
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l2_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    assert exit_code == 0, capsys.readouterr().err
    assert len(provider.requests) == 2
    with sqlite3.connect(database_path) as connection:
        status = connection.execute("SELECT status FROM evaluation_runs").fetchone()
        valid, report_json, validation_json = connection.execute(
            "SELECT valid, report_json, validation_json FROM evaluation_reports"
        ).fetchone()
        stage_1_payload = json.loads(
            connection.execute(
                "SELECT payload_json FROM evaluation_trace_events "
                "WHERE event_type = 'model_call_completed' ORDER BY sequence LIMIT 1"
            ).fetchone()[0]
        )
    assert status == ("completed",)
    assert valid == 0
    assert json.loads(report_json) == conflict
    assert any(
        error["code"] == "failure_type_not_allowed_for_inconclusive"
        for error in json.loads(validation_json)["errors"]
    )
    assert stage_1_payload["visible_output"] == ""
    assert stage_1_payload["evidence_analysis_observation"]["json_valid"] is False


def test_l2_formal_doctor_fails_before_provider_or_outputs(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    evaluation_root = tmp_path / "evaluation"
    shutil.copytree(Path(__file__).parent / "fixtures" / "evaluation", evaluation_root)
    raw_log = (
        evaluation_root
        / "cases"
        / "constructed-assertion-001"
        / "physical-artifacts"
        / "raw.log"
    )
    raw_log.write_text(raw_log.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    provider_factory_called = False

    def unexpected_provider():
        nonlocal provider_factory_called
        provider_factory_called = True
        raise AssertionError("provider must not be created before doctor succeeds")

    monkeypatch.setattr(evaluation_run, "create_model_provider", unexpected_provider)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    args = _l2_eval_args(matrix_path, database_path, artifacts_dir)
    args[args.index(str(SUITE_MANIFEST))] = str(evaluation_root / "tiny-suite.json")

    exit_code = main(args)

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err)["code"] == "invalid_case_manifest"
    assert provider_factory_called is False
    assert not database_path.exists()
    assert not artifacts_dir.exists()


@pytest.mark.skipif(
    os.environ.get("DEVAGENTOPS_LIVE_SILICONFLOW") != "1",
    reason="requires explicit live SiliconFlow smoke opt-in",
)
def test_live_l2_siliconflow_tiny_fixture_end_to_end(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    assert api_key
    matrix_path = tmp_path / "matrix.json"
    _write_l2_matrix(matrix_path)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr(
        evaluation_run,
        "create_model_provider",
        lambda: SiliconFlowProvider(api_key=api_key, timeout_seconds=180),
    )

    exit_code = main(_l2_eval_args(matrix_path, database_path, artifacts_dir))

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    output = json.loads(captured.out)
    json_path = Path(output["artifacts"]["json"])
    markdown_path = Path(output["artifacts"]["markdown"])
    artifact = json.loads(json_path.read_text(encoding="utf-8"))
    started = [
        event
        for event in artifact["trace"]
        if event["event_type"] == "model_call_started"
    ]
    completed = [
        event
        for event in artifact["trace"]
        if event["event_type"] == "model_call_completed"
    ]
    assert len(started) == len(completed) == 2
    assert [event["payload"]["stage_id"] for event in completed] == [
        "evidence_analysis",
        "report_synthesis",
    ]
    assert all(event["payload"]["usage"] for event in completed)
    assert [event["payload"]["usage"]["prompt_tokens"] for event in completed] == [
        event["payload"]["input_tokens"] for event in started
    ]
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, runtime_variant FROM evaluation_runs"
        ).fetchone() == ("completed", "fixed_model_workflow")
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_reports"
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_scores"
        ).fetchone() == (1,)
    secret = api_key.encode("utf-8")
    assert secret not in json_path.read_bytes()
    assert secret not in markdown_path.read_bytes()
    assert secret not in database_path.read_bytes()


def test_docs_record_frozen_l2_semantics_and_fingerprint_limitation() -> None:
    ladder = (
        PROJECT_ROOT / "docs" / "evaluation" / "runtime-capability-ladder.md"
    ).read_text(encoding="utf-8")
    methodology = (
        PROJECT_ROOT / "docs" / "evaluation" / "formal-evaluation-methodology.md"
    ).read_text(encoding="utf-8")

    for document in (ladder, methodology):
        assert "evidence_analysis -> report_synthesis -> stop" in document
        assert "Condition Fingerprint" in document
        assert "Manifest" in document
        assert "combined difference" in document
        assert "Formal L1→L2 comparison" in document
