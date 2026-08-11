import json
import shutil
import sqlite3
import urllib.error
from pathlib import Path

import devagentops.evaluation_run as evaluation_run
from devagentops.cli import main
from devagentops.component_registry import component_fingerprint, load_component_manifest
from devagentops.evaluation_suite import load_case_package
from devagentops.full_context_one_shot import serialize_complete_runtime_input
from devagentops.full_context_one_shot import (
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
    run_full_context_one_shot,
)
from devagentops.model_provider import (
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    SiliconFlowProvider,
    TokenCount,
)
from devagentops.runtime_workspace import RuntimeCaseWorkspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_TASK_CONTRACT = (
    PROJECT_ROOT
    / "components"
    / "frozen"
    / "prompt"
    / "structured-triage-task-contract-v1.json"
)
REGISTRY = PROJECT_ROOT / "components" / "registry.json"
CASE_MANIFEST = (
    Path(__file__).parent
    / "fixtures"
    / "evaluation"
    / "cases"
    / "constructed-assertion-001"
    / "case.json"
)
SUITE_MANIFEST = Path(__file__).parent / "fixtures" / "evaluation" / "tiny-suite.json"

FROZEN_TASK_TEMPLATE = """You are performing DevAgentOps triage for one frozen CI/test failure Case.

Your task is to diagnose the observed failure.

Grounding and citation rules:

- Base the diagnosis only on evidence made available during the current Runtime execution.
- Do not assume facts that are not supported by the available evidence.
- Never invent an Evidence ID.
- Cite only answer-neutral Evidence IDs made available during the current execution.
- Do not cite the same Evidence ID more than once.
- If the available evidence is insufficient for a defensible diagnosis, use
  "inconclusive" rather than guessing.
- Respect the forbidden actions supplied for the Case.
- Do not claim that an action was performed when it was forbidden or when the
  available evidence does not establish that it occurred.

Classification rules:

- classification_status must be either "classified" or "inconclusive".
- For "classified", failure_type must be exactly one of:
  - "test_assertion_failure"
  - "lint_or_type_failure"
  - "dependency_or_install_failure"
  - "config_or_environment_failure"
  - "timeout_or_flaky_failure"
- For "inconclusive", failure_type must be null.

Final deliverable rules:

- The final diagnostic result of the Runtime execution must be exactly one
  DevAgentOps Structured Triage Report V1 object.
- When producing that final report, return only the report object through the
  configured structured-output protocol.
- When producing that final report, do not add Markdown or explanatory text
  outside the report object.
- schema_version must be "1".
- case_id must exactly match the Runtime-supplied Case ID.
- summary must concisely describe the observed failure.
- root_cause must explain the most defensible cause supported by the evidence.
- recommended_action must propose a concrete diagnostic or remediation next step
  without claiming that the action has already been performed.
- confidence must be a number from 0 to 1.
- evidence_references must be a non-empty list of available Evidence IDs supporting
  the report.
- Write summary, root_cause, and recommended_action in concise English.

Case-specific Runtime input:

{runtime_input}"""


def test_frozen_task_contract_matches_issue_30() -> None:
    manifest = load_component_manifest(FROZEN_TASK_CONTRACT)

    assert manifest.component_type == "prompt"
    assert manifest.component_version == "structured-triage-task-contract-v1"
    assert manifest.behavior == {
        "template": FROZEN_TASK_TEMPLATE,
        "variables": ["runtime_input"],
    }

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    record = registry["components"]["prompt"][
        "structured-triage-task-contract-v1"
    ]
    assert record["manifest"] == (
        "frozen/prompt/structured-triage-task-contract-v1.json"
    )
    assert record["fingerprint"] == component_fingerprint(manifest)
    assert FROZEN_TASK_TEMPLATE.count("{runtime_input}") == 1
    for runtime_control in (
        "full_context_one_shot",
        "one-shot",
        "no tools",
        "retrieval",
        "runtime stage",
        "runtime loop",
        "stop rule",
    ):
        assert runtime_control not in FROZEN_TASK_TEMPLATE.casefold()


