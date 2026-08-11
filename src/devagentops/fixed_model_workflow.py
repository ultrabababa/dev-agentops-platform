from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.component_registry import ComponentManifest
from devagentops.full_context_one_shot import (
    CONTEXT_LIMIT_TOKENS,
    MAX_OUTPUT_TOKENS,
    MODEL,
    RUNTIME_INPUT_SERIALIZATION_VERSION,
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
    RuntimeInputSerialization,
    serialize_complete_runtime_input,
)
from devagentops.model_provider import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    TokenCount,
)
from devagentops.runtime_workspace import RuntimeCaseWorkspace


RUNTIME_VARIANT = "fixed_model_workflow"
WORKFLOW_VERSION = "fixed-model-workflow-v1"
EVIDENCE_ANALYSIS_STAGE = "evidence_analysis"
REPORT_SYNTHESIS_STAGE = "report_synthesis"
EVIDENCE_ANALYSIS_CONTROL_VERSION = "l2-evidence-analysis-control-v1"
REPORT_SYNTHESIS_CONTROL_VERSION = "l2-report-synthesis-control-v1"
EVIDENCE_ANALYSIS_MEMO_VERSION = "evidence-analysis-memo-v1"
HANDOFF_VERSION = "fixed-model-workflow-handoff-v1"

EVIDENCE_ANALYSIS_CONTROL = (
    "This is the evidence_analysis intermediate stage of a fixed two-stage "
    "Runtime execution.\n"
    "Analyze the supplied Case and complete Evidence Universe. Extract the "
    "strongest grounded findings, a working failure type, a causal hypothesis, "
    "and material uncertainties.\n"
    "Cite only Evidence IDs available in the supplied Runtime input. Do not "
    "invent Evidence IDs.\n"
    "Return exactly one evidence-analysis-memo-v1 object through the configured "
    "structured-output protocol, with no Markdown or explanatory text outside "
    "that object.\n"
    "This is not the final diagnostic report. Do not produce a Structured "
    "Triage Report V1 in this stage.\n"
    "Do not request tools, Retrieval, another evidence source, a retry, or an "
    "additional stage. The program controls the next stage."
)

REPORT_SYNTHESIS_CONTROL = (
    "This is the report_synthesis final stage of a fixed two-stage Runtime "
    "execution.\n"
    "Use the supplied complete Evidence Universe and the explicitly identified "
    "evidence_analysis intermediate artifact to produce the final diagnostic "
    "result required by the shared Task Contract.\n"
    "Treat the intermediate artifact as model-generated working analysis, not "
    "as evaluator Ground Truth. Resolve conflicts against the supplied evidence "
    "and cite only available Evidence IDs.\n"
    "Return exactly one DevAgentOps Structured Triage Report V1 object through "
    "the configured structured-output protocol, with no Markdown or explanatory "
    "text outside that object.\n"
    "Do not request tools, Retrieval, a verifier, a repair call, a retry, or an "
    "additional stage. The program stops after this stage."
)

EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "devagentops_evidence_analysis_memo_v1",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "schema_version": {"type": "string", "enum": ["1"]},
                "case_id": {"type": "string", "minLength": 1},
                "evidence_findings": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "evidence_id": {"type": "string", "minLength": 1},
                            "finding": {"type": "string", "minLength": 1},
                        },
                        "required": ["evidence_id", "finding"],
                    },
                },
                "working_failure_type": {
                    "anyOf": [
                        {
                            "type": "string",
                            "enum": [
                                "test_assertion_failure",
                                "lint_or_type_failure",
                                "dependency_or_install_failure",
                                "config_or_environment_failure",
                                "timeout_or_flaky_failure",
                            ],
                        },
                        {"type": "null"},
                    ]
                },
                "causal_hypothesis": {"type": "string", "minLength": 1},
                "uncertainties": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
            "required": [
                "schema_version",
                "case_id",
                "evidence_findings",
                "working_failure_type",
                "causal_hypothesis",
                "uncertainties",
            ],
        },
    },
}

