from __future__ import annotations

from dataclasses import dataclass

from devagentops.retrieval.bm25_v1 import bm25_query_hits
from devagentops.retrieval.chunking import chunk_physical_text
from devagentops.retrieval.fusion import reciprocal_rank_fusion
from devagentops.retrieval.packing import pack_selected_hits
from devagentops.retrieval.signals import (
    extract_log_queries,
    extract_repository_queries,
)
from devagentops.retrieval.types import (
    FusedHit,
    PackedSpan,
    RetrievalQuery,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


STATIC_RETRIEVER_BEHAVIOR = {
    "strategy": "static_bm25_multi_query_rrf_v1",
    "settings": {
        "corpus_scope": "case_physical_artifacts",
        "chunking": {
            "strategy": "fixed_line_window_v1",
            "window_lines": 100,
            "overlap_lines": 20,
        },
        "signal_extraction": {
            "log_extractor_version": "failure_signal_extractor_v1",
            "repo_extractor_version": "repo_signal_extractor_v1",
            "per_signal_type_cap": 5,
            "deduplicate": "normalized_content_keep_latest",
            "priority": "specificity_then_later_line",
        },
        "tokenizer": {
            "version": "code_aware_lexical_v1",
            "lowercase": True,
            "preserve_compound_token": True,
            "split_path_separator": True,
            "split_dot": True,
            "split_underscore": True,
            "split_hyphen": True,
            "split_camel_case": True,
            "stemming": False,
            "stopword_removal": False,
        },
        "ranker": {
            "implementation": "bm25s",
            "implementation_version": "0.3.10",
            "method": "lucene",
            "k1": 1.5,
            "b": 0.75,
            "per_query_candidates": 20,
        },
        "fusion": {
            "strategy": "reciprocal_rank_fusion",
            "rank_constant": 60,
            "query_weights": "uniform",
        },
        "selection": {
            "log_top_k": 10,
            "repository_top_k": 10,
            "redistribute_unused_slots": False,
        },
        "packing": {
            "exact_chunk_deduplication": True,
            "overlapping_span_coalescing": True,
            "same_physical_source_only": True,
            "bridge_unretrieved_gaps": False,
            "backfill_after_merge": False,
        },
    },
}


@dataclass(frozen=True)
class StaticRetrievalResult:
    log_chunk_count: int
    repository_chunk_count: int
    log_queries: tuple[RetrievalQuery, ...]
    repository_queries: tuple[RetrievalQuery, ...]
    selected_log_hits: tuple[FusedHit, ...]
    selected_repository_hits: tuple[FusedHit, ...]
    packed_spans: tuple[PackedSpan, ...]

    def trace_dict(self) -> dict[str, object]:
        return {
            "log_chunk_count": self.log_chunk_count,
            "repository_chunk_count": self.repository_chunk_count,
            "log_queries": [query.trace_dict() for query in self.log_queries],
            "repository_queries": [
                query.trace_dict() for query in self.repository_queries
            ],
            "selected_log_chunks": [
                hit.trace_dict() for hit in self.selected_log_hits
            ],
            "selected_repository_chunks": [
                hit.trace_dict() for hit in self.selected_repository_hits
            ],
            "packed_spans": [span.trace_dict() for span in self.packed_spans],
        }


def run_static_retrieval(
    workspace: RuntimeCaseWorkspace,
) -> StaticRetrievalResult:
    settings = STATIC_RETRIEVER_BEHAVIOR["settings"]
    chunking = settings["chunking"]
    extraction = settings["signal_extraction"]
    ranker = settings["ranker"]
    fusion = settings["fusion"]
    selection = settings["selection"]

    raw_log = workspace.read_raw_log_exact()
    log_source_path = workspace.case.raw_log_path
    source_texts = {log_source_path: raw_log}
    log_chunks = chunk_physical_text(
        raw_log,
        source_kind="raw_log",
        source_path=log_source_path,
        window_lines=chunking["window_lines"],
        overlap_lines=chunking["overlap_lines"],
    )
    repository_chunks = []
    for relative_path in workspace.list_repository_files():
        source_path = f"{workspace.case.repository_root}/{relative_path}"
        source_text = workspace.read_repository_file_exact(relative_path)
        source_texts[source_path] = source_text
        repository_chunks.extend(
            chunk_physical_text(
                source_text,
                source_kind="repository_file",
                source_path=source_path,
                repository_relative_path=relative_path,
                window_lines=chunking["window_lines"],
                overlap_lines=chunking["overlap_lines"],
            )
        )
    repository_chunks_tuple = tuple(repository_chunks)

    log_queries = extract_log_queries(
        raw_log,
        source_path=log_source_path,
        per_signal_type_cap=extraction["per_signal_type_cap"],
    )
    log_query_hits = bm25_query_hits(
        log_chunks,
        log_queries,
        per_query_candidates=ranker["per_query_candidates"],
    )
    selected_log = reciprocal_rank_fusion(
        log_chunks,
        log_query_hits,
        rank_constant=fusion["rank_constant"],
        final_top_k=selection["log_top_k"],
    )
    repository_queries = extract_repository_queries(
        tuple(hit.chunk for hit in selected_log),
        per_signal_type_cap=extraction["per_signal_type_cap"],
    )
    repository_query_hits = bm25_query_hits(
        repository_chunks_tuple,
        repository_queries,
        per_query_candidates=ranker["per_query_candidates"],
        include_repository_path=True,
    )
    selected_repository = reciprocal_rank_fusion(
        repository_chunks_tuple,
        repository_query_hits,
        rank_constant=fusion["rank_constant"],
        final_top_k=selection["repository_top_k"],
    )
    packed_spans = pack_selected_hits(
        selected_log,
        selected_repository,
        source_texts=source_texts,
        canonical_coordinates=workspace.canonical_coordinates,
    )
    return StaticRetrievalResult(
        log_chunk_count=len(log_chunks),
        repository_chunk_count=len(repository_chunks_tuple),
        log_queries=log_queries,
        repository_queries=repository_queries,
        selected_log_hits=selected_log,
        selected_repository_hits=selected_repository,
        packed_spans=packed_spans,
    )
