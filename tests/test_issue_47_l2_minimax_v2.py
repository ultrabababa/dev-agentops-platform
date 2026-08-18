from __future__ import annotations

import json
from pathlib import Path

import pytest

from devagentops.conditions.l1.development_output_contract import (
    output_contract_prompt_suffix,
)
from devagentops.conditions.l2.development_workflow_v1 import (
    EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_PROMPT,
    EVIDENCE_ANALYSIS_STAGE,
    REPORT_SYNTHESIS_STAGE,
    ConfiguredFixedModelWorkflowError,
    ConfiguredL2Treatment,
    run_configured_fixed_model_workflow,
)
from devagentops.evaluation.components import load_component_manifest
from devagentops.evaluation.suite import load_case_package
from devagentops.providers.contracts import (
    ExactTokenCount,
)
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
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


class SequenceCompletionProvider:
    def __init__(
        self,
        *,
        visible_outputs: list[str],
        input_tokens: list[int],
    ) -> None:
        self.visible_outputs = visible_outputs
        self.input_tokens = input_tokens
        self.counted_requests = []
        self.requests = []

    def count_input_tokens(self, request):
        index = len(self.counted_requests)
        self.counted_requests.append(request)

        return ExactTokenCount(
            input_tokens=self.input_tokens[index],
            method="deterministic-minimax-fake-tokenizer-v1",
        )

    def complete(self, request):
        index = len(self.requests)
        self.requests.append(request)

        return AssistantMessage(
            content=(
                ThinkingContent(f"private-reasoning-stage-{index + 1}"),
                TextContent(self.visible_outputs[index]),
            ),
            response_id=f"fake-request-{index + 1}",
            response_model="MiniMax-M3",
            usage=TokenUsage(
                input_tokens=self.input_tokens[index],
                output_tokens=100 + index,
            ),
            stop_reason="stop",
            raw_stop_reason="stop",
        )


def _workspace() -> RuntimeCaseWorkspace:
    package = load_case_package(CASE_MANIFEST)
    return RuntimeCaseWorkspace.from_package(package)


def _prompt():
    return load_component_manifest(FROZEN_TASK_CONTRACT)


def _treatment() -> ConfiguredL2Treatment:
    return ConfiguredL2Treatment(
        provider_id="minimax-official",
        model="MiniMax-M3",
        reasoning={
            "thinking": {
                "type": "adaptive",
            },
            "reasoning_split": True,
        },
        generation={
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {
                "mode": "omitted",
            },
        },
        context_limit_tokens=1_000_000,
        max_completion_tokens=65536,
        task_contract_version="structured-triage-task-contract-v1",
        final_output_contract_prompt_suffix=(
            output_contract_prompt_suffix()
        ),
    )


def _memo(case_id: str) -> dict:
    return {
        "schema_version": "1",
        "case_id": case_id,
        "evidence_findings": [
            {
                "evidence_id": "log:assertion-mismatch",
                "finding": (
                    "The observed total was 6 while the test expected 5."
                ),
            }
        ],
        "working_failure_type": "test_assertion_failure",
        "causal_hypothesis": (
            "The implementation multiplies values instead of adding them."
        ),
        "uncertainties": [],
    }


def _report(case_id: str) -> dict:
    return {
        "schema_version": "1",
        "case_id": case_id,
        "classification_status": "classified",
        "failure_type": "test_assertion_failure",
        "summary": "The total assertion failed.",
        "root_cause": (
            "The implementation multiplies values instead of adding them."
        ),
        "recommended_action": (
            "Change the implementation to addition and rerun the test."
        ),
        "confidence": 0.99,
        "evidence_references": [
            {
                "evidence_id": "log:assertion-mismatch",
            }
        ],
    }


