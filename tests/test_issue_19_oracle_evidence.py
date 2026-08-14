from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

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
        "case_fingerprint",
        "forbidden_actions",
    }

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
        "version": "1",
        "pack_version": "oracle_evidence_pack_v1",
        "runtime_input_serialization_version": (
            "selected_evidence_runtime_input_v1"
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