def test_complete_runtime_input_serializes_every_agent_visible_artifact() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)

    first = serialize_complete_runtime_input(workspace)
    second = serialize_complete_runtime_input(workspace)

    assert first == second
    assert first.version == "full_context_runtime_input_v1"
    assert first.byte_count == len(first.text.encode("utf-8"))
    document = json.loads(first.text)
    assert package.case_id in first.text
    assert package.raw_log_path in first.text
    artifacts = document["physical_artifacts"]
    assert artifacts[0]["content"] == workspace.read_raw_log()
    assert [
        artifact["repository_relative_path"] for artifact in artifacts[1:]
    ] == sorted(workspace.list_repository_files())
    for repository_path in workspace.list_repository_files():
        assert repository_path in first.text
        assert any(
            artifact.get("repository_relative_path") == repository_path
            and artifact["content"] == workspace.read_repository_file(repository_path)
            for artifact in artifacts
        )
    for unit in package.canonical_evidence_units:
        assert unit.evidence_id in first.text
        assert unit.source in first.text
        assert unit.content_sha256 in first.text
    assert document["canonical_evidence_coordinates"] == [
        coordinate.as_dict() for coordinate in workspace.canonical_coordinates
    ]
    assert set(document) == {
        "runtime_input_serialization_version",
        "case",
        "evidence_delivery",
        "physical_artifacts",
        "canonical_evidence_coordinates",
    }
    assert "evaluator/required-evidence.json" not in first.text
    assert "evaluator/expected-answer.json" not in first.text
    assert package.expected_answer.root_cause not in first.text


class DeterministicFakeProvider:
    def __init__(self, visible_output: str, *, input_tokens: int = 1000) -> None:
        self.visible_output = visible_output
        self.input_tokens = input_tokens
        self.requests = []

    def count_input_tokens(self, request):
        self.counted_request = request
        return TokenCount(
            input_tokens=self.input_tokens,
            method="deterministic_fake_tokenizer_v1",
        )

    def complete(self, request):
        self.requests.append(request)
        return ModelResponse(
            visible_output=self.visible_output,
            provider_request_id="fake-request-1",
            returned_model="Qwen/Qwen3.5-4B",
            usage={"prompt_tokens": self.input_tokens, "completion_tokens": 120},
            finish_reason="stop",
            latency_ms=7,
        )


def _write_l1_matrix(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "matrix_id": "issue-30-l1",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "l1-tiny-v1",
                        "type": "candidate",
                        "runtime_variant": "full_context_one_shot",
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


def _l1_eval_args(matrix: Path, database: Path, artifacts: Path) -> list[str]:
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
        "l1-tiny-v1",
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts),
    ]

def test_l1_executor_sends_exactly_one_frozen_user_message_and_request() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
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
    provider = DeterministicFakeProvider(json.dumps(report))

    result = run_full_context_one_shot(workspace, prompt, provider)

    assert result.candidate_document == report
    assert len(provider.requests) == 1
    request = provider.requests[0]
    assert request.model == "Qwen/Qwen3.5-4B"
    assert request.messages == (
        {
            "role": "user",
            "content": FROZEN_TASK_TEMPLATE.format(
                runtime_input=result.runtime_input.text
            ),
        },
    )
    assert request.response_format == STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA
    assert request.enable_thinking is False
    assert request.temperature == 0
    assert request.max_tokens == 1024
    assert request.completions == 1
    assert request.stream is False
    assert request.tools is None
    assert result.token_count.input_tokens == 1000
    assert result.context_limit_tokens == 262144