def test_configured_l2_runs_two_independent_requests_with_same_foundation_policy():
    workspace = _workspace()
    treatment = _treatment()

    memo_output = json.dumps(
        _memo(workspace.case.case_id),
        ensure_ascii=False,
    )
    report = _report(workspace.case.case_id)

    provider = SequenceCompletionProvider(
        visible_outputs=[
            memo_output,
            json.dumps(report, ensure_ascii=False),
        ],
        input_tokens=[
            120_000,
            125_000,
        ],
    )

    result = run_configured_fixed_model_workflow(
        workspace,
        _prompt(),
        provider,
        treatment,
    )

    assert result.candidate_document == report

    assert len(provider.counted_requests) == 2
    assert len(provider.requests) == 2

    stage_1_request, stage_2_request = provider.requests

    for request in provider.requests:
        assert request.model == "MiniMax-M3"
        assert request.reasoning == treatment.reasoning
        assert request.generation == treatment.generation
        assert request.tools == ()

        assert len(request.messages) == 1
        assert request.messages[0].__class__.__name__ == "UserMessage"

        assert request.generation["response_format"] == {
            "mode": "omitted",
        }

    stage_1_text = stage_1_request.messages[0].content
    stage_2_text = stage_2_request.messages[0].content

    # Both stages receive the complete Evidence Universe.
    assert result.complete_runtime_input.text in stage_1_text
    assert result.complete_runtime_input.text in stage_2_text

    # Stage 1 uses its own prompt-only intermediate-output contract.
    assert EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_PROMPT in stage_1_text
    assert (
        treatment.final_output_contract_prompt_suffix
        not in stage_1_text
    )

    # Stage 2 receives the exact canonical handoff and the same final-output
    # clarification contract already used by the L1 MiniMax treatment.
    assert result.handoff.text in stage_2_text
    assert (
        treatment.final_output_contract_prompt_suffix
        in stage_2_text
    )

    # No provider-side conversation-history representation is used.
    assert len(stage_1_request.messages) == 1
    assert len(stage_2_request.messages) == 1


def test_configured_l2_handoff_preserves_exact_stage_1_visible_output():
    workspace = _workspace()
    treatment = _treatment()

    memo_output = json.dumps(
        _memo(workspace.case.case_id),
        ensure_ascii=False,
        indent=2,
    )
    report = _report(workspace.case.case_id)

    provider = SequenceCompletionProvider(
        visible_outputs=[
            memo_output,
            json.dumps(report),
        ],
        input_tokens=[
            100_000,
            110_000,
        ],
    )

    result = run_configured_fixed_model_workflow(
        workspace,
        _prompt(),
        provider,
        treatment,
    )

    handoff_document = json.loads(result.handoff.text)

    assert handoff_document["source_stage"] == EVIDENCE_ANALYSIS_STAGE
    assert handoff_document["visible_output"] == memo_output
    assert result.handoff.visible_output_sha256

    stage_2_text = provider.requests[1].messages[0].content

    assert result.handoff.text in stage_2_text


def test_invalid_stage_1_memo_is_observational_and_does_not_gate_stage_2():
    workspace = _workspace()
    treatment = _treatment()

    invalid_memo = (
        "This is grounded working analysis, but it is deliberately not JSON."
    )
    report = _report(workspace.case.case_id)

    provider = SequenceCompletionProvider(
        visible_outputs=[
            invalid_memo,
            json.dumps(report),
        ],
        input_tokens=[
            100_000,
            110_000,
        ],
    )

    result = run_configured_fixed_model_workflow(
        workspace,
        _prompt(),
        provider,
        treatment,
    )

    assert len(provider.requests) == 2

    assert result.evidence_analysis_observation == {
        "json_valid": False,
        "schema_valid": False,
        "case_id_matches": None,
        "evidence_ids_known": None,
    }

    handoff_document = json.loads(result.handoff.text)

    assert handoff_document["visible_output"] == invalid_memo
    assert result.handoff.text in provider.requests[1].messages[0].content
    assert result.candidate_document == report


def test_stage_2_context_infeasible_preserves_truthful_partial_execution():
    workspace = _workspace()
    treatment = _treatment()

    memo_output = json.dumps(
        _memo(workspace.case.case_id),
        ensure_ascii=False,
    )

    provider = SequenceCompletionProvider(
        visible_outputs=[
            memo_output,
        ],
        input_tokens=[
            100_000,
            950_000,
        ],
    )

    with pytest.raises(
        ConfiguredFixedModelWorkflowError,
    ) as exc_info:
        run_configured_fixed_model_workflow(
            workspace,
            _prompt(),
            provider,
            treatment,
        )

    error = exc_info.value

    assert error.code == "l2_context_infeasible"
    assert error.stage_id == REPORT_SYNTHESIS_STAGE

    # Stage 1 was actually dispatched.
    assert len(provider.requests) == 1

    # Stage 2 was token-counted/preflighted but never sent to the provider.
    assert len(provider.counted_requests) == 2

    assert error.context_metadata == {
        "input_tokens": 950_000,
        "token_count_method": (
            "deterministic-minimax-fake-tokenizer-v1"
        ),
        "max_output_tokens": 65536,
        "context_limit_tokens": 1_000_000,
    }


