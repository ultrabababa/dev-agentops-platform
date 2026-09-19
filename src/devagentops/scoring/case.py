from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devagentops.evaluation.suite import OfflineCasePackage
from devagentops.scoring.report import (
    CandidateReportAnalysis,
    REQUIRED_FIELDS_COMPLETENESS_DENOMINATOR,
    ReportValidationResult,
    StructuredTriageReport,
    analyze_candidate_report,
)


@dataclass(frozen=True)
class CaseQualityMetrics:
    failure_type_exact_match: float
    failure_type_reviewed_acceptable_match: float
    report_evidence_hit_rate: float
    required_fields_completeness: float

    def as_dict(self) -> dict[str, float]:
        return {
            "failure_type_exact_match": self.failure_type_exact_match,
            "failure_type_reviewed_acceptable_match": (
                self.failure_type_reviewed_acceptable_match
            ),
            "report_evidence_hit_rate": self.report_evidence_hit_rate,
            "required_fields_completeness": self.required_fields_completeness,
        }


CASE_QUALITY_METRIC_NAMES = tuple(CaseQualityMetrics.__dataclass_fields__)


@dataclass(frozen=True)
class EvidenceDiagnostics:
    """Counts only; unknown_evidence_count is the number of distinct unknown IDs."""

    required_evidence_count: int
    matched_required_evidence_count: int
    unknown_evidence_count: int
    duplicate_evidence_reference_count: int

    def as_dict(self) -> dict[str, int]:
        return {
            "required_evidence_count": self.required_evidence_count,
            "matched_required_evidence_count": (
                self.matched_required_evidence_count
            ),
            "unknown_evidence_count": self.unknown_evidence_count,
            "duplicate_evidence_reference_count": (
                self.duplicate_evidence_reference_count
            ),
        }


@dataclass(frozen=True)
class CaseScoreResult:
    validation: ReportValidationResult
    quality_metrics: CaseQualityMetrics
    evidence_diagnostics: EvidenceDiagnostics
    structured_report: StructuredTriageReport | None

    def as_dict(self) -> dict[str, object]:
        return {
            "validation": self.validation.as_dict(),
            "quality_metrics": self.quality_metrics.as_dict(),
            "evidence_diagnostics": self.evidence_diagnostics.as_dict(),
        }


def _classification_matches(
    analysis: CandidateReportAnalysis,
    package: OfflineCasePackage,
) -> tuple[float, float]:
    """按 Diagnosis Ground Truth 分开记录精确命中与人工认可的替代分类命中。

    两项互斥，primary 命中不会再累加 acceptable；Case 不匹配或 inconclusive
    都没有分类得分。其他字段的协议错误不会自动抹去此项独立的分类结果。
    """
    if (
        not analysis.case_id_matches
        or analysis.classification_status != "classified"
        or analysis.failure_type is None
    ):
        return 0.0, 0.0
    expected = package.expected_answer
    if analysis.failure_type == expected.primary_failure_type:
        return 1.0, 0.0
    if analysis.failure_type in expected.acceptable_failure_types:
        return 0.0, 1.0
    return 0.0, 0.0


def _evidence_score(
    analysis: CandidateReportAnalysis,
    package: OfflineCasePackage,
) -> tuple[float, EvidenceDiagnostics]:
    """计算 Required Evidence 的集合召回率，并仅返回计数型诊断。

    去重后求交，重复引用不能增加命中；出现任一未知 ID 则此项归零。
    分母非空依赖 Case loader 的 Ground Truth 合同。诊断不输出 Required/Missed
    ID 清单，避免从评分结果直接泄露隐藏答案；此函数本身不提供进程级隔离。
    """
    required = set(package.evidence_ground_truth.required_evidence_ids)
    cited = set(analysis.cited_evidence_ids)
    matched_count = len(required & cited)
    diagnostics = EvidenceDiagnostics(
        required_evidence_count=len(required),
        matched_required_evidence_count=matched_count,
        unknown_evidence_count=analysis.distinct_unknown_evidence_id_count,
        duplicate_evidence_reference_count=(
            analysis.duplicate_evidence_reference_count
        ),
    )
    if (
        not analysis.case_id_matches
        or not analysis.has_evidence_reference_list
        or analysis.distinct_unknown_evidence_id_count
    ):
        return 0.0, diagnostics
    return matched_count / len(required), diagnostics


def evaluate_case_report(
    raw_report: Any,
    package: OfflineCasePackage,
) -> CaseScoreResult:
    """Evaluator 侧使用完整 Case Package，对候选报告做确定性校验与四项评分。

    Diagnosis 与 Evidence Ground Truth 分别用于分类和引用比较；摘要、根因文本
    不做语义正确性判定。Schema 无效仍返回独立指标和错误，仅 structured_report
    为 None；执行失败应由上游记录，不能伪造零分报告传入此函数混淆两类失败。
    """
    analysis = analyze_candidate_report(
        raw_report,
        case_id=package.case_id,
        evidence_ids=package.evidence_ids,
    )
    exact_match, acceptable_match = _classification_matches(analysis, package)
    evidence_hit_rate, evidence_diagnostics = _evidence_score(analysis, package)
    completeness = (
        analysis.completeness_filled_count
        / REQUIRED_FIELDS_COMPLETENESS_DENOMINATOR
    )
    metrics = CaseQualityMetrics(
        failure_type_exact_match=exact_match,
        failure_type_reviewed_acceptable_match=acceptable_match,
        report_evidence_hit_rate=evidence_hit_rate,
        required_fields_completeness=completeness,
    )
    structured_report = analysis.construct_structured_report()
    return CaseScoreResult(
        validation=analysis.validation,
        quality_metrics=metrics,
        evidence_diagnostics=evidence_diagnostics,
        structured_report=structured_report,
    )
