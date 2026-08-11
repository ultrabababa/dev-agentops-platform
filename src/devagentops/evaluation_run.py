from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from devagentops.evaluation_artifacts import (
    EvaluationArtifactError,
    write_evaluation_artifacts,
)
from devagentops.evaluation_persistence import (
    canonical_sha256,
    complete_run,
    mark_run_failed,
    persist_failed_run,
    persist_finalizing_run,
)
from devagentops.evaluation_preflight import run_formal_eval_doctor
from devagentops.pipeline_baseline import (
    PIPELINE_VERSION,
    PipelineBaselineError,
    RuntimeCaseWorkspace,
    run_pipeline_baseline,
)
from devagentops.scoring import evaluate_case_report
from devagentops.storage import StorageError, initialize_database
from devagentops.structured_report import REPORT_SCHEMA_VERSION


MODEL_NOT_APPLICABLE = {
    "applicability": "not_applicable",
    "reason": "deterministic_pipeline_uses_no_model",
}
TOOL_CALL_PROTOCOL_NOT_APPLICABLE = {
    "applicability": "not_applicable",
    "reason": "deterministic_pipeline_uses_no_model_or_tools",
}


class EvaluationRunError(RuntimeError):
    def __init__(self, message: str, *, code: str = "evaluation_run_failed"):
        super().__init__(message)
        self.code = code


def run_evaluation(
    *,
    matrix_path: Path,
    registry_path: Path,
    suite_path: Path,
    condition_id: str,
    database_path: Path,
    artifacts_dir: Path,
) -> dict[str, Any]:
    preflight = run_formal_eval_doctor(matrix_path, registry_path, suite_path)
    condition = next(
        (
            candidate
            for candidate in preflight.matrix.conditions
            if candidate.condition_id == condition_id
        ),
        None,
    )
    if condition is None:
        raise EvaluationRunError(
            f"evaluation condition does not exist: {condition_id}",
            code="unknown_evaluation_condition",
        )
    condition_identity = condition.as_dict()
    effective = condition.effective_condition
    _validate_tracer_bullet_condition(effective, len(preflight.suite.cases))

    initialize_database(database_path)
    run_id = str(uuid4())
    code_revision = _code_revision()
    started_at = _now()
    manifest = {
        "manifest_schema_version": "1",
        "run_id": run_id,
        "run_kind": "tracer_bullet",
        "code_revision": code_revision,
        "matrix": {
            "matrix_id": preflight.matrix.matrix_id,
            "matrix_version": preflight.matrix.matrix_version,
            "schema_version": preflight.matrix.schema_version,
        },
        "selected_condition_id": condition.condition_id,
        "effective_condition": effective,
        "condition_fingerprint": condition_identity["condition_fingerprint"],
        "component_versions": effective["components"],
        "component_fingerprints": condition_identity.get(
            "component_fingerprints", {}
        ),
        "runtime_variant": "pipeline_baseline",
        "pipeline_version": PIPELINE_VERSION,
        "evaluation_method": effective["evaluation_method"],
        "evaluation_suite": {
            "schema_version": preflight.suite.schema_version,
            "suite_id": preflight.suite.suite_id,
            "suite_version": preflight.suite.suite_version,
            "suite_fingerprint": preflight.suite.suite_fingerprint,
            "cases": [
                {
                    "case_id": suite_case.case_id,
                    "case_schema_version": suite_case.package.case_schema_version,
                    "case_fingerprint": suite_case.package.case_fingerprint,
                    "weight": suite_case.weight,
                }
                for suite_case in preflight.suite.cases
            ],
        },
        "structured_report_schema_version": REPORT_SCHEMA_VERSION,
        "model_configuration": effective["model"],
        "tool_call_protocol": TOOL_CALL_PROTOCOL_NOT_APPLICABLE,
        "repeat_index": 0,
    }

    trace: list[dict[str, Any]] = []
    _append_event(trace, run_id, "run_started", started_at, payload={})
    case_results: list[dict[str, Any]] = []
    for suite_case in preflight.suite.cases:
        case_id = suite_case.case_id
        _append_event(trace, run_id, "case_started", _now(), case_id=case_id)
        _append_event(trace, run_id, "pipeline_started", _now(), case_id=case_id)
        workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
        try:
            pipeline_result = run_pipeline_baseline(workspace)
        except PipelineBaselineError as exc:
            failure_code = "pipeline_baseline_failed"
            _append_event(
                trace,
                run_id,
                "failure",
                _now(),
                case_id=case_id,
                payload={"code": failure_code, "stage": "pipeline"},
            )
            persist_failed_run(
                database_path,
                manifest=manifest,
                trace_events=trace,
                started_at=started_at,
                failure_code=failure_code,
                failure_message=str(exc),
            )
            raise EvaluationRunError(str(exc), code=failure_code) from exc
        _append_event(
            trace,
            run_id,
            "report_submitted",
            _now(),
            case_id=case_id,
            payload={
                "report_schema_version": REPORT_SCHEMA_VERSION,
                "candidate_report_sha256": canonical_sha256(
                    pipeline_result.raw_report
                ),
            },
        )
        score = evaluate_case_report(
            pipeline_result.raw_report,
            suite_case.package,
        )
        if score.structured_report is None:
            failure_code = "invalid_pipeline_report"
            failure_message = (
                "deterministic Pipeline Baseline produced an invalid report"
            )
            _append_event(
                trace,
                run_id,
                "failure",
                _now(),
                case_id=case_id,
                payload={"code": failure_code, "stage": "evaluation"},
            )
            persist_failed_run(
                database_path,
                manifest=manifest,
                trace_events=trace,
                started_at=started_at,
                failure_code=failure_code,
                failure_message=failure_message,
            )
            raise EvaluationRunError(failure_message, code=failure_code)
        result = {
            "case_id": case_id,
            "case_fingerprint": suite_case.package.case_fingerprint,
            "report": score.structured_report.as_dict(),
            "validation": score.validation.as_dict(),
            "quality_metrics": score.quality_metrics.as_dict(),
            "evidence_diagnostics": score.evidence_diagnostics.as_dict(),
        }
        case_results.append(result)
        _append_event(
            trace,
            run_id,
            "evaluation_completed",
            _now(),
            case_id=case_id,
            payload={"quality_metrics": result["quality_metrics"]},
        )
        _append_event(trace, run_id, "case_completed", _now(), case_id=case_id)

    run_completed_event = _trace_event(
        run_id=run_id,
        sequence=len(trace) + 1,
        event_type="run_completed",
        occurred_at=_now(),
        case_id=None,
        payload={},
    )
    persist_finalizing_run(
        database_path,
        manifest=manifest,
        trace_events=trace,
        case_results=case_results,
        started_at=started_at,
    )
    try:
        complete_run(
            database_path,
            run_completed_event=run_completed_event,
        )
    except StorageError as exc:
        failure_code = "run_finalization_failed"
        failure_event = _failure_event(
            trace,
            run_id,
            failure_code=failure_code,
            stage="persistence",
        )
        mark_run_failed(
            database_path,
            failure_event=failure_event,
            failure_code=failure_code,
            failure_message=str(exc),
        )
        raise EvaluationRunError(str(exc), code=failure_code) from exc

    artifact_document = {
        "artifact_schema_version": "1",
        "run_id": run_id,
        "status": "completed",
        "manifest": manifest,
        "trace": [*trace, run_completed_event],
        "case_results": case_results,
    }
    try:
        artifact_paths = write_evaluation_artifacts(
            artifacts_dir,
            artifact_document,
        )
    except EvaluationArtifactError as exc:
        failure_code = "artifact_write_failed"
        failure_event = _failure_event(
            trace,
            run_id,
            failure_code=failure_code,
            stage="artifact",
        )
        mark_run_failed(
            database_path,
            failure_event=failure_event,
            failure_code=failure_code,
            failure_message=str(exc),
        )
        raise EvaluationRunError(str(exc), code=failure_code) from exc
    return {
        "status": "completed",
        "run_id": run_id,
        "condition_id": condition.condition_id,
        "artifacts": artifact_paths,
    }


