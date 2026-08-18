from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
)

from devagentops.conditions.oracle.evidence_v1 import (
    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT,
    ORACLE_EVIDENCE_PACK_VERSION,
    ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION,
    OracleEvidenceError,
    oracle_evidence_delivery_contract,
    resolve_oracle_evidence_pack,
    serialize_oracle_evidence_pack,
)
from devagentops.evaluation.suite import load_case_package


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORMAL_CASE = (
    PROJECT_ROOT
    / "evaluation"
    / "suites"
    / "triage-v1"
    / "cases"
    / "bugswarm-traccar-170287308"
    / "case.json"
)


def _canonical_sha256(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def test_oracle_pack_resolves_only_required_source_evidence() -> None:
    package = load_case_package(FORMAL_CASE)

    pack = resolve_oracle_evidence_pack(package)
    serialized = serialize_oracle_evidence_pack(pack)
    document = json.loads(serialized.text)

    required_ids = set(
        package.evidence_ground_truth.required_evidence_ids
    )
    optional_ids = set(
        package.evidence_ground_truth.optional_evidence_ids
    )

    assert pack.pack_version == ORACLE_EVIDENCE_PACK_VERSION
    assert pack.case_id == package.case_id
    assert pack.case_schema_version == package.case_schema_version
    assert pack.case_fingerprint == package.case_fingerprint

    assert {item.evidence_id for item in pack.items} == required_ids
    assert not (
        {item.evidence_id for item in pack.items}
        & optional_ids
    )

    assert [item.evidence_id for item in pack.items] == [
        "log:raw-log:lines-2301-2400",
        (
            "repo:src-org-traccar-protocol-"
            "uproprotocoldecoder-java:lines-0001-0083"
        ),
        (
            "repo:test-org-traccar-protocol-"
            "uproprotocoldecodertest-java:lines-0001-0033"
        ),
    ]

    assert document == pack.model_visible_document()

    assert set(document) == {
        "runtime_input_serialization_version",
        "case",
        "evidence_items",
    }

    assert document["runtime_input_serialization_version"] == (
        ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION
    )

    assert set(document["case"]) == {
        "case_id",
        "case_schema_version",
        "forbidden_actions",
    }

    # The full Case fingerprint is evaluator-derived: its frozen fingerprint
    # input includes Required Evidence Ground Truth and Expected Answer.
    # It remains useful for evaluator/runtime audit identity but must never be
    # part of Oracle model-visible input.
    assert "case_fingerprint" not in document["case"]

    assert all(
        set(item) == {
            "evidence_id",
            "source",
            "span",
            "content_sha256",
            "content",
        }
        for item in document["evidence_items"]
    )

    visible_ids = {
        item["evidence_id"]
        for item in document["evidence_items"]
    }

    assert visible_ids == required_ids
    assert visible_ids.isdisjoint(optional_ids)

    # Evaluator-selection structure is not model-visible.
    assert "required_evidence_ids" not in document
    assert "optional_evidence_ids" not in document
    assert "evidence_ground_truth" not in document
    assert "expected_answer" not in document
    assert "evidence_delivery" not in document

    # Internal Oracle identity is runtime/evaluator metadata, not part of the
    # model-visible envelope.
    assert "pack_version" not in document

    assert serialized.byte_count == len(
        serialized.text.encode("utf-8")
    )
    assert serialized.sha256 == hashlib.sha256(
        serialized.text.encode("utf-8")
    ).hexdigest()


def test_oracle_serialization_is_deterministic() -> None:
    package = load_case_package(FORMAL_CASE)

    first_pack = resolve_oracle_evidence_pack(package)
    second_pack = resolve_oracle_evidence_pack(package)

    first = serialize_oracle_evidence_pack(first_pack)
    second = serialize_oracle_evidence_pack(second_pack)

    assert first_pack == second_pack
    assert first == second


def test_required_evidence_file_order_does_not_affect_oracle_input() -> None:
    package = load_case_package(FORMAL_CASE)

    baseline = serialize_oracle_evidence_pack(
        resolve_oracle_evidence_pack(package)
    )

    reversed_ground_truth = replace(
        package.evidence_ground_truth,
        required_evidence_ids=tuple(
            reversed(
                package.evidence_ground_truth.required_evidence_ids
            )
        ),
    )

    reordered_package = replace(
        package,
        evidence_ground_truth=reversed_ground_truth,
    )

    reordered = serialize_oracle_evidence_pack(
        resolve_oracle_evidence_pack(reordered_package)
    )

    assert reordered == baseline


def test_expected_answer_does_not_affect_oracle_model_visible_input() -> None:
    package = load_case_package(FORMAL_CASE)

    baseline = serialize_oracle_evidence_pack(
        resolve_oracle_evidence_pack(package)
    )

    sentinel_summary = (
        "EVALUATOR_ONLY_SENTINEL_SUMMARY_"
        "ISSUE_19_DO_NOT_EXPOSE"
    )
    sentinel_root_cause = (
        "EVALUATOR_ONLY_SENTINEL_ROOT_CAUSE_"
        "ISSUE_19_DO_NOT_EXPOSE"
    )
    sentinel_action = (
        "EVALUATOR_ONLY_SENTINEL_ACTION_"
        "ISSUE_19_DO_NOT_EXPOSE"
    )

    mutated_expected_answer = replace(
        package.expected_answer,
        # Keep this syntactically inside the accepted taxonomy; the point of
        # this test is data-flow isolation, not package-loader validation.
        primary_failure_type="timeout_or_flaky_failure",
        acceptable_failure_types=("lint_or_type_failure",),
        summary=sentinel_summary,
        root_cause=sentinel_root_cause,
        recommended_action=sentinel_action,
    )

    mutated_package = replace(
        package,
        expected_answer=mutated_expected_answer,
    )

    mutated = serialize_oracle_evidence_pack(
        resolve_oracle_evidence_pack(mutated_package)
    )

    # Stronger than merely checking that the sentinel is absent:
    # changing evaluator-only diagnosis data must produce byte-identical
    # model-visible Runtime input.
    assert mutated == baseline

    for sentinel in (
        sentinel_summary,
        sentinel_root_cause,
        sentinel_action,
    ):
        assert sentinel not in mutated.text


def test_oracle_resolver_fails_closed_if_selected_source_changes_after_load(
    tmp_path: Path,
) -> None:
    source_case_root = FORMAL_CASE.parent
    copied_case_root = tmp_path / source_case_root.name

    shutil.copytree(
        source_case_root,
        copied_case_root,
    )

    copied_manifest = copied_case_root / "case.json"

    # Load while the copied frozen package is still internally consistent.
    package = load_case_package(copied_manifest)

    raw_log = (
        copied_case_root
        / "physical-artifacts"
        / "raw.log"
    )

    content = raw_log.read_bytes()
    lines = content.splitlines(keepends=True)

    assert len(lines) >= 2301

    # Mutate a byte range that belongs to a Required Evidence unit only after
    # the Case has passed normal package loading. The Oracle Resolver must
    # independently re-resolve and verify the selected source span.
    lines[2300] = b"ISSUE19_TAMPERED " + lines[2300]

    raw_log.write_bytes(b"".join(lines))

    with pytest.raises(OracleEvidenceError) as exc_info:
        resolve_oracle_evidence_pack(package)

    assert exc_info.value.code == "oracle_evidence_hash_mismatch"


def test_oracle_delivery_contract_has_stable_fingerprint() -> None:
    contract = oracle_evidence_delivery_contract()

    assert contract == {
        "id": "oracle_required_evidence_delivery",
        "version": "2",
        "pack_version": "oracle_evidence_pack_v1",
        "runtime_input_serialization_version": (
            "selected_evidence_runtime_input_v2"
        ),
        "selection": "required_evidence_ids_as_set",
        "ordering": (
            "canonical_source_start_end_evidence_id"
        ),
        "source_resolution": (
            "canonical_line_range_exact_bytes_v1"
        ),
        "integrity": "sha256_verified",
    }

    assert ORACLE_EVIDENCE_DELIVERY_FINGERPRINT == (
        _canonical_sha256(contract)
    )


def test_oracle_resolver_rejects_evaluator_artifact_as_selected_source() -> None:
    package = load_case_package(FORMAL_CASE)

    required_id = (
        package.evidence_ground_truth.required_evidence_ids[0]
    )

    original_unit = next(
        unit
        for unit in package.canonical_evidence_units
        if unit.evidence_id == required_id
    )

    expected_answer_path = (
        package.manifest_path.parent
        / "evaluator"
        / "expected-answer.json"
    )

    expected_answer_lines = (
        expected_answer_path
        .read_bytes()
        .splitlines(keepends=True)
    )

    assert expected_answer_lines

    evaluator_content_sha256 = hashlib.sha256(
        expected_answer_lines[0]
    ).hexdigest()

    malicious_unit = replace(
        original_unit,
        source="evaluator/expected-answer.json",
        start_line=1,
        end_line=1,
        content_sha256=evaluator_content_sha256,
    )

    malicious_units = tuple(
        malicious_unit
        if unit.evidence_id == required_id
        else unit
        for unit in package.canonical_evidence_units
    )

    malicious_package = replace(
        package,
        canonical_evidence_units=malicious_units,
    )

    with pytest.raises(OracleEvidenceError) as exc_info:
        resolve_oracle_evidence_pack(malicious_package)

    assert exc_info.value.code == (
        "oracle_source_not_physical_artifact"
    )


def test_oracle_matrix_v2_identity_is_explicit_and_preserves_foundation() -> None:
    from devagentops.evaluation.matrix import load_evaluation_matrix

    oracle_matrix = load_evaluation_matrix(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "oracle-minimax-m3-development-v2.json"
    )
    l1_matrix = load_evaluation_matrix(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l1-minimax-m3-development-v2.json"
    )

    oracle = oracle_matrix.conditions[0]
    l1 = l1_matrix.conditions[0]

    assert oracle.effective_condition["runtime_variant"] == (
        "model_one_shot"
    )

    oracle_treatment = oracle.effective_condition["treatment"]
    l1_treatment = l1.effective_condition["treatment"]

    # Foundation model / inference / context are controlled equal.
    for field in (
        "provider",
        "model",
        "reasoning",
        "generation",
        "context",
    ):
        assert oracle_treatment[field] == l1_treatment[field]

    oracle_contracts = oracle_treatment["contracts"]
    l1_contracts = l1_treatment["contracts"]

    # Diagnosis and final report contracts remain controlled equal.
    assert oracle_contracts["task"] == l1_contracts["task"]
    assert oracle_contracts["output"] == l1_contracts["output"]

    # Oracle changes the evidence-delivery/runtime-input treatment explicitly.
    assert oracle_contracts["runtime_input"] == {
        "version": ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION
    }
    assert oracle_contracts["evidence_delivery"] == (
        oracle_evidence_delivery_contract()
    )

    assert "evidence_delivery" not in l1_contracts

    # The intervention must change capability identity.
    assert oracle.treatment_fingerprint != l1.treatment_fingerprint
    assert oracle.condition_fingerprint != l1.condition_fingerprint

    # Execution policy is deliberately held fixed.
    assert (
        oracle.execution_policy_fingerprint
        == l1.execution_policy_fingerprint
    )


def test_oracle_delivery_contract_change_changes_treatment_identity(
    tmp_path: Path,
) -> None:
    from devagentops.evaluation.matrix import load_evaluation_matrix

    source = (
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "oracle-minimax-m3-development-v2.json"
    )
    document = json.loads(source.read_text(encoding="utf-8"))

    baseline_path = tmp_path / "baseline.json"
    changed_path = tmp_path / "changed.json"

    baseline_path.write_text(
        json.dumps(document),
        encoding="utf-8",
    )

    changed = json.loads(json.dumps(document))
    changed["conditions"][0]["treatment"]["contracts"][
        "evidence_delivery"
    ]["ordering"] = "different-answer-neutral-order-v2"

    changed_path.write_text(
        json.dumps(changed),
        encoding="utf-8",
    )

    baseline = load_evaluation_matrix(baseline_path).conditions[0]
    modified = load_evaluation_matrix(changed_path).conditions[0]

    assert (
        baseline.execution_policy_fingerprint
        == modified.execution_policy_fingerprint
    )
    assert (
        baseline.treatment_fingerprint
        != modified.treatment_fingerprint
    )
    assert (
        baseline.condition_fingerprint
        != modified.condition_fingerprint
    )


def test_historical_l1_l2_fingerprints_remain_unchanged() -> None:
    from devagentops.evaluation.matrix import load_evaluation_matrix

    l1 = load_evaluation_matrix(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l1-minimax-m3-development-v2.json"
    ).conditions[0]

    l2 = load_evaluation_matrix(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "l2-minimax-m3-development-v2.json"
    ).conditions[0]

    assert l1.treatment_fingerprint == (
        "1d6387a25f7722c30b36be82eaf5f769"
        "9550472a9b136db5964a783c3da758f4"
    )
    assert l1.condition_fingerprint == (
        "c199208feb41748fd67095512871bcd40"
        "6d108ed3444b98854adecf0aa1fcb2a"
    )
    assert l1.execution_policy_fingerprint == (
        "c1f3aa8327a858befa9b77a8cc4bce80"
        "798c5c98a5125a0c31158ce109225e5b"
    )

    assert l2.treatment_fingerprint == (
        "10361eddc287886ef5d634d2a81b163c"
        "d859c0802b40ec164f34c5fb240a0f50"
    )
    assert l2.condition_fingerprint == (
        "92e4260209f63d8c13eea5de821ea0e5"
        "3ba40d47b468b14feac4ab163d9335d1"
    )
    assert l2.execution_policy_fingerprint == (
        "c1f3aa8327a858befa9b77a8cc4bce80"
        "798c5c98a5125a0c31158ce109225e5b"
    )


def _configured_oracle_treatment():
    from devagentops.conditions.l1.development_output_contract import (
        output_contract_prompt_suffix,
    )
    from devagentops.conditions.oracle.one_shot_v1 import (
        ConfiguredOracleTreatment,
    )
    from devagentops.evaluation.matrix import (
        load_evaluation_matrix,
    )

    condition = load_evaluation_matrix(
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "oracle-minimax-m3-development-v2.json"
    ).conditions[0]

    treatment = condition.effective_condition["treatment"]

    return ConfiguredOracleTreatment(
        provider_id=treatment["provider"]["id"],
        model=treatment["model"],
        reasoning=treatment["reasoning"],
        generation=treatment["generation"],
        context_limit_tokens=(
            treatment["context"]["context_window_tokens"]
        ),
        max_completion_tokens=(
            treatment["generation"][
                "max_completion_tokens"
            ]
        ),
        task_contract_version=(
            treatment["contracts"]["task"]["version"]
        ),
        output_contract_prompt_suffix=(
            output_contract_prompt_suffix()
        ),
        runtime_input_serialization_version=(
            treatment["contracts"]["runtime_input"][
                "version"
            ]
        ),
        evidence_delivery_contract=(
            treatment["contracts"]["evidence_delivery"]
        ),
    )


class _OracleFakeProvider:
    def __init__(
        self,
        visible_output: str,
        *,
        input_tokens: int = 1000,
    ) -> None:
        self.visible_output = visible_output
        self.input_tokens = input_tokens
        self.requests = []
        self.complete_calls = 0

    def count_input_tokens(self, request):
        from devagentops.providers.contracts import (
            ExactTokenCount,
        )

        return ExactTokenCount(
            input_tokens=self.input_tokens,
            method="exact-fake-count",
        )

    def complete(self, request):
        self.requests.append(request)
        self.complete_calls += 1

        return AssistantMessage(
            content=(
                ThinkingContent("private reasoning must not be persisted"),
                TextContent(self.visible_output),
            ),
            response_id="oracle-fake-request-1",
            response_model="MiniMax-M3",
            usage=TokenUsage(input_tokens=self.input_tokens, output_tokens=100),
            stop_reason="stop",
            raw_stop_reason="stop",
            latency_ms=7,
        )


def _valid_oracle_fake_report(package) -> dict:
    return {
        "schema_version": "1",
        "case_id": package.case_id,
        "classification_status": "classified",
        "failure_type": (
            package.expected_answer.primary_failure_type
        ),
        "summary": "The frozen evidence supports the diagnosis.",
        "root_cause": (
            "The selected source evidence identifies the failure cause."
        ),
        "recommended_action": (
            "Inspect and correct the behavior indicated by the cited evidence."
        ),
        "confidence": 0.9,
        "evidence_references": [
            {"evidence_id": evidence_id}
            for evidence_id in (
                package.evidence_ground_truth
                .required_evidence_ids
            )
        ],
    }


def test_oracle_one_shot_uses_only_selected_runtime_input_and_one_call() -> None:
    from devagentops.conditions.oracle.one_shot_v1 import (
        run_configured_oracle_one_shot,
    )
    from devagentops.evaluation.components import (
        load_component_manifest,
    )

    package = load_case_package(FORMAL_CASE)
    prompt = load_component_manifest(
        PROJECT_ROOT
        / "components"
        / "frozen"
        / "prompt"
        / "structured-triage-task-contract-v1.json"
    )

    provider = _OracleFakeProvider(
        json.dumps(
            _valid_oracle_fake_report(package)
        )
    )

    started = []

    result = run_configured_oracle_one_shot(
        package,
        prompt,
        provider,
        _configured_oracle_treatment(),
        before_model_call=started.append,
    )

    assert provider.complete_calls == 1
    assert len(provider.requests) == 1
    assert len(started) == 1

    request = provider.requests[0]

    assert request.model == "MiniMax-M3"
    assert request.tools == ()

    visible_prompt = request.messages[0].content

    assert "required_evidence_ids" not in visible_prompt
    assert "optional_evidence_ids" not in visible_prompt
    assert "evaluator/expected-answer.json" not in visible_prompt
    assert package.expected_answer.root_cause not in visible_prompt

    for evidence_id in (
        package.evidence_ground_truth.required_evidence_ids
    ):
        assert evidence_id in visible_prompt

    for evidence_id in (
        package.evidence_ground_truth.optional_evidence_ids
    ):
        assert evidence_id not in visible_prompt

    assert started[0]["logical_call_number"] == 1
    assert started[0]["input_tokens"] == 1000
    assert started[0]["evidence_item_count"] == len(
        package.evidence_ground_truth.required_evidence_ids
    )

    assert result.candidate_document == (
        _valid_oracle_fake_report(package)
    )


def test_oracle_condition_executor_scores_single_fake_sample() -> None:
    from devagentops.conditions.oracle.executor import (
        ConfiguredOracleConditionExecutor,
    )
    from devagentops.evaluation.components import (
        load_component_manifest,
    )
    from devagentops.evaluation.execution import (
        PlannedSample,
        SampleIdentity,
    )
    from devagentops.evaluation.suite import SuiteCase
    from devagentops.evaluation.trace import TraceRecorder

    package = load_case_package(FORMAL_CASE)

    prompt = load_component_manifest(
        PROJECT_ROOT
        / "components"
        / "frozen"
        / "prompt"
        / "structured-triage-task-contract-v1.json"
    )

    provider = _OracleFakeProvider(
        json.dumps(
            _valid_oracle_fake_report(package)
        )
    )

    suite_case = SuiteCase(
        case_id=package.case_id,
        manifest=FORMAL_CASE.as_posix(),
        weight=1,
        package=package,
    )

    identity = SampleIdentity(
        run_id="oracle-test-run",
        case_id=package.case_id,
        repeat_index=0,
        sample_sequence=1,
    )

    sample = PlannedSample(
        identity=identity,
        suite_case=suite_case,
    )

    recorder = TraceRecorder("oracle-test-run")

    executor = ConfiguredOracleConditionExecutor(
        prompt=prompt,
        treatment=_configured_oracle_treatment(),
        provider_factory=lambda: provider,
    )

    result = executor.execute_sample(
        sample,
        recorder,
    )

    assert result.status == "scored"
    assert provider.complete_calls == 1

    assert result.data["outcome"] == {
        "status": "scored"
    }

    assert result.data["quality_metrics"][
        "failure_type_exact_match"
    ] == 1.0

    assert result.data["quality_metrics"][
        "report_evidence_hit_rate"
    ] == 1.0

    assert result.data["quality_metrics"][
        "required_fields_completeness"
    ] == 1.0

    trace = recorder.snapshot()

    assert [
        event["event_type"]
        for event in trace
    ] == [
        "oracle_execution_started",
        "model_call_started",
        "model_call_completed",
        "report_submitted",
        "evaluation_completed",
    ]

    completed = next(
        event
        for event in trace
        if event["event_type"]
        == "model_call_completed"
    )

    assert completed["payload"][
        "actual_call_count"
    ] == 1

    assert completed["payload"][
        "reasoning_observation"
    ]["present"] is True

    assert "reasoning_output" not in completed["payload"]
    assert (
        "private reasoning must not be persisted"
        not in json.dumps(trace)
    )


def test_oracle_context_failure_happens_before_provider_call() -> None:
    from devagentops.conditions.oracle.one_shot_v1 import (
        OracleOneShotError,
        run_configured_oracle_one_shot,
    )
    from devagentops.evaluation.components import (
        load_component_manifest,
    )

    package = load_case_package(FORMAL_CASE)

    prompt = load_component_manifest(
        PROJECT_ROOT
        / "components"
        / "frozen"
        / "prompt"
        / "structured-triage-task-contract-v1.json"
    )

    provider = _OracleFakeProvider(
        "{}",
        input_tokens=999_999,
    )

    with pytest.raises(
        OracleOneShotError
    ) as exc_info:
        run_configured_oracle_one_shot(
            package,
            prompt,
            provider,
            _configured_oracle_treatment(),
        )

    assert exc_info.value.code == (
        "oracle_context_infeasible"
    )
    assert provider.complete_calls == 0
    assert provider.requests == []


class _OracleFormalFakeProvider:
    def __init__(self, provider_index: int) -> None:
        self.provider_index = provider_index
        self.complete_calls = 0
        self.requests = []

    def count_input_tokens(self, request):
        from devagentops.providers.contracts import ExactTokenCount

        return ExactTokenCount(
            input_tokens=1000,
            method="exact-fake-count",
        )

    def complete(self, request):
        import re

        self.complete_calls += 1
        self.requests.append(request)

        prompt = request.messages[0].content

        case_match = re.search(
            r'"case_id"\s*:\s*"([^"]+)"',
            prompt,
        )
        evidence_match = re.search(
            r'"evidence_id"\s*:\s*"([^"]+)"',
            prompt,
        )

        assert case_match is not None
        assert evidence_match is not None

        report = {
            "schema_version": "1",
            "case_id": case_match.group(1),
            "classification_status": "inconclusive",
            "failure_type": None,
            "summary": (
                "The selected evidence is preserved for diagnostic review."
            ),
            "root_cause": (
                "The fake provider intentionally does not assert a diagnosis."
            ),
            "recommended_action": (
                "Review the cited source evidence."
            ),
            "confidence": 0.2,
            "evidence_references": [
                {
                    "evidence_id": evidence_match.group(1),
                }
            ],
        }

        return AssistantMessage(
            content=(
                ThinkingContent("private fake Oracle reasoning must never persist"),
                TextContent(json.dumps(report)),
            ),
            response_id=(
                f"oracle-formal-request-{self.provider_index}"
            ),
            response_model="MiniMax-M3",
            usage=TokenUsage(input_tokens=1000, output_tokens=80),
            stop_reason="stop",
            raw_stop_reason="stop",
            latency_ms=5,
        )


def test_oracle_formal_fake_full_suite_runs_20x3_through_shared_engine(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    import devagentops.evaluation.run_v2 as evaluation_run_v2

    from devagentops.cli import main

    matrix = (
        PROJECT_ROOT
        / "evaluation"
        / "matrices"
        / "oracle-minimax-m3-development-v2.json"
    )
    registry = PROJECT_ROOT / "components" / "registry.json"
    suite = (
        PROJECT_ROOT
        / "evaluation"
        / "suites"
        / "triage-v1"
        / "suite.json"
    )

    providers = []

    def provider_factory(**kwargs):
        provider = _OracleFormalFakeProvider(
            len(providers)
        )
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
        lambda: "a" * 40,
    )
    monkeypatch.setattr(
        evaluation_run_v2,
        "_git_dirty",
        lambda: False,
    )

    database = tmp_path / "oracle.db"
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
            "oracle-minimax-m3-adaptive-development-v1",
            "--database",
            str(database),
            "--artifacts-dir",
            str(artifacts),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert output["status"] == "completed"
    assert output["case_count"] == 20
    assert output["planned_sample_count"] == 60

    assert len(providers) == 60
    assert all(
        provider.complete_calls == 1
        for provider in providers
    )

    all_requests = [
        request
        for provider in providers
        for request in provider.requests
    ]

    assert len(all_requests) == 60

    for request in all_requests:
        prompt = request.messages[0].content

        assert "required_evidence_ids" not in prompt
        assert "optional_evidence_ids" not in prompt
        assert "evaluator/expected-answer.json" not in prompt
        assert "oracle_required_evidence_delivery" not in prompt

    artifact_path = Path(
        output["artifacts"]["json"]
    )
    markdown_path = Path(
        output["artifacts"]["markdown"]
    )

    artifact = json.loads(
        artifact_path.read_text(encoding="utf-8")
    )
    markdown = markdown_path.read_text(
        encoding="utf-8"
    )

    manifest = artifact["manifest"]

    assert manifest["runtime_variant"] == "model_one_shot"
    assert manifest["experiment_identity"] == (
        "oracle-evidence-diagnostic-development"
    )

    assert manifest["treatment"]["contracts"][
        "evidence_delivery"
    ] == oracle_evidence_delivery_contract()

    assert artifact["status"] == "completed"
    assert len(artifact["sample_results"]) == 60
    assert len(artifact["case_aggregates"]) == 20

    assert all(
        result["outcome"]["status"] == "scored"
        for result in artifact["sample_results"]
    )

    assert all(
        result["evidence_delivery"]["fingerprint"]
        == ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
        for result in artifact["sample_results"]
    )

    trace = artifact["trace"]

    started = [
        event
        for event in trace
        if event["event_type"] == "model_call_started"
    ]
    completed = [
        event
        for event in trace
        if event["event_type"] == "model_call_completed"
    ]

    assert len(started) == 60
    assert len(completed) == 60

    assert all(
        event["payload"]["actual_call_count"] == 1
        for event in completed
    )

    serialized_artifact = json.dumps(
        artifact,
        ensure_ascii=False,
    )

    assert (
        "private fake Oracle reasoning must never persist"
        not in serialized_artifact
    )

    assert (
        "# DevAgentOps Formal Oracle Evidence "
        "Diagnostic Evaluation"
        in markdown
    )

    # Formal execution identity is explicit and preserves the shared
    # repeat/concurrency/retry policy.
    assert manifest["execution_policy"] == {
        "repeat_count": 3,
        "max_case_concurrency": 6,
        "retry_count": 0,
        "request_timeout_seconds": 600,
    }

    assert manifest["tool_call_protocol"] == {
        "applicability": "not_applicable",
        "reason": "oracle_model_one_shot_has_no_tools",
    }

    assert manifest["treatment"]["contracts"]["runtime_input"] == {
        "version": "selected_evidence_runtime_input_v2",
    }

    # Every scored Sample must retain enough metadata to audit exact context
    # feasibility and the Oracle evidence-delivery realization without
    # persisting raw private reasoning.
    for result in artifact["sample_results"]:
        assessment = result["context_assessment"]
        observation = result["provider_observation"]
        delivery = result["evidence_delivery"]

        assert assessment == {
            "input_tokens": 1000,
            "method": "exact-fake-count",
            "exact": True,
            "context_window_tokens": 1000000,
            "reserved_completion_tokens": 65536,
        }

        assert len(delivery["runtime_input_sha256"]) == 64
        int(delivery["runtime_input_sha256"], 16)

        assert observation["reasoning"]["present"] is True
        assert observation["reasoning"]["character_count"] > 0
        assert len(observation["reasoning"]["sha256"]) == 64
        assert "reasoning_output" not in observation

    # Deterministic Oracle Runtime input: all repeats of the same frozen Case
    # must receive exactly the same selected-evidence serialization.
    hashes_by_case = {}
    for result in artifact["sample_results"]:
        hashes_by_case.setdefault(
            result["case_id"],
            set(),
        ).add(
            result["evidence_delivery"][
                "runtime_input_sha256"
            ]
        )

    assert len(hashes_by_case) == 20
    assert all(
        len(runtime_hashes) == 1
        for runtime_hashes in hashes_by_case.values()
    )

    # Trace proves the physical call realization: exactly one zero-retry model
    # call for each of the 60 planned Samples.
    assert all(
        event["payload"]["logical_call_number"] == 1
        and event["payload"]["attempt_index"] == 0
        and event["payload"]["retry_count"] == 0
        and event["payload"]["evidence_delivery_fingerprint"]
        == ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
        and len(event["payload"]["runtime_input_sha256"]) == 64
        for event in started
    )

    assert all(
        event["payload"]["logical_call_number"] == 1
        and event["payload"]["attempt_index"] == 0
        and event["payload"]["retry_count"] == 0
        and event["payload"]["actual_call_count"] == 1
        for event in completed
    )

    # The per-Sample Runtime-input identity persisted in the result must match
    # the identity observed immediately before the corresponding model call.
    started_by_sample = {
        (
            event["case_id"],
            event["repeat_index"],
        ): event["payload"]["runtime_input_sha256"]
        for event in started
    }

    result_by_sample = {
        (
            result["case_id"],
            result["repeat_index"],
        ): result["evidence_delivery"][
            "runtime_input_sha256"
        ]
        for result in artifact["sample_results"]
    }

    assert started_by_sample == result_by_sample

    # One provider request was physically realized for every planned Sample.
    request_ids = {
        event["payload"]["provider_request_id"]
        for event in completed
    }
    assert len(request_ids) == 60

    # Private model reasoning may be observed by hash/count metadata only.
    assert all(
        "reasoning_output" not in event["payload"]
        for event in completed
    )


def test_case_fingerprint_is_internal_audit_identity_not_model_visible() -> None:
    package = load_case_package(FORMAL_CASE)

    pack = resolve_oracle_evidence_pack(package)
    baseline = serialize_oracle_evidence_pack(pack)

    assert pack.case_fingerprint == package.case_fingerprint

    changed_pack = replace(
        pack,
        case_fingerprint="f" * 64,
    )

    changed = serialize_oracle_evidence_pack(
        changed_pack
    )

    # Full Case fingerprint includes evaluator-only artifacts, so changing it
    # must have zero influence on the model-visible Oracle Runtime input.
    assert changed == baseline

    document = json.loads(changed.text)
    assert "case_fingerprint" not in document["case"]
