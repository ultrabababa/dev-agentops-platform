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
from devagentops.component_registry import resolve_frozen_component_manifest
from devagentops.evaluation_persistence import (
    canonical_sha256,
    complete_run,
    mark_run_failed,
    persist_failed_run,
    persist_finalizing_run,
)
from devagentops.evaluation_preflight import run_formal_eval_doctor
from devagentops.full_context_one_shot import (
    CONTEXT_LIMIT_TOKENS,
    MAX_OUTPUT_TOKENS,
    RUNTIME_INPUT_SERIALIZATION_VERSION,
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
    FullContextOneShotError,
    run_full_context_one_shot,
)
from devagentops.model_provider import ModelProviderError, create_model_provider
from devagentops.pipeline_baseline import (
    PIPELINE_VERSION,
    PipelineBaselineError,
    run_pipeline_baseline,
)
from devagentops.runtime_workspace import RuntimeCaseWorkspace, RuntimeWorkspaceError
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
L1_MODEL_CONFIGURATION = {
    "provider": "siliconflow",
    "model": "Qwen/Qwen3.5-4B",
}
L1_PROMPT_VERSION = "structured-triage-task-contract-v1"


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
    runtime_variant = effective["runtime_variant"]
    _validate_condition(effective, len(preflight.suite.cases))

    l1_prompt = None
    if runtime_variant == "full_context_one_shot":
        l1_prompt = resolve_frozen_component_manifest(
            registry_path,
            "prompt",
            L1_PROMPT_VERSION,
        )

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
        "runtime_variant": runtime_variant,
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
        "tool_call_protocol": (
            TOOL_CALL_PROTOCOL_NOT_APPLICABLE
            if runtime_variant == "pipeline_baseline"
            else {
                "applicability": "not_applicable",
                "reason": "full_context_one_shot_has_no_tools",
            }
        ),
        "repeat_index": 0,
    }
    if runtime_variant == "pipeline_baseline":
        manifest["pipeline_version"] = PIPELINE_VERSION
    else:
        manifest["task_contract"] = {
            "component_version": L1_PROMPT_VERSION,
            "fingerprint": condition_identity["component_fingerprints"]["prompt"],
        }
        manifest["runtime_input_serialization"] = {
            "version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        }
        manifest["l1_execution"] = {
            "provider": "siliconflow",
            "model": "Qwen/Qwen3.5-4B",
            "context_limit_tokens": CONTEXT_LIMIT_TOKENS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "enable_thinking": False,
            "temperature": 0,
            "completions": 1,
            "stream": False,
            "output_protocol": STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
            "expected_model_calls_per_case": 1,
            "sdk_retries": 0,
            "tools": None,
        }

    trace: list[dict[str, Any]] = []
    _append_event(trace, run_id, "run_started", started_at, payload={})
    case_results: list[dict[str, Any]] = []
    for suite_case in preflight.suite.cases:
        case_id = suite_case.case_id
        _append_event(trace, run_id, "case_started", _now(), case_id=case_id)
        workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
        if runtime_variant == "pipeline_baseline":
            _append_event(trace, run_id, "pipeline_started", _now(), case_id=case_id)
            try:
                pipeline_result = run_pipeline_baseline(workspace)
            except (PipelineBaselineError, RuntimeWorkspaceError) as exc:
                _fail_run(
                    database_path,
                    manifest,
                    trace,
                    started_at,
                    case_id,
                    "pipeline_baseline_failed",
                    "pipeline",
                    str(exc),
                )
            candidate_document: Any = pipeline_result.raw_report
            visible_output = None
        else:
            _append_event(trace, run_id, "l1_execution_started", _now(), case_id=case_id)
            try:
                provider = create_model_provider()
                assert l1_prompt is not None
                l1_result = run_full_context_one_shot(
                    workspace,
                    l1_prompt,
                    provider,
                    before_model_call=lambda payload: _append_event(
                        trace,
                        run_id,
                        "model_call_started",
                        _now(),
                        case_id=case_id,
                        payload=payload,
                    ),
                )
            except (FullContextOneShotError, ModelProviderError, RuntimeWorkspaceError) as exc:
                failure_code = getattr(exc, "code", "l1_execution_failed")
                stage = (
                    "context_feasibility"
                    if failure_code == "l1_context_infeasible"
                    else "model_provider"
                    if isinstance(exc, ModelProviderError)
                    else "l1_execution"
                )
                payload = {"code": failure_code, "stage": stage}
                payload["actual_call_count"] = sum(
                    event["event_type"] == "model_call_started"
                    and event["case_id"] == case_id
                    for event in trace
                )
                if isinstance(exc, ModelProviderError) and exc.http_status is not None:
                    payload["http_status"] = exc.http_status
                _fail_run(
                    database_path,
                    manifest,
                    trace,
                    started_at,
                    case_id,
                    failure_code,
                    stage,
                    str(exc),
                    failure_payload=payload,
                )
            candidate_document = l1_result.candidate_document
            visible_output = l1_result.response.visible_output
            _append_event(
                trace,
                run_id,
                "model_call_completed",
                _now(),
                case_id=case_id,
                payload={
                    "logical_call_number": 1,
                    "provider_request_id": l1_result.response.provider_request_id,
                    "returned_model": l1_result.response.returned_model,
                    "usage": l1_result.response.usage,
                    "latency_ms": l1_result.response.latency_ms,
                    "finish_reason": l1_result.response.finish_reason,
                    "visible_output": visible_output,
                    "actual_call_count": 1,
                },
            )
        _append_event(
            trace,
            run_id,
            "report_submitted",
            _now(),
            case_id=case_id,
            payload={
                "report_schema_version": REPORT_SCHEMA_VERSION,
                "candidate_report_sha256": canonical_sha256(
                    candidate_document
                ),
            },
        )
        score = evaluate_case_report(
            candidate_document,
            suite_case.package,
        )
        if runtime_variant == "pipeline_baseline" and score.structured_report is None:
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
            "report": (
                score.structured_report.as_dict()
                if score.structured_report is not None
                else None
            ),
            "validation": score.validation.as_dict(),
            "quality_metrics": score.quality_metrics.as_dict(),
            "evidence_diagnostics": score.evidence_diagnostics.as_dict(),
        }
        if runtime_variant == "full_context_one_shot":
            result["candidate_document"] = candidate_document
            result["visible_output"] = visible_output
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


