from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path

from devagentops.evaluation.aggregation import (
    AGGREGATION_METHOD,
    aggregate_case,
    aggregate_failure_types,
    aggregate_suite,
)
from devagentops.evaluation.persistence import persist_finalizing_sample_run
from devagentops.storage.database import initialize_database


METRICS = (
    "failure_type_exact_match",
    "failure_type_reviewed_acceptable_match",
    "report_evidence_hit_rate",
    "required_fields_completeness",
)


@dataclass(frozen=True)
class _Package:
    case_fingerprint: str
    expected_answer: object


@dataclass(frozen=True)
class _Answer:
    primary_failure_type: str


@dataclass(frozen=True)
class _SuiteCase:
    case_id: str
    weight: float
    package: _Package


@dataclass(frozen=True)
class _Suite:
    suite_id: str
    suite_version: str
    suite_fingerprint: str
    cases: tuple[_SuiteCase, ...]


def _case(case_id: str, weight: float, failure_type: str) -> _SuiteCase:
    return _SuiteCase(
        case_id,
        weight,
        _Package(f"fingerprint-{case_id}", _Answer(failure_type)),
    )


def _scored(case_id: str, repeat_index: int, value: float, *, valid=True):
    return {
        "case_id": case_id,
        "repeat_index": repeat_index,
        "outcome": {"status": "scored"},
        "validation": {"valid": valid},
        "quality_metrics": {name: value for name in METRICS},
    }


def _failed(case_id: str, repeat_index: int):
    return {
        "case_id": case_id,
        "repeat_index": repeat_index,
        "outcome": {
            "status": "execution_failed",
            "failure_code": "provider_down",
            "failure_stage": "provider",
            "failure_message": "provider failed",
        },
    }


def test_case_arithmetic_mean_and_observation_layers() -> None:
    suite_case = _case("case-a", 1.0, "type-a")
    aggregate = aggregate_case(
        "run-43",
        suite_case,
        [
            _scored("case-a", 0, 1.0),
            _scored("case-a", 1, 0.5, valid=False),
            _failed("case-a", 2),
        ],
    )

    assert aggregate.aggregation_method == AGGREGATION_METHOD
    assert aggregate.requested_sample_count == 3
    assert aggregate.scored_sample_count == 2
    assert aggregate.execution_failed_sample_count == 1
    assert aggregate.execution_coverage == 2 / 3
    assert aggregate.protocol_valid_sample_count == 1
    assert aggregate.protocol_invalid_sample_count == 1
    assert aggregate.protocol_validity_rate == 0.5
    assert aggregate.quality_status == "complete"
    assert aggregate.metric_vector == {name: 0.75 for name in METRICS}
    assert aggregate.scored_repeat_indices == (0, 1)
    assert aggregate.failed_repeat_indices == (2,)


def test_all_failed_case_has_null_quality_without_synthetic_zero() -> None:
    aggregate = aggregate_case(
        "run-43",
        _case("case-a", 0.5, "type-a"),
        [_failed("case-a", index) for index in range(3)],
    )

    assert aggregate.suite_weight == 0.5
    assert aggregate.execution_coverage == 0.0
    assert aggregate.protocol_validity_rate is None
    assert aggregate.quality_status == "incomplete"
    assert aggregate.metric_vector is None


def test_suite_is_case_first_and_prevents_flattened_075_result() -> None:
    cases = (
        _case("case-a", 0.5, "type-a"),
        _case("case-b", 0.5, "type-b"),
    )
    suite = _Suite("suite", "1", "suite-fingerprint", cases)
    case_aggregates = (
        aggregate_case(
            "run-43",
            cases[0],
            [_scored("case-a", index, 1.0) for index in range(3)],
        ),
        aggregate_case(
            "run-43",
            cases[1],
            [_scored("case-b", 0, 0.0), _failed("case-b", 1), _failed("case-b", 2)],
        ),
    )

    aggregate = aggregate_suite("run-43", suite, case_aggregates)

    assert aggregate.metric_vector == {name: 0.5 for name in METRICS}
    assert all(value != 0.75 for value in aggregate.metric_vector.values())
    assert aggregate.execution_coverage == 4 / 6
    assert aggregate.quality_case_coverage == 1.0
    assert aggregate.quality_suite_weight_coverage == 1.0


