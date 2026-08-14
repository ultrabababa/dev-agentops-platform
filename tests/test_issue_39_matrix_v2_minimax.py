import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from devagentops.evaluation.matrix import EvaluationMatrixError, load_evaluation_matrix
from devagentops.evaluation.matrix_v2 import calculate_run_configuration_fingerprint
import devagentops.evaluation.debug_v2 as evaluation_debug_v2
from devagentops.cli import main
from devagentops.providers.contracts import CompletionObservation, ExactTokenCount
from devagentops.providers.contracts import LogicalCompletionRequest
from devagentops.providers.minimax_v1 import (
    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
    MINIMAX_M3_TOKENIZER_REVISION,
    MINIMAX_M3_TOKENIZER_SHA256,
    MiniMaxProvider,
)
from devagentops.providers.openai_compatible import (
    OpenAICompatibleChatCompletionsTransport,
    OpenAICompatibleTransportError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_MATRIX = PROJECT_ROOT / "evaluation/matrices/l1-case-subset-debug-v1.json"
V2_MATRIX = PROJECT_ROOT / "evaluation/matrices/l1-minimax-m3-development-v2.json"
REGISTRY = PROJECT_ROOT / "components/registry.json"
SUITE = PROJECT_ROOT / "evaluation/suites/triage-v1/suite.json"
SMOKE_CASE_ID = "bugswarm-traccar-170287308"


def _v2_document() -> dict:
    return {
        "matrix_id": "l1-minimax-development",
        "matrix_version": "2",
        "schema_version": "2",
        "conditions": [
            {
                "id": "l1-minimax-m3-adaptive-development-v1",
                "type": "candidate",
                "runtime_variant": "full_context_one_shot",
                "suite": "triage-suite-v1",
                "evaluation_method": "triage-method-v1",
                "treatment": {
                    "provider": {
                        "id": "minimax-official",
                        "transport": "openai-compatible-chat-completions",
                        "profile": "minimax-official-v1",
                        "base_url": "https://api.minimaxi.com/v1",
                    },
                    "model": "MiniMax-M3",
                    "reasoning": {
                        "thinking": {"type": "adaptive"},
                        "reasoning_split": True,
                    },
                    "generation": {
                        "temperature": 0,
                        "max_completion_tokens": 65536,
                        "n": 1,
                        "stream": False,
                        "response_format": {"mode": "omitted"},
                    },
                    "contracts": {
                        "task": {
                            "id": "structured-triage-task-contract",
                            "version": "development-clean-clarification-v1",
                            "fingerprint": "1" * 64,
                        },
                        "output": {
                            "id": "structured-triage-report",
                            "version": "1",
                            "fingerprint": "2" * 64,
                        },
                    },
                    "context": {
                        "context_window_tokens": 524288,
                        "policy": "official_guaranteed_minimum_total_context",
                        "source": "https://www.minimax.io/models/text/m3",
                        "tokenizer": {
                            "repository": "MiniMaxAI/MiniMax-M3",
                            "revision": "f0e1c1e04d40177e4673a22097036854f536e9c0",
                            "tokenizer_sha256": "3" * 64,
                            "chat_template_sha256": "4" * 64,
                            "method": "minimax_m3_official_chat_template_adaptive_v1",
                        },
                    },
                },
                "execution_policy": {
                    "repeat_count": 1,
                    "max_case_concurrency": 1,
                    "retry_count": 0,
                    "request_timeout_seconds": 600,
                },
            }
        ],
    }


def test_matrix_loader_dispatches_v1_without_changing_historical_fingerprint(
    tmp_path: Path,
) -> None:
    historical = load_evaluation_matrix(V1_MATRIX)
    assert historical.schema_version == "1"
    assert historical.conditions[0].as_dict()["condition_fingerprint"] == (
        "fa94528f36d543f0f3851065009c17d5f9d58bceb652accf513e4c1b0b90c065"
    )

    v2_path = tmp_path / "matrix-v2.json"
    v2_path.write_text(json.dumps(_v2_document()), encoding="utf-8")
    resolved = load_evaluation_matrix(v2_path)

    assert resolved.schema_version == "2"
    assert resolved.conditions[0].condition_id == (
        "l1-minimax-m3-adaptive-development-v1"
    )
    assert resolved.conditions[0].effective_condition["treatment"]["model"] == (
        "MiniMax-M3"
    )


@pytest.mark.parametrize("policy_field", ["repeat_count", "max_case_concurrency"])
def test_execution_policy_changes_only_execution_and_run_configuration_identity(
    tmp_path: Path,
    policy_field: str,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    changed_path = tmp_path / "changed.json"
    baseline = _v2_document()
    changed = _v2_document()
    changed["conditions"][0]["execution_policy"][policy_field] = 2
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    changed_path.write_text(json.dumps(changed), encoding="utf-8")

    baseline_matrix = load_evaluation_matrix(baseline_path)
    changed_matrix = load_evaluation_matrix(changed_path)
    baseline_condition = baseline_matrix.conditions[0]
    changed_condition = changed_matrix.conditions[0]

    assert baseline_condition.treatment_fingerprint == (
        changed_condition.treatment_fingerprint
    )
    assert baseline_condition.condition_fingerprint == (
        changed_condition.condition_fingerprint
    )
    assert baseline_condition.execution_policy_fingerprint != (
        changed_condition.execution_policy_fingerprint
    )
    common = {
        "suite_fingerprint": "5" * 64,
        "selected_cases": [
            {"case_id": "case-a", "case_fingerprint": "6" * 64, "weight": 1}
        ],
        "code_revision": "a" * 40,
        "git_dirty": False,
    }
    assert calculate_run_configuration_fingerprint(
        baseline_matrix, baseline_condition, **common
    ) != calculate_run_configuration_fingerprint(
        changed_matrix, changed_condition, **common
    )


def test_matrix_v2_rejects_missing_required_treatment_field(tmp_path: Path) -> None:
    document = _v2_document()
    del document["conditions"][0]["treatment"]["context"]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(EvaluationMatrixError, match="missing required field 'context'"):
        load_evaluation_matrix(path)


class _RecordingTransport:
    def __init__(self, response: dict | None = None) -> None:
        self.payloads: list[dict] = []
        self.response = response or {
            "id": "request-39",
            "model": "MiniMax-M3",
            "choices": [
                {
                    "message": {
                        "content": '{"schema_version":"1"}',
                        "reasoning_content": "private reasoning",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 178, "completion_tokens": 9},
        }

    def complete(self, payload: dict):
        self.payloads.append(payload)
        return self.response, 12


def _logical_request() -> LogicalCompletionRequest:
    return LogicalCompletionRequest(
        model="MiniMax-M3",
        messages=({"role": "user", "content": "diagnose this failure"},),
        reasoning={"thinking": {"type": "adaptive"}, "reasoning_split": True},
        generation={
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        },
        tools=None,
    )


def test_minimax_profile_maps_exact_qualified_payload_without_response_format() -> None:
    transport = _RecordingTransport()
    provider = MiniMaxProvider(transport=transport)

    observation = provider.complete(_logical_request())

    assert transport.payloads == [
        {
            "model": "MiniMax-M3",
            "messages": [{"role": "user", "content": "diagnose this failure"}],
            "thinking": {"type": "adaptive"},
            "reasoning_split": True,
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
        }
    ]
    assert "response_format" not in transport.payloads[0]
    assert observation.provider_request_id == "request-39"
    assert observation.visible_output == '{"schema_version":"1"}'
    assert observation.reasoning_output == "private reasoning"
    assert observation.usage["prompt_tokens"] == 178


def test_minimax_transport_failure_is_not_retried() -> None:
    class FailingTransport:
        def __init__(self) -> None:
            self.attempts = 0

        def complete(self, payload: dict):
            self.attempts += 1
            raise OpenAICompatibleTransportError(
                "request failed before a response was returned",
                code="model_provider_transport_error",
            )

    transport = FailingTransport()
    provider = MiniMaxProvider(transport=transport)

    with pytest.raises(OpenAICompatibleTransportError):
        provider.complete(_logical_request())
    assert transport.attempts == 1


def test_openai_compatible_transport_does_not_expose_api_key_in_errors(
    monkeypatch,
) -> None:
    secret = "sentinel-minimax-key-never-expose"
    attempts = 0

    def fail(request, timeout):
        nonlocal attempts
        attempts += 1
        assert request.get_header("Authorization") == f"Bearer {secret}"
        raise urllib.error.URLError(f"transport detail containing {secret}")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    transport = OpenAICompatibleChatCompletionsTransport(
        base_url="https://api.minimaxi.com/v1",
        api_key=secret,
        timeout_seconds=600,
    )

    with pytest.raises(OpenAICompatibleTransportError) as captured:
        transport.complete({"model": "MiniMax-M3"})

    assert attempts == 1
    assert secret not in str(captured.value)
    assert captured.value.code == "model_provider_transport_error"


def test_minimax_exact_counter_uses_pinned_official_adaptive_chat_template() -> None:
    provider = MiniMaxProvider(transport=_RecordingTransport())

    count = provider.count_input_tokens(_logical_request())

    assert MINIMAX_M3_TOKENIZER_REVISION == (
        "f0e1c1e04d40177e4673a22097036854f536e9c0"
    )
    assert MINIMAX_M3_TOKENIZER_SHA256 == (
        "bb1f1626cf01448f1e3b6036d0a061ffc66c91d9046aada14ea23a5441b5ad6e"
    )
    assert MINIMAX_M3_CHAT_TEMPLATE_SHA256 == (
        "11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64"
    )
    assert count.method == "minimax_m3_official_chat_template_adaptive_v1"
    assert count.input_tokens == 180


class _FakeMiniMaxProvider:
    def __init__(self, *, input_tokens: int = 1000) -> None:
        self.input_tokens = input_tokens
        self.requests: list[LogicalCompletionRequest] = []

    def count_input_tokens(self, request: LogicalCompletionRequest) -> ExactTokenCount:
        return ExactTokenCount(
            input_tokens=self.input_tokens,
            method="minimax_m3_official_chat_template_adaptive_v1",
        )

    def complete(self, request: LogicalCompletionRequest) -> CompletionObservation:
        self.requests.append(request)
        return CompletionObservation(
            visible_output=json.dumps(
                {
                    "schema_version": "1",
                    "case_id": SMOKE_CASE_ID,
                    "classification_status": "inconclusive",
                    "failure_type": None,
                    "summary": "The evidence requires further diagnosis.",
                    "root_cause": "The exact cause is not sufficiently supported.",
                    "recommended_action": "Inspect the cited log evidence.",
                    "confidence": 0.2,
                    "evidence_references": [
                        {"evidence_id": "log:raw-log:lines-0001-0100"}
                    ],
                }
            ),
            reasoning_output="private hidden reasoning must never be persisted",
            provider_request_id="minimax-request-39",
            returned_model="MiniMax-M3",
            usage={"prompt_tokens": self.input_tokens, "completion_tokens": 80},
            finish_reason="stop",
            latency_ms=42,
        )


def _debug_args(database: Path, artifacts: Path) -> list[str]:
    return [
        "eval",
        "debug",
        "--matrix",
        str(V2_MATRIX),
        "--registry",
        str(REGISTRY),
        "--suite",
        str(SUITE),
        "--condition",
        "l1-minimax-m3-adaptive-development-v1",
        "--case",
        SMOKE_CASE_ID,
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts),
    ]


def test_matrix_v2_minimax_fake_provider_cli_e2e_is_auditable_and_secret_free(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    secret = "sentinel-minimax-key-never-persist"
    provider = _FakeMiniMaxProvider()
    monkeypatch.setenv("MINIMAX_API_KEY", secret)
    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: provider,
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: False)
    database = tmp_path / "run.db"
    artifacts = tmp_path / "artifacts"

    assert main(_debug_args(database, artifacts)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert len(provider.requests) == 1
    request = provider.requests[0]
    assert request.generation["response_format"] == {"mode": "omitted"}
    artifact_path = Path(output["artifacts"]["json"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    manifest = artifact["manifest"]
    assert manifest["manifest_schema_version"] == "2"
    assert manifest["matrix"]["schema_version"] == "2"
    assert manifest["git_dirty"] is False
    assert len(manifest["treatment_fingerprint"]) == 64
    assert len(manifest["condition_fingerprint"]) == 64
    assert len(manifest["execution_policy_fingerprint"]) == 64
    assert len(manifest["run_configuration_fingerprint"]) == 64
    completed = next(
        event for event in artifact["trace"] if event["event_type"] == "model_call_completed"
    )
    assert completed["payload"]["provider_request_id"] == "minimax-request-39"
    assert completed["payload"]["usage"]["prompt_tokens"] == 1000
    assert completed["payload"]["reasoning_observation"]["present"] is True
    assert "reasoning_output" not in completed["payload"]
    assert artifact["case_results"][0]["outcome"] == {"status": "scored"}
    assert artifact["case_results"][0]["context_assessment"]["input_tokens"] == 1000
    markdown = Path(output["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert "Treatment fingerprint" in markdown
    assert "Run configuration fingerprint" in markdown
    assert "Exact local input tokens: `1000`" in markdown
    assert "Provider request ID: `minimax-request-39`" in markdown
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_runs"
        ).fetchone() == ("completed",)
        assert connection.execute(
            "SELECT status FROM evaluation_case_outcomes"
        ).fetchone() == ("scored",)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_reports"
        ).fetchone() == (1,)
        manifest_json = connection.execute(
            "SELECT manifest_json FROM evaluation_run_manifests"
        ).fetchone()[0]
        trace_json = "".join(
            row[0]
            for row in connection.execute(
                "SELECT payload_json FROM evaluation_trace_events ORDER BY sequence"
            )
        )
    persisted = (
        artifact_path.read_text(encoding="utf-8")
        + markdown
        + manifest_json
        + trace_json
    )
    assert secret not in persisted
    assert "private hidden reasoning must never be persisted" not in persisted


def test_matrix_v2_context_infeasible_makes_zero_provider_calls(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    provider = _FakeMiniMaxProvider(input_tokens=950000)
    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: provider,
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "b" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: True)
    database = tmp_path / "run.db"
    artifacts = tmp_path / "artifacts"

    assert main(_debug_args(database, artifacts)) == 1

    output = json.loads(capsys.readouterr().out)
    assert provider.requests == []
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert artifact["case_results"][0]["outcome"]["failure_code"] == (
        "l1_context_infeasible"
    )
    assert not any(
        event["event_type"] == "model_call_started" for event in artifact["trace"]
    )
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_case_outcomes"
        ).fetchone() == ("execution_failed", "l1_context_infeasible")
