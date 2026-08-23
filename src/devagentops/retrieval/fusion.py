from __future__ import annotations

from collections import defaultdict

from devagentops.retrieval.types import FusedHit, QueryHits, RetrievalChunk


def reciprocal_rank_fusion(
    chunks: tuple[RetrievalChunk, ...],
    query_results: tuple[QueryHits, ...],
    *,
    rank_constant: int = 60,
    final_top_k: int = 10,
) -> tuple[FusedHit, ...]:
    if rank_constant < 1 or final_top_k < 1:
        raise ValueError("RRF rank constant and final_top_k must be positive")
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    contributions = defaultdict(list)
    for query_result in query_results:
        for hit in query_result.hits:
            contributions[hit.chunk_id].append(hit)

    ranked = []
    for chunk_id, hits in contributions.items():
        chunk = chunks_by_id[chunk_id]
        ordered_hits = tuple(sorted(hits, key=lambda item: item.query_id))
        score = sum(1.0 / (rank_constant + hit.bm25_rank) for hit in ordered_hits)
        best_rank = min(hit.bm25_rank for hit in ordered_hits)
        ranked.append((score, best_rank, chunk, ordered_hits))
    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1],
            item[2].source_path,
            item[2].start_line,
            item[2].end_line,
            item[2].chunk_id,
        )
    )
    return tuple(
        FusedHit(
            chunk=chunk,
            rrf_score=score,
            fused_rank=rank,
            contributing_hits=hits,
        )
        for rank, (score, _best_rank, chunk, hits) in enumerate(
            ranked[:final_top_k], start=1
        )
    )
