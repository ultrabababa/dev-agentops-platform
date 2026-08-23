from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.conditions.l1.development_output_contract import (
    OUTPUT_CONTRACT_VERSION,
    evidence_reference_resolution_enabled,
)
from devagentops.conditions.l3.static_retrieval_v1 import (
    ConfiguredL3Treatment,
    StaticRetrievalConditionError,
    run_configured_static_retrieval_one_shot,
)
from devagentops.evaluation.components import ComponentManifest
from devagentops.evaluation.evidence_reference_resolution import (
    EVIDENCE_REFERENCE_RESOLUTION_VERSION,
    canonicalize_evidence_references,
)
from devagentops.evaluation.execution import EventRecorder, PlannedSample, SampleResult
from devagentops.evaluation.persistence import canonical_sha256
from devagentops.providers.contracts import CompletionProvider, CompletionProviderError
from devagentops.providers.execution import ProviderRequestFailed
from devagentops.runtime.messages import assistant_text, assistant_thinking
from devagentops.runtime.workspace import RuntimeCaseWorkspace, RuntimeWorkspaceError
from devagentops.scoring.case import evaluate_case_report
from devagentops.scoring.report import REPORT_SCHEMA_VERSION


@dataclass(frozen=True)
class ConfiguredL3ConditionExecutor:
    prompt: ComponentManifest
    retriever: ComponentManifest
    treatment: ConfiguredL3Treatment
    provider_factory: Callable[[], CompletionProvider]
    output_contract_version: str = OUTPUT_CONTRACT_VERSION

    def execute_sample(
        self,
        sample: PlannedSample,
        recorder: EventRecorder,
    ) -> SampleResult:
        identity = sample.identity
        suite_case = sample.suite_case
        recorder.record(
            "l3_execution_started",
            identity=identity,
            payload={
                "retriever_component_version": (
                    self.treatment.retriever_component_version
                ),
                "retriever_component_fingerprint": (
                    self.treatment.retriever_component_fingerprint
                ),
            },
        )
        actual_call_count = 0

        def after_retrieval(payload: dict[str, Any]) -> None:
            recorder.record(
                "static_retrieval_completed",
                identity=identity,
                payload=payload,
            )

        def before_model_call(payload: dict[str, Any]) -> None:
            nonlocal actual_call_count
            actual_call_count += 1
            recorder.record(
                "model_call_started",
                identity=identity,
                payload={**payload, "attempt_index": 0, "retry_count": 0},
            )

        def after_token_preflight(payload: dict[str, Any]) -> None:
            recorder.record(
                "l3_token_preflight_completed",
                identity=identity,
                payload=payload,
            )

        try:
            workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
            provider = self.provider_factory()
            l3_result = run_configured_static_retrieval_one_shot(
                workspace,
                self.prompt,
                self.retriever,
                provider,
                self.treatment,
                after_retrieval=after_retrieval,
                after_token_preflight=after_token_preflight,
                before_model_call=before_model_call,
            )
        except (
            StaticRetrievalConditionError,
            CompletionProviderError,
            ProviderRequestFailed,
            RuntimeWorkspaceError,
        ) as exc:
            failure_code = getattr(exc, "code", "l3_execution_failed")
            stage = (
                "context_feasibility"
                if failure_code == "l3_context_infeasible"
                else "model_provider"
                if isinstance(exc, (CompletionProviderError, ProviderRequestFailed))
                else "retrieval_workspace"
                if isinstance(exc, RuntimeWorkspaceError)
                else "l3_execution"
            )
            payload: dict[str, Any] = {
                "code": failure_code,
                "stage": stage,
                "actual_call_count": actual_call_count,
                "retry_count": 0,
            }
            if (
                isinstance(exc, (CompletionProviderError, ProviderRequestFailed))
                and exc.http_status
            ):
                payload["http_status"] = exc.http_status
            recorder.record("failure", identity=identity, payload=payload)
            return SampleResult(
                identity=identity,
                status="execution_failed",
                data=_failed_result(
                    suite_case,
                    identity.repeat_index,
                    identity.sample_sequence,
                    failure_code,
                    stage,
                    str(exc),
                    self.treatment,
                ),
            )

        response = l3_result.response
        visible_output = assistant_text(response)
        reasoning_metadata = _reasoning_metadata(assistant_thinking(response))
        recorder.record(
            "model_call_completed",
            identity=identity,
            payload={
                "logical_call_number": 1,
                "attempt_index": 0,
                "provider_request_id": response.response_id,
                "returned_model": response.response_model,
                "usage": response.usage.as_dict(),
                "latency_ms": l3_result.latency_ms,
                "finish_reason": response.stop_reason,
                "visible_output": visible_output,
                "reasoning_observation": reasoning_metadata,
                "actual_call_count": actual_call_count,
                "retry_count": 0,
            },
        )
        model_candidate_document = l3_result.candidate_document
        resolution_enabled = evidence_reference_resolution_enabled(
            self.output_contract_version
        )
        candidate_document = (
            canonicalize_evidence_references(
                model_candidate_document,
                suite_case.package.canonical_evidence_units,
            )
            if resolution_enabled
            else model_candidate_document
        )
        recorder.record(
            "report_submitted",
            identity=identity,
            payload={
                "report_schema_version": REPORT_SCHEMA_VERSION,
                "candidate_report_sha256": canonical_sha256(candidate_document),
            },
        )
        score = evaluate_case_report(candidate_document, suite_case.package)
        result = {
            "case_id": suite_case.case_id,
            "repeat_index": identity.repeat_index,
            "sample_sequence": identity.sample_sequence,
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
            "provider_observation": {
                "provider_request_id": response.response_id,
                "returned_model": response.response_model,
                "usage": response.usage.as_dict(),
                "finish_reason": response.stop_reason,
                "latency_ms": l3_result.latency_ms,
                "reasoning": reasoning_metadata,
            },
            "context_assessment": {
                "input_tokens": l3_result.token_count.input_tokens,
                "method": l3_result.token_count.method,
                "exact": True,
                "context_window_tokens": l3_result.context_limit_tokens,
                "reserved_completion_tokens": self.treatment.max_completion_tokens,
            },
            "retrieval_observation": {
                "retriever_component_version": (
                    self.treatment.retriever_component_version
                ),
                "retriever_component_fingerprint": (
                    self.treatment.retriever_component_fingerprint
                ),
                "log_query_count": len(l3_result.retrieval.log_queries),
                "repository_query_count": len(
                    l3_result.retrieval.repository_queries
                ),
                "selected_log_chunk_count": len(
                    l3_result.retrieval.selected_log_hits
                ),
                "selected_repository_chunk_count": len(
                    l3_result.retrieval.selected_repository_hits
                ),
                "packed_span_count": len(l3_result.retrieval.packed_spans),
                "runtime_input_sha256": l3_result.runtime_input.sha256,
                "runtime_input_byte_count": l3_result.runtime_input.byte_count,
            },
        }
        if resolution_enabled:
            result["model_candidate_document"] = model_candidate_document
            result["evidence_reference_resolution"] = {
                "version": EVIDENCE_REFERENCE_RESOLUTION_VERSION,
                "changed": candidate_document != model_candidate_document,
            }
        recorder.record(
            "evaluation_completed",
            identity=identity,
            payload={"quality_metrics": result["quality_metrics"]},
        )
        return SampleResult(identity=identity, status="scored", data=result)


def _reasoning_metadata(reasoning_output: str | None) -> dict[str, Any]:
    if reasoning_output is None:
        return {"present": False, "character_count": 0, "sha256": None}
    return {
        "present": True,
        "character_count": len(reasoning_output),
        "sha256": hashlib.sha256(reasoning_output.encode("utf-8")).hexdigest(),
    }


def _failed_result(
    suite_case,
    repeat_index: int,
    sample_sequence: int,
    code: str,
    stage: str,
    message: str,
    treatment: ConfiguredL3Treatment,
) -> dict[str, Any]:
    return {
        "case_id": suite_case.case_id,
        "repeat_index": repeat_index,
        "sample_sequence": sample_sequence,
        "case_fingerprint": suite_case.package.case_fingerprint,
        "weight": suite_case.weight,
        "evaluation_failure_type": (
            suite_case.package.expected_answer.primary_failure_type
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
        "retrieval_observation": {
            "retriever_component_version": treatment.retriever_component_version,
            "retriever_component_fingerprint": (
                treatment.retriever_component_fingerprint
            ),
        },
    }