def test_eval_run_dispatches_l1_and_records_model_observations(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l1_matrix(matrix_path)
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
    provider = DeterministicFakeProvider(json.dumps(report))
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"

    exit_code = main(_l1_eval_args(matrix_path, database_path, artifacts_dir))

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    assert len(provider.requests) == 1
    output = json.loads(captured.out)
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    manifest = artifact["manifest"]
    assert manifest["runtime_variant"] == "full_context_one_shot"
    assert "pipeline_version" not in manifest
    assert manifest["model_configuration"]["model"] == "Qwen/Qwen3.5-4B"
    assert manifest["l1_execution"]["expected_model_calls_per_case"] == 1
    assert manifest["l1_execution"]["sdk_retries"] == 0
    events = artifact["trace"]
    returned = next(event for event in events if event["event_type"] == "model_call_completed")
    assert returned["payload"]["usage"]["prompt_tokens"] == 1000
    assert returned["payload"]["provider_request_id"] == "fake-request-1"
    assert returned["payload"]["visible_output"] == json.dumps(report)
    assert returned["payload"]["actual_call_count"] == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, runtime_variant FROM evaluation_runs"
        ).fetchone() == ("completed", "full_context_one_shot")
        assert connection.execute(
            "SELECT valid FROM evaluation_reports"
        ).fetchone() == (1,)


def test_context_infeasible_makes_zero_provider_calls() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    provider = DeterministicFakeProvider(
        "{}",
        input_tokens=262144 - 1024 + 1,
    )

    try:
        run_full_context_one_shot(workspace, prompt, provider)
    except Exception as exc:
        assert getattr(exc, "code", None) == "l1_context_infeasible"
    else:
        raise AssertionError("over-context L1 execution unexpectedly succeeded")

    assert provider.requests == []


def test_exact_context_boundary_remains_executable() -> None:
    package = load_case_package(CASE_MANIFEST)
    workspace = RuntimeCaseWorkspace.from_package(package)
    prompt = load_component_manifest(FROZEN_TASK_CONTRACT)
    provider = DeterministicFakeProvider(
        "{}",
        input_tokens=262144 - 1024,
    )

    run_full_context_one_shot(workspace, prompt, provider)

    assert len(provider.requests) == 1


def test_over_context_run_persists_failure_without_score(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l1_matrix(matrix_path)
    provider = DeterministicFakeProvider(
        "unused",
        input_tokens=262144 - 1024 + 1,
    )
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l1_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err)["code"] == "l1_context_infeasible"
    assert provider.requests == []
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_runs"
        ).fetchone() == ("failed", "l1_context_infeasible")
        assert connection.execute("SELECT COUNT(*) FROM evaluation_reports").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM evaluation_case_scores").fetchone() == (0,)
        failure_payload = json.loads(
            connection.execute(
                "SELECT payload_json FROM evaluation_trace_events WHERE event_type = 'failure'"
            ).fetchone()[0]
        )
        assert failure_payload["actual_call_count"] == 0


def test_formal_doctor_fails_before_provider_or_outputs(
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
    _write_l1_matrix(matrix_path)
    provider_factory_called = False

    def unexpected_provider():
        nonlocal provider_factory_called
        provider_factory_called = True
        raise AssertionError("provider must not be created before doctor succeeds")

    monkeypatch.setattr(evaluation_run, "create_model_provider", unexpected_provider)
    database_path = tmp_path / "devagentops.db"
    artifacts_dir = tmp_path / "artifacts"
    args = _l1_eval_args(matrix_path, database_path, artifacts_dir)
    args[args.index(str(SUITE_MANIFEST))] = str(evaluation_root / "tiny-suite.json")

    exit_code = main(args)

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err)["code"] == "invalid_case_manifest"
    assert provider_factory_called is False
    assert not database_path.exists()
    assert not artifacts_dir.exists()


def test_semantically_invalid_candidate_is_completed_without_repair(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l1_matrix(matrix_path)
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
    visible_output = json.dumps(conflict)
    provider = DeterministicFakeProvider(visible_output)
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l1_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    assert exit_code == 0, capsys.readouterr().err
    assert len(provider.requests) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT status FROM evaluation_runs").fetchone() == (
            "completed",
        )
        valid, report_json, validation_json = connection.execute(
            "SELECT valid, report_json, validation_json FROM evaluation_reports"
        ).fetchone()
        assert valid == 0
        assert json.loads(report_json) == conflict
        validation = json.loads(validation_json)
        assert validation["valid"] is False
        assert any(
            error["code"] == "failure_type_not_allowed_for_inconclusive"
            for error in validation["errors"]
        )


