from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.conditions.oracle.evidence_v1 import (
    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT,
    OracleEvidenceError,
)
from devagentops.conditions.oracle.one_shot_v1 import (
    ConfiguredOracleTreatment,
    OracleOneShotError,
    run_configured_oracle_one_shot,
)
from devagentops.evaluation.components import ComponentManifest
from devagentops.evaluation.execution import (
    EventRecorder,
    PlannedSample,
    SampleResult,
)
from devagentops.evaluation.persistence import canonical_sha256
from devagentops.providers.contracts import CompletionProvider, CompletionProviderError
from devagentops.providers.execution import ProviderRequestFailed
from devagentops.scoring.case import evaluate_case_report
from devagentops.scoring.report import REPORT_SCHEMA_VERSION
from devagentops.runtime.messages import assistant_text, assistant_thinking


@dataclass(frozen=True)
class ConfiguredOracleConditionExecutor:
    prompt: ComponentManifest
    treatment: ConfiguredOracleTreatment
    provider_factory: Callable[[], CompletionProvider]

    def execute_sample(
        self,
        sample: PlannedSample,
        recorder: EventRecorder,
    ) -> SampleResult:
        identity = sample.identity
        suite_case = sample.suite_case

        recorder.record(
            "oracle_execution_started",
            identity=identity,
            payload={
                "evidence_delivery_fingerprint": (
                    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
                ),
            },
        )

        actual_call_count = 0

        def before_model_call(payload: dict[str, Any]) -> None:
            nonlocal actual_call_count
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

        try:
            provider = self.provider_factory()

            oracle_result = run_configured_oracle_one_shot(
                suite_case.package,
                self.prompt,
                provider,
                self.treatment,
                before_model_call=before_model_call,
            )

        except (
            OracleEvidenceError,
            OracleOneShotError,
            CompletionProviderError,
            ProviderRequestFailed,
        ) as exc:
            failure_code = getattr(
                exc,
                "code",
                "oracle_execution_failed",
            )

            if failure_code == "oracle_context_infeasible":
                stage = "context_feasibility"
            elif isinstance(
                exc,
                (CompletionProviderError, ProviderRequestFailed),
            ):
                stage = "model_provider"
            elif isinstance(exc, OracleEvidenceError):
                stage = "oracle_evidence_resolution"
            else:
                stage = "oracle_execution"

            payload: dict[str, Any] = {
                "code": failure_code,
                "stage": stage,
                "actual_call_count": actual_call_count,
                "retry_count": 0,
            }

            if (
                isinstance(
                    exc,
                    (CompletionProviderError, ProviderRequestFailed),
                )
                and exc.http_status
            ):
                payload["http_status"] = exc.http_status

            recorder.record(
                "failure",
                identity=identity,
                payload=payload,
            )

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
                ),
            )

        response = oracle_result.response
        visible_output = assistant_text(response)
        reasoning_metadata = _reasoning_metadata(
            assistant_thinking(response)
        )

        recorder.record(
            "model_call_completed",
            identity=identity,
            payload={
                "logical_call_number": 1,
                "attempt_index": 0,
                "provider_request_id": (
                    response.response_id
                ),
                "returned_model": response.response_model,
                "usage": response.usage.as_dict(),
                "latency_ms": oracle_result.latency_ms,
                "finish_reason": response.stop_reason,
                "visible_output": visible_output,
                "reasoning_observation": reasoning_metadata,
                "actual_call_count": actual_call_count,
                "retry_count": 0,
            },
        )

        candidate_document = oracle_result.candidate_document

        recorder.record(
            "report_submitted",
            identity=identity,
            payload={
                "report_schema_version": (
                    REPORT_SCHEMA_VERSION
                ),
                "candidate_report_sha256": (
                    canonical_sha256(
                        candidate_document
                    )
                ),
            },
        )

        score = evaluate_case_report(
            candidate_document,
            suite_case.package,
        )

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
            "visible_output": visible_output,
            "provider_observation": {
                "provider_request_id": (
                    response.response_id
                ),
                "returned_model": response.response_model,
                "usage": response.usage.as_dict(),
                "finish_reason": response.stop_reason,
                "latency_ms": oracle_result.latency_ms,
                "reasoning": reasoning_metadata,
            },
            "context_assessment": {
                "input_tokens": (
                    oracle_result.token_count.input_tokens
                ),
                "method": oracle_result.token_count.method,
                "exact": True,
                "context_window_tokens": (
                    oracle_result.context_limit_tokens
                ),
                "reserved_completion_tokens": (
                    self.treatment.max_completion_tokens
                ),
            },
            "evidence_delivery": {
                "fingerprint": (
                    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
                ),
                "runtime_input_sha256": (
                    oracle_result.runtime_input.sha256
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
        "evidence_delivery": {
            "fingerprint": (
                ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
            ),
        },
    }