def _validate_tracer_bullet_condition(
    effective_condition: dict[str, Any],
    case_count: int,
) -> None:
    if effective_condition["runtime_variant"] != "pipeline_baseline":
        raise EvaluationRunError(
            "Issue #16 eval run supports only runtime_variant 'pipeline_baseline'",
            code="unsupported_runtime_variant",
        )
    if effective_condition["model"] != MODEL_NOT_APPLICABLE:
        raise EvaluationRunError(
            "Issue #16 pipeline condition requires explicit non-applicable model state",
            code="invalid_pipeline_model_configuration",
        )
    if effective_condition["components"]:
        raise EvaluationRunError(
            "Issue #16 deterministic pipeline does not reference components",
            code="unexpected_pipeline_components",
        )
    if effective_condition["repeats"] != 1 or case_count != 1:
        raise EvaluationRunError(
            "Issue #16 tracer bullet requires one repeat over one tiny fixture case",
            code="unsupported_tracer_bullet_shape",
        )


def _append_event(
    trace: list[dict[str, Any]],
    run_id: str,
    event_type: str,
    occurred_at: str,
    *,
    case_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    trace.append(
        _trace_event(
            run_id=run_id,
            sequence=len(trace) + 1,
            event_type=event_type,
            occurred_at=occurred_at,
            case_id=case_id,
            payload=payload or {},
        )
    )


def _trace_event(
    *,
    run_id: str,
    sequence: int,
    event_type: str,
    occurred_at: str,
    case_id: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "sequence": sequence,
        "event_type": event_type,
        "case_id": case_id,
        "occurred_at": occurred_at,
        "payload": payload,
    }


def _failure_event(
    trace: list[dict[str, Any]],
    run_id: str,
    *,
    failure_code: str,
    stage: str,
) -> dict[str, Any]:
    return _trace_event(
        run_id=run_id,
        sequence=len(trace) + 1,
        event_type="failure",
        occurred_at=_now(),
        case_id=None,
        payload={"code": failure_code, "stage": stage},
    )


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _code_revision() -> str:
    repository_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvaluationRunError(
            "could not resolve the evaluation code revision",
            code="code_revision_unavailable",
        ) from exc
    revision = result.stdout.strip()
    if len(revision) not in {40, 64}:
        raise EvaluationRunError(
            "resolved evaluation code revision is invalid",
            code="invalid_code_revision",
        )
    return revision
