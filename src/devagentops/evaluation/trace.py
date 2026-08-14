from __future__ import annotations

import threading
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Callable

from devagentops.evaluation.execution import SampleIdentity


EventListener = Callable[[dict[str, Any]], None]


class TraceRecorder:
    """Run-scoped, thread-safe recorder for concurrent sample execution."""

    def __init__(
        self,
        run_id: str,
        *,
        event_listener: EventListener | None = None,
    ) -> None:
        self._run_id = run_id
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []
        self._event_listener = event_listener

    def record(
        self,
        event_type: str,
        *,
        identity: SampleIdentity | None = None,
        case_id: str | None = None,
        occurred_at: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event_payload = dict(payload or {})

        if identity is not None:
            if case_id is not None and case_id != identity.case_id:
                raise ValueError("trace case_id does not match sample identity")

            case_id = identity.case_id
            event_payload.setdefault(
                "sample_sequence",
                identity.sample_sequence,
            )

        with self._lock:
            event = {
                "run_id": self._run_id,
                "sequence": len(self._events) + 1,
                "event_type": event_type,
                "case_id": case_id,
                "repeat_index": (
                    identity.repeat_index if identity is not None else None
                ),
                "occurred_at": occurred_at or _now(),
                "payload": event_payload,
            }

            self._events.append(event)

            # The listener receives an independent deep copy so it cannot
            # mutate the canonical stored Trace event.
            listener_event = (
                deepcopy(event)
                if self._event_listener is not None
                else None
            )

            # Preserve the historical record() return shape/behavior.
            result = dict(event)

        # Never invoke external/listener code while holding the Trace lock.
        if listener_event is not None:
            self._event_listener(listener_event)

        return result

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(dict(event) for event in self._events)


def _now() -> str:
    return (
        datetime.now(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
