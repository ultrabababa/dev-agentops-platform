from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Generic, Literal, Protocol, Sequence, TypeVar


class SuiteCaseLike(Protocol):
    case_id: str


SuiteCaseT = TypeVar("SuiteCaseT", bound=SuiteCaseLike)


@dataclass(frozen=True)
class SampleIdentity:
    run_id: str
    case_id: str
    repeat_index: int
    sample_sequence: int

    def as_tuple(self) -> tuple[str, str, int]:
        return (self.run_id, self.case_id, self.repeat_index)


@dataclass(frozen=True)
class PlannedSample(Generic[SuiteCaseT]):
    identity: SampleIdentity
    suite_case: SuiteCaseT


@dataclass(frozen=True)
class SampleResult:
    identity: SampleIdentity
    status: Literal["scored", "execution_failed"]
    data: dict[str, Any]
    trajectory: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ExecutionPolicy:
    repeat_count: int
    max_case_concurrency: int
    retry_count: int

    def validate(self) -> None:
        if self.repeat_count < 1:
            raise ValueError("repeat_count must be a positive integer")
        if self.max_case_concurrency < 1:
            raise ValueError("max_case_concurrency must be a positive integer")
        if self.retry_count != 0:
            raise ValueError("retry_count other than zero is not supported")


class ConditionExecutor(Protocol):
    def execute_sample(
        self,
        sample: PlannedSample,
        recorder: EventRecorder,
    ) -> SampleResult: ...


class EventRecorder(Protocol):
    def record(
        self,
        event_type: str,
        *,
        identity: SampleIdentity | None = None,
        case_id: str | None = None,
        occurred_at: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


def plan_samples(
    *,
    run_id: str,
    suite_cases: Sequence[SuiteCaseT],
    repeat_count: int,
) -> tuple[PlannedSample[SuiteCaseT], ...]:
    if repeat_count < 1:
        raise ValueError("repeat_count must be a positive integer")
    planned: list[PlannedSample[SuiteCaseT]] = []
    for suite_case in suite_cases:
        for repeat_index in range(repeat_count):
            planned.append(
                PlannedSample(
                    identity=SampleIdentity(
                        run_id=run_id,
                        case_id=suite_case.case_id,
                        repeat_index=repeat_index,
                        sample_sequence=len(planned) + 1,
                    ),
                    suite_case=suite_case,
                )
            )
    return tuple(planned)


def execute_sample_plan(
    planned_samples: Sequence[PlannedSample],
    *,
    executor: ConditionExecutor,
    recorder: EventRecorder,
    policy: ExecutionPolicy,
) -> tuple[SampleResult, ...]:
    policy.validate()
    if not planned_samples:
        return ()
    samples_by_case: dict[str, list[PlannedSample]] = defaultdict(list)
    seen_identities: set[tuple[str, str, int]] = set()
    for expected_sequence, sample in enumerate(planned_samples, start=1):
        if sample.identity.sample_sequence != expected_sequence:
            raise ValueError("sample plan sequence must be contiguous and deterministic")
        if sample.identity.as_tuple() in seen_identities:
            raise ValueError("sample plan contains a duplicate sample identity")
        seen_identities.add(sample.identity.as_tuple())
        samples_by_case[sample.identity.case_id].append(sample)
    canonical_plan = [
        sample for case_samples in samples_by_case.values() for sample in case_samples
    ]
    if canonical_plan != list(planned_samples):
        raise ValueError("sample plan must group Cases in deterministic Suite order")
    if any(
        [sample.identity.repeat_index for sample in case_samples]
        != list(range(policy.repeat_count))
        for case_samples in samples_by_case.values()
    ):
        raise ValueError("sample plan repeats do not match execution policy")

    def execute_case(samples: list[PlannedSample]) -> list[SampleResult]:
        results: list[SampleResult] = []
        for sample in samples:
            recorder.record("sample_started", identity=sample.identity)
            result = executor.execute_sample(sample, recorder)
            if result.identity != sample.identity:
                raise ValueError(
                    "Condition executor returned a different sample identity"
                )
            recorder.record(
                "sample_completed" if result.status == "scored" else "sample_failed",
                identity=sample.identity,
                payload={"status": result.status},
            )
            results.append(result)
        return results

    completed: list[SampleResult] = []
    with ThreadPoolExecutor(
        max_workers=min(policy.max_case_concurrency, len(samples_by_case)),
        thread_name_prefix="evaluation-case",
    ) as pool:
        futures = [
            pool.submit(execute_case, samples)
            for samples in samples_by_case.values()
        ]
        for future in as_completed(futures):
            completed.extend(future.result())
    return tuple(sorted(completed, key=lambda result: result.identity.sample_sequence))
