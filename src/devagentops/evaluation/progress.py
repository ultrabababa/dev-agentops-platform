from __future__ import annotations

import sys
import threading
import time
from typing import Any, Callable, TextIO


class EvaluationProgressReporter:
    """Thread-safe stderr progress projection over evaluation Trace events."""

    def __init__(
        self,
        *,
        total_samples: int,
        max_case_concurrency: int,
        stream: TextIO | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if total_samples < 1:
            raise ValueError("total_samples must be a positive integer")
        if max_case_concurrency < 1:
            raise ValueError("max_case_concurrency must be a positive integer")

        self._total_samples = total_samples
        self._max_case_concurrency = max_case_concurrency
        self._stream = stream if stream is not None else sys.stderr
        self._clock = clock
        self._lock = threading.Lock()

        self._run_started_at = self._clock()
        self._sample_started_at: dict[tuple[str, int], float] = {}
        self._terminal_samples: set[tuple[str, int]] = set()

        self._completed = 0
        self._scored = 0
        self._failed = 0
        self._active = 0

        self._safe_write(
            f"Evaluation: {self._total_samples} samples"
            f" | concurrency={self._max_case_concurrency}\n"
        )

    def on_event(self, event: dict[str, Any]) -> None:
        """Consume one Trace event without affecting evaluation semantics."""
        try:
            self._on_event(event)
        except Exception:
            # Progress is an observability side channel. It must never invalidate
            # or alter the underlying evaluation run.
            return

    def _on_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")
        if event_type not in {
            "sample_started",
            "sample_completed",
            "sample_failed",
        }:
            return

        case_id = event.get("case_id")
        repeat_index = event.get("repeat_index")
        if not isinstance(case_id, str) or not isinstance(repeat_index, int):
            return

        key = (case_id, repeat_index)
        now = self._clock()

        with self._lock:
            if event_type == "sample_started":
                if (
                    key in self._sample_started_at
                    or key in self._terminal_samples
                ):
                    return

                self._sample_started_at[key] = now
                self._active += 1
                return

            if key in self._terminal_samples:
                return

            self._terminal_samples.add(key)
            started_at = self._sample_started_at.pop(key, None)

            if started_at is not None and self._active > 0:
                self._active -= 1

            self._completed += 1

            if event_type == "sample_completed":
                self._scored += 1
                status = "scored"
            else:
                self._failed += 1
                status = "failed"

            sample_elapsed = (
                max(0.0, now - started_at)
                if started_at is not None
                else None
            )
            run_elapsed = max(0.0, now - self._run_started_at)

            width = len(str(self._total_samples))
            sample_elapsed_text = (
                f"{sample_elapsed:.1f}s"
                if sample_elapsed is not None
                else "n/a"
            )

            line = (
                f"[{self._completed:>{width}}/{self._total_samples}] "
                f"{status:<6} "
                f"{case_id} "
                f"repeat={repeat_index} "
                f"{sample_elapsed_text}"
                f" | scored={self._scored}"
                f" failed={self._failed}"
                f" active={self._active}"
                f" elapsed={_format_elapsed(run_elapsed)}\n"
            )

            # Keep one terminal progress record atomic with respect to other
            # worker threads.
            self._safe_write(line)

    def snapshot(self) -> dict[str, int]:
        """Return current counters for tests/diagnostics only."""
        with self._lock:
            return {
                "total": self._total_samples,
                "completed": self._completed,
                "scored": self._scored,
                "failed": self._failed,
                "active": self._active,
            }

    def _safe_write(self, text: str) -> None:
        try:
            self._stream.write(text)
            self._stream.flush()
        except Exception:
            # Console observability must not affect evaluation execution.
            return


def _format_elapsed(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
