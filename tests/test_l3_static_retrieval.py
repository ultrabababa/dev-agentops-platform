from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from devagentops.conditions.l1.development_output_contract import (
    CANONICALIZING_OUTPUT_CONTRACT_VERSION,
    output_contract_prompt_suffix,
)
from devagentops.conditions.l3.executor import ConfiguredL3ConditionExecutor
from devagentops.conditions.l3.static_retrieval_v1 import (
    ConfiguredL3Treatment,
    RUNTIME_INPUT_SERIALIZATION_VERSION,
    serialize_static_retrieval_runtime_input,
)
from devagentops.evaluation.components import (
    ComponentManifest,
    component_fingerprint,
    resolve_frozen_component_manifest,
)
from devagentops.evaluation.execution import PlannedSample, SampleIdentity
from devagentops.evaluation.matrix import EvaluationMatrixError, load_evaluation_matrix
from devagentops.evaluation.run_v2 import run_formal_evaluation_v2
from devagentops.evaluation.suite import load_evaluation_suite
from devagentops.evaluation.trace import TraceRecorder
from devagentops.providers.contracts import ExactTokenCount
from devagentops.retrieval.bm25_v1 import bm25_query_hits
from devagentops.retrieval.chunking import chunk_physical_text
from devagentops.retrieval.fusion import reciprocal_rank_fusion
from devagentops.retrieval.packing import pack_selected_hits
from devagentops.retrieval.signals import extract_log_queries
from devagentops.retrieval.static_v1 import (
    STATIC_RETRIEVER_BEHAVIOR,
    run_static_retrieval,
)
from devagentops.retrieval.tokenization import code_aware_tokens
from devagentops.retrieval.types import FusedHit, RetrievalQuery
from devagentops.runtime.messages import AssistantMessage, TextContent, TokenUsage
from devagentops.runtime.workspace import RuntimeCaseWorkspace


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "components/registry.json"
TINY_SUITE = ROOT / "tests/fixtures/evaluation/tiny-suite.json"
L3_MATRIX = ROOT / "evaluation/matrices/l3-minimax-m3-canonicalized-v1.json"
RETRIEVER_VERSION = "l3-static-bm25-multi-query-rrf-v1"


def _lines(count: int, prefix: str = "line") -> str:
    return "".join(f"{prefix} {index}\n" for index in range(1, count + 1))


def _query(text: str, *, query_id: str = "query-1", pool: str = "log"):
    return RetrievalQuery(
        query_id=query_id,
        pool=pool,  # type: ignore[arg-type]
        signal_family="diagnostic",
        normalized_text=text,
        source_path="physical-artifacts/raw.log",
        start_line=1,
        end_line=1,
        specificity=2,
    )


def test_fixed_line_chunks_use_100_20_boundaries_and_never_cross_files() -> None:
    first = chunk_physical_text(
        _lines(205),
        source_kind="raw_log",
        source_path="physical-artifacts/raw.log",
    )
    second = chunk_physical_text(
        _lines(50, "repo"),
        source_kind="repository_file",
        source_path="physical-artifacts/repository/src/example.py",
        repository_relative_path="src/example.py",
    )

    assert [(item.start_line, item.end_line) for item in first] == [
        (1, 100),
        (81, 180),
        (161, 205),
    ]
    assert [(item.start_line, item.end_line) for item in second] == [(1, 50)]
    assert {item.source_path for item in first} == {"physical-artifacts/raw.log"}
    assert {item.source_path for item in second} == {
        "physical-artifacts/repository/src/example.py"
    }
    assert first[-1].content == "".join(
        f"line {index}\n" for index in range(161, 206)
    )


def test_code_aware_tokenizer_preserves_compounds_and_splits_code_boundaries() -> None:
    tokens = code_aware_tokens(
        "FooService.java retry_on_error retryOnError com.foo.Bar the runs runs"
    )

    assert {"fooservice.java", "fooservice", "foo", "service", "java"} <= set(tokens)
    assert {"retry_on_error", "retry", "on", "error"} <= set(tokens)
    assert {"retryonerror", "com.foo.bar", "com", "bar", "the", "runs"} <= set(tokens)
    assert "run" not in tokens
    assert tokens.count("runs") == 2


