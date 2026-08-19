from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

import pytest

import devagentops.runtime.react as react_module
from devagentops.evaluation.components import resolve_frozen_component_manifest
from devagentops.evaluation.development_treatment import (
    validate_minimax_development_condition,
)
from devagentops.evaluation.matrix import load_evaluation_matrix
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    TokenUsage,
    ToolCall,
    ToolResultMessage,
)
from devagentops.runtime.react import (
    ReactConfiguration,
    ReactInfrastructureError,
    build_initial_user_message,
    run_react,
)
from devagentops.runtime.tool_policy import BATCH_PARALLEL_TOOL_POLICY
from devagentops.runtime.tools import ExpectedToolError, ToolExecutionResult


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "components/registry.json"
MATRIX = ROOT / "evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json"


@dataclass(frozen=True)
class FakeCase:
    case_id: str = "case-1"
    case_schema_version: str = "2"
    case_fingerprint: str = "f" * 64
    forbidden_actions: tuple[str, ...] = ("write",)


@dataclass(frozen=True)
class FakeCoordinate:
    evidence_id: str = "E1"

    def as_dict(self):
        return {
            "evidence_id": self.evidence_id,
            "source": "raw.log",
            "span": {"type": "line_range", "start_line": 1, "end_line": 1},
            "content_sha256": "a" * 64,
        }


class FakeWorkspace:
    case = FakeCase()
    canonical_coordinates = (FakeCoordinate(),)


class SequenceProvider:
    def __init__(self, sequence) -> None:
        self.sequence = list(sequence)
        self.requests = []

    def count_input_tokens(self, request):
        raise AssertionError("L4 Runtime must not perform local token preflight")

    def complete(self, request):
        self.requests.append(request)
        return self.sequence.pop(0)


def assistant(*blocks, stop_reason="tool_use") -> AssistantMessage:
    return AssistantMessage(
        content=tuple(blocks),
        response_id="response",
        response_model="MiniMax-M3",
        usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        stop_reason=stop_reason,
        raw_stop_reason="tool_calls" if stop_reason == "tool_use" else stop_reason,
    )


def call(call_id: str, name: str, arguments, raw=None) -> ToolCall:
    return ToolCall(
        id=call_id,
        name=name,
        arguments=arguments,
        raw_arguments=raw if raw is not None else json.dumps(arguments),
    )


def valid_report() -> str:
    return json.dumps(
        {
            "schema_version": "1",
            "case_id": "case-1",
            "classification_status": "classified",
            "failure_type": "test_assertion_failure",
            "summary": "The assertion failed.",
            "root_cause": "The observed values differ from the expectation.",
            "recommended_action": "Inspect and correct the failing assertion inputs.",
            "confidence": 0.9,
            "evidence_references": [{"evidence_id": "E1"}],
        }
    )


def config() -> ReactConfiguration:
    return ReactConfiguration(
        model="MiniMax-M3",
        system_prompt="runtime control",
        reasoning={"thinking": {"type": "adaptive"}, "reasoning_split": True},
        generation={
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        },
        context_limit_tokens=1_000_000,
        max_completion_tokens=65536,
        tool_policy_mode="batch_parallel",
    )


def initial() -> object:
    return build_initial_user_message(
        FakeWorkspace(),
        task_contract_template="Task\n{runtime_input}",
        output_contract_suffix="\nOutput",
    )


def test_batch_executes_concurrently_but_returns_results_in_model_order(monkeypatch) -> None:
    barrier = threading.Barrier(3)

    def fake_execute_tool(workspace, name, arguments):
        barrier.wait(timeout=2)
        return ToolExecutionResult(content=arguments["path"])

    monkeypatch.setattr(react_module, "execute_tool", fake_execute_tool)
    provider = SequenceProvider(
        [
            assistant(
                call("c1", "read", {"path": "/one"}),
                call("c2", "read", {"path": "/two"}),
                call("c3", "read", {"path": "/three"}),
            ),
            assistant(TextContent(valid_report()), stop_reason="stop"),
        ]
    )
    events = []

    result = run_react(
        workspace=FakeWorkspace(),
        provider=provider,
        configuration=config(),
        initial_user_message=initial(),
        on_event=lambda event, payload: events.append((event, payload)),
        sleep=lambda _: None,
    )

    tool_results = [
        message for message in result.messages if isinstance(message, ToolResultMessage)
    ]
    assert [message.tool_call_id for message in tool_results] == ["c1", "c2", "c3"]
    assert [message.content for message in tool_results] == ["/one", "/two", "/three"]
    assert result.steps == 2
    assert len(provider.requests) == 2
    assert [
        payload["tool_call_id"]
        for event, payload in events
        if event == "tool_call_started"
    ] == ["c1", "c2", "c3"]
    assert [
        payload["tool_call_id"]
        for event, payload in events
        if event == "tool_call_completed"
    ] == ["c1", "c2", "c3"]


