from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.component_registry import ComponentManifest
from devagentops.model_provider import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    TokenCount,
)
from devagentops.runtime_workspace import RuntimeCaseWorkspace


RUNTIME_INPUT_SERIALIZATION_VERSION = "full_context_runtime_input_v1"
RUNTIME_VARIANT = "full_context_one_shot"
MODEL = "Qwen/Qwen3.5-4B"
CONTEXT_LIMIT_TOKENS = 262144
MAX_OUTPUT_TOKENS = 1024

STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "devagentops_structured_triage_report_v1",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "schema_version": {"type": "string", "enum": ["1"]},
                "case_id": {"type": "string", "minLength": 1},
                "classification_status": {
                    "type": "string",
                    "enum": ["classified", "inconclusive"],
                },
                "failure_type": {
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
                "summary": {"type": "string", "minLength": 1},
                "root_cause": {"type": "string", "minLength": 1},
                "recommended_action": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence_references": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "evidence_id": {"type": "string", "minLength": 1}
                        },
                        "required": ["evidence_id"],
                    },
                },
            },
            "required": [
                "schema_version",
                "case_id",
                "classification_status",
                "failure_type",
                "summary",
                "root_cause",
                "recommended_action",
                "confidence",
                "evidence_references",
            ],
        },
    },
}


class FullContextOneShotError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RuntimeInputSerialization:
    version: str
    text: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class FullContextOneShotResult:
    candidate_document: Any
    runtime_input: RuntimeInputSerialization
    prompt_text: str
    prompt_sha256: str
    token_count: TokenCount
    context_limit_tokens: int
    response: ModelResponse


def serialize_complete_runtime_input(
    workspace: RuntimeCaseWorkspace,
) -> RuntimeInputSerialization:
    """Serialize the complete Agent-visible Evidence Universe without controls."""
    document = {
        "runtime_input_serialization_version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        "case": workspace.case.as_dict(),
        "evidence_delivery": {
            "mode": "complete_agent_visible_physical_evidence_universe"
        },
        "physical_artifacts": [
            {
                "kind": "raw_log",
                "path": workspace.case.raw_log_path,
                "content": workspace.read_raw_log(),
            },
            *(
                {
                    "kind": "repository_file",
                    "path": f"{workspace.case.repository_root}/{relative_path}",
                    "repository_relative_path": relative_path,
                    "content": workspace.read_repository_file(relative_path),
                }
                for relative_path in workspace.list_repository_files()
            ),
        ],
        "canonical_evidence_coordinates": [
            coordinate.as_dict()
            for coordinate in workspace.canonical_coordinates
        ],
    }
    text = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    encoded = text.encode("utf-8")
    return RuntimeInputSerialization(
        version=RUNTIME_INPUT_SERIALIZATION_VERSION,
        text=text,
        sha256=hashlib.sha256(encoded).hexdigest(),
        byte_count=len(encoded),
    )


def run_full_context_one_shot(
    workspace: RuntimeCaseWorkspace,
    prompt: ComponentManifest,
    provider: ModelProvider,
    *,
    before_model_call: Callable[[dict[str, Any]], None] | None = None,
) -> FullContextOneShotResult:
    if prompt.component_type != "prompt" or prompt.component_version != (
        "structured-triage-task-contract-v1"
    ):
        raise FullContextOneShotError(
            "L1 requires structured-triage-task-contract-v1",
            code="invalid_l1_prompt_component",
        )
    if prompt.behavior.get("variables") != ["runtime_input"]:
        raise FullContextOneShotError(
            "L1 Task Contract must declare only runtime_input",
            code="invalid_l1_prompt_variables",
        )
    runtime_input = serialize_complete_runtime_input(workspace)
    template = prompt.behavior["template"]
    try:
        prompt_text = template.format(runtime_input=runtime_input.text)
    except (KeyError, ValueError) as exc:
        raise FullContextOneShotError(
            "L1 Task Contract could not be rendered",
            code="l1_prompt_render_failed",
        ) from exc
    request = ModelRequest(
        model=MODEL,
        messages=({"role": "user", "content": prompt_text},),
        response_format=STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
        enable_thinking=False,
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
        completions=1,
        stream=False,
        tools=None,
    )
    token_count = provider.count_input_tokens(request)
    if token_count.input_tokens + MAX_OUTPUT_TOKENS > CONTEXT_LIMIT_TOKENS:
        raise FullContextOneShotError(
            "complete L1 request exceeds the frozen model context capability",
            code="l1_context_infeasible",
        )
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    if before_model_call is not None:
        before_model_call(
            {
                "provider": "siliconflow",
                "model": MODEL,
                "prompt_sha256": prompt_sha256,
                "runtime_input_sha256": runtime_input.sha256,
                "runtime_input_byte_count": runtime_input.byte_count,
                "input_tokens": token_count.input_tokens,
                "token_count_method": token_count.method,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "logical_call_number": 1,
            }
        )
    response = provider.complete(request)
    try:
        candidate_document: Any = json.loads(response.visible_output)
    except json.JSONDecodeError:
        candidate_document = response.visible_output
    return FullContextOneShotResult(
        candidate_document=candidate_document,
        runtime_input=runtime_input,
        prompt_text=prompt_text,
        prompt_sha256=prompt_sha256,
        token_count=token_count,
        context_limit_tokens=CONTEXT_LIMIT_TOKENS,
        response=response,
    )