def test_signal_selection_keeps_latest_duplicate_prioritizes_specificity_and_caps() -> None:
    text = "\n".join(
        [
            "ERROR duplicate diagnostic payload",
            "ERROR specific message one",
            "ERROR specific message two",
            "ERROR specific message three",
            "ERROR specific message four",
            "ERROR specific message five",
            "ERROR specific message six",
            "build failed",
            "ERROR duplicate diagnostic payload",
        ]
    )

    queries = extract_log_queries(
        text,
        source_path="physical-artifacts/raw.log",
        per_signal_type_cap=5,
    )
    messages = [
        item for item in queries
        if item.signal_family == "error_or_failure_message"
    ]

    assert len(messages) == 5
    assert all(item.specificity == 1 for item in messages)
    duplicate = next(
        item for item in messages
        if item.normalized_text == "error duplicate diagnostic payload"
    )
    assert duplicate.start_line == 9
    assert all(item.normalized_text != "build failed" for item in messages)
    assert [item.start_line for item in messages] == sorted(
        (item.start_line for item in messages), reverse=True
    )


def test_failed_test_identifier_excludes_passed_tests_before_latest_first_cap() -> None:
    text = "\n".join(
        [
            "tests/test_api.py::test_failed_oldest FAILED",
            "tests/test_api.py::test_failed_two FAILED",
            "tests/test_api.py::test_failed_three FAILED",
            "tests/test_api.py::test_passed_late PASSED",
            "tests/test_api.py::test_failed_four FAILED",
            "tests/test_api.py::test_failed_five FAILED",
            "tests/test_api.py::test_failed_latest FAILED",
            "tests/test_api.py::test_passed_latest PASSED",
        ]
    )

    queries = extract_log_queries(
        text,
        source_path="physical-artifacts/raw.log",
        per_signal_type_cap=5,
    )
    failed_tests = [
        item for item in queries if item.signal_family == "failed_test_identifier"
    ]

    assert len(failed_tests) == 5
    assert all("passed" not in item.normalized_text for item in failed_tests)
    assert [item.start_line for item in failed_tests] == [7, 6, 5, 3, 2]
    assert all(
        item.normalized_text != "tests/test_api.py::test_failed_oldest"
        for item in failed_tests
    )


def test_bm25_candidate_depth_is_top_20_with_deterministic_ties() -> None:
    chunks = tuple(
        chunk_physical_text(
            "alpha\n",
            source_kind="repository_file",
            source_path=f"physical-artifacts/repository/file-{index:02}.txt",
            repository_relative_path=f"file-{index:02}.txt",
        )[0]
        for index in range(25)
    )
    query = _query("alpha")

    result = bm25_query_hits(chunks, (query,), per_query_candidates=20)[0]

    assert len(result.hits) == 20
    assert [hit.bm25_rank for hit in result.hits] == list(range(1, 21))
    selected_paths = [
        next(chunk.source_path for chunk in chunks if chunk.chunk_id == hit.chunk_id)
        for hit in result.hits
    ]
    assert selected_paths == sorted(selected_paths)
    assert selected_paths[-1].endswith("file-19.txt")


def test_equal_weight_rrf_uses_rank_constant_60_and_deterministic_fusion() -> None:
    chunks = tuple(
        chunk_physical_text(
            content,
            source_kind="raw_log",
            source_path="physical-artifacts/raw.log",
        )[0]
        for content in ("alpha beta\n", "alpha\n", "beta\n")
    )
    query_results = bm25_query_hits(
        chunks,
        (_query("alpha", query_id="alpha"), _query("beta", query_id="beta")),
        per_query_candidates=2,
    )

    fused = reciprocal_rank_fusion(chunks, query_results, rank_constant=60, final_top_k=3)

    assert fused[0].chunk.content == "alpha beta\n"
    expected = sum(
        1 / (60 + hit.bm25_rank) for hit in fused[0].contributing_hits
    )
    assert fused[0].rrf_score == pytest.approx(expected)
    assert [hit.fused_rank for hit in fused] == list(range(1, len(fused) + 1))


