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
    """执行 Runtime 调用前的完整输入检查，返回已解析 Matrix 与 Suite。

    先解析所有 Condition 并校验冻结组件，再加载 Suite 中全部 Case、核对
    Case/Suite 指纹，最后检查每个 Condition 的 Suite 引用。任一步异常向上传播，
    调用者尚未开始 Runtime 执行；未选中的 Condition 也必须通过这里的检查。"""
    matrix = load_evaluation_matrix(matrix_path, registry_path)
    suite = load_evaluation_suite(suite_path)
    validate_matrix_suite_references(matrix, suite)
    return FormalEvaluationInputs(matrix=matrix, suite=suite)