def test_malformed_and_expected_errors_do_not_cancel_valid_siblings(monkeypatch) -> None:
    executed = []
    lock = threading.Lock()

    def fake_execute_tool(workspace, name, arguments):
        with lock:
            executed.append(arguments["path"])
        if arguments["path"] == "/expected-error":
            raise ExpectedToolError("missing", code="path_not_found")
        return ToolExecutionResult(content=f"ok:{arguments['path']}")

    monkeypatch.setattr(react_module, "execute_tool", fake_execute_tool)
    provider = SequenceProvider(
        [
            assistant(
                call("valid", "read", {"path": "/valid"}),
                ToolCall("malformed", "read", None, "{broken"),
                call("expected", "read", {"path": "/expected-error"}),
            ),
            assistant(TextContent(valid_report()), stop_reason="stop"),
        ]
    )

    result = run_react(
        workspace=FakeWorkspace(),
        provider=provider,
        configuration=config(),
        initial_user_message=initial(),
        sleep=lambda _: None,
    )

    tool_results = [
        message for message in result.messages if isinstance(message, ToolResultMessage)
    ]
    assert [message.tool_call_id for message in tool_results] == [
        "valid",
        "malformed",
        "expected",
    ]
    assert tool_results[0].is_error is False
    assert tool_results[1].is_error is True
    assert "malformed tool arguments" in tool_results[1].content
    assert tool_results[2].is_error is True
    assert "path_not_found" in tool_results[2].content
    assert set(executed) == {"/valid", "/expected-error"}


def test_duplicate_calls_are_not_deduplicated(monkeypatch) -> None:
    execution_count = 0
    lock = threading.Lock()

    def fake_execute_tool(workspace, name, arguments):
        nonlocal execution_count
        with lock:
            execution_count += 1
        return ToolExecutionResult(content="same")

    monkeypatch.setattr(react_module, "execute_tool", fake_execute_tool)
    provider = SequenceProvider(
        [
            assistant(
                call("one", "read", {"path": "/same"}),
                call("two", "read", {"path": "/same"}),
            ),
            assistant(TextContent(valid_report()), stop_reason="stop"),
        ]
    )

    result = run_react(
        workspace=FakeWorkspace(),
        provider=provider,
        configuration=config(),
        initial_user_message=initial(),
        sleep=lambda _: None,
    )

    assert execution_count == 2
    assert [
        message.tool_call_id
        for message in result.messages
        if isinstance(message, ToolResultMessage)
    ] == ["one", "two"]


def test_unexpected_parallel_tool_exception_remains_sample_infrastructure_failure(
    monkeypatch,
) -> None:
    def fake_execute_tool(workspace, name, arguments):
        if arguments["path"] == "/broken":
            raise ValueError("implementation defect")
        return ToolExecutionResult(content="ok")

    monkeypatch.setattr(react_module, "execute_tool", fake_execute_tool)
    provider = SequenceProvider(
        [
            assistant(
                call("ok", "read", {"path": "/ok"}),
                call("broken", "read", {"path": "/broken"}),
            )
        ]
    )

    with pytest.raises(ReactInfrastructureError) as captured:
        run_react(
            workspace=FakeWorkspace(),
            provider=provider,
            configuration=config(),
            initial_user_message=initial(),
            sleep=lambda _: None,
        )

    assert captured.value.code == "tool_execution_failed"
    assert captured.value.stage == "tool_execution"
    assert captured.value.steps == 1
    assert len(captured.value.messages) == 2
    assert not any(
        isinstance(message, ToolResultMessage) for message in captured.value.messages
    )


def test_length_still_rejects_entire_batch_before_execution(monkeypatch) -> None:
    def must_not_execute(*args, **kwargs):
        pytest.fail("truncated ToolCalls must never execute")

    monkeypatch.setattr(react_module, "execute_tool", must_not_execute)
    provider = SequenceProvider(
        [
            assistant(
                call("one", "read", {"path": "/one"}),
                call("two", "read", {"path": "/two"}),
                stop_reason="length",
            ),
            assistant(TextContent(valid_report()), stop_reason="stop"),
        ]
    )

    result = run_react(
        workspace=FakeWorkspace(),
        provider=provider,
        configuration=config(),
        initial_user_message=initial(),
        sleep=lambda _: None,
    )

    errors = [
        message for message in result.messages if isinstance(message, ToolResultMessage)
    ]
    assert [message.tool_call_id for message in errors] == ["one", "two"]
    assert all(message.is_error for message in errors)


def test_batch_parallel_components_and_matrix_resolve_as_distinct_treatment() -> None:
    runtime_control = resolve_frozen_component_manifest(
        REGISTRY, "prompt", "l4-react-runtime-control-batch-parallel-v1"
    )
    tool_policy = resolve_frozen_component_manifest(
        REGISTRY, "tool_policy", "l4-batch-parallel-tool-policy-v1"
    )
    assert "zero, one, or multiple ToolCalls" in runtime_control.behavior["template"]
    assert "Prefer" not in runtime_control.behavior["template"]
    assert tool_policy.behavior == {"rules": [BATCH_PARALLEL_TOOL_POLICY]}

    matrix = load_evaluation_matrix(MATRIX, REGISTRY)
    condition = matrix.conditions[0]
    contracts = condition.effective_condition["treatment"]["contracts"]
    assert condition.effective_condition["runtime_variant"] == "self_built_react"
    assert contracts["runtime_control"]["version"] == (
        "l4-react-runtime-control-batch-parallel-v1"
    )
    assert contracts["tool_policy"]["version"] == "l4-batch-parallel-tool-policy-v1"
    assert contracts["tool_registry"]["version"] == "l4-investigation-tools-v1"
    assert contracts["output"]["version"] == "development-v2"
    validate_minimax_development_condition(condition.effective_condition, case_count=1)