def test_repository_path_tokens_can_retrieve_a_chunk_without_path_in_content() -> None:
    chunks = tuple(
        chunk_physical_text(
            "same generic content\n",
            source_kind="repository_file",
            source_path=f"physical-artifacts/repository/{path}",
            repository_relative_path=path,
        )[0]
        for path in ("src/AlphaService.java", "src/TargetParser.java")
    )
    query = _query("TargetParser.java", pool="repository")

    result = bm25_query_hits(
        chunks,
        (query,),
        per_query_candidates=2,
        include_repository_path=True,
    )[0]

    first = next(chunk for chunk in chunks if chunk.chunk_id == result.hits[0].chunk_id)
    assert first.repository_relative_path == "src/TargetParser.java"
    assert result.hits[0].bm25_score > result.hits[1].bm25_score


@dataclass(frozen=True)
class _Coordinate:
    evidence_id: str
    source: str
    start_line: int
    end_line: int


def test_packing_coalesces_overlap_without_bridging_gaps_files_or_backfill() -> None:
    source_a = _lines(300)
    source_b = _lines(100, "other")
    chunks_a = chunk_physical_text(
        source_a,
        source_kind="raw_log",
        source_path="physical-artifacts/raw.log",
    )
    chunk_b = chunk_physical_text(
        source_b,
        source_kind="repository_file",
        source_path="physical-artifacts/repository/other.py",
        repository_relative_path="other.py",
    )[0]
    hits = (
        FusedHit(chunks_a[0], 0.2, 1, ()),
        FusedHit(chunks_a[1], 0.1, 2, ()),
        FusedHit(chunks_a[3], 0.05, 3, ()),
    )
    repo_hits = (FusedHit(chunk_b, 0.1, 1, ()),)

    packed = pack_selected_hits(
        hits,
        repo_hits,
        source_texts={
            "physical-artifacts/raw.log": source_a,
            "physical-artifacts/repository/other.py": source_b,
        },
        canonical_coordinates=(
            _Coordinate("log:overlap", "physical-artifacts/raw.log", 90, 95),
            _Coordinate("log:gap", "physical-artifacts/raw.log", 181, 200),
            _Coordinate("repo:other", "physical-artifacts/repository/other.py", 1, 2),
        ),
    )

    assert [(item.source_path, item.start_line, item.end_line) for item in packed] == [
        ("physical-artifacts/raw.log", 1, 180),
        ("physical-artifacts/raw.log", 241, 300),
        ("physical-artifacts/repository/other.py", 1, 100),
    ]
    assert packed[0].derived_from_chunk_ids == (
        chunks_a[0].chunk_id,
        chunks_a[1].chunk_id,
    )
    assert [item.evidence_id for item in packed[0].overlapping_canonical_evidence] == [
        "log:overlap"
    ]
    assert packed[1].overlapping_canonical_evidence == ()
    assert len(packed) == 3


class _Case:
    raw_log_path = "physical-artifacts/raw.log"
    repository_root = "physical-artifacts/repository"


class _Workspace:
    case = _Case()
    canonical_coordinates = ()

    def __init__(self) -> None:
        self.files = {
            f"src/FooService{index}.java": "class FooService { void fail() {} }\n"
            for index in range(15)
        }

    def read_raw_log_exact(self) -> str:
        return "ERROR FooService failed at src/FooService0.java:1\n"

    def list_repository_files(self) -> tuple[str, ...]:
        return tuple(sorted(self.files))

    def read_repository_file_exact(self, relative_path: str) -> str:
        return self.files[relative_path]


def test_log_and_repository_pools_keep_independent_top_k_without_redistribution() -> None:
    result = run_static_retrieval(_Workspace())  # type: ignore[arg-type]

    assert len(result.selected_log_hits) == 1
    assert len(result.selected_repository_hits) == 10
    assert len(result.selected_log_hits) + len(result.selected_repository_hits) == 11


def _retriever_manifest(
    *, behavior: dict | None = None
) -> ComponentManifest:
    return ComponentManifest(
        schema_version="1",
        component_type="retriever_config",
        component_version=RETRIEVER_VERSION,
        behavior=behavior or STATIC_RETRIEVER_BEHAVIOR,
        metadata={},
        path=Path("in-memory-retriever.json"),
    )


