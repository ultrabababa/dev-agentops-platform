from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.conditions.l2.development_workflow_v1 import (
    WORKFLOW_FINGERPRINT,
    ConfiguredFixedModelWorkflowError,
    ConfiguredL2Treatment,
    run_configured_fixed_model_workflow,
)
from devagentops.evaluation.components import ComponentManifest
from devagentops.evaluation.execution import (
    EventRecorder,
    PlannedSample,
    SampleResult,
)
from devagentops.evaluation.persistence import canonical_sha256
from devagentops.providers.contracts import CompletionProvider
from devagentops.providers.openai_compatible import (
    OpenAICompatibleTransportError,
)
from devagentops.runtime.workspace import (
    RuntimeCaseWorkspace,
    RuntimeWorkspaceError,
)
from devagentops.scoring.case import evaluate_case_report
from devagentops.scoring.report import REPORT_SCHEMA_VERSION
from devagentops.runtime.messages import assistant_thinking


@dataclass(frozen=True)
class ConfiguredL2ConditionExecutor:
    prompt: ComponentManifest
    treatment: ConfiguredL2Treatment
    provider_factory: Callable[[], CompletionProvider]

    def execute_sample(
        self,
        sample: PlannedSample,
        recorder: EventRecorder,
    ) -> SampleResult:
        identity = sample.identity
        suite_case = sample.suite_case

        recorder.record(
            "l2_execution_started",
            identity=identity,
        )

        actual_call_count = 0
        current_stage: str | None = None

        def before_model_call(payload: dict[str, Any]) -> None:
            nonlocal actual_call_count, current_stage

            stage_id = payload.get("stage_id")
            if isinstance(stage_id, str):
                current_stage = stage_id

            actual_call_count += 1

            recorder.record(
                "model_call_started",
                identity=identity,
                payload={
                    **payload,
                    "attempt_index": 0,
                    "retry_count": 0,
                },
            )

        def after_model_call(payload: dict[str, Any]) -> None:
            recorder.record(
                "model_call_completed",
                identity=identity,
                payload={
                    **payload,
                    "actual_call_count": actual_call_count,
                    "attempt_index": 0,
                    "retry_count": 0,
                },
            )

        try:
            workspace = RuntimeCaseWorkspace.from_package(
                suite_case.package
            )
            provider = self.provider_factory()

            l2_result = run_configured_fixed_model_workflow(
                workspace,
                self.prompt,
                provider,
                self.treatment,
                before_model_call=before_model_call,
                after_model_call=after_model_call,
            )

        except (
            ConfiguredFixedModelWorkflowError,
            OpenAICompatibleTransportError,
            RuntimeWorkspaceError,
        ) as exc:
            failure_code = getattr(
                exc,
                "code",
                "l2_execution_failed",
            )

            if isinstance(
                exc,
                ConfiguredFixedModelWorkflowError,
            ):
                failure_stage = exc.stage_id
                failure_kind = (
                    "context_feasibility"
                    if failure_code == "l2_context_infeasible"
                    else "l2_execution"
                )
                context_metadata = exc.context_metadata

            elif isinstance(
                exc,
                OpenAICompatibleTransportError,
            ):
                failure_stage = (
                    current_stage
                    if current_stage is not None
                    else "l2_execution"
                )
                failure_kind = "model_provider"
                context_metadata = {}

            else:
                failure_stage = "workspace"
                failure_kind = "runtime_workspace"
                context_metadata = {}

            failure_payload: dict[str, Any] = {
                "code": failure_code,
                "stage": failure_stage,
                "failure_kind": failure_kind,
                "actual_call_count": actual_call_count,
                "retry_count": 0,
            }

            if context_metadata:
                failure_payload["context_metadata"] = (
                    context_metadata
                )

            if (
                isinstance(
                    exc,
                    OpenAICompatibleTransportError,
                )
                and exc.http_status
            ):
                failure_payload["http_status"] = (
                    exc.http_status
                )

            recorder.record(
                "failure",
                identity=identity,
                payload=failure_payload,
            )

            return SampleResult(
                identity=identity,
                status="execution_failed",
                data=_failed_result(
                    suite_case,
                    repeat_index=identity.repeat_index,
                    sample_sequence=identity.sample_sequence,
                    code=failure_code,
                    stage=failure_stage,
                    message=str(exc),
                ),
            )

        candidate_document = l2_result.candidate_document

        recorder.record(
            "report_submitted",
            identity=identity,
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

        stage_observations = [
            {
                "stage_id": stage.stage_id,
                "logical_call_number": (
                    stage.logical_call_number
                ),
                "provider_request_id": (
                    stage.response.response_id
                ),
                "returned_model": (
                    stage.response.response_model
                ),
                "usage": stage.response.usage.as_dict(),
                "finish_reason": (
                    stage.response.stop_reason
                ),
                "latency_ms": stage.response.latency_ms,
                "reasoning": _reasoning_metadata(
                    assistant_thinking(stage.response)
                ),
            }
            for stage in l2_result.stage_calls
        ]

        stage_context_assessments = [
            {
                "stage_id": stage.stage_id,
                "logical_call_number": (
                    stage.logical_call_number
                ),
                "input_tokens": (
                    stage.token_count.input_tokens
                ),
                "method": stage.token_count.method,
                "exact": True,
                "context_window_tokens": (
                    self.treatment.context_limit_tokens
                ),
                "reserved_completion_tokens": (
                    self.treatment.max_completion_tokens
                ),
            }
            for stage in l2_result.stage_calls
        ]

        final_stage = l2_result.stage_calls[-1]

        result = {
            "case_id": suite_case.case_id,
            "repeat_index": identity.repeat_index,
            "sample_sequence": identity.sample_sequence,
            "case_fingerprint": (
                suite_case.package.case_fingerprint
            ),
            "weight": suite_case.weight,
            "evaluation_failure_type": (
                suite_case.package.expected_answer
                .primary_failure_type
            ),
            "outcome": {
                "status": "scored",
            },
            "report": (
                score.structured_report.as_dict()
                if score.structured_report is not None
                else None
            ),
            "validation": score.validation.as_dict(),
            "quality_metrics": (
                score.quality_metrics.as_dict()
            ),
            "evidence_diagnostics": (
                score.evidence_diagnostics.as_dict()
            ),
            "candidate_document": candidate_document,
            "visible_output": l2_result.visible_output,

            # Preserve the generic final-provider observation
            # shape used by the existing evaluation surface.
            "provider_observation": {
                "provider_request_id": (
                    final_stage.response.response_id
                ),
                "returned_model": (
                    final_stage.response.response_model
                ),
                "usage": final_stage.response.usage.as_dict(),
                "finish_reason": (
                    final_stage.response.stop_reason
                ),
                "latency_ms": (
                    final_stage.response.latency_ms
                ),
                "reasoning": _reasoning_metadata(
                    assistant_thinking(final_stage.response)
                ),
            },

            # Preserve the generic final-context assessment
            # shape while exposing explicit L2 stage diagnostics.
            "context_assessment": {
                "input_tokens": (
                    final_stage.token_count.input_tokens
                ),
                "method": final_stage.token_count.method,
                "exact": True,
                "context_window_tokens": (
                    self.treatment.context_limit_tokens
                ),
                "reserved_completion_tokens": (
                    self.treatment.max_completion_tokens
                ),
            },
            "l2_workflow": {
                "workflow_fingerprint": (
                    WORKFLOW_FINGERPRINT
                ),
                "expected_model_calls": 2,
                "actual_call_count": actual_call_count,
                "handoff_sha256": (
                    l2_result.handoff.sha256
                ),
                "stage_1_visible_output_sha256": (
                    l2_result.handoff
                    .visible_output_sha256
                ),
                "evidence_analysis_observation": (
                    l2_result
                    .evidence_analysis_observation
                ),
                "stage_observations": (
                    stage_observations
                ),
                "stage_context_assessments": (
                    stage_context_assessments
                ),
            },
        }

        recorder.record(
            "evaluation_completed",
            identity=identity,
            payload={
                "quality_metrics": (
                    result["quality_metrics"]
                ),
            },
        )

        return SampleResult(
            identity=identity,
            status="scored",
            data=result,
        )


def _reasoning_metadata(
    reasoning_output: str | None,
) -> dict[str, Any]:
    if reasoning_output is None:
        return {
            "present": False,
            "character_count": 0,
            "sha256": None,
        }

    return {
        "present": True,
        "character_count": len(reasoning_output),
        "sha256": hashlib.sha256(
            reasoning_output.encode("utf-8")
        ).hexdigest(),
    }


def _failed_result(
    suite_case,
    *,
    repeat_index: int,
    sample_sequence: int,
    code: str,
    stage: str,
    message: str,
) -> dict[str, Any]:
    return {
        "case_id": suite_case.case_id,
        "repeat_index": repeat_index,
        "sample_sequence": sample_sequence,
        "case_fingerprint": (
            suite_case.package.case_fingerprint
        ),
        "weight": suite_case.weight,
        "evaluation_failure_type": (
            suite_case.package.expected_answer
            .primary_failure_type
        ),
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
        "provider_observation": None,
        "context_assessment": None,
        "l2_workflow": None,
    }