WORKFLOW_IDENTITY = {
    "version": WORKFLOW_VERSION,
    "ordered_stages": [EVIDENCE_ANALYSIS_STAGE, REPORT_SYNTHESIS_STAGE],
    "transition": "evidence_analysis -> report_synthesis -> stop",
    "expected_model_calls_per_case": 2,
    "message_shape": {
        "messages_per_stage": 1,
        "role": "user",
        "runtime_control_heading": "Runtime execution control:",
        "task_contract_control_separator": "exactly_two_lf",
        "heading_control_separator": "exactly_two_lf",
        "runtime_control_location": "outside_runtime_input_after_task_contract",
    },
}
COMPLETE_RUNTIME_INPUT_SERIALIZER_IDENTITY = {
    "version": RUNTIME_INPUT_SERIALIZATION_VERSION,
    "encoding": "utf-8",
    "json": {
        "ensure_ascii": False,
        "indent": 2,
        "sort_keys": True,
        "trailing_newline": True,
    },
    "membership": [
        "public_case",
        "complete_raw_log",
        "all_frozen_repository_manifest_files",
        "canonical_evidence_coordinates",
    ],
    "repository_file_order": "lexicographic_relative_path",
    "evaluator_ground_truth": "excluded",
}
HANDOFF_SERIALIZER_IDENTITY = {
    "version": HANDOFF_VERSION,
    "encoding": "utf-8",
    "json": {
        "ensure_ascii": False,
        "sort_keys": True,
        "separators": [",", ":"],
        "trailing_newline": False,
    },
    "envelope": {
        "keys": [
            "contract_version",
            "source_stage",
            "visible_output",
            "visible_output_sha256",
        ],
        "contract_version_literal": HANDOFF_VERSION,
        "source_stage_literal": EVIDENCE_ANALYSIS_STAGE,
    },
    "visible_output_hash": "sha256_utf8_bytes_lowercase_hex",
    "stage_2_runtime_input_embedding": {
        "complete_runtime_input": "unchanged_prefix",
        "separator_after_complete_runtime_input": "exactly_two_lf",
        "heading": "Case-scoped intermediate artifact:",
        "heading_to_canonical_json_separator": "one_lf",
    },
}


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


WORKFLOW_FINGERPRINT = _canonical_sha256(WORKFLOW_IDENTITY)
COMPLETE_RUNTIME_INPUT_SERIALIZER_FINGERPRINT = _canonical_sha256(
    COMPLETE_RUNTIME_INPUT_SERIALIZER_IDENTITY
)
EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT = hashlib.sha256(
    EVIDENCE_ANALYSIS_CONTROL.encode("utf-8")
).hexdigest()
REPORT_SYNTHESIS_CONTROL_FINGERPRINT = hashlib.sha256(
    REPORT_SYNTHESIS_CONTROL.encode("utf-8")
).hexdigest()
EVIDENCE_ANALYSIS_MEMO_SCHEMA_FINGERPRINT = _canonical_sha256(
    EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA
)
HANDOFF_SERIALIZER_FINGERPRINT = _canonical_sha256(
    HANDOFF_SERIALIZER_IDENTITY
)


class FixedModelWorkflowError(RuntimeError):
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
class HandoffSerialization:
    version: str
    text: str
    sha256: str
    byte_count: int
    visible_output_sha256: str


@dataclass(frozen=True)
class StageCallResult:
    stage_id: str
    logical_call_number: int
    runtime_input_text: str
    runtime_input_sha256: str
    runtime_input_byte_count: int
    prompt_text: str
    prompt_sha256: str
    control_version: str
    control_fingerprint: str
    token_count: TokenCount
    response: ModelResponse


@dataclass(frozen=True)
class FixedModelWorkflowResult:
    candidate_document: Any
    visible_output: str
    complete_runtime_input: RuntimeInputSerialization
    handoff: HandoffSerialization
    evidence_analysis_observation: dict[str, Any]
    stage_calls: tuple[StageCallResult, StageCallResult]


