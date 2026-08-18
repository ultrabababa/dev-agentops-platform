import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

import devagentops.evaluation.debug_v2 as evaluation_debug_v2
from devagentops.cli import main
from devagentops.evaluation.artifacts import EvaluationArtifactError
from devagentops.evaluation.execution import (
    ExecutionPolicy,
    SampleResult,
    execute_sample_plan,
    plan_samples,
)
from devagentops.evaluation.trace import TraceRecorder
from devagentops.evaluation.matrix import load_evaluation_matrix
from devagentops.providers.contracts import ExactTokenCount
from devagentops.providers.openai_compatible import OpenAICompatibleTransportError
from devagentops.runtime.messages import (
    AssistantMessage,
    TextContent,
    ThinkingContent,
    TokenUsage,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATRIX_V2 = PROJECT_ROOT / "evaluation/matrices/l1-minimax-m3-development-v2.json"
REGISTRY = PROJECT_ROOT / "components/registry.json"
SUITE = PROJECT_ROOT / "evaluation/suites/triage-v1/suite.json"


@dataclass(frozen=True)
class _SuiteCase:
    case_id: str


def test_checked_in_matrix_uses_3_6_0_without_changing_capability_identity() -> None:
    matrix = load_evaluation_matrix(MATRIX_V2)
    condition = matrix.conditions[0]

    assert condition.effective_condition["execution_policy"] == {
        "repeat_count": 3,
        "max_case_concurrency": 6,
        "retry_count": 0,
        "request_timeout_seconds": 600,
    }
    assert condition.treatment_fingerprint == (
        "1d6387a25f7722c30b36be82eaf5f7699550472a9b136db5964a783c3da758f4"
    )
    assert condition.condition_fingerprint == (
        "c199208feb41748fd67095512871bcd406d108ed3444b98854adecf0aa1fcb2a"
    )
    assert condition.execution_policy_fingerprint != (
        "0bc0cd052e9dee50caf1fa84f808159d965d3bf78980ef3e9b399b7fa9cfc3e4"
    )


def test_sample_plan_is_unique_and_deterministic_by_case_then_repeat() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=(_SuiteCase("case-a"), _SuiteCase("case-b")),
        repeat_count=3,
    )

    assert [sample.identity.as_tuple() for sample in planned] == [
        ("run-41", "case-a", 0),
        ("run-41", "case-a", 1),
        ("run-41", "case-a", 2),
        ("run-41", "case-b", 0),
        ("run-41", "case-b", 1),
        ("run-41", "case-b", 2),
    ]
    assert [sample.identity.sample_sequence for sample in planned] == list(range(1, 7))
    assert len({sample.identity.as_tuple() for sample in planned}) == 6


def test_scheduler_serializes_same_case_and_overlaps_different_cases() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=(_SuiteCase("case-a"), _SuiteCase("case-b")),
        repeat_count=4,
    )
    lock = threading.Lock()
    active_by_case: dict[str, int] = {}
    active_total = 0
    max_active_total = 0
    repeat_order: dict[str, list[int]] = {"case-a": [], "case-b": []}
    overlap = threading.Barrier(2)

    class FakeConditionExecutor:
        def execute_sample(self, sample, recorder):
            nonlocal active_total, max_active_total
            identity = sample.identity
            with lock:
                assert active_by_case.get(identity.case_id, 0) == 0
                active_by_case[identity.case_id] = 1
                active_total += 1
                max_active_total = max(max_active_total, active_total)
                repeat_order[identity.case_id].append(identity.repeat_index)
            try:
                if identity.repeat_index == 0:
                    overlap.wait(timeout=2)
                time.sleep(0.005)
                return SampleResult(
                    identity=identity,
                    status="scored",
                    data={"outcome": {"status": "scored"}},
                )
            finally:
                with lock:
                    active_total -= 1
                    active_by_case[identity.case_id] = 0

    results = execute_sample_plan(
        planned,
        executor=FakeConditionExecutor(),
        recorder=TraceRecorder("run-41"),
        policy=ExecutionPolicy(
            repeat_count=4,
            max_case_concurrency=2,
            retry_count=0,
        ),
    )

    assert repeat_order == {"case-a": [0, 1, 2, 3], "case-b": [0, 1, 2, 3]}
    assert max_active_total == 2
    assert [result.identity.sample_sequence for result in results] == list(range(1, 9))


