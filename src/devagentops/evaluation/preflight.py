from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devagentops.evaluation.matrix import EvaluationMatrix, load_evaluation_matrix
from devagentops.evaluation.suite import (
    EvaluationSuite,
    load_evaluation_suite,
    validate_matrix_suite_references,
)


@dataclass(frozen=True)
class FormalEvaluationInputs:
    matrix: EvaluationMatrix
    suite: EvaluationSuite

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.matrix.as_dict(),
            "evaluation_suite": self.suite.as_dict(),
        }


def run_formal_eval_doctor(
    matrix_path: Path,
    registry_path: Path,
    suite_path: Path,
) -> FormalEvaluationInputs:
    matrix = load_evaluation_matrix(matrix_path, registry_path)
    suite = load_evaluation_suite(suite_path)
    validate_matrix_suite_references(matrix, suite)
    return FormalEvaluationInputs(matrix=matrix, suite=suite)
