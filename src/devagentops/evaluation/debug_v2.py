from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

from devagentops.conditions.l1.development_output_contract import (
    OUTPUT_CONTRACT_ID,
    OUTPUT_CONTRACT_PROMPT_SHA256,
    OUTPUT_CONTRACT_VERSION,
    OUTPUT_SCHEMA_SHA256,
    output_contract_prompt_suffix,
)
from devagentops.conditions.l1.full_context_v1 import (
    RUNTIME_INPUT_SERIALIZATION_VERSION,
    ConfiguredL1Treatment,
    FullContextOneShotError,
    run_configured_full_context_one_shot,
)
from devagentops.evaluation.artifacts import (
    EvaluationArtifactError,
    write_evaluation_artifacts,
)
from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.matrix_v2 import (
    EvaluationMatrixV2,
    ResolvedConditionV2,
    calculate_run_configuration_fingerprint,
)
from devagentops.evaluation.persistence import (
    canonical_sha256,
    complete_run,
    mark_run_failed,
    persist_finalizing_run,
)
from devagentops.evaluation.run import (
    EvaluationRunError,
    _append_event,
    _code_revision,
    _failure_event,
    _git_dirty,
    _now,
    _trace_event,
)
from devagentops.providers.minimax_v1 import (
    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
    MINIMAX_M3_TOKENIZER_REPOSITORY,
    MINIMAX_M3_TOKENIZER_REVISION,
    MINIMAX_M3_TOKENIZER_SHA256,
    create_minimax_provider,
)
from devagentops.providers.openai_compatible import OpenAICompatibleTransportError
from devagentops.runtime.workspace import RuntimeCaseWorkspace, RuntimeWorkspaceError
from devagentops.scoring.case import evaluate_case_report
from devagentops.scoring.report import REPORT_SCHEMA_VERSION
from devagentops.storage.database import StorageError, initialize_database


TASK_CONTRACT_VERSION = "structured-triage-task-contract-v1"
TASK_CONTRACT_FINGERPRINT = (
    "d96154bc6a5aa436c84f291c16848daec60bdbf1be250dcedc4b115f4b7c4988"
)
CONTEXT_SOURCE_URL = "https://www.minimax.io/models/text/m3"


