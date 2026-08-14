from __future__ import annotations

from collections.abc import Sequence
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
)
from devagentops.conditions.l1.executor import ConfiguredL1ConditionExecutor
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
from devagentops.evaluation.execution import (
    ExecutionPolicy,
    execute_sample_plan,
    plan_samples,
)
from devagentops.evaluation.persistence import (
    complete_run,
    mark_run_failed,
    persist_failed_run,
    persist_finalizing_sample_run,
)
from devagentops.evaluation.run import (
    EvaluationRunError,
    _code_revision,
    _failure_event,
    _git_dirty,
    _now,
)
from devagentops.evaluation.trace import TraceRecorder
from devagentops.providers.minimax_v1 import (
    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
    MINIMAX_M3_TOKENIZER_REPOSITORY,
    MINIMAX_M3_TOKENIZER_REVISION,
    MINIMAX_M3_TOKENIZER_SHA256,
    create_minimax_provider,
)
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
) -> dict[str, Any]:
    effective = condition.effective_condition
    _validate_issue_41_condition(effective, len(selected_cases))
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
    planned_samples = plan_samples(
        run_id=run_id,
        suite_cases=selected_cases,
        repeat_count=execution_policy["repeat_count"],
    )
    manifest = _manifest(
        matrix=matrix,
        suite=suite,
        condition=condition,
        selected_case_ids=selected_case_ids,
        run_id=run_id,
        code_revision=code_revision,
        git_dirty=git_dirty,
        run_configuration_fingerprint=run_configuration_fingerprint,
        planned_sample_count=len(planned_samples),
    )
    recorder = TraceRecorder(run_id)
    recorder.record("run_started", occurred_at=started_at)
    configured_treatment = ConfiguredL1Treatment(
        provider_id=treatment["provider"]["id"],
        model=treatment["model"],
        reasoning=treatment["reasoning"],
        generation=treatment["generation"],
        context_limit_tokens=treatment["context"]["context_window_tokens"],
        max_completion_tokens=treatment["generation"]["max_completion_tokens"],
        task_contract_version=TASK_CONTRACT_VERSION,
        output_contract_prompt_suffix=output_contract_prompt_suffix(),
    )
    executor = ConfiguredL1ConditionExecutor(
        prompt=task_contract_prompt,
        treatment=configured_treatment,
        provider_factory=lambda: create_minimax_provider(
            base_url=treatment["provider"]["base_url"],
            timeout_seconds=execution_policy["request_timeout_seconds"],
        ),
    )
    try:
        results = execute_sample_plan(
            planned_samples,
            executor=executor,
            recorder=recorder,
            policy=ExecutionPolicy(
                repeat_count=execution_policy["repeat_count"],
                max_case_concurrency=execution_policy["max_case_concurrency"],
                retry_count=execution_policy["retry_count"],
            ),
        )
    except Exception as exc:
        failure_message = (
            "Condition execution stopped because of an unexpected run-level error"
        )
        recorder.record(
            "failure",
            payload={"code": "execution_engine_failed", "stage": "execution_engine"},
        )
        persist_failed_run(
            database_path,
            manifest=manifest,
            trace_events=list(recorder.snapshot()),
            started_at=started_at,
            failure_code="execution_engine_failed",
            failure_message=failure_message,
        )
        raise EvaluationRunError(
            failure_message,
            code="execution_engine_failed",
        ) from exc
    sample_results = [result.data for result in results]
    failed_count = sum(result.status == "execution_failed" for result in results)
    scored_count = len(results) - failed_count
    final_status = (
        "completed" if failed_count == 0 else "completed_with_sample_failures"
    )
    metric_preview = {
        "status": "aggregation_deferred",
        "scope": "sample_level_only",
        "reason": "Sample-to-Case-to-Suite aggregation is deferred",
        "coverage": {
            "planned_sample_count": len(results),
            "scored_sample_count": scored_count,
            "failed_sample_count": failed_count,
        },
    }
    run_completed_event = recorder.record(
        "run_completed",
        payload={
            "status": final_status,
            "selected_case_count": len(selected_cases),
            "planned_sample_count": len(results),
            "scored_sample_count": scored_count,
            "failed_sample_count": failed_count,
        },
    )
    trace = list(recorder.snapshot())
    persist_finalizing_sample_run(
        database_path,
        manifest=manifest,
        trace_events=trace[:-1],
        sample_results=sample_results,
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
            trace[:-1],
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
        "trace": trace,
        "sample_results": sample_results,
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
    planned_sample_count: int,
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
        "sample_plan": {
            "planned_sample_count": planned_sample_count,
            "ordering": "suite_case_order_then_repeat_index",
        },
        "structured_report_schema_version": REPORT_SCHEMA_VERSION,
        "model_configuration": {
            "provider": effective["treatment"]["provider"]["id"],
            "model": effective["treatment"]["model"],
        },
        "tool_call_protocol": {
            "applicability": "not_applicable",
            "reason": "full_context_one_shot_has_no_tools",
        },
        "debug_semantics": {
            "formal_evaluation": False,
            "quality_gate_qualification": False,
            "leaderboard_eligible": False,
        },
    }


def _validate_issue_41_condition(effective: dict[str, Any], case_count: int) -> None:
    policy = effective["execution_policy"]
    if effective["runtime_variant"] != "full_context_one_shot" or case_count < 1:
        raise EvaluationRunError(
            "Matrix v2 MiniMax development run requires at least one L1 Case",
            code="unsupported_v2_debug_shape",
        )
    if policy["retry_count"] != 0:
        raise EvaluationRunError(
            "Matrix v2 execution engine does not support retries",
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