def _treatment(
    retriever: ComponentManifest,
    *, context_limit_tokens: int = 1_000_000,
) -> ConfiguredL3Treatment:
    return ConfiguredL3Treatment(
        provider_id="fake",
        model="MiniMax-M3",
        reasoning={"thinking": {"type": "adaptive"}, "reasoning_split": True},
        generation={
            "temperature": 0,
            "max_completion_tokens": 1024,
            "n": 1,
            "stream": False,
            "response_format": {"mode": "omitted"},
        },
        context_limit_tokens=context_limit_tokens,
        max_completion_tokens=1024,
        task_contract_version="structured-triage-task-contract-v1",
        output_contract_prompt_suffix=output_contract_prompt_suffix(),
        runtime_input_serialization_version=RUNTIME_INPUT_SERIALIZATION_VERSION,
        retriever_component_version=RETRIEVER_VERSION,
        retriever_component_fingerprint=component_fingerprint(retriever),
    )


def test_runtime_serialization_exposes_only_selected_physical_evidence_and_overlap() -> None:
    suite = load_evaluation_suite(TINY_SUITE)
    workspace = RuntimeCaseWorkspace.from_package(suite.cases[0].package)
    retrieval = run_static_retrieval(workspace)

    runtime_input = serialize_static_retrieval_runtime_input(workspace, retrieval)
    document = json.loads(runtime_input.text)
    serialized = runtime_input.text.casefold()

    assert document["runtime_input_serialization_version"] == (
        "static_retrieval_runtime_input_v1"
    )
    assert document["evidence_delivery"] == {
        "mode": "deterministic_static_retrieval"
    }
    assert len(document["retrieved_physical_evidence"]) == len(
        retrieval.packed_spans
    )
    assert all("path" in item and "span" in item and "content" in item for item in document["retrieved_physical_evidence"])
    assert "bm25" not in serialized
    assert "rrf" not in serialized
    assert "retrieval_rank" not in serialized
    assert "required_evidence" not in serialized
    assert "expected_answer" not in serialized
    assert "required-evidence.json" not in serialized
    assert "expected-answer.json" not in serialized
    log_item = next(
        item for item in document["retrieved_physical_evidence"]
        if item["kind"] == "raw_log"
    )
    assert [
        overlap["evidence_id"]
        for overlap in log_item["overlapping_canonical_evidence"]
    ] == ["log:assertion-mismatch"]


class _FakeProvider:
    def __init__(self, report: str, *, input_tokens: int = 500) -> None:
        self.report = report
        self.input_tokens = input_tokens
        self.requests = []

    def count_input_tokens(self, request):
        return ExactTokenCount(self.input_tokens, "fake_exact_v1")

    def complete(self, request):
        self.requests.append(request)
        return AssistantMessage(
            content=(TextContent(self.report),),
            response_id="fake-l3-response",
            response_model="MiniMax-M3",
            usage=TokenUsage(
                input_tokens=self.input_tokens,
                output_tokens=50,
                total_tokens=self.input_tokens + 50,
            ),
            stop_reason="stop",
            raw_stop_reason="stop",
        )


def _valid_report(case_id: str, evidence_id: str) -> str:
    return json.dumps(
        {
            "schema_version": "1",
            "case_id": case_id,
            "classification_status": "classified",
            "failure_type": "test_assertion_failure",
            "summary": "The assertion reports a deterministic mismatch.",
            "root_cause": "The implementation returns six instead of five.",
            "recommended_action": "Correct the calculation and rerun the failing test.",
            "confidence": 0.9,
            "evidence_references": [{"evidence_id": evidence_id}],
        }
    )


def _executor(provider: _FakeProvider, *, context_limit_tokens: int = 1_000_000):
    retriever = _retriever_manifest()
    return ConfiguredL3ConditionExecutor(
        prompt=resolve_frozen_component_manifest(
            REGISTRY, "prompt", "structured-triage-task-contract-v1"
        ),
        retriever=retriever,
        treatment=_treatment(
            retriever,
            context_limit_tokens=context_limit_tokens,
        ),
        provider_factory=lambda: provider,
        output_contract_version=CANONICALIZING_OUTPUT_CONTRACT_VERSION,
    )