def run_fixed_model_workflow(
    workspace: RuntimeCaseWorkspace,
    prompt: ComponentManifest,
    provider: ModelProvider,
    *,
    before_model_call: Callable[[dict[str, Any]], None] | None = None,
    after_model_call: Callable[[dict[str, Any]], None] | None = None,
) -> FixedModelWorkflowResult:
    _validate_task_contract(prompt)
    complete_runtime_input = serialize_complete_runtime_input(workspace)

    stage_1_prompt = _render_stage_prompt(
        prompt,
        complete_runtime_input.text,
        EVIDENCE_ANALYSIS_CONTROL,
    )
    stage_1 = _execute_stage(
        provider=provider,
        stage_id=EVIDENCE_ANALYSIS_STAGE,
        logical_call_number=1,
        runtime_input_text=complete_runtime_input.text,
        prompt_text=stage_1_prompt,
        control_version=EVIDENCE_ANALYSIS_CONTROL_VERSION,
        control_fingerprint=EVIDENCE_ANALYSIS_CONTROL_FINGERPRINT,
        response_format=EVIDENCE_ANALYSIS_MEMO_JSON_SCHEMA,
        before_model_call=before_model_call,
    )
    observation = _observe_evidence_analysis_memo(
        stage_1.response.visible_output,
        workspace,
    )
    handoff = serialize_handoff(stage_1.response.visible_output)
    _notify_model_call_completed(
        after_model_call,
        stage_1,
        {
            "evidence_analysis_observation": observation,
            "handoff_sha256": handoff.sha256,
            "visible_output_sha256": handoff.visible_output_sha256,
        },
    )

    stage_2_runtime_input = (
        complete_runtime_input.text
        + ("\n" if complete_runtime_input.text.endswith("\n") else "\n\n")
        + "Case-scoped intermediate artifact:\n"
        + handoff.text
    )
    stage_2_prompt = _render_stage_prompt(
        prompt,
        stage_2_runtime_input,
        REPORT_SYNTHESIS_CONTROL,
    )
    stage_2 = _execute_stage(
        provider=provider,
        stage_id=REPORT_SYNTHESIS_STAGE,
        logical_call_number=2,
        runtime_input_text=stage_2_runtime_input,
        prompt_text=stage_2_prompt,
        control_version=REPORT_SYNTHESIS_CONTROL_VERSION,
        control_fingerprint=REPORT_SYNTHESIS_CONTROL_FINGERPRINT,
        response_format=STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
        before_model_call=before_model_call,
    )
    _notify_model_call_completed(after_model_call, stage_2)
    try:
        candidate_document: Any = json.loads(stage_2.response.visible_output)
    except json.JSONDecodeError:
        candidate_document = stage_2.response.visible_output
    return FixedModelWorkflowResult(
        candidate_document=candidate_document,
        visible_output=stage_2.response.visible_output,
        complete_runtime_input=complete_runtime_input,
        handoff=handoff,
        evidence_analysis_observation=observation,
        stage_calls=(stage_1, stage_2),
    )


def serialize_handoff(visible_output: str) -> HandoffSerialization:
    visible_output_sha256 = hashlib.sha256(
        visible_output.encode("utf-8")
    ).hexdigest()
    document = {
        "contract_version": HANDOFF_VERSION,
        "source_stage": EVIDENCE_ANALYSIS_STAGE,
        "visible_output": visible_output,
        "visible_output_sha256": visible_output_sha256,
    }
    text = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded = text.encode("utf-8")
    return HandoffSerialization(
        version=HANDOFF_VERSION,
        text=text,
        sha256=hashlib.sha256(encoded).hexdigest(),
        byte_count=len(encoded),
        visible_output_sha256=visible_output_sha256,
    )


def _validate_task_contract(prompt: ComponentManifest) -> None:
    if prompt.component_type != "prompt" or prompt.component_version != (
        "structured-triage-task-contract-v1"
    ):
        raise FixedModelWorkflowError(
            "L2 requires structured-triage-task-contract-v1",
            code="invalid_l2_prompt_component",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        )
    if prompt.behavior.get("variables") != ["runtime_input"]:
        raise FixedModelWorkflowError(
            "L2 Task Contract must declare only runtime_input",
            code="invalid_l2_prompt_variables",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        )


def _render_stage_prompt(
    prompt: ComponentManifest,
    runtime_input: str,
    control: str,
) -> str:
    try:
        rendered_task_contract = prompt.behavior["template"].format(
            runtime_input=runtime_input
        )
    except (KeyError, ValueError) as exc:
        raise FixedModelWorkflowError(
            "L2 Task Contract could not be rendered",
            code="l2_prompt_render_failed",
            stage_id=EVIDENCE_ANALYSIS_STAGE,
        ) from exc
    separator = "\n" if rendered_task_contract.endswith("\n") else "\n\n"
    return (
        rendered_task_contract
        + separator
        + "Runtime execution control:\n\n"
        + control
    )