def test_missing_case_quality_makes_suite_incomplete_without_weight_renormalization() -> None:
    cases = (
        _case("case-a", 1.0, "type-a"),
        _case("case-b", 1.0, "type-a"),
    )
    suite = _Suite("suite", "1", "suite-fingerprint", cases)
    case_aggregates = (
        aggregate_case("run-43", cases[0], [_scored("case-a", 0, 1.0)]),
        aggregate_case("run-43", cases[1], [_failed("case-b", 0)]),
    )

    aggregate = aggregate_suite("run-43", suite, case_aggregates)

    assert aggregate.quality_status == "incomplete"
    assert aggregate.metric_vector is None
    assert aggregate.cases_with_quality == 1
    assert aggregate.cases_without_quality == 1
    assert aggregate.quality_case_coverage == 0.5
    assert aggregate.quality_suite_weight_coverage == 0.5


def test_failure_types_use_case_first_fixed_configured_weights_and_stable_order() -> None:
    cases = (
        _case("case-a", 1.0, "type-b"),
        _case("case-b", 1.0, "type-a"),
        _case("case-c", 1.0, "type-b"),
    )
    suite = _Suite("suite", "1", "suite-fingerprint", cases)
    case_aggregates = tuple(
        aggregate_case(
            "run-43",
            case,
            [_scored(case.case_id, 0, value)],
        )
        for case, value in zip(cases, (1.0, 0.25, 0.0), strict=True)
    )

    aggregates = aggregate_failure_types("run-43", suite, case_aggregates)

    assert [item.failure_type for item in aggregates] == ["type-b", "type-a"]
    assert aggregates[0].configured_suite_weight == 2.0
    assert aggregates[0].metric_vector == {name: 0.5 for name in METRICS}
    assert aggregates[1].metric_vector == {name: 0.25 for name in METRICS}


def test_raw_samples_and_formal_aggregates_persist_in_one_run(tmp_path: Path) -> None:
    cases = (
        _case("case-a", 1.0, "type-a"),
        _case("case-b", 1.0, "type-b"),
    )
    suite = _Suite("suite", "1", "s" * 64, cases)
    sample_results = [
        {
            **_scored("case-a", 0, 1.0),
            "sample_sequence": 1,
            "weight": 1.0,
            "evaluation_failure_type": "type-a",
            "candidate_document": {"case_id": "case-a"},
            "report": None,
            "evidence_diagnostics": {},
        },
        {
            **_failed("case-b", 0),
            "sample_sequence": 2,
            "weight": 1.0,
            "evaluation_failure_type": "type-b",
        },
    ]
    case_aggregates = tuple(
        aggregate_case("run-43", case, [sample_results[index]])
        for index, case in enumerate(cases)
    )
    suite_aggregate = aggregate_suite("run-43", suite, case_aggregates)
    type_aggregates = aggregate_failure_types("run-43", suite, case_aggregates)
    database = tmp_path / "evaluation.db"
    initialize_database(database)
    manifest = {
        "manifest_schema_version": "2",
        "run_id": "run-43",
        "selected_condition_id": "condition-v2",
        "runtime_variant": "full_context_one_shot",
        "evaluation_method": "structured_report_v1",
        "condition_fingerprint": "c" * 64,
        "code_revision": "d" * 40,
        "structured_report_schema_version": "1",
        "evaluation_suite": {
            "suite_id": "suite",
            "suite_version": "1",
            "cases": [
                {"case_id": case.case_id, "weight": case.weight} for case in cases
            ],
        },
    }

    persist_finalizing_sample_run(
        database,
        manifest=manifest,
        trace_events=[],
        sample_results=sample_results,
        started_at="2026-08-14T00:00:00Z",
        case_aggregates=[item.as_dict() for item in case_aggregates],
        suite_aggregate=suite_aggregate.as_dict(),
        failure_type_aggregates=[item.as_dict() for item in type_aggregates],
    )

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_outcomes"
        ).fetchone() == (2,)
        assert connection.execute(
            "SELECT case_id, quality_status, metrics_json "
            "FROM evaluation_case_aggregates ORDER BY case_sequence"
        ).fetchall() == [
            ("case-a", "complete", json.dumps({name: 1.0 for name in METRICS}, separators=(",", ":"), sort_keys=True)),
            ("case-b", "incomplete", None),
        ]
        assert connection.execute(
            "SELECT quality_status, metrics_json FROM evaluation_suite_aggregates"
        ).fetchone() == ("incomplete", None)
        assert connection.execute(
            "SELECT failure_type FROM evaluation_failure_type_aggregates "
            "ORDER BY type_sequence"
        ).fetchall() == [("type-a",), ("type-b",)]