def test_stage_callbacks_expose_ordered_two_stage_execution_without_raw_reasoning():
    workspace = _workspace()
    treatment = _treatment()

    provider = SequenceCompletionProvider(
        visible_outputs=[
            json.dumps(_memo(workspace.case.case_id)),
            json.dumps(_report(workspace.case.case_id)),
        ],
        input_tokens=[
            100_000,
            110_000,
        ],
    )

    started = []
    completed = []

    run_configured_fixed_model_workflow(
        workspace,
        _prompt(),
        provider,
        treatment,
        before_model_call=started.append,
        after_model_call=completed.append,
    )

    assert [
        item["stage_id"]
        for item in started
    ] == [
        EVIDENCE_ANALYSIS_STAGE,
        REPORT_SYNTHESIS_STAGE,
    ]

    assert [
        item["logical_call_number"]
        for item in started
    ] == [1, 2]

    assert [
        item["stage_id"]
        for item in completed
    ] == [
        EVIDENCE_ANALYSIS_STAGE,
        REPORT_SYNTHESIS_STAGE,
    ]

    assert [
        item["logical_call_number"]
        for item in completed
    ] == [1, 2]

    # Only derived metadata about private reasoning leaves the workflow seam.
    assert all(
        "reasoning_output" not in item
        for item in completed
    )

    for item in completed:
        observation = item["reasoning_observation"]
        assert observation["present"] is True
        assert observation["character_count"] > 0
        assert observation["sha256"]


def _planned_sample():
    from devagentops.evaluation.execution import (
        PlannedSample,
        SampleIdentity,
    )
    from devagentops.evaluation.suite import SuiteCase

    package = load_case_package(CASE_MANIFEST)

    suite_case = SuiteCase(
        case_id=package.case_id,
        manifest=str(CASE_MANIFEST),
        weight=1,
        package=package,
    )

    return PlannedSample(
        identity=SampleIdentity(
            run_id="run-1",
            case_id=package.case_id,
            repeat_index=0,
            sample_sequence=1,
        ),
        suite_case=suite_case,
    )


