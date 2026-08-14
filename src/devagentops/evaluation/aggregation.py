from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Protocol, Sequence

from devagentops.scoring.case import CASE_QUALITY_METRIC_NAMES


AGGREGATION_METHOD = "case-first-weighted-mean"
AGGREGATION_VERSION = "1"
METRIC_NAMES = CASE_QUALITY_METRIC_NAMES


class _ExpectedAnswerLike(Protocol):
    primary_failure_type: str


class _PackageLike(Protocol):
    case_fingerprint: str
    expected_answer: _ExpectedAnswerLike


class SuiteCaseLike(Protocol):
    case_id: str
    weight: int | float
    package: _PackageLike


class SuiteLike(Protocol):
    suite_id: str
    suite_version: str
    suite_fingerprint: str
    cases: Sequence[SuiteCaseLike]


@dataclass(frozen=True)
class CaseAggregate:
    run_id: str
    case_id: str
    case_fingerprint: str
    failure_type: str
    suite_weight: float
    aggregation_method: str
    aggregation_version: str
    requested_sample_count: int
    scored_sample_count: int
    execution_failed_sample_count: int
    execution_coverage: float
    protocol_valid_sample_count: int
    protocol_invalid_sample_count: int
    protocol_validity_rate: float | None
    quality_status: str
    metric_vector: dict[str, float] | None
    scored_repeat_indices: tuple[int, ...]
    failed_repeat_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["scored_repeat_indices"] = list(self.scored_repeat_indices)
        value["failed_repeat_indices"] = list(self.failed_repeat_indices)
        return value


@dataclass(frozen=True)
class SuiteAggregate:
    run_id: str
    suite_id: str
    suite_version: str
    suite_fingerprint: str
    aggregation_method: str
    aggregation_version: str
    configured_suite_weight: float
    total_case_count: int
    requested_sample_count: int
    scored_sample_count: int
    execution_failed_sample_count: int
    execution_coverage: float
    protocol_valid_sample_count: int
    protocol_invalid_sample_count: int
    protocol_validity_rate: float | None
    cases_with_quality: int
    cases_without_quality: int
    quality_case_coverage: float
    quality_suite_weight_coverage: float
    quality_status: str
    metric_vector: dict[str, float] | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FailureTypeAggregate:
    run_id: str
    failure_type: str
    aggregation_method: str
    aggregation_version: str
    case_count: int
    configured_suite_weight: float
    requested_sample_count: int
    scored_sample_count: int
    execution_failed_sample_count: int
    execution_coverage: float
    protocol_valid_sample_count: int
    protocol_invalid_sample_count: int
    protocol_validity_rate: float | None
    cases_with_quality: int
    cases_without_quality: int
    quality_case_coverage: float
    quality_suite_weight_coverage: float
    quality_status: str
    metric_vector: dict[str, float] | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def aggregate_case(
    run_id: str,
    suite_case: SuiteCaseLike,
    samples: Sequence[dict[str, Any]],
) -> CaseAggregate:
    if not samples:
        raise ValueError(f"Case {suite_case.case_id!r} has no planned samples")
    if any(sample["case_id"] != suite_case.case_id for sample in samples):
        raise ValueError("Case aggregation received a sample for another Case")
    repeats = [sample["repeat_index"] for sample in samples]
    if repeats != sorted(repeats) or len(repeats) != len(set(repeats)):
        raise ValueError("Case samples must have unique deterministic repeat order")

    scored = [
        sample for sample in samples if sample["outcome"]["status"] == "scored"
    ]
    failed = [
        sample
        for sample in samples
        if sample["outcome"]["status"] == "execution_failed"
    ]
    if len(scored) + len(failed) != len(samples):
        raise ValueError("sample outcome must be scored or execution_failed")
    valid_count = sum(bool(sample["validation"]["valid"]) for sample in scored)
    invalid_count = len(scored) - valid_count
    metrics = None
    if scored:
        metrics = {
            name: math.fsum(sample["quality_metrics"][name] for sample in scored)
            / len(scored)
            for name in METRIC_NAMES
        }
    return CaseAggregate(
        run_id=run_id,
        case_id=suite_case.case_id,
        case_fingerprint=suite_case.package.case_fingerprint,
        failure_type=suite_case.package.expected_answer.primary_failure_type,
        suite_weight=float(suite_case.weight),
        aggregation_method=AGGREGATION_METHOD,
        aggregation_version=AGGREGATION_VERSION,
        requested_sample_count=len(samples),
        scored_sample_count=len(scored),
        execution_failed_sample_count=len(failed),
        execution_coverage=len(scored) / len(samples),
        protocol_valid_sample_count=valid_count,
        protocol_invalid_sample_count=invalid_count,
        protocol_validity_rate=(valid_count / len(scored) if scored else None),
        quality_status="complete" if scored else "incomplete",
        metric_vector=metrics,
        scored_repeat_indices=tuple(sample["repeat_index"] for sample in scored),
        failed_repeat_indices=tuple(sample["repeat_index"] for sample in failed),
    )


