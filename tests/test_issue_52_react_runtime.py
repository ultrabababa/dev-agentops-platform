from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from devagentops.providers.contracts import CompletionProviderError
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    TokenUsage,
    ToolCall,
    ToolResultMessage,
)
from devagentops.runtime.react import (
    MAX_STEPS,
    ReactConfiguration,
    ReactInfrastructureError,
    build_initial_user_message,
    run_react,
    serialize_initial_runtime_input,
)
from devagentops.runtime.workspace import RuntimeWorkspaceError


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

    def __init__(self, *, unexpected_read_error: bool = False) -> None:
        self.unexpected_read_error = unexpected_read_error

    def read_raw_log(self) -> str:
        if self.unexpected_read_error:
            raise ValueError("implementation defect")
        return "failure line\n"

    def list_repository_files(self) -> tuple[str, ...]:
        return ("src/a.py",)

    def read_repository_file(self, relative_path: str) -> str:
        if relative_path != "src/a.py":
            raise RuntimeWorkspaceError("repository file is outside the frozen workspace")
        return "source\n"


class SequenceProvider:
    def __init__(self, sequence) -> None:
        self.sequence = list(sequence)
        self.requests = []

    def count_input_tokens(self, request):
        raise AssertionError("L4 Runtime must not perform local token preflight")

    def complete(self, request):
        self.requests.append(request)
        item = self.sequence.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def assistant(*blocks, stop_reason="tool_use") -> AssistantMessage:
    return AssistantMessage(
        content=tuple(blocks),
        response_id="response",
        response_model="MiniMax-M3",
        usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        stop_reason=stop_reason,
        raw_stop_reason="tool_calls" if stop_reason == "tool_use" else stop_reason,
        provider_fields={"reasoning_details": [{"text": "opaque"}]},
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


def config(*, max_steps=MAX_STEPS) -> ReactConfiguration:
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
        max_steps=max_steps,
    )


def initial(workspace=None):
    return build_initial_user_message(
        workspace or FakeWorkspace(),
        task_contract_template="Task\n{runtime_input}",
        output_contract_suffix="\nOutput",
    )


