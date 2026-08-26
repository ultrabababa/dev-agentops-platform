from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from devagentops.explorer.catalog import EvaluationCatalog, connect_readonly


class ExplorerDataError(RuntimeError):
    """Raised when frozen evaluation data violates its persisted contract."""


def _json_value(value: str, *, field: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ExplorerDataError(f"invalid JSON in {field}: {exc.msg}") from exc


def _json_object(value: str, *, field: str) -> dict[str, Any]:
    parsed = _json_value(value, field=field)
    if not isinstance(parsed, dict):
        raise ExplorerDataError(f"expected JSON object in {field}")
    return parsed


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _safe_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    model = manifest.get("model_configuration")
    model_configuration = {}
    if isinstance(model, dict):
        model_configuration = {
            key: model[key] for key in ("provider", "model") if key in model
        }
    output_contract: dict[str, Any] = {}
    treatment = manifest.get("treatment")
    if isinstance(treatment, dict):
        contracts = treatment.get("contracts")
        if isinstance(contracts, dict) and isinstance(contracts.get("output"), dict):
            output = contracts["output"]
            output_contract = {
                key: output[key]
                for key in (
                    "id",
                    "version",
                    "schema_version",
                    "evidence_reference_resolution",
                )
                if key in output
            }
    return {
        "schema_version": manifest.get("manifest_schema_version"),
        "run_kind": manifest.get("run_kind"),
        "model_configuration": model_configuration,
        "output_contract": output_contract,
        "code_revision": manifest.get("code_revision"),
        "git_dirty": manifest.get("git_dirty"),
        "suite_fingerprint": (
            manifest.get("evaluation_suite", {}).get("suite_fingerprint")
            if isinstance(manifest.get("evaluation_suite"), dict)
            else None
        ),
        "treatment_fingerprint": manifest.get("treatment_fingerprint"),
        "condition_fingerprint": manifest.get("condition_fingerprint"),
        "execution_policy_fingerprint": manifest.get(
            "execution_policy_fingerprint"
        ),
        "run_configuration_fingerprint": manifest.get(
            "run_configuration_fingerprint"
        ),
        "evaluation_method": manifest.get("evaluation_method"),
        "structured_report_schema_version": manifest.get(
            "structured_report_schema_version"
        ),
    }


def _safe_report(report: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: report.get(key)
        for key in (
            "schema_version", "case_id", "classification_status", "failure_type",
            "summary", "root_cause", "recommended_action", "confidence",
        )
        if key in report
    }
    references = report.get("evidence_references")
    if isinstance(references, list):
        result["evidence_references"] = [
            {"evidence_id": item.get("evidence_id")}
            for item in references
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
    return result


def _safe_validation(validation: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"valid": bool(validation.get("valid"))}
    errors = validation.get("errors")
    if isinstance(errors, list):
        result["errors"] = [
            {
                key: item[key]
                for key in ("code", "field", "message")
                if key in item
            }
            for item in errors
            if isinstance(item, dict)
        ]
    return result


class EvaluationRepository:
    def __init__(self, catalog: EvaluationCatalog):
        self.catalog = catalog

    def _connect(self, run_id: str) -> sqlite3.Connection:
        try:
            path = self.catalog.path_for_run(run_id)
        except KeyError as exc:
            raise KeyError(run_id) from exc
        return connect_readonly(path)

    def list_runs(self) -> list[dict[str, Any]]:
        return [self.get_run(run.run_id) for run in self.catalog.runs]

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._connect(run_id) as connection:
            row = connection.execute(
                "SELECT r.*, m.manifest_json, m.manifest_sha256 "
                "FROM evaluation_runs r JOIN evaluation_run_manifests m USING (run_id) "
                "WHERE r.run_id=?",
                (run_id,),
            ).fetchone()
            if row is None:
                raise KeyError(run_id)
            manifest = _json_object(row["manifest_json"], field="manifest_json")
            suite = connection.execute(
                "SELECT * FROM evaluation_suite_aggregates WHERE run_id=?",
                (run_id,),
            ).fetchone()
            failure_types = connection.execute(
                "SELECT * FROM evaluation_failure_type_aggregates "
                "WHERE run_id=? ORDER BY type_sequence",
                (run_id,),
            ).fetchall()
            counts = connection.execute(
                "SELECT COUNT(*) AS planned, "
                "SUM(status='scored') AS scored, "
                "SUM(status='execution_failed') AS failed "
                "FROM evaluation_sample_outcomes WHERE run_id=?",
                (run_id,),
            ).fetchone()
        metadata = self.catalog.metadata_for_run(run_id)
        return {
            "run_id": row["run_id"],
            "status": row["status"],
            "condition_id": row["condition_id"],
            "runtime_variant": row["runtime_variant"],
            "suite_id": row["suite_id"],
            "suite_version": row["suite_version"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "planned_samples": int(counts["planned"] or 0),
            "scored_samples": int(counts["scored"] or 0),
            "failed_samples": int(counts["failed"] or 0),
            "catalog": {
                "stage": metadata.stage,
                "role": metadata.role,
                "condition_family": metadata.condition_family,
                "representative": metadata.representative,
                "comparison_group": metadata.comparison_group,
            },
            "manifest": _safe_manifest(manifest),
            "manifest_sha256": row["manifest_sha256"],
            "suite_aggregate": self._aggregate(suite),
            "failure_type_aggregates": [self._aggregate(item) for item in failure_types],
        }

    @staticmethod
    def _aggregate(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        metrics = result.pop("metrics_json", None)
        result["metrics"] = (
            _json_object(metrics, field="metrics_json") if metrics is not None else None
        )
        quality = result["metrics"] or {}
        result["formal_metric_vector"] = {
            "execution_coverage": result.get("execution_coverage"),
            "failure_type_exact_match": quality.get("failure_type_exact_match"),
            "report_evidence_hit_rate": quality.get("report_evidence_hit_rate"),
            "required_fields_completeness": quality.get(
                "required_fields_completeness"
            ),
            "protocol_validity_rate": result.get("protocol_validity_rate"),
        }
        return result

    def list_run_cases(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect(run_id) as connection:
            rows = connection.execute(
                "SELECT * FROM evaluation_case_aggregates WHERE run_id=? "
                "ORDER BY case_sequence",
                (run_id,),
            ).fetchall()
        return [self._aggregate(row) for row in rows]  # type: ignore[misc]

    def get_sample(self, run_id: str, case_id: str, repeat_index: int) -> dict[str, Any]:
        with self._connect(run_id) as connection:
            outcome = connection.execute(
                "SELECT * FROM evaluation_sample_outcomes "
                "WHERE run_id=? AND case_id=? AND repeat_index=?",
                (run_id, case_id, repeat_index),
            ).fetchone()
            if outcome is None:
                raise KeyError((run_id, case_id, repeat_index))
            report = connection.execute(
                "SELECT * FROM evaluation_sample_reports "
                "WHERE run_id=? AND case_id=? AND repeat_index=?",
                (run_id, case_id, repeat_index),
            ).fetchone()
            score = connection.execute(
                "SELECT * FROM evaluation_sample_scores "
                "WHERE run_id=? AND case_id=? AND repeat_index=?",
                (run_id, case_id, repeat_index),
            ).fetchone()
            trajectory_available = False
            if _table_exists(connection, "evaluation_sample_trajectory_messages"):
                trajectory_available = connection.execute(
                    "SELECT 1 FROM evaluation_sample_trajectory_messages "
                    "WHERE run_id=? AND case_id=? AND repeat_index=? LIMIT 1",
                    (run_id, case_id, repeat_index),
                ).fetchone() is not None
            trace_available = connection.execute(
                "SELECT 1 FROM evaluation_trace_events "
                "WHERE run_id=? AND case_id=? AND repeat_index=? LIMIT 1",
                (run_id, case_id, repeat_index),
            ).fetchone() is not None
        result: dict[str, Any] = {
            "identity": {"run_id": run_id, "case_id": case_id, "repeat_index": repeat_index},
            "outcome": dict(outcome),
            "report": None,
            "validation": None,
            "score": None,
            "diagnostics": None,
            "trajectory_available": trajectory_available,
            "trace_available": trace_available,
        }
        if report is not None:
            report_value = _json_value(report["report_json"], field="report_json")
            result["report"] = (
                _safe_report(report_value) if isinstance(report_value, dict) else None
            )
            result["validation"] = _safe_validation(
                _json_object(report["validation_json"], field="validation_json")
            )
        if score is not None:
            result["score"] = _json_object(score["metrics_json"], field="metrics_json")
            result["diagnostics"] = _json_object(
                score["diagnostics_json"], field="diagnostics_json"
            )
        return result

    def get_trajectory(self, run_id: str, case_id: str, repeat_index: int) -> list[dict[str, Any]]:
        with self._connect(run_id) as connection:
            if not _table_exists(connection, "evaluation_sample_trajectory_messages"):
                return []
            rows = connection.execute(
                "SELECT message_index, message_role, message_json "
                "FROM evaluation_sample_trajectory_messages "
                "WHERE run_id=? AND case_id=? AND repeat_index=? "
                "ORDER BY message_index",
                (run_id, case_id, repeat_index),
            ).fetchall()
        return [
            {
                "message_index": row["message_index"],
                "message_role": row["message_role"],
                "message": _json_object(row["message_json"], field="message_json"),
            }
            for row in rows
        ]

    def get_trace(self, run_id: str, case_id: str, repeat_index: int) -> list[dict[str, Any]]:
        with self._connect(run_id) as connection:
            rows = connection.execute(
                "SELECT sequence, event_type, occurred_at, payload_json "
                "FROM evaluation_trace_events WHERE run_id=? AND case_id=? "
                "AND repeat_index=? ORDER BY sequence",
                (run_id, case_id, repeat_index),
            ).fetchall()
        return [
            {
                "sequence": row["sequence"],
                "event_type": row["event_type"],
                "occurred_at": row["occurred_at"],
                "payload": _json_object(row["payload_json"], field="payload_json"),
            }
            for row in rows
        ]
