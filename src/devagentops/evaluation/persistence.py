from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from devagentops.storage.database import StorageError, create_database_engine


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def persist_finalizing_run(
    database_path: Path,
    *,
    manifest: dict[str, Any],
    trace_events: list[dict[str, Any]],
    case_results: list[dict[str, Any]],
    started_at: str,
) -> None:
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs "
                    "(run_id, status, condition_id, runtime_variant, suite_id, "
                    "suite_version, condition_fingerprint, code_revision, started_at) "
                    "VALUES (:run_id, 'finalizing', :condition_id, :runtime_variant, "
                    ":suite_id, :suite_version, :condition_fingerprint, "
                    ":code_revision, :started_at)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "condition_id": manifest["selected_condition_id"],
                    "runtime_variant": manifest["runtime_variant"],
                    "suite_id": manifest["evaluation_suite"]["suite_id"],
                    "suite_version": manifest["evaluation_suite"]["suite_version"],
                    "condition_fingerprint": manifest["condition_fingerprint"],
                    "code_revision": manifest["code_revision"],
                    "started_at": started_at,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO evaluation_run_manifests "
                    "(run_id, schema_version, manifest_json, manifest_sha256) "
                    "VALUES (:run_id, :schema_version, :manifest_json, "
                    ":manifest_sha256)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "schema_version": manifest["manifest_schema_version"],
                    "manifest_json": canonical_json(manifest),
                    "manifest_sha256": canonical_sha256(manifest),
                },
            )
            for event in trace_events:
                _insert_trace_event(connection, event)
            case_metadata = {
                item["case_id"]: item
                for item in manifest["evaluation_suite"]["cases"]
            }
            for sequence, result in enumerate(case_results, start=1):
                outcome = result.get("outcome", {"status": "scored"})
                connection.execute(
                    text(
                        "INSERT INTO evaluation_case_outcomes "
                        "(run_id, case_id, sequence, suite_weight, "
                        "evaluation_failure_type, status, failure_code, "
                        "failure_stage, failure_message) VALUES "
                        "(:run_id, :case_id, :sequence, :suite_weight, "
                        ":evaluation_failure_type, :status, :failure_code, "
                        ":failure_stage, :failure_message)"
                    ),
                    {
                        "run_id": manifest["run_id"],
                        "case_id": result["case_id"],
                        "sequence": sequence,
                        "suite_weight": result.get(
                            "weight",
                            case_metadata[result["case_id"]]["weight"],
                        ),
                        "evaluation_failure_type": result.get(
                            "evaluation_failure_type"
                        ),
                        "status": outcome["status"],
                        "failure_code": outcome.get("failure_code"),
                        "failure_stage": outcome.get("failure_stage"),
                        "failure_message": outcome.get("failure_message"),
                    },
                )
                if outcome["status"] != "scored":
                    continue
                candidate_document = result.get(
                    "candidate_document",
                    result["report"],
                )
                connection.execute(
                    text(
                        "INSERT INTO evaluation_reports "
                        "(run_id, case_id, schema_version, valid, report_json, "
                        "validation_json, report_sha256) VALUES "
                        "(:run_id, :case_id, :schema_version, :valid, :report_json, "
                        ":validation_json, :report_sha256)"
                    ),
                    {
                        "run_id": manifest["run_id"],
                        "case_id": result["case_id"],
                        "schema_version": manifest[
                            "structured_report_schema_version"
                        ],
                        "valid": result["validation"]["valid"],
                        "report_json": canonical_json(candidate_document),
                        "validation_json": canonical_json(result["validation"]),
                        "report_sha256": canonical_sha256(candidate_document),
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO evaluation_case_scores "
                        "(run_id, case_id, evaluation_method, metrics_json, "
                        "diagnostics_json) VALUES "
                        "(:run_id, :case_id, :evaluation_method, :metrics_json, "
                        ":diagnostics_json)"
                    ),
                    {
                        "run_id": manifest["run_id"],
                        "case_id": result["case_id"],
                        "evaluation_method": manifest["evaluation_method"],
                        "metrics_json": canonical_json(result["quality_metrics"]),
                        "diagnostics_json": canonical_json(
                            result["evidence_diagnostics"]
                        ),
                    },
                )
    except SQLAlchemyError as exc:
        raise StorageError(f"Failed to persist evaluation run: {exc}") from exc
    finally:
        engine.dispose()


