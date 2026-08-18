from __future__ import annotations

import json
from pathlib import Path

import pytest

from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.matrix import EvaluationMatrixError, load_evaluation_matrix
from devagentops.evaluation.development_treatment import (
    validate_minimax_development_condition,
)
from devagentops.runtime.tool_policy import BASELINE_TOOL_POLICY
from devagentops.runtime.tools import TOOL_DEFINITIONS


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "components/registry.json"
MATRIX = ROOT / "evaluation/matrices/l4-minimax-m3-development-v2.json"


def test_l4_frozen_manifests_match_runtime_provider_contracts() -> None:
    runtime_control = resolve_frozen_component_manifest(
        REGISTRY, "prompt", "l4-react-runtime-control-v1"
    )
    tool_registry = resolve_frozen_component_manifest(
        REGISTRY, "tool_registry", "l4-investigation-tools-v1"
    )
    tool_policy = resolve_frozen_component_manifest(
        REGISTRY, "tool_policy", "l4-single-sequential-tool-policy-v1"
    )
    assert "zero or one ToolCall" in runtime_control.behavior["template"]
    provider_tools = [
        {
            "name": definition.name,
            "description": definition.description,
            "parameters": definition.parameters,
        }
        for definition in TOOL_DEFINITIONS
    ]
    manifest_provider_tools = [
        {key: item[key] for key in ("name", "description", "parameters")}
        for item in tool_registry.behavior["tools"]
    ]
    assert manifest_provider_tools == provider_tools
    assert tool_policy.behavior == {"rules": [BASELINE_TOOL_POLICY]}
    assert "runtime" not in json.loads(REGISTRY.read_text())["components"]


def test_l4_matrix_resolves_all_four_frozen_component_identities() -> None:
    matrix = load_evaluation_matrix(MATRIX, REGISTRY)
    condition = matrix.conditions[0]
    assert condition.effective_condition["runtime_variant"] == "self_built_react"
    contracts = condition.effective_condition["treatment"]["contracts"]
    assert contracts["runtime"]["max_steps"] == 100
    assert condition.effective_condition["execution_policy"]["retry_count"] == 3
    validate_minimax_development_condition(condition.effective_condition, case_count=1)


@pytest.mark.parametrize(
    "contract_key", ["runtime_control", "tool_registry", "tool_policy"]
)
def test_l4_matrix_doctor_rejects_missing_or_mismatched_component_identity(
    tmp_path: Path, contract_key: str
) -> None:
    document = json.loads(MATRIX.read_text(encoding="utf-8"))
    contract = document["conditions"][0]["treatment"]["contracts"][contract_key]
    contract["fingerprint"] = "0" * 64
    path = tmp_path / "l4-invalid.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(EvaluationMatrixError, match=contract_key):
        load_evaluation_matrix(path, REGISTRY)

    del document["conditions"][0]["treatment"]["contracts"][contract_key]
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(EvaluationMatrixError, match=contract_key):
        load_evaluation_matrix(path, REGISTRY)
