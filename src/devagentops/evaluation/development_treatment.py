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


def validate_minimax_development_condition(
    effective: dict[str, Any],
    case_count: int,
) -> None:
    from devagentops.evaluation.run import EvaluationRunError

    policy = effective["execution_policy"]
    runtime_variant = effective["runtime_variant"]
    if (
        runtime_variant
        not in {"full_context_one_shot", "fixed_model_workflow"}
        or case_count < 1
    ):
        raise EvaluationRunError(
            "Matrix v2 MiniMax development run requires at least one supported Case",
            code="unsupported_v2_debug_shape",
        )
    if policy["retry_count"] != 0:
        raise EvaluationRunError(
            "Matrix v2 execution engine does not support retries",
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
        "runtime_input": {
            "version": RUNTIME_INPUT_SERIALIZATION_VERSION,
        },
    }

    if any(
        contracts.get(name) != value
        for name, value in common_contracts.items()
    ):
        raise EvaluationRunError(
            "unsupported MiniMax development contract identity",
            code="unsupported_v2_contract_identity",
        )

    if runtime_variant == "full_context_one_shot":
        if set(contracts) != set(common_contracts):
            raise EvaluationRunError(
                "unsupported L1 MiniMax development contract identity",
                code="unsupported_v2_contract_identity",
            )
    else:
        from devagentops.conditions.l2.development_workflow_v1 import (
            WORKFLOW_FINGERPRINT,
            WORKFLOW_VERSION,
        )

        expected_workflow = {
            "version": WORKFLOW_VERSION,
            "fingerprint": WORKFLOW_FINGERPRINT,
        }

        if (
            set(contracts) != {*common_contracts, "workflow"}
            or contracts.get("workflow") != expected_workflow
        ):
            raise EvaluationRunError(
                "unsupported L2 MiniMax development workflow identity",
                code="unsupported_v2_contract_identity",
            )
    context = treatment["context"]
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