def persist_finalizing_sample_run(
    database_path: Path,
    *,
    manifest: dict[str, Any],
    trace_events: list[dict[str, Any]],
    sample_results: list[dict[str, Any]],
    started_at: str,
    case_aggregates: list[dict[str, Any]] | None = None,
    suite_aggregate: dict[str, Any] | None = None,
    failure_type_aggregates: list[dict[str, Any]] | None = None,
) -> None:
    sample_sequences = [result["sample_sequence"] for result in sample_results]
    if sample_sequences != sorted(sample_sequences) or len(sample_sequences) != len(
        set(sample_sequences)
    ):
        raise ValueError("sample results must have unique deterministic sequence order")
    aggregate_inputs = (
        case_aggregates,
        suite_aggregate,
        failure_type_aggregates,
    )
    if any(value is not None for value in aggregate_inputs) and not all(
        value is not None for value in aggregate_inputs
    ):
        raise ValueError("formal aggregate persistence requires all aggregate layers")
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs "
                    "(run_id, status, condition_id, runtime_variant, suite_id, "
                    "suite_version, condition_fingerprint, code_revision, started_at) "
                    "VALUES (:run_id, 'finalizing', :condition_id, :runtime_variant, "
                    ":suite_id, :suite_version, :condition_fingerprint, "
                    ":code_revision, :started_at)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "condition_id": manifest["selected_condition_id"],
                    "runtime_variant": manifest["runtime_variant"],
                    "suite_id": manifest["evaluation_suite"]["suite_id"],
                    "suite_version": manifest["evaluation_suite"]["suite_version"],
                    "condition_fingerprint": manifest["condition_fingerprint"],
                    "code_revision": manifest["code_revision"],
                    "started_at": started_at,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO evaluation_run_manifests "
                    "(run_id, schema_version, manifest_json, manifest_sha256) "
                    "VALUES (:run_id, :schema_version, :manifest_json, "
                    ":manifest_sha256)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "schema_version": manifest["manifest_schema_version"],
                    "manifest_json": canonical_json(manifest),
                    "manifest_sha256": canonical_sha256(manifest),
                },
            )
            for event in trace_events:
                _insert_trace_event(connection, event)
            case_metadata = {
                item["case_id"]: item
                for item in manifest["evaluation_suite"]["cases"]
            }
            for result in sample_results:
                outcome = result["outcome"]
                parameters = {
                    "run_id": manifest["run_id"],
                    "case_id": result["case_id"],
                    "repeat_index": result["repeat_index"],
                    "sample_sequence": result["sample_sequence"],
                    "suite_weight": result.get(
                        "weight",
                        case_metadata[result["case_id"]]["weight"],
                    ),
                    "evaluation_failure_type": result.get(
                        "evaluation_failure_type"
                    ),
                    "status": outcome["status"],
                    "failure_code": outcome.get("failure_code"),
                    "failure_stage": outcome.get("failure_stage"),
                    "failure_message": outcome.get("failure_message"),
                }
                connection.execute(
                    text(
                        "INSERT INTO evaluation_sample_outcomes "
                        "(run_id, case_id, repeat_index, sample_sequence, "
                        "suite_weight, evaluation_failure_type, status, "
                        "failure_code, failure_stage, failure_message) VALUES "
                        "(:run_id, :case_id, :repeat_index, :sample_sequence, "
                        ":suite_weight, :evaluation_failure_type, :status, "
                        ":failure_code, :failure_stage, :failure_message)"
                    ),
                    parameters,
                )
                if outcome["status"] != "scored":
                    continue
                candidate_document = result.get(
                    "candidate_document",
                    result["report"],
                )
                connection.execute(
                    text(
                        "INSERT INTO evaluation_sample_reports "
                        "(run_id, case_id, repeat_index, schema_version, valid, "
                        "report_json, validation_json, report_sha256) VALUES "
                        "(:run_id, :case_id, :repeat_index, :schema_version, :valid, "
                        ":report_json, :validation_json, :report_sha256)"
                    ),
                    {
                        "run_id": manifest["run_id"],
                        "case_id": result["case_id"],
                        "repeat_index": result["repeat_index"],
                        "schema_version": manifest[
                            "structured_report_schema_version"
                        ],
                        "valid": result["validation"]["valid"],
                        "report_json": canonical_json(candidate_document),
                        "validation_json": canonical_json(result["validation"]),
                        "report_sha256": canonical_sha256(candidate_document),
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO evaluation_sample_scores "
                        "(run_id, case_id, repeat_index, evaluation_method, "
                        "metrics_json, diagnostics_json) VALUES "
                        "(:run_id, :case_id, :repeat_index, :evaluation_method, "
                        ":metrics_json, :diagnostics_json)"
                    ),
                    {
                        "run_id": manifest["run_id"],
                        "case_id": result["case_id"],
                        "repeat_index": result["repeat_index"],
                        "evaluation_method": manifest["evaluation_method"],
                        "metrics_json": canonical_json(result["quality_metrics"]),
                        "diagnostics_json": canonical_json(
                            result["evidence_diagnostics"]
                        ),
                    },
                )
            if case_aggregates is not None:
                _insert_formal_aggregates(
                    connection,
                    case_aggregates=case_aggregates,
                    suite_aggregate=suite_aggregate,
                    failure_type_aggregates=failure_type_aggregates,
                )
    except SQLAlchemyError as exc:
        raise StorageError(f"Failed to persist evaluation sample run: {exc}") from exc
    finally:
        engine.dispose()


