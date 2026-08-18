from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from devagentops.evaluation.components import ComponentManifest
from devagentops.evaluation.execution import (
    EventRecorder,
    PlannedSample,
    SampleResult,
)
from devagentops.providers.contracts import CompletionProvider, CompletionProviderError
from devagentops.runtime.messages import (
    ToolDefinition,
    assistant_thinking,
    message_to_dict,
)
from devagentops.runtime.react import (
    ReactConfiguration,
    ReactInfrastructureError,
    build_initial_user_message,
    run_react,
)
from devagentops.runtime.tool_policy import BASELINE_TOOL_POLICY
from devagentops.runtime.tools import TOOL_DEFINITIONS, TOOL_SEMANTICS
from devagentops.runtime.workspace import RuntimeCaseWorkspace, RuntimeWorkspaceError
from devagentops.scoring.case import evaluate_case_report
from devagentops.scoring.report import REPORT_SCHEMA_VERSION


RUNTIME_VARIANT = "self_built_react"


@dataclass(frozen=True)
class ConfiguredL4Treatment:
    provider_id: str
    model: str
    reasoning: dict[str, Any]
    generation: dict[str, Any]
    context_limit_tokens: int
    max_completion_tokens: int
    task_contract_version: str
    runtime_control_version: str
    tool_registry_version: str
    tool_policy_version: str
    output_contract_prompt_suffix: str


@dataclass(frozen=True)
class ConfiguredL4ConditionExecutor:
    prompt: ComponentManifest
    runtime_control: ComponentManifest
    tool_registry: ComponentManifest
    tool_policy: ComponentManifest
    treatment: ConfiguredL4Treatment
    provider_factory: Callable[[], CompletionProvider]

    def execute_sample(
        self,
        sample: PlannedSample,
        recorder: EventRecorder,
    ) -> SampleResult:
        identity = sample.identity
        suite_case = sample.suite_case
        recorder.record("l4_execution_started", identity=identity)
        messages = ()
        try:
            tools = self._validated_tools()
            workspace = RuntimeCaseWorkspace.from_package(suite_case.package)
            initial_message = build_initial_user_message(
                workspace,
                task_contract_template=self.prompt.behavior["template"],
                output_contract_suffix=self.treatment.output_contract_prompt_suffix,
            )
            provider = self.provider_factory()
            runtime_result = run_react(
                workspace=workspace,
                provider=provider,
                configuration=ReactConfiguration(
                    model=self.treatment.model,
                    system_prompt=self.runtime_control.behavior["template"],
                    reasoning=self.treatment.reasoning,
                    generation=self.treatment.generation,
                    context_limit_tokens=self.treatment.context_limit_tokens,
                    max_completion_tokens=self.treatment.max_completion_tokens,
                    tools=tools,
                ),
                initial_user_message=initial_message,
                on_event=lambda event_type, payload: recorder.record(
                    event_type, identity=identity, payload=payload
                ),
            )
            messages = runtime_result.messages
        except (
            ReactInfrastructureError,
            RuntimeWorkspaceError,
            CompletionProviderError,
        ) as exc:
            if isinstance(exc, ReactInfrastructureError):
                messages = exc.messages
                failure_code = exc.code
                stage = exc.stage
                steps = exc.steps
                request_attempts = exc.request_attempts
            elif isinstance(exc, CompletionProviderError):
                failure_code = exc.code
                stage = "model_provider"
                steps = 0
                request_attempts = 0
            else:
                failure_code = "l4_workspace_failed"
                stage = "workspace"
                steps = 0
                request_attempts = 0
            recorder.record(
                "failure",
                identity=identity,
                payload={
                    "code": failure_code,
                    "stage": stage,
                    "steps": steps,
                    "request_attempts": request_attempts,
                },
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
                    steps=steps,
                    request_attempts=request_attempts,
                ),
                trajectory=tuple(message_to_dict(message) for message in messages),
            )

        score = evaluate_case_report(
            runtime_result.candidate_document,
            suite_case.package,
        )
        candidate_document = runtime_result.candidate_document
        response = runtime_result.final_assistant
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
            "terminal_reason": runtime_result.terminal_reason,
            "agent_steps": runtime_result.steps,
            "provider_request_attempts": runtime_result.request_attempts,
            "report": (
                score.structured_report.as_dict()
                if score.structured_report is not None
                else None
            ),
            "validation": score.validation.as_dict(),
            "quality_metrics": score.quality_metrics.as_dict(),
            "evidence_diagnostics": score.evidence_diagnostics.as_dict(),
            "candidate_document": candidate_document,
            "visible_output": runtime_result.visible_output,
            "provider_observation": (
                {
                    "provider_request_id": response.response_id,
                    "returned_model": response.response_model,
                    "usage": response.usage.as_dict(),
                    "finish_reason": response.stop_reason,
                    "raw_finish_reason": response.raw_stop_reason,
                    "latency_ms": runtime_result.final_latency_ms,
                    "reasoning": _reasoning_metadata(
                        assistant_thinking(response)
                    ),
                }
                if response is not None
                else None
            ),
            "context_assessment": {
                "per_step_input_tokens": [
                    count.input_tokens for count in runtime_result.token_counts
                ],
                "method": (
                    runtime_result.token_counts[0].method
                    if runtime_result.token_counts
                    else None
                ),
                "exact": True,
                "context_window_tokens": self.treatment.context_limit_tokens,
                "reserved_completion_tokens": self.treatment.max_completion_tokens,
            },
        }
        recorder.record(
            "evaluation_completed",
            identity=identity,
            payload={"quality_metrics": result["quality_metrics"]},
        )
        return SampleResult(
            identity=identity,
            status="scored",
            data=result,
            trajectory=tuple(message_to_dict(message) for message in messages),
        )

    def _validated_tools(self) -> tuple[ToolDefinition, ...]:
        expected_versions = (
            (self.prompt, "prompt", self.treatment.task_contract_version),
            (
                self.runtime_control,
                "prompt",
                self.treatment.runtime_control_version,
            ),
            (
                self.tool_registry,
                "tool_registry",
                self.treatment.tool_registry_version,
            ),
            (self.tool_policy, "tool_policy", self.treatment.tool_policy_version),
        )
        for manifest, component_type, version in expected_versions:
            if (
                manifest.component_type != component_type
                or manifest.component_version != version
            ):
                raise ReactInfrastructureError(
                    "L4 resolved a mismatched frozen Component",
                    code="invalid_l4_component_identity",
                    stage="l4_execution",
                    messages=(),
                    steps=0,
                    request_attempts=0,
                )
        if self.tool_policy.behavior != {"rules": [BASELINE_TOOL_POLICY]}:
            raise ReactInfrastructureError(
                "L4 Tool Policy does not match the baseline single-call contract",
                code="invalid_l4_tool_policy",
                stage="l4_execution",
                messages=(),
                steps=0,
                request_attempts=0,
            )
        return validate_l4_tool_registry(self.tool_registry)


