from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.artifacts import (
    EvaluationArtifactError,
    write_evaluation_artifacts,
)
from devagentops.evaluation.persistence import (
    canonical_sha256,
    complete_run,
    mark_run_failed,
    persist_finalizing_run,
)
from devagentops.evaluation.preflight import run_formal_eval_doctor
from devagentops.evaluation.run import (
    L1_MODEL_CONFIGURATION,
    L1_PROMPT_VERSION,
    EvaluationRunError,
    _append_event,
    _code_revision,
    _failure_event,
    _now,
    _trace_event,
)
from devagentops.conditions.l1.full_context_v1 import (
    CONTEXT_LIMIT_TOKENS,
    MAX_OUTPUT_TOKENS,
    RUNTIME_INPUT_SERIALIZATION_VERSION,
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
    FullContextOneShotError,
    run_full_context_one_shot,
)
from devagentops.providers.siliconflow_v1 import (
    QWEN3_5_4B_TOKEN_COUNT_METHOD,
    QWEN3_5_4B_TOKENIZER_REVISION,
    QWEN3_5_4B_TOKENIZER_SHA256,
    ModelProviderError,
    create_model_provider,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace, RuntimeWorkspaceError
from devagentops.scoring.case import evaluate_case_report
from devagentops.storage.database import StorageError, initialize_database
from devagentops.scoring.report import REPORT_SCHEMA_VERSION


def run_case_subset_debug(
    *,
    matrix_path: Path,
    registry_path: Path,
    suite_path: Path,
    condition_id: str,
    case_ids: Sequence[str],
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
    effective = condition.effective_condition
    _validate_l1_debug_condition(effective)
    selected_cases = _select_cases(preflight.suite.cases, case_ids)
    task_contract_prompt = resolve_frozen_component_manifest(
        registry_path,
        "prompt",
        L1_PROMPT_VERSION,
    )

    initialize_database(database_path)
    run_id = str(uuid4())
    started_at = _now()
    condition_identity = condition.as_dict()
    selected_case_ids = [suite_case.case_id for suite_case in selected_cases]
    manifest = {
        "manifest_schema_version": "1",
        "run_id": run_id,
        "run_kind": "case_subset_debug",
        "code_revision": _code_revision(),
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
        "runtime_variant": effective["runtime_variant"],
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
        "case_selection": {
            "mode": "explicit_subset",
            "case_ids": selected_case_ids,
        },
        "structured_report_schema_version": REPORT_SCHEMA_VERSION,
        "model_configuration": effective["model"],
        "tool_call_protocol": {
            "applicability": "not_applicable",
            "reason": "full_context_one_shot_has_no_tools",
        },
        "repeat_index": 0,
        "task_contract": {
            "component_version": L1_PROMPT_VERSION,
            "fingerprint": condition_identity["component_fingerprints"]["prompt"],
        },
        "runtime_input_serialization": {
            "version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        },
        "l1_execution": {
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
            "token_accounting": {
                "method": QWEN3_5_4B_TOKEN_COUNT_METHOD,
                "tokenizer_revision": QWEN3_5_4B_TOKENIZER_REVISION,
                "tokenizer_sha256": QWEN3_5_4B_TOKENIZER_SHA256,
            },
        },
        "debug_semantics": {
            "formal_evaluation": False,
            "quality_gate_qualification": False,
            "leaderboard_eligible": False,
        },
    }

    trace: list[dict[str, Any]] = []
    _append_event(trace, run_id, "run_started", started_at, payload={})
    case_results: list[dict[str, Any]] = []
    for suite_case in selected_cases:
        case_id = suite_case.case_id
        _append_event(trace, run_id, "case_started", _now(), case_id=case_id)
        _append_event(trace, run_id, "l1_execution_started", _now(), case_id=case_id)
        try:
            workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
            provider = create_model_provider()
            l1_result = run_full_context_one_shot(
                workspace,
                task_contract_prompt,
                provider,
                before_model_call=lambda payload, case_id=case_id: _append_event(
                    trace,
                    run_id,
                    "model_call_started",
                    _now(),
                    case_id=case_id,
                    payload=payload,
                ),
            )
        except (
            FullContextOneShotError,
            ModelProviderError,
            RuntimeWorkspaceError,
        ) as exc:
            failure_code = getattr(exc, "code", "l1_execution_failed")
            stage = (
                "context_feasibility"
                if failure_code == "l1_context_infeasible"
                else "model_provider"
                if isinstance(exc, ModelProviderError)
                else "l1_execution"
            )
            failure_payload = {
                "code": failure_code,
                "stage": stage,
                "actual_call_count": sum(
                    event["event_type"] == "model_call_started"
                    and event["case_id"] == case_id
                    for event in trace
                ),
            }
            if isinstance(exc, ModelProviderError) and exc.http_status is not None:
                failure_payload["http_status"] = exc.http_status
            _append_event(
                trace,
                run_id,
                "failure",
                _now(),
                case_id=case_id,
                payload=failure_payload,
            )
            case_results.append(
                {
                    "case_id": case_id,
                    "case_fingerprint": suite_case.package.case_fingerprint,
                    "weight": suite_case.weight,
                    "evaluation_failure_type": (
                        suite_case.package.expected_answer.primary_failure_type
                    ),
                    "outcome": {
                        "status": "execution_failed",
                        "failure_code": failure_code,
                        "failure_stage": stage,
                        "failure_message": str(exc),
                    },
                    "report": None,
                    "validation": None,
                    "quality_metrics": None,
                    "evidence_diagnostics": None,
                    "candidate_document": None,
                    "visible_output": None,
                }
            )
            _append_event(trace, run_id, "case_failed", _now(), case_id=case_id)
            continue
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
                "candidate_report_sha256": canonical_sha256(candidate_document),
            },
        )
        score = evaluate_case_report(candidate_document, suite_case.package)
        result = {
            "case_id": case_id,
            "case_fingerprint": suite_case.package.case_fingerprint,
            "weight": suite_case.weight,
            "evaluation_failure_type": (
                suite_case.package.expected_answer.primary_failure_type
            ),
            "outcome": {"status": "scored"},
            "report": (
                score.structured_report.as_dict()
                if score.structured_report is not None
                else None
            ),
            "validation": score.validation.as_dict(),
            "quality_metrics": score.quality_metrics.as_dict(),
            "evidence_diagnostics": score.evidence_diagnostics.as_dict(),
            "candidate_document": candidate_document,
            "visible_output": visible_output,
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

    final_status = (
        "completed_with_case_failures"
        if any(
            result["outcome"]["status"] == "execution_failed"
            for result in case_results
        )
        else "completed"
    )
    metric_preview = _build_metric_preview(case_results)
    run_completed_event = _trace_event(
        run_id=run_id,
        sequence=len(trace) + 1,
        event_type="run_completed",
        occurred_at=_now(),
        case_id=None,
        payload={
            "status": final_status,
            "selected_case_count": len(case_results),
            "scored_case_count": sum(
                result["outcome"]["status"] == "scored"
                for result in case_results
            ),
            "failed_case_count": sum(
                result["outcome"]["status"] == "execution_failed"
                for result in case_results
            ),
        },
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
            status=final_status,
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
        "status": final_status,
        "manifest": manifest,
        "trace": [*trace, run_completed_event],
        "case_results": case_results,
        "metric_preview": metric_preview,
    }
    try:
        artifact_paths = write_evaluation_artifacts(artifacts_dir, artifact_document)
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
        "status": final_status,
        "run_id": run_id,
        "condition_id": condition.condition_id,
        "selected_case_ids": selected_case_ids,
        "metric_preview": metric_preview,
        "artifacts": artifact_paths,
    }


def _validate_l1_debug_condition(effective: dict[str, Any]) -> None:
    if effective["runtime_variant"] != "full_context_one_shot":
        raise EvaluationRunError(
            "Case Subset Debug initially supports only full_context_one_shot",
            code="unsupported_debug_runtime_variant",
        )
    if effective["repeats"] != 1:
        raise EvaluationRunError(
            "Case Subset Debug requires exactly one repeat",
            code="unsupported_debug_repeat_count",
        )
    if effective["model"] != L1_MODEL_CONFIGURATION:
        raise EvaluationRunError(
            "L1 requires the frozen SiliconFlow Qwen/Qwen3.5-4B model identity",
            code="invalid_l1_model_configuration",
        )
    if effective["components"] != {"prompt": L1_PROMPT_VERSION}:
        raise EvaluationRunError(
            "L1 requires only structured-triage-task-contract-v1",
            code="invalid_l1_component_configuration",
        )
    if effective["budgets"] != {
        "context_limit_tokens": CONTEXT_LIMIT_TOKENS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }:
        raise EvaluationRunError(
            "L1 requires the frozen context and output token limits",
            code="invalid_l1_budget_configuration",
        )


def _select_cases(suite_cases, case_ids: Sequence[str]):
    requested = list(case_ids)
    if not requested:
        raise EvaluationRunError(
            "Case Subset Debug requires at least one --case",
            code="empty_case_selection",
        )
    if len(set(requested)) != len(requested):
        raise EvaluationRunError(
            "Case Subset Debug Case selection contains duplicates",
            code="duplicate_case_selection",
        )
    known_ids = {suite_case.case_id for suite_case in suite_cases}
    unknown = sorted(set(requested) - known_ids)
    if unknown:
        raise EvaluationRunError(
            f"Case Subset Debug Case selection contains unknown IDs: {unknown}",
            code="unknown_case_selection",
        )
    requested_ids = set(requested)
    return tuple(
        suite_case for suite_case in suite_cases if suite_case.case_id in requested_ids
    )


def _build_metric_preview(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names = (
        "failure_type_exact_match",
        "failure_type_reviewed_acceptable_match",
        "report_evidence_hit_rate",
        "required_fields_completeness",
    )

    def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
        scored = [
            result
            for result in results
            if result["outcome"]["status"] == "scored"
        ]
        selected_weight = sum(result["weight"] for result in results)
        scored_weight = sum(result["weight"] for result in scored)
        failed_weight = selected_weight - scored_weight
        coverage = {
            "selected_case_count": len(results),
            "scored_case_count": len(scored),
            "failed_case_count": len(results) - len(scored),
            "selected_weight": selected_weight,
            "scored_weight": scored_weight,
            "failed_weight": failed_weight,
            "complete": len(scored) == len(results),
        }
        metric_vector = None
        if scored_weight:
            metric_vector = {
                name: sum(
                    result["quality_metrics"][name] * result["weight"]
                    for result in scored
                )
                / scored_weight
                for name in metric_names
            }
        return {"coverage": coverage, "metric_vector": metric_vector}

    overall = summarize(case_results)
    failure_types = sorted(
        {result["evaluation_failure_type"] for result in case_results}
    )
    by_failure_type = []
    for failure_type in failure_types:
        group = [
            result
            for result in case_results
            if result["evaluation_failure_type"] == failure_type
        ]
        group_summary = summarize(group)
        by_failure_type.append(
            {
                "failure_type": failure_type,
                **group_summary,
            }
        )
    return {
        "status": "complete" if overall["coverage"]["complete"] else "incomplete",
        "coverage": overall["coverage"],
        "overall": {"metric_vector": overall["metric_vector"]},
        "by_failure_type": by_failure_type,
    }
