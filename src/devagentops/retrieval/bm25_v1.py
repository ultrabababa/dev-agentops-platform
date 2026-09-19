from __future__ import annotations

import bm25s

from devagentops.retrieval.tokenization import code_aware_tokens
from devagentops.retrieval.types import (
    PerQueryHit,
    QueryHits,
    RetrievalChunk,
    RetrievalQuery,
)


def bm25_query_hits(
    chunks: tuple[RetrievalChunk, ...],
    queries: tuple[RetrievalQuery, ...],
    *,
    per_query_candidates: int = 20,
    include_repository_path: bool = False,
) -> tuple[QueryHits, ...]:
    """在一个 Case 内为每个确定性 query 独立计算 BM25 Top-K 正分候选。

    repo pool 可把 relative path tokens 与正文 tokens 放入同一 document，使日志中的
    文件名能召回源码；没有额外 path 权重。分数相同按物理路径/行范围/chunk ID
    稳定排序。此处只产生 per-query ranks，不读取 Canonical/Required Evidence。
    """
    if per_query_candidates < 1:
        raise ValueError("per_query_candidates must be positive")
    if not chunks or not queries:
        return tuple(QueryHits(query=query, hits=()) for query in queries)

    tokenized_documents = []
    for chunk in chunks:
        tokens: list[str] = []
        if include_repository_path and chunk.repository_relative_path is not None:
            tokens.extend(code_aware_tokens(chunk.repository_relative_path))
        tokens.extend(code_aware_tokens(chunk.content))
        tokenized_documents.append(tokens)

    ranker = bm25s.BM25(method="lucene", k1=1.5, b=0.75)
    ranker.index(tokenized_documents, show_progress=False)
    results: list[QueryHits] = []
    for query in queries:
        query_tokens = code_aware_tokens(query.normalized_text)
        if not query_tokens:
            results.append(QueryHits(query=query, hits=()))
            continue
        raw_scores = ranker.get_scores(query_tokens)
        scored = sorted(
            (
                (float(raw_scores[index]), chunk)
                for index, chunk in enumerate(chunks)
                if float(raw_scores[index]) > 0.0
            ),
            key=lambda item: (
                -item[0],
                item[1].source_path,
                item[1].start_line,
                item[1].end_line,
                item[1].chunk_id,
            ),
        )[: min(per_query_candidates, len(chunks))]
        results.append(
            QueryHits(
                query=query,
                hits=tuple(
                    PerQueryHit(
                        query_id=query.query_id,
                        chunk_id=chunk.chunk_id,
                        bm25_score=score,
                        bm25_rank=rank,
                    )
                    for rank, (score, chunk) in enumerate(scored, start=1)
                ),
            )
        )
    return tuple(results)