def _validate_condition(
    effective_condition: dict[str, Any],
    case_count: int,
) -> None:
    runtime_variant = effective_condition["runtime_variant"]
    if runtime_variant not in {"pipeline_baseline", "full_context_one_shot"}:
        raise EvaluationRunError(
            f"unsupported runtime_variant {runtime_variant!r}",
            code="unsupported_runtime_variant",
        )
    if effective_condition["repeats"] != 1 or case_count != 1:
        raise EvaluationRunError(
            "evaluation tracer bullet requires one repeat over one Case",
            code="unsupported_tracer_bullet_shape",
        )
    if runtime_variant == "pipeline_baseline":
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
        return
    if effective_condition["model"] != L1_MODEL_CONFIGURATION:
        raise EvaluationRunError(
            "L1 requires the frozen SiliconFlow Qwen/Qwen3.5-4B model identity",
            code="invalid_l1_model_configuration",
        )
    if effective_condition["components"] != {"prompt": L1_PROMPT_VERSION}:
        raise EvaluationRunError(
            "L1 requires only structured-triage-task-contract-v1",
            code="invalid_l1_component_configuration",
        )
    expected_budgets = {
        "context_limit_tokens": CONTEXT_LIMIT_TOKENS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    if effective_condition["budgets"] != expected_budgets:
        raise EvaluationRunError(
            "L1 requires the frozen context and output token limits",
            code="invalid_l1_budget_configuration",
        )


def _fail_run(
    database_path: Path,
    manifest: dict[str, Any],
    trace: list[dict[str, Any]],
    started_at: str,
    case_id: str,
    failure_code: str,
    stage: str,
    failure_message: str,
    *,
    failure_payload: dict[str, Any] | None = None,
) -> None:
    _append_event(
        trace,
        manifest["run_id"],
        "failure",
        _now(),
        case_id=case_id,
        payload=failure_payload or {"code": failure_code, "stage": stage},
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
