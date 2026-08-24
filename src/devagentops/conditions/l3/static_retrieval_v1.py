from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.evaluation.components import (
    ComponentManifest,
    component_fingerprint,
)
from devagentops.providers.contracts import (
    CompletionProvider,
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.providers.execution import execute_completion_request
from devagentops.retrieval.static_v1 import (
    STATIC_RETRIEVER_BEHAVIOR,
    StaticRetrievalResult,
    run_static_retrieval,
)
from devagentops.runtime.messages import AssistantMessage, UserMessage, assistant_text
from devagentops.runtime.workspace import RuntimeCaseWorkspace


RUNTIME_INPUT_SERIALIZATION_VERSION = "static_retrieval_runtime_input_v1"
RUNTIME_VARIANT = "static_retrieval"


class StaticRetrievalConditionError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class StaticRetrievalRuntimeInput:
    version: str
    text: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class ConfiguredL3Treatment:
    provider_id: str
    model: str
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    context_limit_tokens: int
    max_completion_tokens: int
    task_contract_version: str
    output_contract_prompt_suffix: str
    runtime_input_serialization_version: str
    retriever_component_version: str
    retriever_component_fingerprint: str


@dataclass(frozen=True)
class StaticRetrievalOneShotResult:
    candidate_document: Any
    retrieval: StaticRetrievalResult
    runtime_input: StaticRetrievalRuntimeInput
    prompt_text: str
    prompt_sha256: str
    token_count: ExactTokenCount
    context_limit_tokens: int
    response: AssistantMessage
    latency_ms: int


def serialize_static_retrieval_runtime_input(
    workspace: RuntimeCaseWorkspace,
    retrieval: StaticRetrievalResult,
) -> StaticRetrievalRuntimeInput:
    document = {
        "runtime_input_serialization_version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        "case": workspace.case.as_dict(),
        "evidence_delivery": {"mode": "deterministic_static_retrieval"},
        "retrieved_physical_evidence": [
            span.model_visible_dict() for span in retrieval.packed_spans
        ],
    }
    text = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    encoded = text.encode("utf-8")
    return StaticRetrievalRuntimeInput(
        version=RUNTIME_INPUT_SERIALIZATION_VERSION,
        text=text,
        sha256=hashlib.sha256(encoded).hexdigest(),
        byte_count=len(encoded),
    )


def run_configured_static_retrieval_one_shot(
    workspace: RuntimeCaseWorkspace,
    prompt: ComponentManifest,
    retriever: ComponentManifest,
    provider: CompletionProvider,
    treatment: ConfiguredL3Treatment,
    *,
    after_retrieval: Callable[[dict[str, Any]], None] | None = None,
    after_token_preflight: Callable[[dict[str, Any]], None] | None = None,
    before_model_call: Callable[[dict[str, Any]], None] | None = None,
) -> StaticRetrievalOneShotResult:
    _validate_contracts(prompt, retriever, treatment)
    retrieval = run_static_retrieval(workspace)
    runtime_input = serialize_static_retrieval_runtime_input(workspace, retrieval)
    if after_retrieval is not None:
        after_retrieval(
            {
                "retriever_component_version": treatment.retriever_component_version,
                "retriever_component_fingerprint": (
                    treatment.retriever_component_fingerprint
                ),
                **retrieval.trace_dict(),
                "runtime_input_serialization_version": runtime_input.version,
                "runtime_input_sha256": runtime_input.sha256,
                "runtime_input_byte_count": runtime_input.byte_count,
            }
        )

    try:
        prompt_text = prompt.behavior["template"].format(
            runtime_input=runtime_input.text
        )
    except (KeyError, ValueError) as exc:
        raise StaticRetrievalConditionError(
            "L3 Task Contract could not be rendered",
            code="l3_prompt_render_failed",
        ) from exc
    prompt_text += treatment.output_contract_prompt_suffix
    request = LogicalCompletionRequest(
        model=treatment.model,
        messages=(UserMessage(prompt_text),),
        reasoning=treatment.reasoning,
        generation=treatment.generation,
    )
    token_count = provider.count_input_tokens(request)
    context_feasible = not (
        token_count.input_tokens + treatment.max_completion_tokens
        > treatment.context_limit_tokens
    )
    if after_token_preflight is not None:
        after_token_preflight(
            {
                "runtime_input_sha256": runtime_input.sha256,
                "runtime_input_byte_count": runtime_input.byte_count,
                "input_tokens": token_count.input_tokens,
                "token_count_method": token_count.method,
                "reserved_completion_tokens": treatment.max_completion_tokens,
                "context_limit_tokens": treatment.context_limit_tokens,
                "context_feasible": context_feasible,
            }
        )
    if not context_feasible:
        raise StaticRetrievalConditionError(
            "L3 request exceeds the configured model context capability",
            code="l3_context_infeasible",
        )
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
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
                "retriever_component_version": treatment.retriever_component_version,
                "retriever_component_fingerprint": (
                    treatment.retriever_component_fingerprint
                ),
            }
        )
    execution = execute_completion_request(provider, request)
    response = execution.assistant
    visible_output = assistant_text(response)
    try:
        candidate_document: Any = json.loads(visible_output)
    except json.JSONDecodeError:
        candidate_document = visible_output
    return StaticRetrievalOneShotResult(
        candidate_document=candidate_document,
        retrieval=retrieval,
        runtime_input=runtime_input,
        prompt_text=prompt_text,
        prompt_sha256=prompt_sha256,
        token_count=token_count,
        context_limit_tokens=treatment.context_limit_tokens,
        response=response,
        latency_ms=execution.latency_ms,
    )


def _validate_contracts(
    prompt: ComponentManifest,
    retriever: ComponentManifest,
    treatment: ConfiguredL3Treatment,
) -> None:
    if (
        prompt.component_type != "prompt"
        or prompt.component_version != treatment.task_contract_version
    ):
        raise StaticRetrievalConditionError(
            "L3 treatment references a different Task Contract",
            code="invalid_l3_prompt_component",
        )
    if prompt.behavior.get("variables") != ["runtime_input"]:
        raise StaticRetrievalConditionError(
            "L3 Task Contract must declare only runtime_input",
            code="invalid_l3_prompt_variables",
        )
    if (
        treatment.runtime_input_serialization_version
        != RUNTIME_INPUT_SERIALIZATION_VERSION
    ):
        raise StaticRetrievalConditionError(
            "L3 treatment references a different Runtime Input contract",
            code="invalid_l3_runtime_input_contract",
        )
    if (
        retriever.component_type != "retriever_config"
        or retriever.component_version != treatment.retriever_component_version
        or retriever.behavior != STATIC_RETRIEVER_BEHAVIOR
        or component_fingerprint(retriever)
        != treatment.retriever_component_fingerprint
    ):
        raise StaticRetrievalConditionError(
            "L3 treatment references an unsupported Retriever component",
            code="invalid_l3_retriever_component",
        )
