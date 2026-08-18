from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from devagentops.conditions.l1.development_output_contract import (
    output_contract_prompt_suffix,
)
from devagentops.conditions.l1.executor import ConfiguredL1ConditionExecutor
from devagentops.conditions.l1.full_context_v1 import ConfiguredL1Treatment
from devagentops.conditions.l2.development_workflow_v1 import ConfiguredL2Treatment
from devagentops.conditions.l2.executor import ConfiguredL2ConditionExecutor
from devagentops.conditions.l4.react_condition import (
    ConfiguredL4ConditionExecutor,
    ConfiguredL4Treatment,
)
from devagentops.conditions.oracle.executor import (
    ConfiguredOracleConditionExecutor,
)
from devagentops.conditions.oracle.one_shot_v1 import (
    ConfiguredOracleTreatment,
)
from devagentops.evaluation.aggregation import (
    aggregate_case,
    aggregate_failure_types,
    aggregate_suite,
)
from devagentops.evaluation.artifacts import (
    EvaluationArtifactError,
    write_evaluation_artifacts,
)
from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.development_treatment import (
    L4_RUNTIME_CONTROL_VERSION,
    L4_TOOL_POLICY_VERSION,
    L4_TOOL_REGISTRY_VERSION,
    TASK_CONTRACT_VERSION,
    validate_minimax_development_condition,
)
from devagentops.evaluation.execution import (
    ExecutionPolicy,
    execute_sample_plan,
    plan_samples,
)
from devagentops.evaluation.matrix_v2 import (
    EvaluationMatrixV2,
    ResolvedConditionV2,
    calculate_run_configuration_fingerprint,
)
from devagentops.evaluation.persistence import (
    complete_run,
    mark_run_failed,
    persist_failed_run,
    persist_finalizing_sample_run,
)
from devagentops.evaluation.progress import EvaluationProgressReporter
from devagentops.evaluation.trace import TraceRecorder
from devagentops.providers.minimax_v1 import create_minimax_provider
from devagentops.scoring.report import REPORT_SCHEMA_VERSION
from devagentops.storage.database import StorageError, initialize_database


