from __future__ import annotations

from typing import Any

from devagentops.conditions.l1.development_output_contract import (
    OUTPUT_CONTRACT_ID,
    OUTPUT_CONTRACT_PROMPT_SHA256,
    OUTPUT_CONTRACT_VERSION,
    OUTPUT_SCHEMA_SHA256,
)
from devagentops.conditions.l1.full_context_v1 import (
    RUNTIME_INPUT_SERIALIZATION_VERSION,
)
from devagentops.conditions.oracle.evidence_v1 import (
    ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION,
    oracle_evidence_delivery_contract,
)
from devagentops.providers.minimax_v1 import (
    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
    MINIMAX_M3_TOKENIZER_REPOSITORY,
    MINIMAX_M3_TOKENIZER_REVISION,
    MINIMAX_M3_TOKENIZER_SHA256,
)


TASK_CONTRACT_VERSION = "structured-triage-task-contract-v1"
TASK_CONTRACT_FINGERPRINT = (
    "d96154bc6a5aa436c84f291c16848daec60bdbf1be250dcedc4b115f4b7c4988"
)
CONTEXT_SOURCE_URL = "https://www.minimax.io/models/text/m3"
L4_RUNTIME_INPUT_VERSION = "l4_tool_workspace_runtime_input_v1"
L4_RUNTIME_CONTROL_VERSION = "l4-react-runtime-control-v1"
L4_RUNTIME_CONTROL_FINGERPRINT = (
    "06db8a3bf29e4f8f9cc34972efceecccbc265fa7d25dcb40b1523b9a0b2a1a26"
)
L4_TOOL_REGISTRY_VERSION = "l4-investigation-tools-v1"
L4_TOOL_REGISTRY_FINGERPRINT = (
    "734ae48e68f66c04a82a60eb4d8d67f1688203c040552524bd5640cb91ac9ff5"
)
L4_TOOL_POLICY_VERSION = "l4-single-sequential-tool-policy-v1"
L4_TOOL_POLICY_FINGERPRINT = (
    "fd218879f82d7c090304522e6c938102ee633e10eaa09733ffda99760db5c26c"
)


def validate_minimax_development_condition(
    effective: dict[str, Any],
    case_count: int,
) -> None:
    from devagentops.evaluation.run import EvaluationRunError

    policy = effective["execution_policy"]
    runtime_variant = effective["runtime_variant"]
    if (
        runtime_variant
        not in {
            "full_context_one_shot",
            "fixed_model_workflow",
            "model_one_shot",
            "self_built_react",
        }
        or case_count < 1
    ):
        raise EvaluationRunError(
            "Matrix v2 MiniMax development run requires at least one supported Case",
            code="unsupported_v2_debug_shape",
        )
    expected_retry_count = 3 if runtime_variant == "self_built_react" else 0
    if policy["retry_count"] != expected_retry_count:
        raise EvaluationRunError(
            "Matrix v2 execution policy does not match the Runtime retry contract",
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
    common_contracts = {
        "task": {
            "component_type": "prompt",
            "version": TASK_CONTRACT_VERSION,
            "fingerprint": TASK_CONTRACT_FINGERPRINT,
        },
        "output": {
            "id": OUTPUT_CONTRACT_ID,
            "version": OUTPUT_CONTRACT_VERSION,
            "prompt_suffix_sha256": OUTPUT_CONTRACT_PROMPT_SHA256,
            "schema_version": "1",
            "schema_sha256": OUTPUT_SCHEMA_SHA256,
        },
    }

    l1_contracts = {
        **common_contracts,
        "runtime_input": {
            "version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        },
    }

    if runtime_variant == "full_context_one_shot":
        expected_contracts = l1_contracts
        contract_label = "L1"
    elif runtime_variant == "fixed_model_workflow":
        from devagentops.conditions.l2.development_workflow_v1 import (
            WORKFLOW_FINGERPRINT,
            WORKFLOW_VERSION,
        )

        expected_contracts = {
            **l1_contracts,
            "workflow": {
                "version": WORKFLOW_VERSION,
                "fingerprint": WORKFLOW_FINGERPRINT,
            },
        }
        contract_label = "L2"
    elif runtime_variant == "model_one_shot":
        expected_contracts = {
            **common_contracts,
            "runtime_input": {
                "version": ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION,
            },
            "evidence_delivery": oracle_evidence_delivery_contract(),
        }
        contract_label = "Oracle"
    else:
        expected_contracts = {
            **common_contracts,
            "runtime_input": {"version": L4_RUNTIME_INPUT_VERSION},
            "runtime_control": {
                "component_type": "prompt",
                "version": L4_RUNTIME_CONTROL_VERSION,
                "fingerprint": L4_RUNTIME_CONTROL_FINGERPRINT,
            },
            "tool_registry": {
                "component_type": "tool_registry",
                "version": L4_TOOL_REGISTRY_VERSION,
                "fingerprint": L4_TOOL_REGISTRY_FINGERPRINT,
            },
            "tool_policy": {
                "component_type": "tool_policy",
                "version": L4_TOOL_POLICY_VERSION,
                "fingerprint": L4_TOOL_POLICY_FINGERPRINT,
            },
        }
        contract_label = "L4"

    if contracts != expected_contracts:
        raise EvaluationRunError(
            f"unsupported {contract_label} MiniMax development contract identity",
            code="unsupported_v2_contract_identity",
        )

    context = treatment["context"]
    if runtime_variant == "self_built_react":
        expected_context = {
            "assessment": "provider_reported",
            "method": "provider_response_usage",
            "context_window_tokens": 1000000,
            "advertised_maximum_tokens": 1000000,
            "guaranteed_minimum_label": "512K",
            "policy": "observe_provider_usage_no_local_preflight",
            "source": {
                "url": CONTEXT_SOURCE_URL,
                "accessed_on": "2026-08-14",
                "contract_version": "minimax-m3-api-context-2026-08-14",
            },
        }
        if context != expected_context:
            raise EvaluationRunError(
                "unsupported L4 provider-reported context accounting identity",
                code="unsupported_v2_context_identity",
            )
        return

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