def persist_failed_run(
    database_path: Path,
    *,
    manifest: dict[str, Any],
    trace_events: list[dict[str, Any]],
    started_at: str,
    failure_code: str,
    failure_message: str,
) -> None:
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs "
                    "(run_id, status, condition_id, runtime_variant, suite_id, "
                    "suite_version, condition_fingerprint, code_revision, started_at, "
                    "completed_at, failure_code, failure_message) VALUES "
                    "(:run_id, 'failed', :condition_id, :runtime_variant, :suite_id, "
                    ":suite_version, :condition_fingerprint, :code_revision, "
                    ":started_at, :completed_at, :failure_code, :failure_message)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "condition_id": manifest["selected_condition_id"],
                    "runtime_variant": manifest["runtime_variant"],
                    "suite_id": manifest["evaluation_suite"]["suite_id"],
                    "suite_version": manifest["evaluation_suite"]["suite_version"],
                    "condition_fingerprint": manifest["condition_fingerprint"],
                    "code_revision": manifest["code_revision"],
                    "started_at": started_at,
                    "completed_at": trace_events[-1]["occurred_at"],
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO evaluation_run_manifests "
                    "(run_id, schema_version, manifest_json, manifest_sha256) "
                    "VALUES (:run_id, :schema_version, :manifest_json, "
                    ":manifest_sha256)"
                ),
                {
                    "run_id": manifest["run_id"],
                    "schema_version": manifest["manifest_schema_version"],
                    "manifest_json": canonical_json(manifest),
                    "manifest_sha256": canonical_sha256(manifest),
                },
            )
            for event in trace_events:
                _insert_trace_event(connection, event)
    except SQLAlchemyError as exc:
        raise StorageError(f"Failed to persist failed evaluation run: {exc}") from exc
    finally:
        engine.dispose()


def complete_run(
    database_path: Path,
    *,
    run_completed_event: dict[str, Any],
    status: str = "completed",
) -> None:
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            _insert_trace_event(connection, run_completed_event)
            connection.execute(
                text(
                    "UPDATE evaluation_runs SET status = :status, "
                    "completed_at = :completed_at WHERE run_id = :run_id"
                ),
                {
                    "completed_at": run_completed_event["occurred_at"],
                    "run_id": run_completed_event["run_id"],
                    "status": status,
                },
            )
    except SQLAlchemyError as exc:
        raise StorageError(f"Failed to complete evaluation run: {exc}") from exc
    finally:
        engine.dispose()


def mark_run_failed(
    database_path: Path,
    *,
    failure_event: dict[str, Any],
    failure_code: str,
    failure_message: str,
) -> None:
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            parameters = {"run_id": failure_event["run_id"]}
            connection.execute(
                text(
                    "DELETE FROM evaluation_failure_type_aggregates "
                    "WHERE run_id = :run_id"
                ),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_suite_aggregates WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_case_aggregates WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_sample_scores WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_sample_reports WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_sample_outcomes WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_case_outcomes WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_case_scores WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text("DELETE FROM evaluation_reports WHERE run_id = :run_id"),
                parameters,
            )
            connection.execute(
                text(
                    "DELETE FROM evaluation_trace_events "
                    "WHERE run_id = :run_id AND event_type = 'run_completed'"
                ),
                parameters,
            )
            connection.execute(
                text(
                    "UPDATE evaluation_runs SET status = 'failed', "
                    "completed_at = :completed_at, failure_code = :failure_code, "
                    "failure_message = :failure_message WHERE run_id = :run_id"
                ),
                {
                    "run_id": failure_event["run_id"],
                    "completed_at": failure_event["occurred_at"],
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                },
            )
            _insert_trace_event(connection, failure_event)
    except SQLAlchemyError as exc:
        raise StorageError(f"Failed to mark evaluation run as failed: {exc}") from exc
    finally:
        engine.dispose()


def _insert_trace_event(connection, event: dict[str, Any]) -> None:
    connection.execute(
        text(
            "INSERT INTO evaluation_trace_events "
            "(run_id, sequence, event_type, case_id, repeat_index, occurred_at, "
            "payload_json) VALUES (:run_id, :sequence, :event_type, :case_id, "
            ":repeat_index, :occurred_at, :payload_json)"
        ),
        {
            "run_id": event["run_id"],
            "sequence": event["sequence"],
            "event_type": event["event_type"],
            "case_id": event["case_id"],
            "repeat_index": event.get("repeat_index"),
            "occurred_at": event["occurred_at"],
            "payload_json": canonical_json(event["payload"]),
        },
    )