def run_formal_evaluation_v2(
    *,
    matrix: EvaluationMatrixV2,
    suite,
    condition: ResolvedConditionV2,
    registry_path: Path,
    database_path: Path,
    artifacts_dir: Path,
) -> dict[str, Any]:
    effective = condition.effective_condition
    validate_minimax_development_condition(effective, len(suite.cases))
    if effective["suite"] != suite.suite_id:
        from devagentops.evaluation.run import EvaluationRunError

        raise EvaluationRunError(
            "Matrix v2 formal condition does not reference the loaded Suite",
            code="formal_suite_mismatch",
        )
    treatment = effective["treatment"]
    execution_policy = effective["execution_policy"]
    runtime_variant = effective["runtime_variant"]
    code_revision = _code_revision()
    git_dirty = _git_dirty()
    selected_cases = [
        {
            "case_id": item.case_id,
            "case_fingerprint": item.package.case_fingerprint,
            "weight": item.weight,
        }
        for item in suite.cases
    ]
    run_configuration_fingerprint = calculate_run_configuration_fingerprint(
        matrix,
        condition,
        suite_fingerprint=suite.suite_fingerprint,
        selected_cases=selected_cases,
        code_revision=code_revision,
        git_dirty=git_dirty,
        run_kind="formal_full_suite",
    )
    prompt = resolve_frozen_component_manifest(
        registry_path,
        "prompt",
        TASK_CONTRACT_VERSION,
    )
    if runtime_variant == "self_built_react":
        runtime_control = resolve_frozen_component_manifest(
            registry_path, "prompt", L4_RUNTIME_CONTROL_VERSION
        )
        tool_registry = resolve_frozen_component_manifest(
            registry_path, "tool_registry", L4_TOOL_REGISTRY_VERSION
        )
        tool_policy = resolve_frozen_component_manifest(
            registry_path, "tool_policy", L4_TOOL_POLICY_VERSION
        )
    initialize_database(database_path)
    run_id = str(uuid4())
    started_at = _now()
    planned_samples = plan_samples(
        run_id=run_id,
        suite_cases=suite.cases,
        repeat_count=execution_policy["repeat_count"],
    )
    manifest = _manifest(
        matrix=matrix,
        suite=suite,
        condition=condition,
        run_id=run_id,
        code_revision=code_revision,
        git_dirty=git_dirty,
        run_configuration_fingerprint=run_configuration_fingerprint,
        planned_sample_count=len(planned_samples),
    )
    progress = EvaluationProgressReporter(
        total_samples=len(planned_samples),
        max_case_concurrency=execution_policy["max_case_concurrency"],
    )
    recorder = TraceRecorder(
        run_id,
        event_listener=progress.on_event,
    )
    recorder.record("run_started", occurred_at=started_at)
    provider_factory = lambda: create_minimax_provider(
        base_url=treatment["provider"]["base_url"],
        timeout_seconds=execution_policy["request_timeout_seconds"],
    )

    if runtime_variant == "full_context_one_shot":
        executor = ConfiguredL1ConditionExecutor(
            prompt=prompt,
            treatment=ConfiguredL1Treatment(
                provider_id=treatment["provider"]["id"],
                model=treatment["model"],
                reasoning=treatment["reasoning"],
                generation=treatment["generation"],
                context_limit_tokens=treatment["context"][
                    "context_window_tokens"
                ],
                max_completion_tokens=treatment["generation"][
                    "max_completion_tokens"
                ],
                task_contract_version=TASK_CONTRACT_VERSION,
                output_contract_prompt_suffix=output_contract_prompt_suffix(),
            ),
            provider_factory=provider_factory,
        )
    elif runtime_variant == "fixed_model_workflow":
        executor = ConfiguredL2ConditionExecutor(
            prompt=prompt,
            treatment=ConfiguredL2Treatment(
                provider_id=treatment["provider"]["id"],
                model=treatment["model"],
                reasoning=treatment["reasoning"],
                generation=treatment["generation"],
                context_limit_tokens=treatment["context"][
                    "context_window_tokens"
                ],
                max_completion_tokens=treatment["generation"][
                    "max_completion_tokens"
                ],
                task_contract_version=TASK_CONTRACT_VERSION,
                final_output_contract_prompt_suffix=(
                    output_contract_prompt_suffix()
                ),
            ),
            provider_factory=provider_factory,
        )
    elif runtime_variant == "model_one_shot":
        executor = ConfiguredOracleConditionExecutor(
            prompt=prompt,
            treatment=ConfiguredOracleTreatment(
                provider_id=treatment["provider"]["id"],
                model=treatment["model"],
                reasoning=treatment["reasoning"],
                generation=treatment["generation"],
                context_limit_tokens=treatment["context"][
                    "context_window_tokens"
                ],
                max_completion_tokens=treatment["generation"][
                    "max_completion_tokens"
                ],
                task_contract_version=TASK_CONTRACT_VERSION,
                output_contract_prompt_suffix=(
                    output_contract_prompt_suffix()
                ),
                runtime_input_serialization_version=(
                    treatment["contracts"]["runtime_input"]["version"]
                ),
                evidence_delivery_contract=(
                    treatment["contracts"]["evidence_delivery"]
                ),
            ),
            provider_factory=provider_factory,
        )
    elif runtime_variant == "self_built_react":
        executor = ConfiguredL4ConditionExecutor(
            prompt=prompt,
            runtime_control=runtime_control,
            tool_registry=tool_registry,
            tool_policy=tool_policy,
            treatment=ConfiguredL4Treatment(
                provider_id=treatment["provider"]["id"],
                model=treatment["model"],
                reasoning=treatment["reasoning"],
                generation=treatment["generation"],
                context_limit_tokens=treatment["context"][
                    "context_window_tokens"
                ],
                max_completion_tokens=treatment["generation"][
                    "max_completion_tokens"
                ],
                task_contract_version=TASK_CONTRACT_VERSION,
                runtime_control_version=L4_RUNTIME_CONTROL_VERSION,
                tool_registry_version=L4_TOOL_REGISTRY_VERSION,
                tool_policy_version=L4_TOOL_POLICY_VERSION,
                output_contract_prompt_suffix=output_contract_prompt_suffix(),
            ),
            provider_factory=provider_factory,
        )
    else:
        from devagentops.evaluation.run import EvaluationRunError

        raise EvaluationRunError(
            f"unsupported Matrix v2 formal runtime variant: {runtime_variant}",
            code="unsupported_v2_runtime_variant",
        )
    try:
        results = execute_sample_plan(
            planned_samples,
            executor=executor,
            recorder=recorder,
            policy=ExecutionPolicy(
                repeat_count=execution_policy["repeat_count"],
                max_case_concurrency=execution_policy["max_case_concurrency"],
                retry_count=(
                    0
                    if runtime_variant == "self_built_react"
                    else execution_policy["retry_count"]
                ),
            ),
        )
        sample_results = [result.data for result in results]
        by_case = {
            suite_case.case_id: [
                result
                for result in sample_results
                if result["case_id"] == suite_case.case_id
            ]
            for suite_case in suite.cases
        }
        case_aggregates = tuple(
            aggregate_case(run_id, suite_case, by_case[suite_case.case_id])
            for suite_case in suite.cases
        )
        suite_aggregate = aggregate_suite(run_id, suite, case_aggregates)
        failure_type_aggregates = aggregate_failure_types(
            run_id,
            suite,
            case_aggregates,
        )
    except Exception as exc:
        _persist_run_level_failure(
            database_path,
            manifest,
            recorder,
            started_at,
            code="formal_execution_failed",
            stage="formal_execution",
        )
        from devagentops.evaluation.run import EvaluationRunError

        raise EvaluationRunError(
            "Formal Matrix v2 execution stopped because of a run-level error",
            code="formal_execution_failed",
        ) from exc

    failed_count = sum(result.status == "execution_failed" for result in results)
    final_status = (
        "completed" if failed_count == 0 else "completed_with_sample_failures"
    )
    run_completed_event = recorder.record(
        "run_completed",
        payload={
            "status": final_status,
            "case_count": len(suite.cases),
            "planned_sample_count": len(results),
            "scored_sample_count": len(results) - failed_count,
            "failed_sample_count": failed_count,
            "suite_quality_status": suite_aggregate.quality_status,
        },
    )
    trace = list(recorder.snapshot())
    try:
        persist_finalizing_sample_run(
            database_path,
            manifest=manifest,
            trace_events=trace[:-1],
            sample_results=sample_results,
            started_at=started_at,
            case_aggregates=[item.as_dict() for item in case_aggregates],
            suite_aggregate=suite_aggregate.as_dict(),
            failure_type_aggregates=[
                item.as_dict() for item in failure_type_aggregates
            ],
            sample_trajectories={
                (result.identity.case_id, result.identity.repeat_index): (
                    result.trajectory
                )
                for result in results
                if result.trajectory
            },
        )
    except StorageError as exc:
        from devagentops.evaluation.run import EvaluationRunError

        raise EvaluationRunError(str(exc), code="run_persistence_failed") from exc
    try:
        complete_run(
            database_path,
            run_completed_event=run_completed_event,
            status=final_status,
        )
    except StorageError as exc:
        from devagentops.evaluation.run import EvaluationRunError, _failure_event

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
        "artifact_schema_version": "3",
        "run_id": run_id,
        "status": final_status,
        "manifest": manifest,
        "trace": trace,
        "sample_results": sample_results,
        "case_aggregates": [item.as_dict() for item in case_aggregates],
        "suite_aggregate": suite_aggregate.as_dict(),
        "failure_type_aggregates": [
            item.as_dict() for item in failure_type_aggregates
        ],
    }
    try:
        artifact_paths = write_evaluation_artifacts(artifacts_dir, document)
    except EvaluationArtifactError as exc:
        from devagentops.evaluation.run import EvaluationRunError, _failure_event

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
        "case_count": len(suite.cases),
        "planned_sample_count": len(results),
        "suite_quality_status": suite_aggregate.quality_status,
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
    run_id: str,
    code_revision: str,
    git_dirty: bool,
    run_configuration_fingerprint: str,
    planned_sample_count: int,
) -> dict[str, Any]:
    effective = condition.effective_condition
    runtime_variant = effective["runtime_variant"]

    experiment_identity = {
        "full_context_one_shot": "l1-development-treatment-milestone",
        "fixed_model_workflow": "l2-development-treatment-integration",
        "model_one_shot": "oracle-evidence-diagnostic-development",
        "self_built_react": "l4-self-built-react-development",
    }[runtime_variant]

    tool_protocol_reason = {
        "full_context_one_shot": "full_context_one_shot_has_no_tools",
        "fixed_model_workflow": "fixed_model_workflow_has_no_tools",
        "model_one_shot": "oracle_model_one_shot_has_no_tools",
        "self_built_react": "minimax_native_tools_from_frozen_tool_registry",
    }[runtime_variant]

    return {
        "manifest_schema_version": "2",
        "run_id": run_id,
        "run_kind": "formal_full_suite",
        "experiment_identity": experiment_identity,
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
                    "failure_type": (
                        item.package.expected_answer.primary_failure_type
                    ),
                }
                for item in suite.cases
            ],
        },
        "case_selection": {
            "mode": "full_suite",
            "case_ids": [item.case_id for item in suite.cases],
        },
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
            "applicability": (
                "applicable"
                if runtime_variant == "self_built_react"
                else "not_applicable"
            ),
            "reason": tool_protocol_reason,
        },
        "formal_semantics": {
            "formal_evaluation": True,
            "full_suite": True,
            "leaderboard_eligible": False,
            "final_benchmark_freeze": False,
        },
    }


def _persist_run_level_failure(
    database_path: Path,
    manifest: dict[str, Any],
    recorder: TraceRecorder,
    started_at: str,
    *,
    code: str,
    stage: str,
) -> None:
    recorder.record("failure", payload={"code": code, "stage": stage})
    persist_failed_run(
        database_path,
        manifest=manifest,
        trace_events=list(recorder.snapshot()),
        started_at=started_at,
        failure_code=code,
        failure_message="Formal Matrix v2 run failed before finalization",
    )


def _code_revision() -> str:
    from devagentops.evaluation.run import _code_revision as historical_code_revision

    return historical_code_revision()


def _git_dirty() -> bool:
    from devagentops.evaluation.run import _git_dirty as historical_git_dirty

    return historical_git_dirty()


def _now() -> str:
    from devagentops.evaluation.run import _now as historical_now

    return historical_now()
