from __future__ import annotations

import io
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import devagentops.cli as cli
from devagentops.evaluation.execution import SampleIdentity
from devagentops.evaluation.progress import EvaluationProgressReporter
from devagentops.evaluation.trace import TraceRecorder


class _Clock:
    def __init__(self, *values: float) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


def _identity(
    *,
    case_id: str = "case-a",
    repeat_index: int = 0,
    sample_sequence: int = 1,
) -> SampleIdentity:
    return SampleIdentity(
        run_id="run-1",
        case_id=case_id,
        repeat_index=repeat_index,
        sample_sequence=sample_sequence,
    )


def test_trace_recorder_without_listener_preserves_historical_behavior() -> None:
    recorder = TraceRecorder("run-1")

    event = recorder.record(
        "sample_started",
        identity=_identity(),
        occurred_at="2026-08-14T00:00:00.000000Z",
        payload={"value": "original"},
    )

    assert event == {
        "run_id": "run-1",
        "sequence": 1,
        "event_type": "sample_started",
        "case_id": "case-a",
        "repeat_index": 0,
        "occurred_at": "2026-08-14T00:00:00.000000Z",
        "payload": {
            "value": "original",
            "sample_sequence": 1,
        },
    }
    assert recorder.snapshot() == (event,)


def test_trace_listener_is_copy_isolated_and_runs_outside_trace_lock() -> None:
    listener_lock_observations: list[bool] = []
    recorder_holder: dict[str, TraceRecorder] = {}

    def listener(event: dict) -> None:
        recorder = recorder_holder["recorder"]

        acquired = recorder._lock.acquire(blocking=False)
        listener_lock_observations.append(acquired)
        if acquired:
            recorder._lock.release()

        event["payload"]["nested"]["value"] = "listener-mutated"
        event["event_type"] = "listener-mutated"

    recorder = TraceRecorder(
        "run-1",
        event_listener=listener,
    )
    recorder_holder["recorder"] = recorder

    recorder.record(
        "sample_started",
        identity=_identity(),
        payload={
            "nested": {
                "value": "canonical",
            }
        },
    )

    stored = recorder.snapshot()[0]

    assert listener_lock_observations == [True]
    assert stored["event_type"] == "sample_started"
    assert stored["payload"]["nested"]["value"] == "canonical"


def test_progress_reporter_tracks_scored_sample_and_writes_one_line() -> None:
    stream = io.StringIO()
    clock = _Clock(
        0.0,  # reporter construction
        1.0,  # sample_started
        3.5,  # sample_completed
    )
    reporter = EvaluationProgressReporter(
        total_samples=3,
        max_case_concurrency=2,
        stream=stream,
        clock=clock,
    )

    reporter.on_event(
        {
            "event_type": "sample_started",
            "case_id": "case-a",
            "repeat_index": 0,
        }
    )

    assert reporter.snapshot() == {
        "total": 3,
        "completed": 0,
        "scored": 0,
        "failed": 0,
        "active": 1,
    }

    reporter.on_event(
        {
            "event_type": "sample_completed",
            "case_id": "case-a",
            "repeat_index": 0,
        }
    )

    assert reporter.snapshot() == {
        "total": 3,
        "completed": 1,
        "scored": 1,
        "failed": 0,
        "active": 0,
    }

    lines = stream.getvalue().splitlines()

    assert lines[0] == "Evaluation: 3 samples | concurrency=2"
    assert lines[1].startswith("[1/3] scored case-a repeat=0 2.5s")
    assert "scored=1" in lines[1]
    assert "failed=0" in lines[1]
    assert "active=0" in lines[1]
    assert "elapsed=00:00:03" in lines[1]


def test_progress_reporter_tracks_failures_and_ignores_duplicate_terminal_event() -> None:
    stream = io.StringIO()
    clock = _Clock(
        0.0,
        1.0,
        2.0,
        3.0,
    )
    reporter = EvaluationProgressReporter(
        total_samples=1,
        max_case_concurrency=1,
        stream=stream,
        clock=clock,
    )

    started = {
        "event_type": "sample_started",
        "case_id": "case-a",
        "repeat_index": 0,
    }
    failed = {
        "event_type": "sample_failed",
        "case_id": "case-a",
        "repeat_index": 0,
    }

    reporter.on_event(started)
    reporter.on_event(failed)
    reporter.on_event(failed)

    assert reporter.snapshot() == {
        "total": 1,
        "completed": 1,
        "scored": 0,
        "failed": 1,
        "active": 0,
    }

    lines = stream.getvalue().splitlines()
    assert len(lines) == 2
    assert lines[1].startswith("[1/1] failed case-a repeat=0")


def test_progress_reporter_is_thread_safe_under_concurrent_events() -> None:
    sample_count = 40
    stream = io.StringIO()
    reporter = EvaluationProgressReporter(
        total_samples=sample_count,
        max_case_concurrency=8,
        stream=stream,
    )

    started_events = [
        {
            "event_type": "sample_started",
            "case_id": f"case-{index}",
            "repeat_index": 0,
        }
        for index in range(sample_count)
    ]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reporter.on_event, started_events))

    assert reporter.snapshot()["active"] == sample_count

    terminal_events = [
        {
            "event_type": (
                "sample_completed"
                if index % 2 == 0
                else "sample_failed"
            ),
            "case_id": f"case-{index}",
            "repeat_index": 0,
        }
        for index in range(sample_count)
    ]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reporter.on_event, terminal_events))

    assert reporter.snapshot() == {
        "total": sample_count,
        "completed": sample_count,
        "scored": sample_count // 2,
        "failed": sample_count // 2,
        "active": 0,
    }

    lines = stream.getvalue().splitlines()

    # One header plus exactly one terminal record per Sample.
    assert len(lines) == sample_count + 1
    assert all(line.startswith("[") for line in lines[1:])


def test_progress_reporter_never_propagates_observability_failure() -> None:
    class _BrokenStream:
        def write(self, text: str) -> None:
            raise OSError("simulated terminal failure")

        def flush(self) -> None:
            raise OSError("simulated terminal failure")

    reporter = EvaluationProgressReporter(
        total_samples=1,
        max_case_concurrency=1,
        stream=_BrokenStream(),
    )

    reporter.on_event(
        {
            "event_type": "sample_started",
            "case_id": "case-a",
            "repeat_index": 0,
        }
    )
    reporter.on_event(
        {
            "event_type": "sample_completed",
            "case_id": "case-a",
            "repeat_index": 0,
        }
    )

    assert reporter.snapshot() == {
        "total": 1,
        "completed": 1,
        "scored": 1,
        "failed": 0,
        "active": 0,
    }


def test_cli_progress_on_stderr_preserves_single_json_stdout(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    def fake_run_evaluation(**kwargs):
        print(
            "[1/1] scored case-a repeat=0 1.0s",
            file=__import__("sys").stderr,
        )
        return {
            "status": "completed",
            "run_id": "run-1",
        }

    monkeypatch.setattr(cli, "run_evaluation", fake_run_evaluation)

    exit_code = cli.main(
        [
            "eval",
            "run",
            "--matrix",
            str(tmp_path / "matrix.json"),
            "--registry",
            str(tmp_path / "registry.json"),
            "--suite",
            str(tmp_path / "suite.json"),
            "--condition",
            "condition-a",
            "--database",
            str(tmp_path / "db.sqlite"),
            "--artifacts-dir",
            str(tmp_path / "artifacts"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == {
        "status": "completed",
        "run_id": "run-1",
    }
    assert captured.out.count("\n") == 1
    assert "[1/1] scored case-a" in captured.err
