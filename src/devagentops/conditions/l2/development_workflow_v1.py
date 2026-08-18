from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.conditions.l1.full_context_v1 import (
    RuntimeInputSerialization,
    serialize_complete_runtime_input,
)
from devagentops.conditions.l2.fixed_workflow_v1 import (
    EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA,
    HANDOFF_SERIALIZER_FINGERPRINT,
    HandoffSerialization,
    serialize_handoff,
)
from devagentops.evaluation.components import ComponentManifest
from devagentops.providers.contracts import (
    CompletionProvider,
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.runtime.messages import (
    AssistantMessage,
    UserMessage,
    assistant_text,
    assistant_thinking,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


RUNTIME_VARIANT = "fixed_model_workflow"
WORKFLOW_VERSION = "fixed-model-workflow-minimax-development-v1"

EVIDENCE_ANALYSIS_STAGE = "evidence_analysis"
REPORT_SYNTHESIS_STAGE = "report_synthesis"

EVIDENCE_ANALYSIS_CONTROL_VERSION = (
    "l2-minimax-evidence-analysis-control-development-v1"
)
REPORT_SYNTHESIS_CONTROL_VERSION = (
    "l2-minimax-report-synthesis-control-development-v1"
)
EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_VERSION = (
    "evidence-analysis-memo-prompt-development-v1"
)


EVIDENCE_ANALYSIS_CONTROL = (
    "This is the evidence_analysis intermediate stage of a fixed two-stage "
    "Runtime execution.\n"
    "Analyze the supplied Case and complete Evidence Universe before the final "
    "diagnostic report is produced.\n"
    "Identify the strongest grounded findings, a working failure type, the "
    "most defensible causal hypothesis, and material uncertainties.\n"
    "Cite only Evidence IDs available in the supplied Runtime input. Never "
    "invent an Evidence ID.\n"
    "The shared Task Contract describes the final Runtime deliverable, but "
    "this stage is explicitly intermediate. Do not produce the final "
    "Structured Triage Report V1 here.\n"
    "Do not request tools, Retrieval, another evidence source, a retry, or an "
    "additional stage. The Runtime controls the next transition."
)

REPORT_SYNTHESIS_CONTROL = (
    "This is the report_synthesis final stage of a fixed two-stage Runtime "
    "execution.\n"
    "Use the supplied complete Evidence Universe together with the explicitly "
    "identified evidence_analysis intermediate artifact to produce the final "
    "diagnostic result required by the shared Task Contract.\n"
    "Treat the intermediate artifact as model-generated working analysis, not "
    "as evaluator Ground Truth. Resolve any conflict against the supplied "
    "Evidence Universe.\n"
    "Cite only Evidence IDs available in the supplied Runtime input. Never "
    "invent an Evidence ID.\n"
    "This is the final stage. Produce the Structured Triage Report V1 required "
    "by the shared Task Contract.\n"
    "Do not request tools, Retrieval, a verifier, a repair call, a retry, or "
    "an additional stage. The Runtime stops after this stage."
)


EVIDENCE_ANALYSIS_MEMO_SCHEMA: dict[str, Any] = (
    EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA["json_schema"]["schema"]
)


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


EVIDENCE_ANALYSIS_MEMO_SCHEMA_SHA256 = _canonical_sha256(
    EVIDENCE_ANALYSIS_MEMO_SCHEMA
)


def evidence_analysis_output_contract_prompt_suffix() -> str:
    schema = json.dumps(
        EVIDENCE_ANALYSIS_MEMO_SCHEMA,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (
        "\n\n"
        "EVIDENCE ANALYSIS OUTPUT CONTRACT\n\n"
        "Your entire response for this intermediate stage MUST be exactly one "
        "valid JSON object.\n"
        "Do NOT output Markdown.\n"
        "Do NOT output code fences.\n"
        "Do NOT output explanations before or after the JSON.\n"
        "Do NOT produce the final Structured Triage Report V1 in this stage.\n"
        "Do NOT omit required fields or add fields outside this schema.\n\n"
        "You MUST satisfy this JSON Schema exactly:\n\n"
        f"{schema}\n"
    )


EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_PROMPT = (
    evidence_analysis_output_contract_prompt_suffix()
)
EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_SHA256 = hashlib.sha256(
    EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_PROMPT.encode("utf-8")
).hexdigest()

EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT = hashlib.sha256(
    EVIDENCE_ANALYSIS_CONTROL.encode("utf-8")
).hexdigest()

REPORT_SYNTHESIS_CONTROL_FINGERPRINT = hashlib.sha256(
    REPORT_SYNTHESIS_CONTROL.encode("utf-8")
).hexdigest()


WORKFLOW_IDENTITY = {
    "version": WORKFLOW_VERSION,
    "ordered_stages": [
        EVIDENCE_ANALYSIS_STAGE,
        REPORT_SYNTHESIS_STAGE,
    ],
    "transition": "evidence_analysis -> report_synthesis -> stop",
    "expected_model_calls_per_sample": 2,
    "conversation_history": "none",
    "stage_request_shape": {
        "messages_per_stage": 1,
        "role": "user",
    },
    "stage_1": {
        "control_version": EVIDENCE_ANALYSIS_CONTROL_VERSION,
        "control_fingerprint": EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT,
        "output_contract_version": (
            EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_VERSION
        ),
        "output_contract_sha256": (
            EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_SHA256
        ),
        "memo_schema_sha256": EVIDENCE_ANALYSIS_MEMO_SCHEMA_SHA256,
        "protocol_enforcement": "prompt_only",
    },
    "handoff": {
        "serializer_fingerprint": HANDOFF_SERIALIZER_FINGERPRINT,
        "source": "exact_stage_1_visible_output",
    },
    "stage_2": {
        "control_version": REPORT_SYNTHESIS_CONTROL_VERSION,
        "control_fingerprint": REPORT_SYNTHESIS_CONTROL_FINGERPRINT,
        "final_output_contract": "inherited_from_treatment",
    },
}

WORKFLOW_FINGERPRINT = _canonical_sha256(WORKFLOW_IDENTITY)


class ConfiguredFixedModelWorkflowError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        stage_id: str,
        context_metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage_id = stage_id
        self.context_metadata = context_metadata or {}


@dataclass(frozen=True)
class ConfiguredL2Treatment:
    provider_id: str
    model: str
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    context_limit_tokens: int
    max_completion_tokens: int
    task_contract_version: str
    final_output_contract_prompt_suffix: str


@dataclass(frozen=True)
class ConfiguredStageCallResult:
    stage_id: str
    logical_call_number: int
    runtime_input_text: str
    runtime_input_sha256: str
    runtime_input_byte_count: int
    prompt_text: str
    prompt_sha256: str
    control_version: str
    control_fingerprint: str
    token_count: ExactTokenCount
    response: AssistantMessage


@dataclass(frozen=True)
class ConfiguredFixedModelWorkflowResult:
    candidate_document: Any
    visible_output: str
    complete_runtime_input: RuntimeInputSerialization
    handoff: HandoffSerialization
    evidence_analysis_observation: dict[str, Any]
    stage_calls: tuple[
        ConfiguredStageCallResult,
        ConfiguredStageCallResult,
    ]


def run_configured_fixed_model_workflow(
    workspace: RuntimeCaseWorkspace,
    prompt: ComponentManifest,
    provider: CompletionProvider,
    treatment: ConfiguredL2Treatment,
    *,
    before_model_call: Callable[[dict[str, Any]], None] | None = None,
    after_model_call: Callable[[dict[str, Any]], None] | None = None,
) -> ConfiguredFixedModelWorkflowResult:
    _validate_task_contract(prompt, treatment)

    complete_runtime_input = serialize_complete_runtime_input(workspace)

    stage_1_prompt = _render_stage_prompt(
        prompt,
        complete_runtime_input.text,
        EVIDENCE_ANALYSIS_CONTROL,
        EVIDENCE_ANALYSIS_OUTPUT_CONTRACT_PROMPT,
    )

    stage_1 = _execute_stage(
        provider=provider,
        treatment=treatment,
        stage_id=EVIDENCE_ANALYSIS_STAGE,
        logical_call_number=1,
        runtime_input_text=complete_runtime_input.text,
        prompt_text=stage_1_prompt,
        control_version=EVIDENCE_ANALYSIS_CONTROL_VERSION,
        control_fingerprint=EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT,
        before_model_call=before_model_call,
    )

    stage_1_visible_output = assistant_text(stage_1.response)
    observation = observe_evidence_analysis_memo(stage_1_visible_output, workspace)

    handoff = serialize_handoff(stage_1_visible_output)

    _notify_model_call_completed(
        after_model_call,
        stage_1,
        extra={
            "evidence_analysis_observation": observation,
            "handoff_sha256": handoff.sha256,
            "visible_output_sha256": handoff.visible_output_sha256,
        },
    )

    stage_2_runtime_input = _stage_2_runtime_input(
        complete_runtime_input.text,
        handoff.text,
    )

    stage_2_prompt = _render_stage_prompt(
        prompt,
        stage_2_runtime_input,
        REPORT_SYNTHESIS_CONTROL,
        treatment.final_output_contract_prompt_suffix,
    )

    stage_2 = _execute_stage(
        provider=provider,
        treatment=treatment,
        stage_id=REPORT_SYNTHESIS_STAGE,
        logical_call_number=2,
        runtime_input_text=stage_2_runtime_input,
        prompt_text=stage_2_prompt,
        control_version=REPORT_SYNTHESIS_CONTROL_VERSION,
        control_fingerprint=REPORT_SYNTHESIS_CONTROL_FINGERPRINT,
        before_model_call=before_model_call,
    )

    _notify_model_call_completed(
        after_model_call,
        stage_2,
    )

    stage_2_visible_output = assistant_text(stage_2.response)
    try:
        candidate_document: Any = json.loads(stage_2_visible_output)
    except json.JSONDecodeError:
        candidate_document = stage_2_visible_output

    return ConfiguredFixedModelWorkflowResult(
        candidate_document=candidate_document,
        visible_output=stage_2_visible_output,
        complete_runtime_input=complete_runtime_input,
        handoff=handoff,
        evidence_analysis_observation=observation,
        stage_calls=(stage_1, stage_2),
    )


def _validate_task_contract(
    prompt: ComponentManifest,
    treatment: ConfiguredL2Treatment,
) -> None:
    if (
        prompt.component_type != "prompt"
        or prompt.component_version != treatment.task_contract_version
    ):
        raise ConfiguredFixedModelWorkflowError(
            "configured L2 treatment references a different Task Contract",
            code="invalid_l2_prompt_component",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        )

    if prompt.behavior.get("variables") != ["runtime_input"]:
        raise ConfiguredFixedModelWorkflowError(
            "L2 Task Contract must declare only runtime_input",
            code="invalid_l2_prompt_variables",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        )


def _render_stage_prompt(
    prompt: ComponentManifest,
    runtime_input: str,
    control: str,
    output_contract_suffix: str,
) -> str:
    try:
        rendered_task_contract = prompt.behavior["template"].format(
            runtime_input=runtime_input
        )
    except (KeyError, ValueError) as exc:
        raise ConfiguredFixedModelWorkflowError(
            "L2 Task Contract could not be rendered",
            code="l2_prompt_render_failed",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        ) from exc

    separator = (
        "\n"
        if rendered_task_contract.endswith("\n")
        else "\n\n"
    )

    return (
        rendered_task_contract
        + separator
        + "Runtime execution control:\n\n"
        + control
        + output_contract_suffix
    )


def _stage_2_runtime_input(
    complete_runtime_input: str,
    handoff_text: str,
) -> str:
    separator = (
        "\n"
        if complete_runtime_input.endswith("\n")
        else "\n\n"
    )

    return (
        complete_runtime_input
        + separator
        + "Case-scoped intermediate artifact:\n"
        + handoff_text
    )


def _execute_stage(
    *,
    provider: CompletionProvider,
    treatment: ConfiguredL2Treatment,
    stage_id: str,
    logical_call_number: int,
    runtime_input_text: str,
    prompt_text: str,
    control_version: str,
    control_fingerprint: str,
    before_model_call: Callable[[dict[str, Any]], None] | None,
) -> ConfiguredStageCallResult:
    request = LogicalCompletionRequest(
        model=treatment.model,
        messages=(UserMessage(prompt_text),),
        reasoning=treatment.reasoning,
        generation=treatment.generation,
    )

    token_count = provider.count_input_tokens(request)

    context_metadata = {
        "input_tokens": token_count.input_tokens,
        "token_count_method": token_count.method,
        "max_output_tokens": treatment.max_completion_tokens,
        "context_limit_tokens": treatment.context_limit_tokens,
    }

    if (
        token_count.input_tokens + treatment.max_completion_tokens
        > treatment.context_limit_tokens
    ):
        raise ConfiguredFixedModelWorkflowError(
            f"complete L2 {stage_id} request exceeds the configured "
            "model context capability",
            code="l2_context_infeasible",
            stage_id=stage_id,
            context_metadata=context_metadata,
        )

    prompt_sha256 = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()

    runtime_input_encoded = runtime_input_text.encode("utf-8")
    runtime_input_sha256 = hashlib.sha256(
        runtime_input_encoded
    ).hexdigest()

    if before_model_call is not None:
        before_model_call(
            {
                "provider": treatment.provider_id,
                "model": treatment.model,
                "stage_id": stage_id,
                "logical_call_number": logical_call_number,
                "prompt_sha256": prompt_sha256,
                "runtime_input_sha256": runtime_input_sha256,
                "runtime_input_byte_count": len(runtime_input_encoded),
                "control_version": control_version,
                "control_fingerprint": control_fingerprint,
                **context_metadata,
            }
        )

    response = provider.complete(request)

    return ConfiguredStageCallResult(
        stage_id=stage_id,
        logical_call_number=logical_call_number,
        runtime_input_text=runtime_input_text,
        runtime_input_sha256=runtime_input_sha256,
        runtime_input_byte_count=len(runtime_input_encoded),
        prompt_text=prompt_text,
        prompt_sha256=prompt_sha256,
        control_version=control_version,
        control_fingerprint=control_fingerprint,
        token_count=token_count,
        response=response,
    )


def _notify_model_call_completed(
    callback: Callable[[dict[str, Any]], None] | None,
    stage: ConfiguredStageCallResult,
    extra: dict[str, Any] | None = None,
) -> None:
    if callback is None:
        return

    callback(
        {
            "stage_id": stage.stage_id,
            "logical_call_number": stage.logical_call_number,
            "provider_request_id": stage.response.response_id,
            "returned_model": stage.response.response_model,
            "usage": stage.response.usage.as_dict(),
            "latency_ms": stage.response.latency_ms,
            "finish_reason": stage.response.stop_reason,
            "visible_output": assistant_text(stage.response),
            "reasoning_observation": _reasoning_metadata(
                assistant_thinking(stage.response)
            ),
            **(extra or {}),
        }
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


def observe_evidence_analysis_memo(
    visible_output: str,
    workspace: RuntimeCaseWorkspace,
) -> dict[str, Any]:
    try:
        document = json.loads(visible_output)
    except json.JSONDecodeError:
        return {
            "json_valid": False,
            "schema_valid": False,
            "case_id_matches": None,
            "evidence_ids_known": None,
        }

    schema_valid = _memo_matches_schema(document)

    case_id_matches = (
        document.get("case_id") == workspace.case.case_id
        if isinstance(document, dict)
        else False
    )

    known_evidence_ids = {
        coordinate.evidence_id
        for coordinate in workspace.canonical_coordinates
    }

    findings = (
        document.get("evidence_findings")
        if isinstance(document, dict)
        else None
    )

    evidence_ids_known = False

    if isinstance(findings, list):
        evidence_ids_known = all(
            isinstance(finding, dict)
            and isinstance(finding.get("evidence_id"), str)
            and finding["evidence_id"] in known_evidence_ids
            for finding in findings
        )

    return {
        "json_valid": True,
        "schema_valid": schema_valid,
        "case_id_matches": case_id_matches,
        "evidence_ids_known": evidence_ids_known,
    }


def _memo_matches_schema(document: Any) -> bool:
    if not isinstance(document, dict) or set(document) != {
        "schema_version",
        "case_id",
        "evidence_findings",
        "working_failure_type",
        "causal_hypothesis",
        "uncertainties",
    }:
        return False

    if document["schema_version"] != "1":
        return False

    if (
        not isinstance(document["case_id"], str)
        or not document["case_id"]
    ):
        return False

    findings = document["evidence_findings"]

    if not isinstance(findings, list) or not findings:
        return False

    if any(
        not isinstance(finding, dict)
        or set(finding) != {"evidence_id", "finding"}
        or not isinstance(finding["evidence_id"], str)
        or not finding["evidence_id"]
        or not isinstance(finding["finding"], str)
        or not finding["finding"]
        for finding in findings
    ):
        return False

    working_failure_type = document["working_failure_type"]

    if working_failure_type is not None and (
        not isinstance(working_failure_type, str)
        or working_failure_type
        not in {
            "test_assertion_failure",
            "lint_or_type_failure",
            "dependency_or_install_failure",
            "config_or_environment_failure",
            "timeout_or_flaky_failure",
        }
    ):
        return False

    if (
        not isinstance(document["causal_hypothesis"], str)
        or not document["causal_hypothesis"]
    ):
        return False

    uncertainties = document["uncertainties"]

    return isinstance(uncertainties, list) and all(
        isinstance(uncertainty, str) and bool(uncertainty)
        for uncertainty in uncertainties
    )