def run_case_subset_debug_v2(
    *,
    matrix: EvaluationMatrixV2,
    suite,
    condition: ResolvedConditionV2,
    selected_cases: Sequence,
    registry_path: Path,
    database_path: Path,
    artifacts_dir: Path,
    metric_preview_builder: Callable[[list[dict[str, Any]]], dict[str, Any]],
) -> dict[str, Any]:
    effective = condition.effective_condition
    _validate_issue_39_condition(effective, len(selected_cases))
    treatment = effective["treatment"]
    execution_policy = effective["execution_policy"]
    selected_case_ids = [suite_case.case_id for suite_case in selected_cases]
    code_revision = _code_revision()
    git_dirty = _git_dirty()
    run_configuration_fingerprint = calculate_run_configuration_fingerprint(
        matrix,
        condition,
        suite_fingerprint=suite.suite_fingerprint,
        selected_cases=[
            {
                "case_id": item.case_id,
                "case_fingerprint": item.package.case_fingerprint,
                "weight": item.weight,
            }
            for item in selected_cases
        ],
        code_revision=code_revision,
        git_dirty=git_dirty,
    )
    task_contract_prompt = resolve_frozen_component_manifest(
        registry_path,
        "prompt",
        TASK_CONTRACT_VERSION,
    )
    initialize_database(database_path)
    run_id = str(uuid4())
    started_at = _now()
    manifest = _manifest(
        matrix=matrix,
        suite=suite,
        condition=condition,
        selected_case_ids=selected_case_ids,
        run_id=run_id,
        code_revision=code_revision,
        git_dirty=git_dirty,
        run_configuration_fingerprint=run_configuration_fingerprint,
    )

    suite_case = selected_cases[0]
    case_id = suite_case.case_id
    trace: list[dict[str, Any]] = []
    _append_event(trace, run_id, "run_started", started_at, payload={})
    _append_event(trace, run_id, "case_started", _now(), case_id=case_id)
    _append_event(trace, run_id, "l1_execution_started", _now(), case_id=case_id)
    case_results: list[dict[str, Any]] = []
    try:
        workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
        provider = create_minimax_provider(
            base_url=treatment["provider"]["base_url"],
            timeout_seconds=execution_policy["request_timeout_seconds"],
        )
        l1_result = run_configured_full_context_one_shot(
            workspace,
            task_contract_prompt,
            provider,
            ConfiguredL1Treatment(
                provider_id=treatment["provider"]["id"],
                model=treatment["model"],
                reasoning=treatment["reasoning"],
                generation=treatment["generation"],
                context_limit_tokens=treatment["context"]["context_window_tokens"],
                max_completion_tokens=treatment["generation"][
                    "max_completion_tokens"
                ],
                task_contract_version=TASK_CONTRACT_VERSION,
                output_contract_prompt_suffix=output_contract_prompt_suffix(),
            ),
            before_model_call=lambda payload: _append_event(
                trace,
                run_id,
                "model_call_started",
                _now(),
                case_id=case_id,
                payload={**payload, "attempt": 1, "retry_count": 0},
            ),
        )
    except (
        FullContextOneShotError,
        OpenAICompatibleTransportError,
        RuntimeWorkspaceError,
    ) as exc:
        failure_code = getattr(exc, "code", "l1_execution_failed")
        stage = (
            "context_feasibility"
            if failure_code == "l1_context_infeasible"
            else "model_provider"
            if isinstance(exc, OpenAICompatibleTransportError)
            else "l1_execution"
        )
        payload = {
            "code": failure_code,
            "stage": stage,
            "actual_call_count": sum(
                event["event_type"] == "model_call_started" for event in trace
            ),
            "retry_count": 0,
        }
        if isinstance(exc, OpenAICompatibleTransportError) and exc.http_status:
            payload["http_status"] = exc.http_status
        _append_event(trace, run_id, "failure", _now(), case_id=case_id, payload=payload)
        case_results.append(
            _failed_result(suite_case, failure_code, stage, str(exc))
        )
        _append_event(trace, run_id, "case_failed", _now(), case_id=case_id)
    else:
        response = l1_result.response
        reasoning_metadata = _reasoning_metadata(response.reasoning_output)
        _append_event(
            trace,
            run_id,
            "model_call_completed",
            _now(),
            case_id=case_id,
            payload={
                "logical_call_number": 1,
                "provider_request_id": response.provider_request_id,
                "returned_model": response.returned_model,
                "usage": response.usage,
                "latency_ms": response.latency_ms,
                "finish_reason": response.finish_reason,
                "visible_output": response.visible_output,
                "reasoning_observation": reasoning_metadata,
                "actual_call_count": 1,
                "retry_count": 0,
            },
        )
        candidate_document = l1_result.candidate_document
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
        case_results.append(
            {
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
                "visible_output": response.visible_output,
                "provider_observation": {
                    "provider_request_id": response.provider_request_id,
                    "returned_model": response.returned_model,
                    "usage": response.usage,
                    "finish_reason": response.finish_reason,
                    "latency_ms": response.latency_ms,
                    "reasoning": reasoning_metadata,
                },
                "context_assessment": {
                    "input_tokens": l1_result.token_count.input_tokens,
                    "method": l1_result.token_count.method,
                    "exact": True,
                    "context_window_tokens": l1_result.context_limit_tokens,
                    "reserved_completion_tokens": treatment["generation"][
                        "max_completion_tokens"
                    ],
                },
            }
        )
        _append_event(
            trace,
            run_id,
            "evaluation_completed",
            _now(),
            case_id=case_id,
            payload={"quality_metrics": case_results[0]["quality_metrics"]},
        )
        _append_event(trace, run_id, "case_completed", _now(), case_id=case_id)

    final_status = (
        "completed"
        if case_results[0]["outcome"]["status"] == "scored"
        else "completed_with_case_failures"
    )
    metric_preview = metric_preview_builder(case_results)
    run_completed_event = _trace_event(
        run_id=run_id,
        sequence=len(trace) + 1,
        event_type="run_completed",
        occurred_at=_now(),
        case_id=None,
        payload={
            "status": final_status,
            "selected_case_count": 1,
            "scored_case_count": int(final_status == "completed"),
            "failed_case_count": int(final_status != "completed"),
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
        failure_event = _failure_event(
            trace,
            run_id,
            failure_code="run_finalization_failed",
            stage="persistence",
        )
        mark_run_failed(
            database_path,
            failure_event=failure_event,
            failure_code="run_finalization_failed",
            failure_message=str(exc),
        )
        raise EvaluationRunError(str(exc), code="run_finalization_failed") from exc

    document = {
        "artifact_schema_version": "2",
        "run_id": run_id,
        "status": final_status,
        "manifest": manifest,
        "trace": [*trace, run_completed_event],
        "case_results": case_results,
        "metric_preview": metric_preview,
    }
    try:
        artifact_paths = write_evaluation_artifacts(artifacts_dir, document)
    except EvaluationArtifactError as exc:
        failure_event = _failure_event(
            trace,
            run_id,
            failure_code="artifact_write_failed",
            stage="artifact",
        )
        mark_run_failed(
            database_path,
            failure_event=failure_event,
            failure_code="artifact_write_failed",
            failure_message=str(exc),
        )
        raise EvaluationRunError(str(exc), code="artifact_write_failed") from exc
    return {
        "status": final_status,
        "run_id": run_id,
        "condition_id": condition.condition_id,
        "selected_case_ids": selected_case_ids,
        "metric_preview": metric_preview,
        "fingerprints": {
            "treatment": condition.treatment_fingerprint,
            "condition": condition.condition_fingerprint,
            "execution_policy": condition.execution_policy_fingerprint,
            "run_configuration": run_configuration_fingerprint,
        },
        "artifacts": artifact_paths,
    }


def _manifest(
    *,
    matrix: EvaluationMatrixV2,
    suite,
    condition: ResolvedConditionV2,
    selected_case_ids: list[str],
    run_id: str,
    code_revision: str,
    git_dirty: bool,
    run_configuration_fingerprint: str,
) -> dict[str, Any]:
    effective = condition.effective_condition
    return {
        "manifest_schema_version": "2",
        "run_id": run_id,
        "run_kind": "case_subset_debug",
        "code_revision": code_revision,
        "git_dirty": git_dirty,
        "matrix": {
            "matrix_id": matrix.matrix_id,
            "matrix_version": matrix.matrix_version,
            "schema_version": matrix.schema_version,
        },
        "selected_condition_id": condition.condition_id,
        "effective_condition": effective,
        "treatment": effective["treatment"],
        "execution_policy": effective["execution_policy"],
        "treatment_fingerprint": condition.treatment_fingerprint,
        "condition_fingerprint": condition.condition_fingerprint,
        "execution_policy_fingerprint": condition.execution_policy_fingerprint,
        "run_configuration_fingerprint": run_configuration_fingerprint,
        "runtime_variant": effective["runtime_variant"],
        "evaluation_method": effective["evaluation_method"],
        "evaluation_suite": {
            "schema_version": suite.schema_version,
            "suite_id": suite.suite_id,
            "suite_version": suite.suite_version,
            "suite_fingerprint": suite.suite_fingerprint,
            "cases": [
                {
                    "case_id": item.case_id,
                    "case_schema_version": item.package.case_schema_version,
                    "case_fingerprint": item.package.case_fingerprint,
                    "weight": item.weight,
                }
                for item in suite.cases
            ],
        },
        "case_selection": {"mode": "explicit_subset", "case_ids": selected_case_ids},
        "structured_report_schema_version": REPORT_SCHEMA_VERSION,
        "model_configuration": {
            "provider": effective["treatment"]["provider"]["id"],
            "model": effective["treatment"]["model"],
        },
        "tool_call_protocol": {
            "applicability": "not_applicable",
            "reason": "full_context_one_shot_has_no_tools",
        },
        "repeat_index": 0,
        "debug_semantics": {
            "formal_evaluation": False,
            "quality_gate_qualification": False,
            "leaderboard_eligible": False,
        },
    }


def _validate_issue_39_condition(effective: dict[str, Any], case_count: int) -> None:
    policy = effective["execution_policy"]
    if effective["runtime_variant"] != "full_context_one_shot" or case_count != 1:
        raise EvaluationRunError(
            "Matrix v2 MiniMax development run requires exactly one L1 Case",
            code="unsupported_v2_debug_shape",
        )
    if {key: policy[key] for key in ("repeat_count", "max_case_concurrency", "retry_count")} != {
        "repeat_count": 1,
        "max_case_concurrency": 1,
        "retry_count": 0,
    }:
        raise EvaluationRunError(
            "Issue #39 execution policy requires 1/1/0",
            code="unsupported_v2_execution_policy",
        )
    treatment = effective["treatment"]
    expected = {
        "provider": {
            "id": "minimax-official",
            "transport": "openai-compatible-chat-completions",
            "profile": "minimax-official-v1",
            "base_url": "https://api.minimaxi.com/v1",
        },
        "model": "MiniMax-M3",
        "reasoning": {"thinking": {"type": "adaptive"}, "reasoning_split": True},
        "generation": {
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        },
    }
    for field, value in expected.items():
        if treatment[field] != value:
            raise EvaluationRunError(
                f"unsupported Issue #39 MiniMax treatment field {field!r}",
                code="unsupported_v2_treatment",
            )
    contracts = treatment["contracts"]
    if contracts["task"] != {
        "component_type": "prompt",
        "version": TASK_CONTRACT_VERSION,
        "fingerprint": TASK_CONTRACT_FINGERPRINT,
    } or contracts["output"] != {
        "id": OUTPUT_CONTRACT_ID,
        "version": OUTPUT_CONTRACT_VERSION,
        "prompt_suffix_sha256": OUTPUT_CONTRACT_PROMPT_SHA256,
        "schema_version": "1",
        "schema_sha256": OUTPUT_SCHEMA_SHA256,
    } or contracts["runtime_input"] != {"version": RUNTIME_INPUT_SERIALIZATION_VERSION}:
        raise EvaluationRunError(
            "unsupported Issue #39 contract identity",
            code="unsupported_v2_contract_identity",
        )
    context = treatment["context"]
    tokenizer = context["tokenizer"]
    if (
        context["assessment"] != "exact"
        or context["context_window_tokens"] != 1000000
        or context["source"]["url"] != CONTEXT_SOURCE_URL
        or tokenizer["repository"] != MINIMAX_M3_TOKENIZER_REPOSITORY
        or tokenizer["revision"] != MINIMAX_M3_TOKENIZER_REVISION
        or tokenizer["tokenizer_sha256"] != MINIMAX_M3_TOKENIZER_SHA256
        or tokenizer["chat_template_sha256"] != MINIMAX_M3_CHAT_TEMPLATE_SHA256
        or tokenizer["renderer"] != "jinja2-3.1.6-sandbox-trim-lstrip-v1"
    ):
        raise EvaluationRunError(
            "unsupported Issue #39 context assessment identity",
            code="unsupported_v2_context_identity",
        )


def _reasoning_metadata(reasoning_output: str | None) -> dict[str, Any]:
    if reasoning_output is None:
        return {"present": False, "character_count": 0, "sha256": None}
    return {
        "present": True,
        "character_count": len(reasoning_output),
        "sha256": hashlib.sha256(reasoning_output.encode("utf-8")).hexdigest(),
    }


def _failed_result(suite_case, code: str, stage: str, message: str) -> dict[str, Any]:
    return {
        "case_id": suite_case.case_id,
        "case_fingerprint": suite_case.package.case_fingerprint,
        "weight": suite_case.weight,
        "evaluation_failure_type": suite_case.package.expected_answer.primary_failure_type,
        "outcome": {
            "status": "execution_failed",
            "failure_code": code,
            "failure_stage": stage,
            "failure_message": message,
        },
        "report": None,
        "validation": None,
        "quality_metrics": None,
        "evidence_diagnostics": None,
        "candidate_document": None,
        "visible_output": None,
    }