def test_failed_sample_does_not_stop_later_repeats_or_other_cases() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=(_SuiteCase("case-a"), _SuiteCase("case-b")),
        repeat_count=3,
    )
    executed: list[tuple[str, int]] = []
    lock = threading.Lock()
    recorder = TraceRecorder("run-41")

    class FailingConditionExecutor:
        def execute_sample(self, sample, event_recorder):
            identity = sample.identity
            with lock:
                executed.append((identity.case_id, identity.repeat_index))
            if identity.case_id == "case-a" and identity.repeat_index == 0:
                return SampleResult(
                    identity=identity,
                    status="execution_failed",
                    data={
                        "outcome": {
                            "status": "execution_failed",
                            "failure_code": "expected_provider_failure",
                            "failure_stage": "model_provider",
                            "failure_message": "sanitized failure",
                        },
                        "quality_metrics": None,
                    },
                )
            return SampleResult(
                identity=identity,
                status="scored",
                data={"outcome": {"status": "scored"}},
            )

    results = execute_sample_plan(
        planned,
        executor=FailingConditionExecutor(),
        recorder=recorder,
        policy=ExecutionPolicy(3, 2, 0),
    )

    assert len(results) == 6
    assert results[0].status == "execution_failed"
    assert results[0].data["quality_metrics"] is None
    assert set(executed) == {
        ("case-a", 0), ("case-a", 1), ("case-a", 2),
        ("case-b", 0), ("case-b", 1), ("case-b", 2),
    }
    terminal = [
        event
        for event in recorder.snapshot()
        if event["event_type"] in {"sample_completed", "sample_failed"}
    ]
    assert len(terminal) == 6
    assert sum(event["event_type"] == "sample_failed" for event in terminal) == 1


def test_reversed_case_completion_does_not_change_sample_result_order() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=(_SuiteCase("slow-case"), _SuiteCase("fast-case")),
        repeat_count=2,
    )

    class ReversedCompletionExecutor:
        def execute_sample(self, sample, recorder):
            if sample.identity.case_id == "slow-case":
                time.sleep(0.02)
            return SampleResult(
                sample.identity,
                "scored",
                {"outcome": {"status": "scored"}},
            )

    results = execute_sample_plan(
        planned,
        executor=ReversedCompletionExecutor(),
        recorder=TraceRecorder("run-41"),
        policy=ExecutionPolicy(2, 2, 0),
    )

    assert [result.identity.case_id for result in results] == [
        "slow-case", "slow-case", "fast-case", "fast-case"
    ]
    assert [result.identity.sample_sequence for result in results] == [1, 2, 3, 4]


def test_scheduler_limits_active_cases_when_more_cases_are_ready() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=tuple(_SuiteCase(f"case-{index}") for index in range(5)),
        repeat_count=2,
    )
    lock = threading.Lock()
    active = 0
    maximum_active = 0

    class BoundedExecutor:
        def execute_sample(self, sample, recorder):
            nonlocal active, maximum_active
            with lock:
                active += 1
                maximum_active = max(maximum_active, active)
            try:
                time.sleep(0.01)
                return SampleResult(
                    sample.identity,
                    "scored",
                    {"outcome": {"status": "scored"}},
                )
            finally:
                with lock:
                    active -= 1

    results = execute_sample_plan(
        planned,
        executor=BoundedExecutor(),
        recorder=TraceRecorder("run-41"),
        policy=ExecutionPolicy(2, 2, 0),
    )

    assert len(results) == 10
    assert maximum_active == 2


def test_concurrent_trace_sequences_are_unique_and_monotonic() -> None:
    recorder = TraceRecorder("run-41")
    planned = plan_samples(
        run_id="run-41",
        suite_cases=tuple(_SuiteCase(f"case-{index}") for index in range(8)),
        repeat_count=5,
    )

    class RecordingConditionExecutor:
        def execute_sample(self, sample, event_recorder):
            event_recorder.record(
                "condition_event",
                identity=sample.identity,
                payload={"value": sample.identity.sample_sequence},
            )
            return SampleResult(sample.identity, "scored", {"outcome": {"status": "scored"}})

    execute_sample_plan(
        planned,
        executor=RecordingConditionExecutor(),
        recorder=recorder,
        policy=ExecutionPolicy(5, 4, 0),
    )

    events = recorder.snapshot()
    sequences = [event["sequence"] for event in events]
    assert sequences == list(range(1, len(events) + 1))
    assert len(sequences) == len(set(sequences))
    assert all(
        event["repeat_index"] is not None
        for event in events
        if event["event_type"] != "run_started"
    )


def test_scheduler_does_not_convert_programmer_errors_to_sample_failures() -> None:
    planned = plan_samples(
        run_id="run-41",
        suite_cases=(_SuiteCase("case-a"),),
        repeat_count=1,
    )

    class BrokenExecutor:
        def execute_sample(self, sample, recorder):
            raise RuntimeError("programmer bug")

    with pytest.raises(RuntimeError, match="programmer bug"):
        execute_sample_plan(
            planned,
            executor=BrokenExecutor(),
            recorder=TraceRecorder("run-41"),
            policy=ExecutionPolicy(1, 1, 0),
        )


