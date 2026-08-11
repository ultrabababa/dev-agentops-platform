from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from devagentops.storage import StorageError, create_database_engine


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
            for result in case_results:
                report = result["report"]
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
                        "schema_version": report["schema_version"],
                        "valid": result["validation"]["valid"],
                        "report_json": canonical_json(report),
                        "validation_json": canonical_json(result["validation"]),
                        "report_sha256": canonical_sha256(report),
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
) -> None:
    engine = create_database_engine(database_path)
    try:
        with engine.begin() as connection:
            _insert_trace_event(connection, run_completed_event)
            connection.execute(
                text(
                    "UPDATE evaluation_runs SET status = 'completed', "
                    "completed_at = :completed_at WHERE run_id = :run_id"
                ),
                {
                    "completed_at": run_completed_event["occurred_at"],
                    "run_id": run_completed_event["run_id"],
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
            "(run_id, sequence, event_type, case_id, occurred_at, payload_json) "
            "VALUES (:run_id, :sequence, :event_type, :case_id, :occurred_at, "
            ":payload_json)"
        ),
        {
            "run_id": event["run_id"],
            "sequence": event["sequence"],
            "event_type": event["event_type"],
            "case_id": event["case_id"],
            "occurred_at": event["occurred_at"],
            "payload_json": canonical_json(event["payload"]),
        },
    )
