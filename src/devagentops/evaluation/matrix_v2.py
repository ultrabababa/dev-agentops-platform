from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devagentops.evaluation.components import validate_component_references
from devagentops.evaluation.matrix_v1 import EvaluationMatrixError


MATRIX_FIELDS = {"matrix_id", "matrix_version", "schema_version", "conditions"}
CONDITION_FIELDS = {
    "id",
    "type",
    "runtime_variant",
    "suite",
    "evaluation_method",
    "treatment",
    "execution_policy",
}
TREATMENT_FIELDS = {
    "provider",
    "model",
    "reasoning",
    "generation",
    "contracts",
    "context",
}
PROVIDER_FIELDS = {"id", "transport", "profile", "base_url"}
EXECUTION_POLICY_FIELDS = {
    "repeat_count",
    "max_case_concurrency",
    "retry_count",
    "request_timeout_seconds",
}
CONDITION_TYPES = {"anchor", "ablation", "candidate"}


def canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class ResolvedConditionV2:
    condition_id: str
    effective_condition: dict[str, Any]

    @property
    def treatment_fingerprint(self) -> str:
        return canonical_sha256(self.effective_condition["treatment"])

    @property
    def execution_policy_fingerprint(self) -> str:
        return canonical_sha256(self.effective_condition["execution_policy"])

    @property
    def condition_fingerprint(self) -> str:
        return canonical_sha256(
            {
                "type": self.effective_condition["type"],
                "runtime_variant": self.effective_condition["runtime_variant"],
                "suite": self.effective_condition["suite"],
                "evaluation_method": self.effective_condition["evaluation_method"],
                "treatment_fingerprint": self.treatment_fingerprint,
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "effective_condition": self.effective_condition,
            "treatment_fingerprint": self.treatment_fingerprint,
            "condition_fingerprint": self.condition_fingerprint,
            "execution_policy_fingerprint": self.execution_policy_fingerprint,
        }


@dataclass(frozen=True)
class EvaluationMatrixV2:
    matrix_id: str
    matrix_version: str
    schema_version: str
    conditions: tuple[ResolvedConditionV2, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "matrix_version": self.matrix_version,
            "schema_version": self.schema_version,
            "conditions": [condition.as_dict() for condition in self.conditions],
        }


def calculate_run_configuration_fingerprint(
    matrix: EvaluationMatrixV2,
    condition: ResolvedConditionV2,
    *,
    suite_fingerprint: str,
    selected_cases: list[dict[str, Any]],
    code_revision: str,
    git_dirty: bool,
    run_kind: str | None = None,
) -> str:
    identity = {
        "matrix": {
            "matrix_id": matrix.matrix_id,
            "matrix_version": matrix.matrix_version,
            "schema_version": matrix.schema_version,
        },
        "condition_id": condition.condition_id,
        "condition_fingerprint": condition.condition_fingerprint,
        "treatment_fingerprint": condition.treatment_fingerprint,
        "execution_policy_fingerprint": condition.execution_policy_fingerprint,
        "suite_fingerprint": suite_fingerprint,
        "selected_cases": selected_cases,
        "code_revision": code_revision,
        "git_dirty": git_dirty,
    }
    if run_kind is not None:
        identity["run_kind"] = run_kind
    return canonical_sha256(identity)


def load_evaluation_matrix_v2(
    path: Path,
    component_registry_path: Path | None = None,
) -> EvaluationMatrixV2:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationMatrixError(
            f"invalid JSON in evaluation matrix {path}: {exc.msg}"
        ) from exc
    _require_exact_fields(document, MATRIX_FIELDS, "evaluation matrix")
    if document["schema_version"] != "2":
        raise EvaluationMatrixError("Matrix v2 loader requires schema_version '2'")
    if not isinstance(document["conditions"], list) or not document["conditions"]:
        raise EvaluationMatrixError("evaluation matrix conditions must be a non-empty list")

    seen: set[str] = set()
    resolved: list[ResolvedConditionV2] = []
    for raw in document["conditions"]:
        if not isinstance(raw, dict):
            raise EvaluationMatrixError("Matrix v2 condition must be an object")
        condition_id = raw.get("id", "<unknown>")
        _require_exact_fields(raw, CONDITION_FIELDS, f"condition {condition_id!r}")
        if not isinstance(condition_id, str) or not condition_id:
            raise EvaluationMatrixError("Matrix v2 condition id must be a non-empty string")
        if condition_id in seen:
            raise EvaluationMatrixError(f"duplicate condition id {condition_id!r}")
        seen.add(condition_id)
        if raw["type"] not in CONDITION_TYPES:
            raise EvaluationMatrixError(
                f"condition {condition_id!r} has unsupported condition type {raw['type']!r}"
            )
        _validate_treatment(raw["treatment"], condition_id)
        _validate_execution_policy(raw["execution_policy"], condition_id)
        if component_registry_path is not None:
            _validate_registry_contracts(
                raw,
                component_registry_path,
                condition_id=condition_id,
            )
        effective = {key: value for key, value in raw.items() if key != "id"}
        resolved.append(ResolvedConditionV2(condition_id, effective))
    return EvaluationMatrixV2(
        matrix_id=document["matrix_id"],
        matrix_version=document["matrix_version"],
        schema_version="2",
        conditions=tuple(resolved),
    )


def _validate_registry_contracts(
    condition: dict[str, Any],
    registry_path: Path,
    *,
    condition_id: str,
) -> None:
    contracts = condition["treatment"]["contracts"]
    references = [("task", "prompt")]
    if condition["runtime_variant"] == "static_retrieval":
        references.append(("retriever", "retriever_config"))
    if condition["runtime_variant"] == "self_built_react":
        references.extend(
            [
                ("runtime_control", "prompt"),
                ("tool_registry", "tool_registry"),
                ("tool_policy", "tool_policy"),
            ]
        )
    for contract_key, component_type in references:
        identity = contracts.get(contract_key, {})
        if (
            identity.get("component_type") != component_type
            or not isinstance(identity.get("version"), str)
            or not identity["version"]
        ):
            raise EvaluationMatrixError(
                f"condition {condition_id!r} has invalid {contract_key} contract identity"
            )
        fingerprints = validate_component_references(
            {component_type: identity["version"]},
            registry_path,
            condition_id=condition_id,
        )
        if identity.get("fingerprint") != fingerprints[component_type]:
            raise EvaluationMatrixError(
                f"condition {condition_id!r} {contract_key} contract fingerprint "
                "does not match the Component Registry"
            )


def _validate_treatment(value: Any, condition_id: str) -> None:
    if not isinstance(value, dict):
        raise EvaluationMatrixError(f"condition {condition_id!r} treatment must be an object")
    _require_exact_fields(value, TREATMENT_FIELDS, f"condition {condition_id!r} treatment")
    provider = value["provider"]
    if not isinstance(provider, dict):
        raise EvaluationMatrixError(f"condition {condition_id!r} provider must be an object")
    _require_exact_fields(provider, PROVIDER_FIELDS, f"condition {condition_id!r} provider")
    if not all(isinstance(provider[field], str) and provider[field] for field in PROVIDER_FIELDS):
        raise EvaluationMatrixError(f"condition {condition_id!r} provider fields must be strings")
    if not isinstance(value["model"], str) or not value["model"]:
        raise EvaluationMatrixError(f"condition {condition_id!r} model must be a non-empty string")
    for field in ("reasoning", "generation", "contracts", "context"):
        if not isinstance(value[field], dict):
            raise EvaluationMatrixError(
                f"condition {condition_id!r} treatment field {field!r} must be an object"
            )


def _validate_execution_policy(value: Any, condition_id: str) -> None:
    if not isinstance(value, dict):
        raise EvaluationMatrixError(
            f"condition {condition_id!r} execution_policy must be an object"
        )
    _require_exact_fields(
        value,
        EXECUTION_POLICY_FIELDS,
        f"condition {condition_id!r} execution_policy",
    )
    for field in EXECUTION_POLICY_FIELDS:
        if not isinstance(value[field], int) or isinstance(value[field], bool):
            raise EvaluationMatrixError(
                f"condition {condition_id!r} execution_policy {field!r} must be an integer"
            )
    if (
        value["repeat_count"] < 1
        or value["max_case_concurrency"] < 1
        or value["request_timeout_seconds"] < 1
    ):
        raise EvaluationMatrixError(
            f"condition {condition_id!r} repeat_count, max_case_concurrency, and "
            "request_timeout_seconds must be positive"
        )
    if value["retry_count"] < 0:
        raise EvaluationMatrixError(
            f"condition {condition_id!r} retry_count must be non-negative"
        )


def _require_exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = fields - set(value)
    if missing:
        raise EvaluationMatrixError(f"{label} is missing required field {sorted(missing)[0]!r}")
    unknown = set(value) - fields
    if unknown:
        raise EvaluationMatrixError(f"{label} has unknown field {sorted(unknown)[0]!r}")
