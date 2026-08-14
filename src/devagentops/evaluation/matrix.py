"""Stable dispatch surface for the historical Matrix schema v1 implementation."""

from devagentops.evaluation.matrix_v1 import (
    EvaluationMatrix,
    EvaluationMatrixError,
    ResolvedCondition,
    load_evaluation_matrix,
)

__all__ = [
    "EvaluationMatrix",
    "EvaluationMatrixError",
    "ResolvedCondition",
    "load_evaluation_matrix",
]