@pytest.mark.parametrize(
    ("policy", "message"),
    [
        (ExecutionPolicy(0, 1, 0), "repeat_count"),
        (ExecutionPolicy(1, 0, 0), "max_case_concurrency"),
        (ExecutionPolicy(1, 1, 1), "retry_count"),
    ],
)
def test_execution_engine_rejects_invalid_or_retrying_policy(
    policy: ExecutionPolicy,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        execute_sample_plan(
            (),
            executor=object(),
            recorder=TraceRecorder("run-41"),
            policy=policy,
        )


def test_repository_cli_persists_repeated_samples_without_flattening(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    selected_case_ids = [
        "bugswarm-traccar-170287308",
        "bugswarm-retrofit-113047638",
    ]
    providers = []

    class FakeProvider:
        def __init__(self, provider_index: int) -> None:
            self.provider_index = provider_index
            self.complete_calls = 0

        def count_input_tokens(self, request):
            return ExactTokenCount(1000, "exact-fake-count")

        def complete(self, request):
            self.complete_calls += 1
            return AssistantMessage(
                content=(
                    ThinkingContent("raw-reasoning-sentinel-must-not-persist"),
                    TextContent("not-json-but-still-a-scored-observation"),
                ),
                response_id=f"request-{self.provider_index}",
                response_model="MiniMax-M3",
                usage=TokenUsage(input_tokens=1000, output_tokens=25),
                stop_reason="stop",
                raw_stop_reason="stop",
                latency_ms=10,
            )

    def provider_factory(**kwargs):
        provider = FakeProvider(len(providers))
        providers.append(provider)
        return provider

    monkeypatch.setenv("MINIMAX_API_KEY", "secret-sentinel-must-not-persist")
    monkeypatch.setattr(evaluation_debug_v2, "create_minimax_provider", provider_factory)
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: False)
    database = tmp_path / "evaluation.db"
    artifacts = tmp_path / "artifacts"
    args = [
        "eval", "debug",
        "--matrix", str(MATRIX_V2),
        "--registry", str(REGISTRY),
        "--suite", str(SUITE),
        "--condition", "l1-minimax-m3-adaptive-development-v1",
        "--database", str(database),
        "--artifacts-dir", str(artifacts),
    ]
    for case_id in selected_case_ids:
        args.extend(["--case", case_id])

    assert main(args) == 0

    output = json.loads(capsys.readouterr().out)
    artifact_path = Path(output["artifacts"]["json"])
    markdown_path = Path(output["artifacts"]["markdown"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    samples = artifact["sample_results"]
    assert output["status"] == "completed"
    assert len(providers) == 6
    assert all(provider.complete_calls == 1 for provider in providers)
    assert [
        (sample["case_id"], sample["repeat_index"], sample["sample_sequence"])
        for sample in samples
    ] == [
        (selected_case_ids[0], 0, 1),
        (selected_case_ids[0], 1, 2),
        (selected_case_ids[0], 2, 3),
        (selected_case_ids[1], 0, 4),
        (selected_case_ids[1], 1, 5),
        (selected_case_ids[1], 2, 6),
    ]
    assert artifact["metric_preview"]["status"] == "aggregation_deferred"
    terminal_events = [
        event
        for event in artifact["trace"]
        if event["event_type"] in {"sample_completed", "sample_failed"}
    ]
    assert len(terminal_events) == 6
    assert all(event["repeat_index"] in {0, 1, 2} for event in terminal_events)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_runs"
        ).fetchone() == ("completed",)
        assert connection.execute(
            "SELECT case_id, repeat_index, sample_sequence, status "
            "FROM evaluation_sample_outcomes ORDER BY sample_sequence"
        ).fetchall() == [
            (sample["case_id"], sample["repeat_index"], sample["sample_sequence"], "scored")
            for sample in samples
        ]
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_reports"
        ).fetchone() == (6,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_scores"
        ).fetchone() == (6,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_case_outcomes"
        ).fetchone() == (0,)
        persisted = "".join(
            str(value)
            for table, column in [
                ("evaluation_run_manifests", "manifest_json"),
                ("evaluation_trace_events", "payload_json"),
                ("evaluation_sample_reports", "report_json"),
            ]
            for (value,) in connection.execute(f"SELECT {column} FROM {table}")
        )
    persisted += artifact_path.read_text(encoding="utf-8")
    persisted += markdown_path.read_text(encoding="utf-8")
    assert "secret-sentinel-must-not-persist" not in persisted
    assert "raw-reasoning-sentinel-must-not-persist" not in persisted
    assert "Reasoning metadata" in markdown_path.read_text(encoding="utf-8")


def test_context_and_provider_failures_are_isolated_and_persisted_per_sample(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    case_a = "bugswarm-traccar-170287308"
    case_b = "bugswarm-retrofit-113047638"
    count_index = {case_a: 0, case_b: 0}
    complete_calls = 0
    lock = threading.Lock()

    class FaultInjectingProvider:
        def __init__(self) -> None:
            self.should_fail_provider = False

        def count_input_tokens(self, request):
            content = request.messages[0].content
            case_id = case_a if case_a in content else case_b
            with lock:
                repeat_index = count_index[case_id]
                count_index[case_id] += 1
            if case_id == case_a and repeat_index == 0:
                return ExactTokenCount(950000, "exact-fake-count")
            if case_id == case_b and repeat_index == 0:
                self.should_fail_provider = True
            return ExactTokenCount(1000, "exact-fake-count")

        def complete(self, request):
            nonlocal complete_calls
            with lock:
                complete_calls += 1
            if self.should_fail_provider:
                raise OpenAICompatibleTransportError(
                    "sanitized provider failure",
                    code="model_provider_transport_error",
                )
            return AssistantMessage(
                content=(TextContent("invalid-observation-is-still-scored"),),
                response_id="request-success",
                response_model="MiniMax-M3",
                usage=TokenUsage(input_tokens=1000, output_tokens=10),
                stop_reason="stop",
                raw_stop_reason="stop",
                latency_ms=10,
            )

    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: FaultInjectingProvider(),
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "b" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: False)
    database = tmp_path / "evaluation.db"
    artifacts = tmp_path / "artifacts"

    assert main([
        "eval", "debug",
        "--matrix", str(MATRIX_V2),
        "--registry", str(REGISTRY),
        "--suite", str(SUITE),
        "--condition", "l1-minimax-m3-adaptive-development-v1",
        "--case", case_a,
        "--case", case_b,
        "--database", str(database),
        "--artifacts-dir", str(artifacts),
    ]) == 1

    output = json.loads(capsys.readouterr().out)
    artifact = json.loads(Path(output["artifacts"]["json"]).read_text())
    assert output["status"] == "completed_with_sample_failures"
    assert complete_calls == 5
    assert count_index == {case_a: 3, case_b: 3}
    assert [sample["outcome"]["status"] for sample in artifact["sample_results"]] == [
        "execution_failed", "scored", "scored",
        "execution_failed", "scored", "scored",
    ]
    assert artifact["sample_results"][0]["outcome"]["failure_stage"] == (
        "context_feasibility"
    )
    assert artifact["sample_results"][3]["outcome"]["failure_stage"] == (
        "model_provider"
    )
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_outcomes"
        ).fetchone() == (6,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_reports"
        ).fetchone() == (4,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_scores"
        ).fetchone() == (4,)
        assert connection.execute(
            "SELECT metrics_json FROM evaluation_sample_scores "
            "WHERE case_id = ? AND repeat_index = 0",
            (case_a,),
        ).fetchone() is None