def test_l3_retrieves_then_issues_exactly_one_request_and_uses_shared_final_path() -> None:
    suite = load_evaluation_suite(TINY_SUITE)
    suite_case = suite.cases[0]
    provider = _FakeProvider(
        _valid_report(suite_case.case_id, "log:assertion-mismatch")
    )
    recorder = TraceRecorder("run-l3")
    result = _executor(provider).execute_sample(
        PlannedSample(
            SampleIdentity("run-l3", suite_case.case_id, 0, 1),
            suite_case,
        ),
        recorder,
    )

    assert result.status == "scored"
    assert len(provider.requests) == 1
    assert result.data["validation"]["valid"] is True
    assert result.data["evidence_reference_resolution"]["version"] == (
        "canonical-line-range-normalization-v1"
    )
    assert result.data["context_assessment"] == {
        "input_tokens": 500,
        "method": "fake_exact_v1",
        "exact": True,
        "context_window_tokens": 1_000_000,
        "reserved_completion_tokens": 1024,
    }
    event_types = [event["event_type"] for event in recorder.snapshot()]
    assert event_types == [
        "l3_execution_started",
        "static_retrieval_completed",
        "l3_token_preflight_completed",
        "model_call_started",
        "model_call_completed",
        "report_submitted",
        "evaluation_completed",
    ]
    prompt = provider.requests[0].messages[0].content.casefold()
    assert "deterministic_static_retrieval" in prompt
    assert "bm25_score" not in prompt
    assert "rrf_score" not in prompt
    assert "required-evidence.json" not in prompt
    assert "expected-answer.json" not in prompt


def test_exact_token_preflight_fails_without_truncation_or_model_request() -> None:
    suite = load_evaluation_suite(TINY_SUITE)
    suite_case = suite.cases[0]
    provider = _FakeProvider(
        _valid_report(suite_case.case_id, "log:assertion-mismatch"),
        input_tokens=9000,
    )
    recorder = TraceRecorder("run-l3")
    result = _executor(provider, context_limit_tokens=9500).execute_sample(
        PlannedSample(
            SampleIdentity("run-l3", suite_case.case_id, 0, 1),
            suite_case,
        ),
        recorder,
    )

    assert result.status == "execution_failed"
    assert result.data["outcome"]["failure_code"] == "l3_context_infeasible"
    assert provider.requests == []
    event_types = [event["event_type"] for event in recorder.snapshot()]
    assert "static_retrieval_completed" in event_types
    preflight = next(
        event for event in recorder.snapshot()
        if event["event_type"] == "l3_token_preflight_completed"
    )
    assert preflight["payload"]["context_feasible"] is False
    assert preflight["payload"]["input_tokens"] == 9000
    assert "model_call_started" not in event_types
    assert event_types[-1] == "failure"