def _insert_formal_aggregates(
    connection,
    *,
    case_aggregates: list[dict[str, Any]],
    suite_aggregate: dict[str, Any] | None,
    failure_type_aggregates: list[dict[str, Any]] | None,
) -> None:
    if suite_aggregate is None or failure_type_aggregates is None:
        raise ValueError("formal aggregate persistence requires all aggregate layers")
    for case_sequence, aggregate in enumerate(case_aggregates, start=1):
        connection.execute(
            text(
                "INSERT INTO evaluation_case_aggregates "
                "(run_id, case_id, case_sequence, case_fingerprint, failure_type, "
                "suite_weight, aggregation_method, aggregation_version, "
                "requested_sample_count, scored_sample_count, "
                "execution_failed_sample_count, execution_coverage, "
                "protocol_valid_sample_count, protocol_invalid_sample_count, "
                "protocol_validity_rate, quality_status, metrics_json, "
                "scored_repeat_indices_json, failed_repeat_indices_json) VALUES "
                "(:run_id, :case_id, :case_sequence, :case_fingerprint, "
                ":failure_type, :suite_weight, :aggregation_method, "
                ":aggregation_version, :requested_sample_count, "
                ":scored_sample_count, :execution_failed_sample_count, "
                ":execution_coverage, :protocol_valid_sample_count, "
                ":protocol_invalid_sample_count, :protocol_validity_rate, "
                ":quality_status, :metrics_json, :scored_repeat_indices_json, "
                ":failed_repeat_indices_json)"
            ),
            {
                **aggregate,
                "case_sequence": case_sequence,
                "metrics_json": (
                    canonical_json(aggregate["metric_vector"])
                    if aggregate["metric_vector"] is not None
                    else None
                ),
                "scored_repeat_indices_json": canonical_json(
                    aggregate["scored_repeat_indices"]
                ),
                "failed_repeat_indices_json": canonical_json(
                    aggregate["failed_repeat_indices"]
                ),
            },
        )
    connection.execute(
        text(
            "INSERT INTO evaluation_suite_aggregates "
            "(run_id, suite_id, suite_version, suite_fingerprint, "
            "aggregation_method, aggregation_version, configured_suite_weight, "
            "total_case_count, requested_sample_count, scored_sample_count, "
            "execution_failed_sample_count, execution_coverage, "
            "protocol_valid_sample_count, protocol_invalid_sample_count, "
            "protocol_validity_rate, cases_with_quality, cases_without_quality, "
            "quality_case_coverage, quality_suite_weight_coverage, quality_status, "
            "metrics_json) VALUES (:run_id, :suite_id, :suite_version, "
            ":suite_fingerprint, :aggregation_method, :aggregation_version, "
            ":configured_suite_weight, :total_case_count, :requested_sample_count, "
            ":scored_sample_count, :execution_failed_sample_count, "
            ":execution_coverage, :protocol_valid_sample_count, "
            ":protocol_invalid_sample_count, :protocol_validity_rate, "
            ":cases_with_quality, :cases_without_quality, :quality_case_coverage, "
            ":quality_suite_weight_coverage, :quality_status, :metrics_json)"
        ),
        {
            **suite_aggregate,
            "metrics_json": (
                canonical_json(suite_aggregate["metric_vector"])
                if suite_aggregate["metric_vector"] is not None
                else None
            ),
        },
    )
    for type_sequence, aggregate in enumerate(failure_type_aggregates, start=1):
        connection.execute(
            text(
                "INSERT INTO evaluation_failure_type_aggregates "
                "(run_id, failure_type, type_sequence, aggregation_method, "
                "aggregation_version, case_count, configured_suite_weight, "
                "requested_sample_count, scored_sample_count, "
                "execution_failed_sample_count, execution_coverage, "
                "protocol_valid_sample_count, protocol_invalid_sample_count, "
                "protocol_validity_rate, cases_with_quality, cases_without_quality, "
                "quality_case_coverage, quality_suite_weight_coverage, "
                "quality_status, metrics_json) VALUES (:run_id, :failure_type, "
                ":type_sequence, :aggregation_method, :aggregation_version, "
                ":case_count, :configured_suite_weight, :requested_sample_count, "
                ":scored_sample_count, :execution_failed_sample_count, "
                ":execution_coverage, :protocol_valid_sample_count, "
                ":protocol_invalid_sample_count, :protocol_validity_rate, "
                ":cases_with_quality, :cases_without_quality, "
                ":quality_case_coverage, :quality_suite_weight_coverage, "
                ":quality_status, :metrics_json)"
            ),
            {
                **aggregate,
                "type_sequence": type_sequence,
                "metrics_json": (
                    canonical_json(aggregate["metric_vector"])
                    if aggregate["metric_vector"] is not None
                    else None
                ),
            },
        )