def test_artifact_failure_marks_run_failed_and_removes_sample_rows(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    class SuccessfulProvider:
        def count_input_tokens(self, request):
            return ExactTokenCount(1000, "exact-fake-count")

        def complete(self, request):
            return AssistantMessage(
                content=(TextContent("invalid-but-scored"),),
                response_id="request-success",
                response_model="MiniMax-M3",
                usage=TokenUsage(input_tokens=1000),
                stop_reason="stop",
                raw_stop_reason="stop",
                latency_ms=1,
            )

    monkeypatch.setattr(
        evaluation_debug_v2,
        "create_minimax_provider",
        lambda **kwargs: SuccessfulProvider(),
    )
    monkeypatch.setattr(evaluation_debug_v2, "_code_revision", lambda: "c" * 40)
    monkeypatch.setattr(evaluation_debug_v2, "_git_dirty", lambda: False)
    monkeypatch.setattr(
        evaluation_debug_v2,
        "write_evaluation_artifacts",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            EvaluationArtifactError("artifact unavailable")
        ),
    )
    database = tmp_path / "evaluation.db"

    assert main([
        "eval", "debug",
        "--matrix", str(MATRIX_V2),
        "--registry", str(REGISTRY),
        "--suite", str(SUITE),
        "--condition", "l1-minimax-m3-adaptive-development-v1",
        "--case", "bugswarm-traccar-170287308",
        "--database", str(database),
        "--artifacts-dir", str(tmp_path / "artifacts"),
    ]) == 2

    capsys.readouterr()
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT status, failure_code FROM evaluation_runs"
        ).fetchone() == ("failed", "artifact_write_failed")
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_outcomes"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_reports"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM evaluation_sample_scores"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT event_type FROM evaluation_trace_events ORDER BY sequence"
        ).fetchall()[-1] == ("failure",)