def aggregate_suite(
    run_id: str,
    suite: SuiteLike,
    case_aggregates: Sequence[CaseAggregate],
) -> SuiteAggregate:
    _validate_case_order(suite, case_aggregates)
    values = _aggregate_group(case_aggregates)
    return SuiteAggregate(
        run_id=run_id,
        suite_id=suite.suite_id,
        suite_version=suite.suite_version,
        suite_fingerprint=suite.suite_fingerprint,
        aggregation_method=AGGREGATION_METHOD,
        aggregation_version=AGGREGATION_VERSION,
        configured_suite_weight=values["configured_weight"],
        total_case_count=len(case_aggregates),
        **values["coverage"],
        quality_status=values["quality_status"],
        metric_vector=values["metric_vector"],
    )


def aggregate_failure_types(
    run_id: str,
    suite: SuiteLike,
    case_aggregates: Sequence[CaseAggregate],
) -> tuple[FailureTypeAggregate, ...]:
    _validate_case_order(suite, case_aggregates)
    failure_type_order = tuple(
        dict.fromkeys(
            case.package.expected_answer.primary_failure_type for case in suite.cases
        )
    )
    results: list[FailureTypeAggregate] = []
    for failure_type in failure_type_order:
        group = [
            aggregate
            for aggregate in case_aggregates
            if aggregate.failure_type == failure_type
        ]
        values = _aggregate_group(group)
        results.append(
            FailureTypeAggregate(
                run_id=run_id,
                failure_type=failure_type,
                aggregation_method=AGGREGATION_METHOD,
                aggregation_version=AGGREGATION_VERSION,
                case_count=len(group),
                configured_suite_weight=values["configured_weight"],
                **values["coverage"],
                quality_status=values["quality_status"],
                metric_vector=values["metric_vector"],
            )
        )
    return tuple(results)


def _validate_case_order(
    suite: SuiteLike,
    case_aggregates: Sequence[CaseAggregate],
) -> None:
    expected = [case.case_id for case in suite.cases]
    actual = [aggregate.case_id for aggregate in case_aggregates]
    if actual != expected:
        raise ValueError("Case aggregates must exactly follow Suite Case order")


def _aggregate_group(
    case_aggregates: Sequence[CaseAggregate],
) -> dict[str, Any]:
    if not case_aggregates:
        raise ValueError("aggregate group must contain at least one Case")
    configured_weight = math.fsum(item.suite_weight for item in case_aggregates)
    requested = sum(item.requested_sample_count for item in case_aggregates)
    scored = sum(item.scored_sample_count for item in case_aggregates)
    failed = sum(item.execution_failed_sample_count for item in case_aggregates)
    protocol_valid = sum(
        item.protocol_valid_sample_count for item in case_aggregates
    )
    protocol_invalid = sum(
        item.protocol_invalid_sample_count for item in case_aggregates
    )
    with_quality = [item for item in case_aggregates if item.metric_vector is not None]
    available_weight = math.fsum(item.suite_weight for item in with_quality)
    complete = len(with_quality) == len(case_aggregates)
    metric_vector = None
    if complete:
        metric_vector = {
            name: math.fsum(
                item.metric_vector[name] * item.suite_weight
                for item in case_aggregates
                if item.metric_vector is not None
            )
            / configured_weight
            for name in METRIC_NAMES
        }
    coverage = {
        "requested_sample_count": requested,
        "scored_sample_count": scored,
        "execution_failed_sample_count": failed,
        "execution_coverage": scored / requested,
        "protocol_valid_sample_count": protocol_valid,
        "protocol_invalid_sample_count": protocol_invalid,
        "protocol_validity_rate": protocol_valid / scored if scored else None,
        "cases_with_quality": len(with_quality),
        "cases_without_quality": len(case_aggregates) - len(with_quality),
        "quality_case_coverage": len(with_quality) / len(case_aggregates),
        "quality_suite_weight_coverage": available_weight / configured_weight,
    }
    return {
        "configured_weight": configured_weight,
        "coverage": coverage,
        "quality_status": "complete" if complete else "incomplete",
        "metric_vector": metric_vector,
    }
