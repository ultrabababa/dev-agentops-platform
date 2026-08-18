from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.conditions.oracle.evidence_v1 import (
    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT,
    ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION,
    OracleRuntimeInputSerialization,
    oracle_evidence_delivery_contract,
    resolve_oracle_evidence_pack,
    serialize_oracle_evidence_pack,
)
from devagentops.evaluation.components import ComponentManifest
from devagentops.evaluation.suite import OfflineCasePackage
from devagentops.providers.contracts import (
    CompletionProvider,
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.providers.execution import execute_completion_request
from devagentops.runtime.messages import AssistantMessage, UserMessage, assistant_text


RUNTIME_VARIANT = "model_one_shot"


class OracleOneShotError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ConfiguredOracleTreatment:
    provider_id: str
    model: str
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    context_limit_tokens: int
    max_completion_tokens: int
    task_contract_version: str
    output_contract_prompt_suffix: str
    runtime_input_serialization_version: str
    evidence_delivery_contract: dict[str, str]


@dataclass(frozen=True)
class OracleOneShotResult:
    candidate_document: Any
    runtime_input: OracleRuntimeInputSerialization
    prompt_text: str
    prompt_sha256: str
    token_count: ExactTokenCount
    context_limit_tokens: int
    response: AssistantMessage
    latency_ms: int


def run_configured_oracle_one_shot(
    package: OfflineCasePackage,
    prompt: ComponentManifest,
    provider: CompletionProvider,
    treatment: ConfiguredOracleTreatment,
    *,
    before_model_call: Callable[[dict[str, Any]], None] | None = None,
) -> OracleOneShotResult:
    if (
        prompt.component_type != "prompt"
        or prompt.component_version != treatment.task_contract_version
    ):
        raise OracleOneShotError(
            "Oracle treatment references a different Task Contract",
            code="invalid_oracle_prompt_component",
        )

    if prompt.behavior.get("variables") != ["runtime_input"]:
        raise OracleOneShotError(
            "Oracle Task Contract must declare only runtime_input",
            code="invalid_oracle_prompt_variables",
        )

    if (
        treatment.runtime_input_serialization_version
        != ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION
    ):
        raise OracleOneShotError(
            "Oracle treatment references a different Runtime Input contract",
            code="invalid_oracle_runtime_input_contract",
        )

    if treatment.evidence_delivery_contract != oracle_evidence_delivery_contract():
        raise OracleOneShotError(
            "Oracle treatment references a different Evidence Delivery contract",
            code="invalid_oracle_evidence_delivery_contract",
        )

    pack = resolve_oracle_evidence_pack(package)
    runtime_input = serialize_oracle_evidence_pack(pack)

    try:
        prompt_text = prompt.behavior["template"].format(
            runtime_input=runtime_input.text
        )
    except (KeyError, ValueError) as exc:
        raise OracleOneShotError(
            "Oracle Task Contract could not be rendered",
            code="oracle_prompt_render_failed",
        ) from exc

    prompt_text += treatment.output_contract_prompt_suffix

    request = LogicalCompletionRequest(
        model=treatment.model,
        messages=(UserMessage(prompt_text),),
        reasoning=treatment.reasoning,
        generation=treatment.generation,
    )

    token_count = provider.count_input_tokens(request)

    if (
        token_count.input_tokens + treatment.max_completion_tokens
        > treatment.context_limit_tokens
    ):
        raise OracleOneShotError(
            "Oracle request exceeds the configured model context capability",
            code="oracle_context_infeasible",
        )

    prompt_sha256 = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()

    if before_model_call is not None:
        before_model_call(
            {
                "provider": treatment.provider_id,
                "model": treatment.model,
                "prompt_sha256": prompt_sha256,
                "runtime_input_sha256": runtime_input.sha256,
                "runtime_input_byte_count": runtime_input.byte_count,
                "input_tokens": token_count.input_tokens,
                "token_count_method": token_count.method,
                "max_output_tokens": treatment.max_completion_tokens,
                "logical_call_number": 1,
                "evidence_delivery_fingerprint": (
                    ORACLE_EVIDENCE_DELIVERY_FINGERPRINT
                ),
                "evidence_item_count": len(pack.items),
            }
        )

    execution = execute_completion_request(provider, request)
    response = execution.assistant
    visible_output = assistant_text(response)

    try:
        candidate_document: Any = json.loads(
            visible_output
        )
    except json.JSONDecodeError:
        candidate_document = visible_output

    return OracleOneShotResult(
        candidate_document=candidate_document,
        runtime_input=runtime_input,
        prompt_text=prompt_text,
        prompt_sha256=prompt_sha256,
        token_count=token_count,
        context_limit_tokens=treatment.context_limit_tokens,
        response=response,
        latency_ms=execution.latency_ms,
    )