class RateLimitedFakeProvider(DeterministicFakeProvider):
    def complete(self, request):
        self.requests.append(request)
        raise ModelProviderError(
            "SiliconFlow request failed with HTTP 429",
            code="model_provider_rate_limited",
            http_status=429,
        )


def test_429_is_failed_once_without_report_or_score(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    matrix_path = tmp_path / "matrix.json"
    _write_l1_matrix(matrix_path)
    provider = RateLimitedFakeProvider("unused")
    monkeypatch.setattr(evaluation_run, "create_model_provider", lambda: provider)
    database_path = tmp_path / "devagentops.db"

    exit_code = main(
        _l1_eval_args(matrix_path, database_path, tmp_path / "artifacts")
    )

    error = json.loads(capsys.readouterr().err)
    assert exit_code == 2
    assert error["code"] == "model_provider_rate_limited"
    assert len(provider.requests) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_runs"
        ).fetchone() == ("failed", "model_provider_rate_limited")
        assert connection.execute("SELECT COUNT(*) FROM evaluation_reports").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM evaluation_case_scores").fetchone() == (0,)
        failure_payload = json.loads(
            connection.execute(
                "SELECT payload_json FROM evaluation_trace_events WHERE event_type = 'failure'"
            ).fetchone()[0]
        )
        assert failure_payload["http_status"] == 429
        assert failure_payload["actual_call_count"] == 1


def test_siliconflow_adapter_sanitizes_429_and_has_no_retry(
    monkeypatch,
) -> None:
    calls = []

    def rate_limited(request, *, timeout):
        calls.append((request, timeout))
        raise urllib.error.HTTPError(
            request.full_url,
            429,
            "rate limited",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", rate_limited)
    provider = SiliconFlowProvider(api_key="qualification-secret")
    request = ModelRequest(
        model="Qwen/Qwen3.5-4B",
        messages=({"role": "user", "content": "one message"},),
        response_format=STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
        enable_thinking=False,
        temperature=0,
        max_tokens=1024,
        completions=1,
        stream=False,
        tools=None,
    )

    try:
        provider.complete(request)
    except ModelProviderError as exc:
        assert exc.code == "model_provider_rate_limited"
        assert exc.http_status == 429
        assert "qualification-secret" not in str(exc)
    else:
        raise AssertionError("simulated 429 unexpectedly succeeded")

    assert len(calls) == 1
    sent = json.loads(calls[0][0].data)
    assert sent["messages"] == [{"role": "user", "content": "one message"}]
    assert "tools" not in sent
    assert sent["n"] == 1


def test_docs_freeze_task_contract_runtime_control_boundary() -> None:
    adr = (
        PROJECT_ROOT
        / "docs"
        / "adr"
        / "0127-staged-runtime-capability-ladder-and-reference-boundary.md"
    ).read_text(encoding="utf-8")
    methodology = (
        PROJECT_ROOT / "docs" / "evaluation" / "formal-evaluation-methodology.md"
    ).read_text(encoding="utf-8")

    adr_section = adr.split("### Task Contract and Runtime Control Separation", 1)[1]
    adr_section = adr_section.split("### Oracle is orthogonal", 1)[0]
    assert "case-specific data plane" in adr_section
    assert "must not conceal imperative Runtime control policy" in adr_section
    assert "explicit, versioned, and recorded as treatment" in adr_section
    methodology_section = methodology.split(
        "### 4.1 Shared Task Contract 与 Runtime Treatment", 1
    )[1]
    methodology_section = methodology_section.split("## 5.", 1)[0]
    assert "共享控制变量" in methodology_section
    assert "rendered request" in methodology_section
    assert "combined difference" in methodology_section
