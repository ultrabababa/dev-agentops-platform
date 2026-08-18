from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

from devagentops.conditions.l1.development_output_contract import (
    output_contract_prompt_suffix,
)
from devagentops.conditions.l4.react_condition import (
    ConfiguredL4ConditionExecutor,
    ConfiguredL4Treatment,
)
from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.development_treatment import (
    L4_RUNTIME_CONTROL_VERSION,
    L4_TOOL_POLICY_VERSION,
    L4_TOOL_REGISTRY_VERSION,
    TASK_CONTRACT_VERSION,
)
from devagentops.evaluation.execution import PlannedSample, SampleIdentity
from devagentops.evaluation.suite import load_evaluation_suite
from devagentops.evaluation.trace import TraceRecorder
from devagentops.evaluation.matrix import load_evaluation_matrix
from devagentops.evaluation.run_v2 import run_formal_evaluation_v2
from devagentops.providers.contracts import ExactTokenCount
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "components/registry.json"
SUITE = ROOT / "evaluation/suites/triage-v1/suite.json"
MATRIX = ROOT / "evaluation/matrices/l4-minimax-m3-development-v2.json"


class FakeProvider:
    def __init__(self, report: str) -> None:
        self.report = report
        self.requests = []

    def count_input_tokens(self, request):
        assert len(request.tools) == 4
        assert request.system_prompt
        return ExactTokenCount(input_tokens=321, method="fake-exact")

    def complete(self, request):
        self.requests.append(request)
        return AssistantMessage(
            content=(
                ThinkingContent("private provider reasoning"),
                TextContent(self.report),
            ),
            response_id="fake-response",
            response_model="MiniMax-M3",
            usage=TokenUsage(input_tokens=321, output_tokens=100, total_tokens=421),
            stop_reason="stop",
            raw_stop_reason="stop",
            provider_fields={
                "reasoning_content": "private provider reasoning",
                "reasoning_details": [{"text": "private provider reasoning"}],
            },
        )


def test_l4_condition_reuses_sample_trace_scorer_and_separate_trajectory() -> None:
    suite = load_evaluation_suite(SUITE)
    suite_case = suite.cases[0]
    evidence_id = suite_case.package.canonical_evidence_units[0].evidence_id
    report = json.dumps(
        {
            "schema_version": "1",
            "case_id": suite_case.case_id,
            "classification_status": "inconclusive",
            "failure_type": None,
            "summary": "The available evidence is insufficient.",
            "root_cause": "The exact cause cannot be established from the observed facts.",
            "recommended_action": "Inspect the cited failure span and related source context.",
            "confidence": 0.4,
            "evidence_references": [{"evidence_id": evidence_id}],
        }
    )
    provider = FakeProvider(report)
    executor = ConfiguredL4ConditionExecutor(
        prompt=resolve_frozen_component_manifest(
            REGISTRY, "prompt", TASK_CONTRACT_VERSION
        ),
        runtime_control=resolve_frozen_component_manifest(
            REGISTRY, "prompt", L4_RUNTIME_CONTROL_VERSION
        ),
        tool_registry=resolve_frozen_component_manifest(
            REGISTRY, "tool_registry", L4_TOOL_REGISTRY_VERSION
        ),
        tool_policy=resolve_frozen_component_manifest(
            REGISTRY, "tool_policy", L4_TOOL_POLICY_VERSION
        ),
        treatment=ConfiguredL4Treatment(
            provider_id="fake",
            model="MiniMax-M3",
            reasoning={"thinking": {"type": "adaptive"}, "reasoning_split": True},
            generation={
                "temperature": 0,
                "max_completion_tokens": 65536,
                "n": 1,
                "stream": False,
                "response_format": {"mode": "omitted"},
            },
            context_limit_tokens=1_000_000,
            max_completion_tokens=65536,
            task_contract_version=TASK_CONTRACT_VERSION,
            runtime_control_version=L4_RUNTIME_CONTROL_VERSION,
            tool_registry_version=L4_TOOL_REGISTRY_VERSION,
            tool_policy_version=L4_TOOL_POLICY_VERSION,
            output_contract_prompt_suffix=output_contract_prompt_suffix(),
        ),
        provider_factory=lambda: provider,
    )
    identity = SampleIdentity("run", suite_case.case_id, 0, 1)
    recorder = TraceRecorder("run")
    result = executor.execute_sample(
        PlannedSample(identity=identity, suite_case=suite_case), recorder
    )

    assert result.status == "scored"
    assert result.data["terminal_reason"] == "report_submitted"
    assert result.data["validation"]["valid"] is True
    assert [message["role"] for message in result.trajectory] == ["user", "assistant"]
    assert result.trajectory[1]["provider_fields"]["reasoning_details"] == [
        {"text": "private provider reasoning"}
    ]
    assert "latency_ms" not in result.trajectory[1]
    completed = next(
        event
        for event in recorder.snapshot()
        if event["event_type"] == "model_call_completed"
    )
    assert isinstance(completed["payload"]["latency_ms"], int)
    trace_json = json.dumps(recorder.snapshot())
    assert "private provider reasoning" not in trace_json
    assert report not in trace_json
    initial_prompt = provider.requests[0].messages[0].content
    assert "required-evidence.json" not in initial_prompt
    assert "expected-answer.json" not in initial_prompt


def test_one_case_fake_formal_path_persists_trajectory_and_keeps_artifact_separate(
    tmp_path: Path, monkeypatch
) -> None:
    import devagentops.evaluation.run_v2 as run_v2

    suite = load_evaluation_suite(SUITE)
    one_case_suite = replace(suite, cases=(suite.cases[0],))
    suite_case = one_case_suite.cases[0]
    evidence_id = suite_case.package.canonical_evidence_units[0].evidence_id
    report = json.dumps(
        {
            "schema_version": "1",
            "case_id": suite_case.case_id,
            "classification_status": "inconclusive",
            "failure_type": None,
            "summary": "The evidence does not establish one definitive cause.",
            "root_cause": "The exact causal mechanism remains uncertain from the visible facts.",
            "recommended_action": "Inspect the cited span and compare it with the failing source path.",
            "confidence": 0.3,
            "evidence_references": [{"evidence_id": evidence_id}],
        }
    )
    monkeypatch.setattr(run_v2, "create_minimax_provider", lambda **_: FakeProvider(report))
    monkeypatch.setattr(run_v2, "_code_revision", lambda: "d" * 40)
    monkeypatch.setattr(run_v2, "_git_dirty", lambda: False)
    matrix = load_evaluation_matrix(MATRIX, REGISTRY)
    database = tmp_path / "l4.db"
    artifacts = tmp_path / "artifacts"
    result = run_formal_evaluation_v2(
        matrix=matrix,
        suite=one_case_suite,
        condition=matrix.conditions[0],
        registry_path=REGISTRY,
        database_path=database,
        artifacts_dir=artifacts,
    )
    assert result["status"] == "completed"
    assert result["planned_sample_count"] == 3
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_trajectory_messages"
        ).fetchone() == (6,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_trace_events WHERE payload_json LIKE '%private provider reasoning%'"
        ).fetchone() == (0,)
    artifact = json.loads(
        (artifacts / result["run_id"] / "evaluation.json").read_text(encoding="utf-8")
    )
    assert "trajectory" not in json.dumps(artifact)
    assert "private provider reasoning" not in json.dumps(artifact)
