import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from devagentops.evaluation.matrix import EvaluationMatrixError, load_evaluation_matrix
from devagentops.evaluation.matrix_v2 import calculate_run_configuration_fingerprint
import devagentops.evaluation.debug_v2 as evaluation_debug_v2
from devagentops.cli import main
from devagentops.providers.contracts import (
    CompletionProviderError,
    ExactTokenCount,
    LogicalCompletionRequest,
)
from devagentops.providers.execution import (
    CompletionRequestRetryPolicy,
    ProviderRequestFailed,
    execute_completion_request,
)
from devagentops.providers.minimax_v1 import (
    MINIMAX_M3_CHAT_TEMPLATE_SHA256,
    MINIMAX_M3_TOKENIZER_REVISION,
    MINIMAX_M3_TOKENIZER_SHA256,
    MiniMaxProvider,
)
from devagentops.providers.openai_compatible import (
    OpenAICompatibleChatCompletionsTransport,
    OpenAICompatibleTransportError,
)
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
    ToolCall,
    ToolDefinition,
    ToolResultMessage,
    UserMessage,
    assistant_text,
    assistant_thinking,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_MATRIX = PROJECT_ROOT / "evaluation/matrices/l1-case-subset-debug-v1.json"
V2_MATRIX = PROJECT_ROOT / "evaluation/matrices/l1-minimax-m3-development-v2.json"
REGISTRY = PROJECT_ROOT / "components/registry.json"
SUITE = PROJECT_ROOT / "evaluation/suites/triage-v1/suite.json"
SMOKE_CASE_ID = "bugswarm-traccar-170287308"


def _v2_document() -> dict:
    return {
        "matrix_id": "l1-minimax-development",
        "matrix_version": "2",
        "schema_version": "2",
        "conditions": [
            {
                "id": "l1-minimax-m3-adaptive-development-v1",
                "type": "candidate",
                "runtime_variant": "full_context_one_shot",
                "suite": "triage-suite-v1",
                "evaluation_method": "triage-method-v1",
                "treatment": {
                    "provider": {
                        "id": "minimax-official",
                        "transport": "openai-compatible-chat-completions",
                        "profile": "minimax-official-v1",
                        "base_url": "https://api.minimaxi.com/v1",
                    },
                    "model": "MiniMax-M3",
                    "reasoning": {
                        "thinking": {"type": "adaptive"},
                        "reasoning_split": True,
                    },
                    "generation": {
                        "temperature": 0,
                        "max_completion_tokens": 65536,
                        "n": 1,
                        "stream": False,
                        "response_format": {"mode": "omitted"},
                    },
                    "contracts": {
                        "task": {
                            "id": "structured-triage-task-contract",
                            "version": "development-clean-clarification-v1",
                            "fingerprint": "1" * 64,
                        },
                        "output": {
                            "id": "structured-triage-report",
                            "version": "1",
                            "fingerprint": "2" * 64,
                        },
                    },
                    "context": {
                        "context_window_tokens": 524288,
                        "policy": "official_guaranteed_minimum_total_context",
                        "source": "https://www.minimax.io/models/text/m3",
                        "tokenizer": {
                            "repository": "MiniMaxAI/MiniMax-M3",
                            "revision": "f0e1c1e04d40177e4673a22097036854f536e9c0",
                            "tokenizer_sha256": "3" * 64,
                            "chat_template_sha256": "4" * 64,
                            "method": "minimax_m3_official_chat_template_adaptive_v1",
                        },
                    },
                },
                "execution_policy": {
                    "repeat_count": 1,
                    "max_case_concurrency": 1,
                    "retry_count": 0,
                    "request_timeout_seconds": 600,
                },
            }
        ],
    }