def test_retrieval_and_runtime_input_modules_do_not_reference_evaluator_ground_truth() -> None:
    paths = [
        ROOT / "src/devagentops/retrieval/static_v1.py",
        ROOT / "src/devagentops/retrieval/packing.py",
        ROOT / "src/devagentops/conditions/l3/static_retrieval_v1.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths).casefold()

    assert "required_evidence" not in source
    assert "expected_answer" not in source
    assert "required-evidence.json" not in source
    assert "expected-answer.json" not in source


@pytest.mark.parametrize("mutation", ["missing", "fingerprint"])
def test_matrix_v2_requires_the_frozen_l3_retriever_identity(
    tmp_path: Path,
    mutation: str,
) -> None:
    document = json.loads(L3_MATRIX.read_text(encoding="utf-8"))
    contracts = document["conditions"][0]["treatment"]["contracts"]
    if mutation == "missing":
        del contracts["retriever"]
    else:
        contracts["retriever"]["fingerprint"] = "0" * 64
    path = tmp_path / "invalid-l3-matrix.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(EvaluationMatrixError, match="retriever"):
        load_evaluation_matrix(path, REGISTRY)


def test_historical_model_condition_fingerprints_remain_unchanged() -> None:
    expected = {
        "l1-minimax-m3-canonicalized-v2.json": (
            "405117b791f9c9c30540c58e462db1ec8ce612287b777cb5e5062c2b8aa2164b",
            "eefb6748ed56e88eb602d9cd2703bc1d188f88cb5c9280d7ddffdb8bb942bb59",
        ),
        "l2-minimax-m3-canonicalized-v2.json": (
            "04f12735fd385cdcfd7ec4959542f2657c0f4c1066c76bbe6876fa52979ee663",
            "b20eb42c5ee13e30053531181d6a13a86f490d666342f8222d94782223a8a6e7",
        ),
        "oracle-minimax-m3-canonicalized-v2.json": (
            "fc0430616cde8d5a17e2cfad55f96e0851843b5c3ade91234a03aec31a49f92d",
            "f5e80610f5bcd0b6345dcb2d1ff35c77db87ada381135eea34ee501ad20b1a87",
        ),
        "l4-minimax-m3-canonicalized-v2.json": (
            "d83fe7866d3d31e6a5e39c8d9f976925c1cbb2aa76c7985542cf2c140afc11dd",
            "1be4b5aa06b06a7c63f0d4c271a7d7c21c0e9f5ac177affd94064970b2465fba",
        ),
        "l4-minimax-m3-batch-parallel-canonicalized-v1.json": (
            "c988c570a1e0ed5623933c8c419605cd1f6c2066d2bbe224c6748178391d181e",
            "d3353424ccfdfeb03772ebf4ff4bd8f1ca6861b051136d2571ef7dea39bae62e",
        ),
    }

    for name, fingerprints in expected.items():
        matrix = load_evaluation_matrix(
            ROOT / "evaluation/matrices" / name,
            REGISTRY,
        )
        condition = matrix.conditions[0]
        assert (
            condition.treatment_fingerprint,
            condition.condition_fingerprint,
        ) == fingerprints


def test_tiny_fake_provider_formal_dispatch_uses_l3_and_persists_trace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import devagentops.evaluation.run_v2 as run_v2

    suite = load_evaluation_suite(TINY_SUITE)
    suite_case = suite.cases[0]
    document = json.loads(L3_MATRIX.read_text(encoding="utf-8"))
    document["matrix_id"] = "l3-tiny-fake-qualification"
    condition_document = document["conditions"][0]
    condition_document["id"] = "l3-tiny-fake-qualification-v1"
    condition_document["suite"] = suite.suite_id
    condition_document["execution_policy"].update(
        {"repeat_count": 1, "max_case_concurrency": 1}
    )
    matrix_path = tmp_path / "l3-tiny-fake.json"
    matrix_path.write_text(json.dumps(document), encoding="utf-8")
    matrix = load_evaluation_matrix(matrix_path, REGISTRY)
    provider = _FakeProvider(
        _valid_report(suite_case.case_id, "log:assertion-mismatch")
    )
    monkeypatch.setattr(run_v2, "create_minimax_provider", lambda **_: provider)
    monkeypatch.setattr(run_v2, "_code_revision", lambda: "a" * 40)
    monkeypatch.setattr(run_v2, "_git_dirty", lambda: False)

    result = run_formal_evaluation_v2(
        matrix=matrix,
        suite=suite,
        condition=matrix.conditions[0],
        registry_path=REGISTRY,
        database_path=tmp_path / "l3.db",
        artifacts_dir=tmp_path / "artifacts",
    )

    assert result["status"] == "completed"
    assert result["planned_sample_count"] == 1
    assert len(provider.requests) == 1
    artifact = json.loads(
        Path(result["artifacts"]["json"]).read_text(encoding="utf-8")
    )
    assert artifact["manifest"]["runtime_variant"] == "static_retrieval"
    assert artifact["manifest"]["treatment"]["contracts"]["retriever"] == {
        "component_type": "retriever_config",
        "version": RETRIEVER_VERSION,
        "fingerprint": "fe3a1056b1afd9f9ee1765b023fcf22362f090ec05ef1d5ac9da37171a010587",
    }
    event_types = [event["event_type"] for event in artifact["trace"]]
    assert event_types.count("static_retrieval_completed") == 1
    assert event_types.count("model_call_started") == 1
    assert event_types.count("model_call_completed") == 1
