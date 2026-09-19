"""Schema-dispatch surface preserving the historical Matrix v1 implementation."""

import json
from pathlib import Path

from devagentops.evaluation.matrix_v1 import (
    EvaluationMatrix,
    EvaluationMatrixError,
    ResolvedCondition,
    load_evaluation_matrix as load_evaluation_matrix_v1,
)
from devagentops.evaluation.matrix_v2 import EvaluationMatrixV2, load_evaluation_matrix_v2


def load_evaluation_matrix(
    path: Path,
    component_registry_path: Path | None = None,
) -> EvaluationMatrix | EvaluationMatrixV2:
    """按 schema_version 分派 Matrix loader，不在此选择要运行的 Condition。

    v2 使用显式 Treatment/Execution Policy；其他版本交给历史 v1 loader。
    传入 Registry 才会校验组件引用，故 structural-only 不等同于正式 preflight。"""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationMatrixError(
            f"invalid JSON in evaluation matrix {path}: {exc.msg}"
        ) from exc
    if document.get("schema_version") == "2":
        return load_evaluation_matrix_v2(path, component_registry_path)
    return load_evaluation_matrix_v1(path, component_registry_path)

__all__ = [
    "EvaluationMatrix",
    "EvaluationMatrixError",
    "EvaluationMatrixV2",
    "ResolvedCondition",
    "load_evaluation_matrix",
]