def test_multi_step_trajectory_uses_complete_history_and_submits_valid_report() -> None:
    provider = SequenceProvider(
        [
            assistant(call("c1", "read", {"path": "/raw.log"})),
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
    assert result.terminal_reason == "report_submitted"
    assert result.steps == 2
    assert [type(message).__name__ for message in result.messages] == [
        "UserMessage", "AssistantMessage", "ToolResultMessage", "AssistantMessage"
    ]
    assert len(provider.requests[1].messages) == 3
    assert len(provider.requests[1].tools) == 4
    assert result.provider_input_tokens == (10, 10)
    assert "report_submitted" in [event for event, _ in events]


def test_zero_tool_call_invalid_report_is_scored_terminal_even_on_length() -> None:
    provider = SequenceProvider([assistant(TextContent("not json"), stop_reason="length")])
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    assert result.terminal_reason == "model_stopped_without_valid_report"
    assert result.candidate_document == "not json"


def test_zero_tool_call_valid_report_is_accepted_even_on_length() -> None:
    provider = SequenceProvider(
        [assistant(TextContent(valid_report()), stop_reason="length")]
    )
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    assert result.terminal_reason == "report_submitted"
    assert result.steps == 1


def test_step_100_legal_tool_executes_but_never_requests_step_101() -> None:
    decisions = [assistant(call(f"c{index}", "ls", {})) for index in range(MAX_STEPS)]
    provider = SequenceProvider(decisions)
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    assert result.terminal_reason == "max_steps_exhausted"
    assert result.steps == MAX_STEPS
    assert len(provider.requests) == MAX_STEPS
    assert isinstance(result.messages[-1], ToolResultMessage)
    assert result.messages[-1].tool_call_id == "c99"


@pytest.mark.parametrize(
    ("decision", "expected_fragment"),
    [
        (assistant(call("c", "bash", {})), "unknown_tool"),
        (assistant(call("c", "read", {"path": "/raw.log", "extra": 1})), "unknown field"),
        (assistant(ToolCall("c", "read", None, "{broken")), "malformed tool arguments"),
    ],
)
def test_invalid_model_actions_are_agent_visible_and_recoverable(decision, expected_fragment) -> None:
    provider = SequenceProvider(
        [decision, assistant(TextContent(valid_report()), stop_reason="stop")]
    )
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    error = result.messages[2]
    assert isinstance(error, ToolResultMessage) and error.is_error
    assert expected_fragment in error.content
    assert result.terminal_reason == "report_submitted"
    assert len(provider.requests) == 2


def test_length_tool_call_and_multi_call_execute_none_and_close_every_id() -> None:
    length_decision = assistant(
        call("length", "read", {"path": "/raw.log"}), stop_reason="length"
    )
    multi_decision = assistant(
        call("one", "read", {"path": "/raw.log"}),
        call("two", "ls", {}),
    )
    provider = SequenceProvider(
        [length_decision, multi_decision, assistant(TextContent(valid_report()), stop_reason="stop")]
    )
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    errors = [message for message in result.messages if isinstance(message, ToolResultMessage)]
    assert [message.tool_call_id for message in errors] == ["length", "one", "two"]
    assert all(message.is_error for message in errors)
    assert all("failure line" not in message.content for message in errors)


def test_expected_domain_error_recovers_but_unexpected_tool_error_is_infrastructure_failure() -> None:
    provider = SequenceProvider(
        [
            assistant(call("missing", "read", {"path": "/repository/missing"})),
            assistant(TextContent(valid_report()), stop_reason="stop"),
        ]
    )
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=lambda _: None,
    )
    assert isinstance(result.messages[2], ToolResultMessage)
    assert result.messages[2].is_error

    broken_provider = SequenceProvider(
        [assistant(call("broken", "read", {"path": "/raw.log"}))]
    )
    with pytest.raises(ReactInfrastructureError) as exc_info:
        run_react(
            workspace=FakeWorkspace(unexpected_read_error=True),
            provider=broken_provider,
            configuration=config(),
            initial_user_message=initial(FakeWorkspace(unexpected_read_error=True)),
            sleep=lambda _: None,
        )
    assert exc_info.value.code == "tool_execution_failed"


def test_agent_visible_tool_error_content_obeys_utf8_byte_cap() -> None:
    provider = SequenceProvider(
        [
            assistant(call("huge", "界" * 20_000, {})),
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

    error_result = result.messages[2]
    assert isinstance(error_result, ToolResultMessage)
    assert len(error_result.content.encode("utf-8")) <= 50 * 1024
    assert "[truncated: ToolResult exceeded 50 KiB]" in error_result.content
    error_event = next(payload for event, payload in events if event == "tool_call_error")
    assert error_event["truncated"] is True


def test_same_request_retry_success_preserves_conversation_and_uses_backoff() -> None:
    failure = CompletionProviderError(
        "temporary",
        code="model_provider_transport_error",
        retry_disposition="ordinary",
    )
    provider = SequenceProvider(
        [failure, failure, assistant(TextContent(valid_report()), stop_reason="stop")]
    )
    backoffs = []
    result = run_react(
        workspace=FakeWorkspace(), provider=provider, configuration=config(),
        initial_user_message=initial(), sleep=backoffs.append,
    )
    assert result.request_attempts == 3
    assert backoffs == [2.0, 4.0]
    assert provider.requests[0] == provider.requests[1] == provider.requests[2]
    assert len(result.messages) == 2


def test_retry_exhaustion_is_provider_request_infrastructure_failure() -> None:
    failures = [
        CompletionProviderError(
            "temporary",
            code="model_provider_transport_error",
            retry_disposition="ordinary",
        )
        for _ in range(4)
    ]
    provider = SequenceProvider(failures)
    with pytest.raises(ReactInfrastructureError) as exc_info:
        run_react(
            workspace=FakeWorkspace(), provider=provider, configuration=config(),
            initial_user_message=initial(), sleep=lambda _: None,
        )
    assert exc_info.value.code == "provider_request_failed"
    assert exc_info.value.steps == 0
    assert exc_info.value.request_attempts == 4
    assert len(exc_info.value.messages) == 1


def test_timeout_retries_once_and_auth_failure_does_not_retry() -> None:
    timeout_provider = SequenceProvider(
        [
            CompletionProviderError(
                "timeout",
                code="model_provider_timeout",
                retry_disposition="timeout",
            ),
            CompletionProviderError(
                "timeout",
                code="model_provider_timeout",
                retry_disposition="timeout",
            ),
        ]
    )
    backoffs = []
    with pytest.raises(ReactInfrastructureError) as timeout_error:
        run_react(
            workspace=FakeWorkspace(), provider=timeout_provider, configuration=config(),
            initial_user_message=initial(), sleep=backoffs.append,
        )
    assert timeout_error.value.request_attempts == 2
    assert backoffs == [2.0]

    auth_provider = SequenceProvider(
        [CompletionProviderError(
            "denied",
            code="model_provider_credentials_missing",
            retry_disposition="nonretryable",
        )]
    )
    with pytest.raises(ReactInfrastructureError) as auth_error:
        run_react(
            workspace=FakeWorkspace(), provider=auth_provider, configuration=config(),
            initial_user_message=initial(), sleep=lambda _: pytest.fail("must not retry"),
        )
    assert auth_error.value.request_attempts == 1


def test_initial_input_exposes_coordinates_but_not_physical_or_evaluator_content() -> None:
    text = serialize_initial_runtime_input(FakeWorkspace())
    assert '"evidence_id": "E1"' in text
    assert '"raw_log": "/raw.log"' in text
    assert "failure line" not in text
    assert "required-evidence.json" not in text
    assert "expected-answer.json" not in text
    assert "required_evidence_ids" not in text
