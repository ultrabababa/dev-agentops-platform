from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from devagentops.retrieval.types import (
    CanonicalOverlap,
    FusedHit,
    PackedSpan,
)


class CanonicalCoordinate(Protocol):
    evidence_id: str
    source: str
    start_line: int
    end_line: int


@dataclass
class _MutableSpan:
    source_kind: str
    source_path: str
    repository_relative_path: str | None
    start_line: int
    end_line: int
    best_retrieval_rank: int
    chunk_ids: list[str]


def pack_selected_hits(
    log_hits: tuple[FusedHit, ...],
    repository_hits: tuple[FusedHit, ...],
    *,
    source_texts: Mapping[str, str],
    canonical_coordinates: Iterable[CanonicalCoordinate],
) -> tuple[PackedSpan, ...]:
    log_spans = _coalesce(
        sorted(log_hits, key=lambda hit: (hit.chunk.start_line, hit.chunk.end_line)),
    )
    repository_file_order: dict[str, int] = {}
    for hit in repository_hits:
        repository_file_order[hit.chunk.source_path] = min(
            hit.fused_rank,
            repository_file_order.get(hit.chunk.source_path, hit.fused_rank),
        )
    repository_spans = _coalesce(
        sorted(
            repository_hits,
            key=lambda hit: (
                repository_file_order[hit.chunk.source_path],
                hit.chunk.source_path,
                hit.chunk.start_line,
                hit.chunk.end_line,
            ),
        )
    )
    coordinates = tuple(canonical_coordinates)
    return tuple(
        _finalize(span, source_texts=source_texts, coordinates=coordinates)
        for span in (*log_spans, *repository_spans)
    )


def _coalesce(hits: list[FusedHit]) -> tuple[_MutableSpan, ...]:
    spans: list[_MutableSpan] = []
    seen_chunk_ids: set[str] = set()
    for hit in hits:
        chunk = hit.chunk
        if chunk.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk.chunk_id)
        if (
            spans
            and spans[-1].source_path == chunk.source_path
            and chunk.start_line <= spans[-1].end_line
        ):
            current = spans[-1]
            current.end_line = max(current.end_line, chunk.end_line)
            current.best_retrieval_rank = min(current.best_retrieval_rank, hit.fused_rank)
            current.chunk_ids.append(chunk.chunk_id)
            continue
        spans.append(
            _MutableSpan(
                source_kind=chunk.source_kind,
                source_path=chunk.source_path,
                repository_relative_path=chunk.repository_relative_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                best_retrieval_rank=hit.fused_rank,
                chunk_ids=[chunk.chunk_id],
            )
        )
    return tuple(spans)


def _finalize(
    span: _MutableSpan,
    *,
    source_texts: Mapping[str, str],
    coordinates: tuple[CanonicalCoordinate, ...],
) -> PackedSpan:
    source_text = source_texts[span.source_path]
    lines = source_text.splitlines(keepends=True)
    if span.start_line < 1 or span.end_line > len(lines):
        raise ValueError(f"packed span exceeds physical source: {span.source_path}")
    content = "".join(lines[span.start_line - 1 : span.end_line])
    overlaps = tuple(
        CanonicalOverlap(
            evidence_id=coordinate.evidence_id,
            source=coordinate.source,
            start_line=coordinate.start_line,
            end_line=coordinate.end_line,
        )
        for coordinate in coordinates
        if coordinate.source == span.source_path
        and coordinate.start_line <= span.end_line
        and span.start_line <= coordinate.end_line
    )
    return PackedSpan(
        source_kind=span.source_kind,  # type: ignore[arg-type]
        source_path=span.source_path,
        repository_relative_path=span.repository_relative_path,
        start_line=span.start_line,
        end_line=span.end_line,
        content=content,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        best_retrieval_rank=span.best_retrieval_rank,
        derived_from_chunk_ids=tuple(span.chunk_ids),
        overlapping_canonical_evidence=overlaps,
    )