def validate_l4_tool_registry(
    tool_registry: ComponentManifest,
) -> tuple[ToolDefinition, ...]:
    expected_tools = [
        {
            "name": definition.name,
            "description": definition.description,
            "parameters": definition.parameters,
            "semantics": TOOL_SEMANTICS[definition.name],
        }
        for definition in TOOL_DEFINITIONS
    ]
    if tool_registry.behavior != {"tools": expected_tools}:
        raise ReactInfrastructureError(
            "L4 Tool Registry semantics differ from Runtime implementation",
            code="invalid_l4_tool_registry",
            stage="l4_execution",
            messages=(),
            steps=0,
            request_attempts=0,
        )
    return TOOL_DEFINITIONS


def _reasoning_metadata(reasoning: str | None) -> dict[str, Any]:
    if reasoning is None:
        return {"present": False, "character_count": 0, "sha256": None}
    return {
        "present": True,
        "character_count": len(reasoning),
        "sha256": hashlib.sha256(reasoning.encode("utf-8")).hexdigest(),
    }


def _failed_result(
    suite_case,
    repeat_index: int,
    sample_sequence: int,
    code: str,
    stage: str,
    message: str,
    *,
    steps: int,
    request_attempts: int,
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
        "terminal_reason": "provider_request_failed" if code == "provider_request_failed" else None,
        "agent_steps": steps,
        "provider_request_attempts": request_attempts,
        "report": None,
        "validation": None,
        "quality_metrics": None,
        "evidence_diagnostics": None,
        "candidate_document": None,
        "visible_output": None,
        "provider_observation": None,
        "context_assessment": None,
    }
