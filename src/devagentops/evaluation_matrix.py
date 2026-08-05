from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devagentops.component_registry import validate_component_references


class EvaluationMatrixError(RuntimeError):
    pass


CONDITION_FIELDS = {
    "id",
    "extends",
    "type",
    "runtime_variant",
    "suite",
    "evaluation_method",
    "model",
    "components",
    "budgets",
    "repeats",
}
CONDITION_TYPES = {"anchor", "ablation", "candidate"}
MATRIX_FIELDS = {
    "matrix_id",
    "matrix_version",
    "schema_version",
    "defaults",
    "conditions",
}
REQUIRED_MATRIX_FIELDS = MATRIX_FIELDS - {"defaults"}
REQUIRED_EFFECTIVE_FIELDS = {
    "type",
    "runtime_variant",
    "suite",
    "evaluation_method",
    "model",
    "components",
    "budgets",
    "repeats",
}


def _fingerprint(value: dict[str, Any]) -> str:
    # Compare the experiment's effective configuration, not JSON whitespace or key order.
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    # Preserve shared defaults so resolving one condition cannot affect another one.
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass(frozen=True)
class ResolvedCondition:
    condition_id: str
    effective_condition: dict[str, Any]
    component_fingerprints: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        fingerprint_input = self.effective_condition
        result: dict[str, Any] = {
            "condition_id": self.condition_id,
            "effective_condition": self.effective_condition,
        }
        if self.component_fingerprints is not None:
            result["component_fingerprints"] = self.component_fingerprints
            fingerprint_input = {
                **self.effective_condition,
                "component_fingerprints": self.component_fingerprints,
            }
        result["condition_fingerprint"] = _fingerprint(fingerprint_input)
        return result


@dataclass(frozen=True)
class EvaluationMatrix:
    matrix_id: str
    matrix_version: str
    schema_version: str
    conditions: tuple[ResolvedCondition, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "matrix_version": self.matrix_version,
            "schema_version": self.schema_version,
            "conditions": [condition.as_dict() for condition in self.conditions],
        }


def load_evaluation_matrix(
    path: Path,
    component_registry_path: Path | None = None,
) -> EvaluationMatrix:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationMatrixError(
            f"invalid JSON in evaluation matrix {path}: {exc.msg}"
        ) from exc
    missing_matrix_fields = REQUIRED_MATRIX_FIELDS - set(document)
    if missing_matrix_fields:
        field = sorted(missing_matrix_fields)[0]
        raise EvaluationMatrixError(
            f"evaluation matrix is missing required field {field!r}"
        )
    unknown_matrix_fields = set(document) - MATRIX_FIELDS
    if unknown_matrix_fields:
        field = sorted(unknown_matrix_fields)[0]
        raise EvaluationMatrixError(f"evaluation matrix has unknown field {field!r}")
    defaults = document.get("defaults", {})
    unknown_default_fields = set(defaults) - (CONDITION_FIELDS - {"id", "extends"})
    if unknown_default_fields:
        field = sorted(unknown_default_fields)[0]
        raise EvaluationMatrixError(
            f"evaluation matrix defaults have unknown field {field!r}"
        )
    raw_conditions = document["conditions"]
    for condition in raw_conditions:
        unknown_fields = set(condition) - CONDITION_FIELDS
        if unknown_fields:
            field = sorted(unknown_fields)[0]
            raise EvaluationMatrixError(
                f"condition {condition.get('id', '<unknown>')!r} has "
                f"unknown field {field!r}"
            )
    seen_condition_ids: set[str] = set()
    for condition in raw_conditions:
        condition_id = condition["id"]
        if condition_id in seen_condition_ids:
            raise EvaluationMatrixError(
                f"duplicate condition id {condition_id!r}"
            )
        seen_condition_ids.add(condition_id)
    conditions_by_id = {
        condition["id"]: condition for condition in raw_conditions
    }

    # Detect cycles before enforcing the one-level policy so cyclic input gets a precise error.
    for condition in raw_conditions:
        seen = {condition["id"]}
        current = condition
        while "extends" in current:
            parent_id = current["extends"]
            if parent_id not in conditions_by_id:
                break
            if parent_id in seen:
                raise EvaluationMatrixError(
                    "condition extension cycle detected at "
                    f"{parent_id!r}"
                )
            seen.add(parent_id)
            current = conditions_by_id[parent_id]

    # V1 intentionally permits only child -> parent inheritance to keep experiments explainable.
    for condition in raw_conditions:
        parent_id = condition.get("extends")
        if parent_id is None or parent_id not in conditions_by_id:
            continue
        if "extends" in conditions_by_id[parent_id]:
            raise EvaluationMatrixError(
                "condition extension supports one level only; "
                f"parent {parent_id!r} also extends another condition"
            )

    def resolve(condition: dict[str, Any]) -> dict[str, Any]:
        # IDs name conditions and `extends` is a configuration shortcut; neither changes behavior.
        own_fields = {
            key: value
            for key, value in condition.items()
            if key not in {"id", "extends"}
        }
        parent_id = condition.get("extends")
        if parent_id is None:
            effective = _merge(defaults, own_fields)
        else:
            if parent_id not in conditions_by_id:
                raise EvaluationMatrixError(
                    f"condition {condition['id']!r} extends unknown condition "
                    f"{parent_id!r}"
                )
            parent = conditions_by_id[parent_id]
            parent_fields = {
                key: value
                for key, value in parent.items()
                if key not in {"id", "extends"}
            }
            effective = _merge(_merge(defaults, parent_fields), own_fields)

        if effective.get("type") not in CONDITION_TYPES:
            raise EvaluationMatrixError(
                f"condition {condition['id']!r} has unsupported condition type "
                f"{effective.get('type')!r}"
            )
        missing_fields = REQUIRED_EFFECTIVE_FIELDS - set(effective)
        if missing_fields:
            field = sorted(missing_fields)[0]
            raise EvaluationMatrixError(
                f"condition {condition['id']!r} is missing required field "
                f"{field!r} after resolution"
            )
        return effective

    conditions = tuple(
        ResolvedCondition(
            condition_id=condition["id"],
            effective_condition=resolve(condition),
        )
        for condition in raw_conditions
    )
    if component_registry_path is not None:
        conditions = tuple(
            ResolvedCondition(
                condition_id=condition.condition_id,
                effective_condition=condition.effective_condition,
                component_fingerprints=validate_component_references(
                    condition.effective_condition["components"],
                    component_registry_path,
                    condition_id=condition.condition_id,
                ),
            )
            for condition in conditions
        )
    return EvaluationMatrix(
        matrix_id=document["matrix_id"],
        matrix_version=document["matrix_version"],
        schema_version=document["schema_version"],
        conditions=conditions,
    )