def test_matrix_loader_dispatches_v1_without_changing_historical_fingerprint(
    tmp_path: Path,
) -> None:
    historical = load_evaluation_matrix(V1_MATRIX)
    assert historical.schema_version == "1"
    assert historical.conditions[0].as_dict()["condition_fingerprint"] == (
        "fa94528f36d543f0f3851065009c17d5f9d58bceb652accf513e4c1b0b90c065"
    )

    v2_path = tmp_path / "matrix-v2.json"
    v2_path.write_text(json.dumps(_v2_document()), encoding="utf-8")
    resolved = load_evaluation_matrix(v2_path)

    assert resolved.schema_version == "2"
    assert resolved.conditions[0].condition_id == (
        "l1-minimax-m3-adaptive-development-v1"
    )
    assert resolved.conditions[0].effective_condition["treatment"]["model"] == (
        "MiniMax-M3"
    )


@pytest.mark.parametrize("policy_field", ["repeat_count", "max_case_concurrency"])
def test_execution_policy_changes_only_execution_and_run_configuration_identity(
    tmp_path: Path,
    policy_field: str,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    changed_path = tmp_path / "changed.json"
    baseline = _v2_document()
    changed = _v2_document()
    changed["conditions"][0]["execution_policy"][policy_field] = 2
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    changed_path.write_text(json.dumps(changed), encoding="utf-8")

    baseline_matrix = load_evaluation_matrix(baseline_path)
    changed_matrix = load_evaluation_matrix(changed_path)
    baseline_condition = baseline_matrix.conditions[0]
    changed_condition = changed_matrix.conditions[0]

    assert baseline_condition.treatment_fingerprint == (
        changed_condition.treatment_fingerprint
    )
    assert baseline_condition.condition_fingerprint == (
        changed_condition.condition_fingerprint
    )
    assert baseline_condition.execution_policy_fingerprint != (
        changed_condition.execution_policy_fingerprint
    )
    common = {
        "suite_fingerprint": "5" * 64,
        "selected_cases": [
            {"case_id": "case-a", "case_fingerprint": "6" * 64, "weight": 1}
        ],
        "code_revision": "a" * 40,
        "git_dirty": False,
    }
    assert calculate_run_configuration_fingerprint(
        baseline_matrix, baseline_condition, **common
    ) != calculate_run_configuration_fingerprint(
        changed_matrix, changed_condition, **common
    )


def test_matrix_v2_rejects_missing_required_treatment_field(tmp_path: Path) -> None:
    document = _v2_document()
    del document["conditions"][0]["treatment"]["context"]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(EvaluationMatrixError, match="missing required field 'context'"):
        load_evaluation_matrix(path)


class _RecordingTransport:
    def __init__(self, response: dict | None = None) -> None:
        self.payloads: list[dict] = []
        self.response = response or {
            "id": "request-39",
            "model": "MiniMax-M3",
            "choices": [
                {
                    "message": {
                        "content": '{"schema_version":"1"}',
                        "reasoning_content": "private reasoning",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 178, "completion_tokens": 9},
        }

    def complete(self, payload: dict):
        self.payloads.append(payload)
        return self.response


class _SequenceTransport:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.payloads: list[dict] = []

    def complete(self, payload: dict):
        self.payloads.append(payload)
        return self.responses.pop(0)


def _logical_request() -> LogicalCompletionRequest:
    return LogicalCompletionRequest(
        model="MiniMax-M3",
        messages=(UserMessage("diagnose this failure"),),
        reasoning={"thinking": {"type": "adaptive"}, "reasoning_split": True},
        generation={
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        },
    )


def test_minimax_profile_maps_exact_qualified_payload_without_response_format() -> None:
    transport = _RecordingTransport()
    provider = MiniMaxProvider(transport=transport)

    observation = provider.complete(_logical_request())

    assert transport.payloads == [
        {
            "model": "MiniMax-M3",
            "messages": [{"role": "user", "content": "diagnose this failure"}],
            "thinking": {"type": "adaptive"},
            "reasoning_split": True,
            "temperature": 0,
            "max_completion_tokens": 65536,
            "n": 1,
            "stream": False,
        }
    ]
    assert "response_format" not in transport.payloads[0]
    assert observation.response_id == "request-39"
    assert assistant_text(observation) == '{"schema_version":"1"}'
    assert assistant_thinking(observation) == "private reasoning"
    assert observation.usage.input_tokens == 178


def test_minimax_transport_failure_is_not_retried() -> None:
    class FailingTransport:
        def __init__(self) -> None:
            self.attempts = 0

        def complete(self, payload: dict):
            self.attempts += 1
            raise OpenAICompatibleTransportError(
                "request failed before a response was returned",
                code="model_provider_transport_error",
            )

    transport = FailingTransport()
    provider = MiniMaxProvider(transport=transport)

    with pytest.raises(OpenAICompatibleTransportError):
        provider.complete(_logical_request())
    assert transport.attempts == 1


def test_openai_compatible_transport_does_not_expose_api_key_in_errors(
    monkeypatch,
) -> None:
    secret = "sentinel-minimax-key-never-expose"
    attempts = 0

    def fail(request, timeout):
        nonlocal attempts
        attempts += 1
        assert request.get_header("Authorization") == f"Bearer {secret}"
        raise urllib.error.URLError(f"transport detail containing {secret}")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    transport = OpenAICompatibleChatCompletionsTransport(
        base_url="https://api.minimaxi.com/v1",
        api_key=secret,
        timeout_seconds=600,
    )

    with pytest.raises(OpenAICompatibleTransportError) as captured:
        transport.complete({"model": "MiniMax-M3"})

    assert attempts == 1
    assert secret not in str(captured.value)
    assert captured.value.code == "model_provider_transport_error"


def test_minimax_exact_counter_uses_pinned_official_adaptive_chat_template() -> None:
    provider = MiniMaxProvider(transport=_RecordingTransport())

    count = provider.count_input_tokens(_logical_request())

    assert MINIMAX_M3_TOKENIZER_REVISION == (
        "f0e1c1e04d40177e4673a22097036854f536e9c0"
    )
    assert MINIMAX_M3_TOKENIZER_SHA256 == (
        "bb1f1626cf01448f1e3b6036d0a061ffc66c91d9046aada14ea23a5441b5ad6e"
    )
    assert MINIMAX_M3_CHAT_TEMPLATE_SHA256 == (
        "11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64"
    )
    assert count.method == "minimax_m3_official_chat_template_adaptive_v1"
    assert count.input_tokens == 180


def test_minimax_native_tool_call_preserves_strict_and_raw_arguments() -> None:
    raw_arguments = '{"path":"/raw.log","offset":1}'
    transport = _RecordingTransport(
        {
            "id": "tool-response",
            "model": "MiniMax-M3",
            "choices": [{
                "message": {
                    "content": None,
                    "reasoning_content": "inspect the log",
                    "reasoning_details": [
                        {"type": "text", "text": "opaque continuation"},
                        {"type": "encrypted", "data": "sentinel"},
                    ],
                    "tool_calls": [{
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "read", "arguments": raw_arguments},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {
                "prompt_tokens": 200,
                "completion_tokens": 20,
                "total_tokens": 220,
                "completion_tokens_details": {"reasoning_tokens": 7},
            },
            "base_resp": {"status_code": 0, "status_msg": ""},
        }
    )
    assistant = MiniMaxProvider(transport=transport).complete(_logical_request())

    call = next(block for block in assistant.content if isinstance(block, ToolCall))
    assert call.arguments == {"path": "/raw.log", "offset": 1}
    assert call.raw_arguments == raw_arguments
    assert assistant.stop_reason == "tool_use"
    assert assistant.raw_stop_reason == "tool_calls"
    assert assistant.provider_fields == {
        "reasoning_content": "inspect the log",
        "reasoning_details": [
            {"type": "text", "text": "opaque continuation"},
            {"type": "encrypted", "data": "sentinel"},
        ],
    }
    assert assistant.usage.total_tokens == 220
    assert assistant.usage.provider_fields == {
        "completion_tokens_details": {"reasoning_tokens": 7}
    }


@pytest.mark.parametrize(
    "raw_arguments",
    [
        '{"path":',
        '["/raw.log"]',
        '{"offset":NaN}',
        '{"offset":Infinity}',
    ],
)
def test_minimax_malformed_tool_arguments_remain_a_model_decision(
    raw_arguments: str,
) -> None:
    transport = _RecordingTransport(
        {
            "id": "malformed-tool-response",
            "model": "MiniMax-M3",
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call-bad",
                        "type": "function",
                        "function": {"name": "read", "arguments": raw_arguments},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {},
        }
    )

    assistant = MiniMaxProvider(transport=transport).complete(_logical_request())
    call = next(block for block in assistant.content if isinstance(block, ToolCall))
    assert call.arguments is None
    assert call.raw_arguments == raw_arguments


def test_minimax_malformed_raw_tool_history_refuses_exact_count_but_replays_wire() -> None:
    raw_arguments = '{"path":'
    assistant = AssistantMessage(
        content=(
            ToolCall(
                id="call-bad",
                name="read",
                arguments=None,
                raw_arguments=raw_arguments,
            ),
        ),
        response_id="malformed-history",
        response_model="MiniMax-M3",
        usage=TokenUsage(),
        stop_reason="tool_use",
        raw_stop_reason="tool_calls",
    )
    request = LogicalCompletionRequest(
        model="MiniMax-M3",
        messages=(
            UserMessage("inspect"),
            assistant,
            ToolResultMessage(
                "call-bad", "read", "malformed tool arguments", True
            ),
        ),
        reasoning=_logical_request().reasoning,
        generation=_logical_request().generation,
    )
    transport = _RecordingTransport()
    provider = MiniMaxProvider(transport=transport)

    with pytest.raises(CompletionProviderError) as captured:
        provider.count_input_tokens(request)

    assert captured.value.code == "exact_token_count_unqualified"
    assert captured.value.retry_disposition == "nonretryable"
    provider.complete(request)
    assert transport.payloads[0]["messages"][1]["tool_calls"][0]["function"][
        "arguments"
    ] == raw_arguments


def test_minimax_continuation_and_exact_counter_share_typed_serialization() -> None:
    tool = ToolDefinition(
        name="read",
        description="Read bounded lines.",
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )
    assistant = AssistantMessage(
        content=(
            ThinkingContent("inspect"),
            ToolCall(
                id="call-1",
                name="read",
                arguments={"path": "/raw.log"},
                raw_arguments='{ "path" : "/raw.log" }',
            ),
        ),
        response_id="response-1",
        response_model="MiniMax-M3",
        usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        stop_reason="tool_use",
        raw_stop_reason="tool_calls",
        provider_fields={
            "reasoning_content": "inspect",
            "reasoning_details": [{"type": "text", "text": "full-state"}],
        },
    )
    request = LogicalCompletionRequest(
        model="MiniMax-M3",
        system_prompt="Runtime control.",
        messages=(
            UserMessage("diagnose"),
            assistant,
            ToolResultMessage("call-1", "read", "line 1", False),
        ),
        tools=(tool,),
        reasoning=_logical_request().reasoning,
        generation=_logical_request().generation,
    )
    transport = _RecordingTransport()
    provider = MiniMaxProvider(transport=transport)

    count = provider.count_input_tokens(request)
    provider.complete(request)

    assert count.input_tokens > provider.count_input_tokens(_logical_request()).input_tokens
    payload = transport.payloads[0]
    assert payload["messages"][0] == {
        "role": "system",
        "content": "Runtime control.",
    }
    assert payload["messages"][2]["reasoning_details"] == [
        {"type": "text", "text": "full-state"}
    ]
    assert payload["messages"][2]["tool_calls"][0]["function"]["arguments"] == (
        '{ "path" : "/raw.log" }'
    )
    assert payload["messages"][3] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "name": "read",
        "content": "line 1",
    }
    assert payload["tools"] == [{
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read bounded lines.",
            "parameters": tool.parameters,
        },
    }]


def test_minimax_reasoning_details_only_round_trips_without_synthetic_content() -> None:
    reasoning_details = [
        {"type": "text", "text": "opaque continuation"},
        {"type": "encrypted", "data": "sentinel"},
    ]
    parsed = MiniMaxProvider(
        transport=_RecordingTransport({
            "id": "details-only",
            "model": "MiniMax-M3",
            "choices": [{
                "message": {
                    "content": "continue",
                    "reasoning_details": reasoning_details,
                },
                "finish_reason": "stop",
            }],
            "usage": {},
        })
    ).complete(_logical_request())
    replay_transport = _RecordingTransport()
    replay_provider = MiniMaxProvider(transport=replay_transport)
    replay_request = LogicalCompletionRequest(
        model="MiniMax-M3",
        messages=(UserMessage("first"), parsed, UserMessage("next")),
        reasoning=_logical_request().reasoning,
        generation=_logical_request().generation,
    )

    replay_provider.complete(replay_request)

    replayed_assistant = replay_transport.payloads[0]["messages"][1]
    assert replayed_assistant["reasoning_details"] == reasoning_details
    assert "reasoning_content" not in replayed_assistant


def test_minimax_exact_count_includes_reasoning_details_only_continuation() -> None:
    reasoning_text = "reasoning-details-only-sentinel " * 30
    parsed = MiniMaxProvider(
        transport=_RecordingTransport({
            "id": "details-only-count",
            "model": "MiniMax-M3",
            "choices": [{
                "message": {
                    "content": "continue",
                    "reasoning_details": [{"type": "text", "text": reasoning_text}],
                },
                "finish_reason": "stop",
            }],
            "usage": {},
        })
    ).complete(_logical_request())
    without_reasoning = AssistantMessage(
        content=(TextContent("continue"),),
        response_id=parsed.response_id,
        response_model=parsed.response_model,
        usage=parsed.usage,
        stop_reason=parsed.stop_reason,
        raw_stop_reason=parsed.raw_stop_reason,
    )

    def request_with(assistant_message: AssistantMessage) -> LogicalCompletionRequest:
        return LogicalCompletionRequest(
            model="MiniMax-M3",
            messages=(UserMessage("first"), assistant_message, UserMessage("next")),
            reasoning=_logical_request().reasoning,
            generation=_logical_request().generation,
        )

    provider = MiniMaxProvider(transport=_RecordingTransport())
    details_count = provider.count_input_tokens(request_with(parsed)).input_tokens
    baseline_count = provider.count_input_tokens(
        request_with(without_reasoning)
    ).input_tokens

    assert details_count > baseline_count


def test_minimax_nonzero_provider_status_is_not_a_successful_completion() -> None:
    provider = MiniMaxProvider(
        transport=_RecordingTransport(
            {"base_resp": {"status_code": 1004, "status_msg": "auth failed"}}
        )
    )
    with pytest.raises(CompletionProviderError) as captured:
        provider.complete(_logical_request())
    assert captured.value.retry_disposition == "nonretryable"


@pytest.mark.parametrize("status_code", [1000, 1002, 1024, 1033])
def test_minimax_transient_provider_status_retries_same_logical_request(
    status_code: int,
) -> None:
    success = _RecordingTransport().response
    transport = _SequenceTransport([
        {"base_resp": {"status_code": status_code, "status_msg": "temporary"}},
        success,
    ])
    backoffs: list[float] = []

    execution = execute_completion_request(
        MiniMaxProvider(transport=transport),
        _logical_request(),
        retry_policy=CompletionRequestRetryPolicy(
            ordinary_backoffs=(2.0, 4.0, 8.0),
            timeout_backoffs=(2.0,),
        ),
        sleep=backoffs.append,
    )

    assert execution.attempts == 2
    assert backoffs == [2.0]
    assert transport.payloads[0] == transport.payloads[1]


def test_minimax_timeout_provider_status_retries_only_once() -> None:
    transport = _SequenceTransport([
        {"base_resp": {"status_code": 1001, "status_msg": "timeout"}},
        {"base_resp": {"status_code": 1001, "status_msg": "timeout"}},
        _RecordingTransport().response,
    ])
    backoffs: list[float] = []

    with pytest.raises(ProviderRequestFailed) as captured:
        execute_completion_request(
            MiniMaxProvider(transport=transport),
            _logical_request(),
            retry_policy=CompletionRequestRetryPolicy(
                ordinary_backoffs=(2.0, 4.0, 8.0),
                timeout_backoffs=(2.0,),
            ),
            sleep=backoffs.append,
        )

    assert captured.value.attempts == 2
    assert backoffs == [2.0]
    assert len(transport.payloads) == 2


@pytest.mark.parametrize("status_code", [1004, 1008, 1026, 2013])
def test_minimax_nonretryable_provider_status_does_not_retry(
    status_code: int,
) -> None:
    transport = _SequenceTransport([
        {"base_resp": {"status_code": status_code, "status_msg": "rejected"}},
        _RecordingTransport().response,
    ])

    with pytest.raises(ProviderRequestFailed) as captured:
        execute_completion_request(
            MiniMaxProvider(transport=transport),
            _logical_request(),
            retry_policy=CompletionRequestRetryPolicy(
                ordinary_backoffs=(2.0, 4.0, 8.0),
                timeout_backoffs=(2.0,),
            ),
            sleep=lambda _: pytest.fail("nonretryable status must not sleep"),
        )

    assert captured.value.attempts == 1
    assert len(transport.payloads) == 1


@pytest.mark.parametrize(
    "error",
    [
        OpenAICompatibleTransportError(
            "rate limited", code="model_provider_rate_limited", http_status=429
        ),
        OpenAICompatibleTransportError(
            "unavailable", code="model_provider_http_error", http_status=503
        ),
        OpenAICompatibleTransportError(
            "network", code="model_provider_transport_error"
        ),
    ],
)
def test_openai_transport_transients_use_ordinary_retry(
    error: OpenAICompatibleTransportError,
) -> None:
    class FailOnceProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            self.calls += 1
            if self.calls == 1:
                raise error
            return MiniMaxProvider(
                transport=_RecordingTransport()
            ).complete(request)

    backoffs: list[float] = []
    execution = execute_completion_request(
        FailOnceProvider(),
        _logical_request(),
        retry_policy=CompletionRequestRetryPolicy(
            ordinary_backoffs=(2.0, 4.0, 8.0),
            timeout_backoffs=(2.0,),
        ),
        sleep=backoffs.append,
    )

    assert execution.attempts == 2
    assert backoffs == [2.0]


def test_openai_request_timeout_retries_only_once() -> None:
    class AlwaysTimeoutProvider:
        def complete(self, request):
            raise OpenAICompatibleTransportError(
                "timeout", code="model_provider_timeout"
            )

    backoffs: list[float] = []
    with pytest.raises(ProviderRequestFailed) as captured:
        execute_completion_request(
            AlwaysTimeoutProvider(),
            _logical_request(),
            retry_policy=CompletionRequestRetryPolicy(
                ordinary_backoffs=(2.0, 4.0, 8.0),
                timeout_backoffs=(2.0,),
            ),
            sleep=backoffs.append,
        )
    assert captured.value.attempts == 2
    assert backoffs == [2.0]


class _FakeMiniMaxProvider:
    def __init__(self, *, input_tokens: int = 1000) -> None:
        self.input_tokens = input_tokens
        self.requests: list[LogicalCompletionRequest] = []

    def count_input_tokens(self, request: LogicalCompletionRequest) -> ExactTokenCount:
        return ExactTokenCount(
            input_tokens=self.input_tokens,
            method="minimax_m3_official_chat_template_adaptive_v1",
        )

    def complete(self, request: LogicalCompletionRequest) -> AssistantMessage:
        self.requests.append(request)
        return AssistantMessage(
            content=(
                ThinkingContent("private hidden reasoning must never be persisted"),
                TextContent(json.dumps({
                    "schema_version": "1",
                    "case_id": SMOKE_CASE_ID,
                    "classification_status": "inconclusive",
                    "failure_type": None,
                    "summary": "The evidence requires further diagnosis.",
                    "root_cause": "The exact cause is not sufficiently supported.",
                    "recommended_action": "Inspect the cited log evidence.",
                    "confidence": 0.2,
                    "evidence_references": [
                        {"evidence_id": "log:raw-log:lines-0001-0100"}
                    ],
                })),
            ),
            response_id="minimax-request-39",
            response_model="MiniMax-M3",
            usage=TokenUsage(input_tokens=self.input_tokens, output_tokens=80),
            stop_reason="stop",
            raw_stop_reason="stop",
        )


def _debug_args(database: Path, artifacts: Path) -> list[str]:
    return [
        "eval",
        "debug",
        "--matrix",
        str(V2_MATRIX),
        "--registry",
        str(REGISTRY),
        "--suite",
        str(SUITE),
        "--condition",
        "l1-minimax-m3-adaptive-development-v1",
        "--case",
        SMOKE_CASE_ID,
        "--database",
        str(database),
        "--artifacts-dir",
        str(artifacts),
    ]


def test_matrix_v2_minimax_fake_provider_cli_e2e_is_auditable_and_secret_free(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    secret = "sentinel-minimax-key-never-persist"
    provider = _FakeMiniMaxProvider()
    monkeypatch.setenv("MINIMAX_API_KEY", secret)
    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: provider,
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: False)
    database = tmp_path / "run.db"
    artifacts = tmp_path / "artifacts"

    assert main(_debug_args(database, artifacts)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert len(provider.requests) == 3
    request = provider.requests[0]
    assert request.generation["response_format"] == {"mode": "omitted"}
    artifact_path = Path(output["artifacts"]["json"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    manifest = artifact["manifest"]
    assert manifest["manifest_schema_version"] == "2"
    assert manifest["matrix"]["schema_version"] == "2"
    assert manifest["git_dirty"] is False
    assert len(manifest["treatment_fingerprint"]) == 64
    assert len(manifest["condition_fingerprint"]) == 64
    assert len(manifest["execution_policy_fingerprint"]) == 64
    assert len(manifest["run_configuration_fingerprint"]) == 64
    completed = [
        event
        for event in artifact["trace"]
        if event["event_type"] == "model_call_completed"
    ]
    assert len(completed) == 3
    assert all(
        event["payload"]["provider_request_id"] == "minimax-request-39"
        for event in completed
    )
    assert all(event["payload"]["usage"]["input_tokens"] == 1000 for event in completed)
    assert all(event["payload"]["reasoning_observation"]["present"] for event in completed)
    assert all("reasoning_output" not in event["payload"] for event in completed)
    assert [
        result["outcome"] for result in artifact["sample_results"]
    ] == [{"status": "scored"}] * 3
    assert all(
        result["context_assessment"]["input_tokens"] == 1000
        for result in artifact["sample_results"]
    )
    markdown = Path(output["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert "Treatment fingerprint" in markdown
    assert "Run configuration fingerprint" in markdown
    assert "Exact local input tokens: `1000`" in markdown
    assert "Provider request ID: `minimax-request-39`" in markdown
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_runs"
        ).fetchone() == ("completed",)
        assert connection.execute(
            "SELECT status FROM evaluation_sample_outcomes ORDER BY sample_sequence"
        ).fetchall() == [("scored",), ("scored",), ("scored",)]
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_reports"
        ).fetchone() == (3,)
        manifest_json = connection.execute(
            "SELECT manifest_json FROM evaluation_run_manifests"
        ).fetchone()[0]
        trace_json = "".join(
            row[0]
            for row in connection.execute(
                "SELECT payload_json FROM evaluation_trace_events ORDER BY sequence"
            )
        )
    persisted = (
        artifact_path.read_text(encoding="utf-8")
        + markdown
        + manifest_json
        + trace_json
    )
    assert secret not in persisted
    assert "private hidden reasoning must never be persisted" not in persisted


def test_matrix_v2_context_infeasible_makes_zero_provider_calls(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    provider = _FakeMiniMaxProvider(input_tokens=950000)
    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: provider,
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "b" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: True)
    database = tmp_path / "run.db"
    artifacts = tmp_path / "artifacts"

    assert main(_debug_args(database, artifacts)) == 1

    output = json.loads(capsys.readouterr().out)
    assert provider.requests == []
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert all(
        result["outcome"]["failure_code"] == "l1_context_infeasible"
        for result in artifact["sample_results"]
    )
    assert not any(
        event["event_type"] == "model_call_started" for event in artifact["trace"]
    )
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_sample_outcomes "
            "ORDER BY sample_sequence"
        ).fetchall() == [
            ("execution_failed", "l1_context_infeasible"),
            ("execution_failed", "l1_context_infeasible"),
            ("execution_failed", "l1_context_infeasible"),
        ]