def _execute_stage(
    *,
    provider: ModelProvider,
    stage_id: str,
    logical_call_number: int,
    runtime_input_text: str,
    prompt_text: str,
    control_version: str,
    control_fingerprint: str,
    response_format: dict[str, Any],
    before_model_call: Callable[[dict[str, Any]], None] | None,
) -> StageCallResult:
    request = ModelRequest(
        model=MODEL,
        messages=({"role": "user", "content": prompt_text},),
        response_format=response_format,
        enable_thinking=False,
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
        completions=1,
        stream=False,
        tools=None,
    )
    token_count = provider.count_input_tokens(request)
    context_metadata = {
        "input_tokens": token_count.input_tokens,
        "token_count_method": token_count.method,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "context_limit_tokens": CONTEXT_LIMIT_TOKENS,
    }
    if token_count.input_tokens + MAX_OUTPUT_TOKENS > CONTEXT_LIMIT_TOKENS:
        raise FixedModelWorkflowError(
            f"complete L2 {stage_id} request exceeds the frozen model context capability",
            code="l2_context_infeasible",
            stage_id=stage_id,
            context_metadata=context_metadata,
        )
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    runtime_input_encoded = runtime_input_text.encode("utf-8")
    started_payload = {
        "provider": "siliconflow",
        "model": MODEL,
        "stage_id": stage_id,
        "logical_call_number": logical_call_number,
        "prompt_sha256": prompt_sha256,
        "message_content_sha256": prompt_sha256,
        "request_sha256": _canonical_sha256(request.provider_payload()),
        "runtime_input_sha256": hashlib.sha256(runtime_input_encoded).hexdigest(),
        "runtime_input_byte_count": len(runtime_input_encoded),
        "control_version": control_version,
        "control_fingerprint": control_fingerprint,
        "output_protocol_sha256": _canonical_sha256(response_format),
        **context_metadata,
    }
    if before_model_call is not None:
        before_model_call(started_payload)
    response = provider.complete(request)
    if not isinstance(response.visible_output, str):
        raise FixedModelWorkflowError(
            f"L2 {stage_id} provider response did not expose a visible string",
            code="model_provider_protocol_error",
            stage_id=stage_id,
        )
    return StageCallResult(
        stage_id=stage_id,
        logical_call_number=logical_call_number,
        runtime_input_text=runtime_input_text,
        runtime_input_sha256=started_payload["runtime_input_sha256"],
        runtime_input_byte_count=started_payload["runtime_input_byte_count"],
        prompt_text=prompt_text,
        prompt_sha256=prompt_sha256,
        control_version=control_version,
        control_fingerprint=control_fingerprint,
        token_count=token_count,
        response=response,
    )


def _notify_model_call_completed(
    callback: Callable[[dict[str, Any]], None] | None,
    stage: StageCallResult,
    extra: dict[str, Any] | None = None,
) -> None:
    if callback is None:
        return
    callback(
        {
            "stage_id": stage.stage_id,
            "logical_call_number": stage.logical_call_number,
            "provider_request_id": stage.response.provider_request_id,
            "returned_model": stage.response.returned_model,
            "usage": stage.response.usage,
            "latency_ms": stage.response.latency_ms,
            "finish_reason": stage.response.finish_reason,
            "visible_output": stage.response.visible_output,
            **(extra or {}),
        }
    )


def _observe_evidence_analysis_memo(
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
        coordinate.evidence_id for coordinate in workspace.canonical_coordinates
    }
    findings = document.get("evidence_findings") if isinstance(document, dict) else None
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
    if not isinstance(document["case_id"], str) or not document["case_id"]:
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
    if not isinstance(document["causal_hypothesis"], str) or not document[
        "causal_hypothesis"
    ]:
        return False
    uncertainties = document["uncertainties"]
    return isinstance(uncertainties, list) and all(
        isinstance(uncertainty, str) and bool(uncertainty)
        for uncertainty in uncertainties
    )