def test_l2_condition_executor_emits_truthful_two_stage_trace():
    from devagentops.conditions.l2.executor import (
        ConfiguredL2ConditionExecutor,
    )
    from devagentops.evaluation.trace import TraceRecorder

    sample = _planned_sample()
    case_id = sample.identity.case_id

    provider = SequenceCompletionProvider(
        visible_outputs=[
            json.dumps(_memo(case_id)),
            json.dumps(_report(case_id)),
        ],
        input_tokens=[
            100_000,
            110_000,
        ],
    )

    executor = ConfiguredL2ConditionExecutor(
        prompt=_prompt(),
        treatment=_treatment(),
        provider_factory=lambda: provider,
    )

    recorder = TraceRecorder("run-1")

    result = executor.execute_sample(
        sample,
        recorder,
    )

    assert result.status == "scored"
    assert len(provider.requests) == 2

    events = list(recorder.snapshot())

    assert [
        event["event_type"]
        for event in events
    ] == [
        "l2_execution_started",
        "model_call_started",
        "model_call_completed",
        "model_call_started",
        "model_call_completed",
        "report_submitted",
        "evaluation_completed",
    ]

    model_events = [
        event
        for event in events
        if event["event_type"]
        in {
            "model_call_started",
            "model_call_completed",
        }
    ]

    assert [
        event["payload"]["stage_id"]
        for event in model_events
    ] == [
        EVIDENCE_ANALYSIS_STAGE,
        EVIDENCE_ANALYSIS_STAGE,
        REPORT_SYNTHESIS_STAGE,
        REPORT_SYNTHESIS_STAGE,
    ]

    assert [
        event["payload"]["logical_call_number"]
        for event in model_events
    ] == [
        1,
        1,
        2,
        2,
    ]

    assert result.data["l2_workflow"][
        "actual_call_count"
    ] == 2

    assert len(
        result.data["l2_workflow"][
            "stage_observations"
        ]
    ) == 2

    assert len(
        result.data["l2_workflow"][
            "stage_context_assessments"
        ]
    ) == 2

    # Raw/private model reasoning must never enter Sample data.
    serialized = json.dumps(
        result.data,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "private-reasoning-stage-1" not in serialized
    assert "private-reasoning-stage-2" not in serialized


def test_l2_condition_executor_stage_1_context_failure_makes_zero_calls():
    from devagentops.conditions.l2.executor import (
        ConfiguredL2ConditionExecutor,
    )
    from devagentops.evaluation.trace import TraceRecorder

    sample = _planned_sample()

    provider = SequenceCompletionProvider(
        visible_outputs=[],
        input_tokens=[
            950_000,
        ],
    )

    executor = ConfiguredL2ConditionExecutor(
        prompt=_prompt(),
        treatment=_treatment(),
        provider_factory=lambda: provider,
    )

    recorder = TraceRecorder("run-1")

    result = executor.execute_sample(
        sample,
        recorder,
    )

    assert result.status == "execution_failed"

    assert result.data["outcome"][
        "failure_code"
    ] == "l2_context_infeasible"

    assert result.data["outcome"][
        "failure_stage"
    ] == EVIDENCE_ANALYSIS_STAGE

    assert len(provider.counted_requests) == 1
    assert len(provider.requests) == 0

    failure = [
        event
        for event in recorder.snapshot()
        if event["event_type"] == "failure"
    ][0]

    assert failure["payload"][
        "actual_call_count"
    ] == 0

    assert failure["payload"][
        "failure_kind"
    ] == "context_feasibility"


def test_l2_condition_executor_stage_2_context_failure_preserves_one_call():
    from devagentops.conditions.l2.executor import (
        ConfiguredL2ConditionExecutor,
    )
    from devagentops.evaluation.trace import TraceRecorder

    sample = _planned_sample()
    case_id = sample.identity.case_id

    provider = SequenceCompletionProvider(
        visible_outputs=[
            json.dumps(_memo(case_id)),
        ],
        input_tokens=[
            100_000,
            950_000,
        ],
    )

    executor = ConfiguredL2ConditionExecutor(
        prompt=_prompt(),
        treatment=_treatment(),
        provider_factory=lambda: provider,
    )

    recorder = TraceRecorder("run-1")

    result = executor.execute_sample(
        sample,
        recorder,
    )

    assert result.status == "execution_failed"

    assert result.data["outcome"][
        "failure_code"
    ] == "l2_context_infeasible"

    assert result.data["outcome"][
        "failure_stage"
    ] == REPORT_SYNTHESIS_STAGE

    # Stage 1 reached the provider.
    assert len(provider.requests) == 1

    # Stage 2 was exactly token-counted but rejected before dispatch.
    assert len(provider.counted_requests) == 2

    events = list(recorder.snapshot())

    assert [
        event["event_type"]
        for event in events
    ] == [
        "l2_execution_started",
        "model_call_started",
        "model_call_completed",
        "failure",
    ]

    failure = events[-1]

    assert failure["payload"][
        "actual_call_count"
    ] == 1

    assert failure["payload"][
        "stage"
    ] == REPORT_SYNTHESIS_STAGE


def test_l2_matrix_v2_preserves_l1_foundation_and_adds_only_workflow_capability():
    from devagentops.evaluation.development_treatment import (
        validate_minimax_development_condition,
    )
    from devagentops.evaluation.matrix_v2 import (
        load_evaluation_matrix_v2,
    )

    l1_matrix = load_evaluation_matrix_v2(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l1-minimax-m3-development-v2.json",
        PROJECT_ROOT / "components" / "registry.json",
    )

    l2_matrix = load_evaluation_matrix_v2(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l2-minimax-m3-development-v2.json",
        PROJECT_ROOT / "components" / "registry.json",
    )

    l1 = l1_matrix.conditions[0]
    l2 = l2_matrix.conditions[0]

    validate_minimax_development_condition(
        l1.effective_condition,
        20,
    )
    validate_minimax_development_condition(
        l2.effective_condition,
        20,
    )

    assert (
        l1.effective_condition["runtime_variant"]
        == "full_context_one_shot"
    )
    assert (
        l2.effective_condition["runtime_variant"]
        == "fixed_model_workflow"
    )

    l1_treatment = l1.effective_condition["treatment"]
    l2_treatment = l2.effective_condition["treatment"]

    # Foundation model/inference policy is identical.
    for field in (
        "provider",
        "model",
        "reasoning",
        "generation",
        "context",
    ):
        assert l2_treatment[field] == l1_treatment[field]

    # Shared Task, final-report and Runtime-input contracts are identical.
    for field in (
        "task",
        "output",
        "runtime_input",
    ):
        assert (
            l2_treatment["contracts"][field]
            == l1_treatment["contracts"][field]
        )

    assert "workflow" not in l1_treatment["contracts"]

    assert l2_treatment["contracts"]["workflow"] == {
        "version": (
            "fixed-model-workflow-minimax-development-v1"
        ),
        "fingerprint": (
            "adeac998a5ab0c74bdfb3540a5517b6c"
            "86c1e5b835379e55f24daf2766bff40d"
        ),
    }

    # L2 differs as a complete Treatment because it adds fixed workflow
    # capability, even though the model foundation is held constant.
    assert (
        l2.treatment_fingerprint
        != l1.treatment_fingerprint
    )

    assert (
        l2.condition_fingerprint
        != l1.condition_fingerprint
    )

    # Historical L1 identities must remain literal invariants.
    assert l1.treatment_fingerprint == (
        "1d6387a25f7722c30b36be82eaf5f769"
        "9550472a9b136db5964a783c3da758f4"
    )

    assert l1.condition_fingerprint == (
        "c199208feb41748fd67095512871bcd406"
        "d108ed3444b98854adecf0aa1fcb2a"
    )

    assert l1.execution_policy_fingerprint == (
        "c1f3aa8327a858befa9b77a8cc4bce807"
        "98c5c98a5125a0c31158ce109225e5b"
    )

    assert (
        l2.execution_policy_fingerprint
        == l1.execution_policy_fingerprint
    )


def test_l2_formal_cli_runs_20x3_with_exactly_two_calls_per_sample(
    tmp_path,
    monkeypatch,
    capsys,
):
    import devagentops.evaluation.run_v2 as evaluation_run_v2
    from devagentops.cli import main
    from devagentops.providers.contracts import (
        ExactTokenCount,
    )

    matrix = (
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l2-minimax-m3-development-v2.json"
    )
    registry = PROJECT_ROOT / "components" / "registry.json"
    suite = (
        PROJECT_ROOT
        / "evaluation"
        / "suites"
        / "triage-v1"
        / "suite.json"
    )
    condition = "l2-minimax-m3-adaptive-development-v1"

    providers = []

    class FormalFakeProvider:
        def __init__(self, provider_index):
            self.provider_index = provider_index
            self.complete_calls = 0
            self.requests = []

        def count_input_tokens(self, request):
            return ExactTokenCount(
                input_tokens=1000,
                method="exact-fake-count",
            )

        def complete(self, request):
            self.complete_calls += 1
            self.requests.append(request)

            if self.complete_calls == 1:
                visible_output = (
                    "stage-1-analysis-intentionally-not-json"
                )
            elif self.complete_calls == 2:
                visible_output = (
                    "stage-2-report-intentionally-not-json"
                )
            else:
                raise AssertionError(
                    "L2 Sample made more than two provider calls"
                )

            return AssistantMessage(
                content=(
                    ThinkingContent("private-l2-reasoning-must-not-persist"),
                    TextContent(visible_output),
                ),
                response_id=(
                    f"l2-request-{self.provider_index}"
                    f"-{self.complete_calls}"
                ),
                response_model="MiniMax-M3",
                usage=TokenUsage(input_tokens=1000, output_tokens=10),
                stop_reason="stop",
                raw_stop_reason="stop",
            )

    def provider_factory(**kwargs):
        provider = FormalFakeProvider(len(providers))
        providers.append(provider)
        return provider

    monkeypatch.setattr(
        evaluation_run_v2,
        "create_minimax_provider",
        provider_factory,
    )
    monkeypatch.setattr(
        evaluation_run_v2,
        "_code_revision",
        lambda: "b" * 40,
    )
    monkeypatch.setattr(
        evaluation_run_v2,
        "_git_dirty",
        lambda: False,
    )

    database = tmp_path / "devagentops.db"
    artifacts = tmp_path / "artifacts"

    exit_code = main(
        [
            "eval",
            "run",
            "--matrix",
            str(matrix),
            "--registry",
            str(registry),
            "--suite",
            str(suite),
            "--condition",
            condition,
            "--database",
            str(database),
            "--artifacts-dir",
            str(artifacts),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()

    # stdout remains exactly one final machine-readable JSON document.
    output = json.loads(captured.out)
    assert captured.out.count("\n") == 1

    # Progress remains Sample-level: 60 terminal records, not 120 Stage records.
    assert "Evaluation: 60 samples | concurrency=6" in captured.err
    assert captured.err.count("] scored ") == 60

    assert output["status"] == "completed"
    assert output["condition_id"] == condition
    assert output["planned_sample_count"] == 60
    assert output["suite_quality_status"] == "complete"

    assert output["fingerprints"]["treatment"] == (
        "10361eddc287886ef5d634d2a81b163c"
        "d859c0802b40ec164f34c5fb240a0f50"
    )
    assert output["fingerprints"]["condition"] == (
        "92e4260209f63d8c13eea5de821ea0e"
        "53ba40d47b468b14feac4ab163d9335d1"
    )
    assert output["fingerprints"]["execution_policy"] == (
        "c1f3aa8327a858befa9b77a8cc4bce807"
        "98c5c98a5125a0c31158ce109225e5b"
    )

    # One provider instance per Sample, exactly two sequential model calls.
    assert len(providers) == 60
    assert sum(
        provider.complete_calls
        for provider in providers
    ) == 120
    assert all(
        provider.complete_calls == 2
        for provider in providers
    )

    for provider in providers:
        assert len(provider.requests) == 2

        first, second = provider.requests

        # Both stages inherit the exact same MiniMax foundation policy.
        assert first.model == second.model == "MiniMax-M3"
        assert first.reasoning == second.reasoning
        assert first.generation == second.generation

        assert first.generation["response_format"] == {
            "mode": "omitted",
        }

    artifact = json.loads(
        Path(output["artifacts"]["json"]).read_text()
    )
    markdown = Path(
        output["artifacts"]["markdown"]
    ).read_text()

    assert artifact["manifest"]["runtime_variant"] == (
        "fixed_model_workflow"
    )
    assert artifact["manifest"]["experiment_identity"] == (
        "l2-development-treatment-integration"
    )
    assert artifact["manifest"]["tool_call_protocol"] == {
        "applicability": "not_applicable",
        "reason": "fixed_model_workflow_has_no_tools",
    }

    assert len(artifact["sample_results"]) == 60
    assert len(artifact["case_aggregates"]) == 20
    assert len(artifact["failure_type_aggregates"]) == 5

    assert artifact["suite_aggregate"][
        "total_case_count"
    ] == 20
    assert artifact["suite_aggregate"][
        "requested_sample_count"
    ] == 60
    assert artifact["suite_aggregate"][
        "scored_sample_count"
    ] == 60
    assert artifact["suite_aggregate"][
        "protocol_invalid_sample_count"
    ] == 60
    assert artifact["suite_aggregate"][
        "quality_status"
    ] == "complete"

    events = artifact["trace"]

    assert sum(
        event["event_type"] == "model_call_started"
        for event in events
    ) == 120
    assert sum(
        event["event_type"] == "model_call_completed"
        for event in events
    ) == 120
    assert sum(
        event["event_type"] == "l2_execution_started"
        for event in events
    ) == 60

    started = [
        event
        for event in events
        if event["event_type"] == "model_call_started"
    ]

    assert sum(
        event["payload"]["stage_id"]
        == EVIDENCE_ANALYSIS_STAGE
        for event in started
    ) == 60
    assert sum(
        event["payload"]["stage_id"]
        == REPORT_SYNTHESIS_STAGE
        for event in started
    ) == 60

    assert (
        "# DevAgentOps Formal L2 Development Evaluation"
        in markdown
    )
    assert (
        "L2 development-treatment integration evaluation"
        in markdown
    )
    assert (
        "L1 development-treatment milestone experiment"
        not in markdown
    )

    serialized_artifact = json.dumps(
        artifact,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert (
        "private-l2-reasoning-must-not-persist"
        not in serialized_artifact
    )
