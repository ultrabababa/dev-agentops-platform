from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SourceKind = Literal["raw_log", "repository_file"]
RetrievalPool = Literal["log", "repository"]


@dataclass(frozen=True)
class RetrievalChunk:
    chunk_id: str
    source_kind: SourceKind
    source_path: str
    repository_relative_path: str | None
    start_line: int
    end_line: int
    content: str
    content_sha256: str

    def trace_dict(self) -> dict[str, object]:
        document: dict[str, object] = {
            "chunk_id": self.chunk_id,
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_sha256": self.content_sha256,
            "byte_count": len(self.content.encode("utf-8")),
        }
        if self.repository_relative_path is not None:
            document["repository_relative_path"] = self.repository_relative_path
        return document


@dataclass(frozen=True)
class RetrievalQuery:
    query_id: str
    pool: RetrievalPool
    signal_family: str
    normalized_text: str
    source_path: str
    start_line: int
    end_line: int
    specificity: int

    def trace_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "pool": self.pool,
            "signal_family": self.signal_family,
            "normalized_text": self.normalized_text,
            "source_path": self.source_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "specificity": self.specificity,
        }


@dataclass(frozen=True)
class PerQueryHit:
    query_id: str
    chunk_id: str
    bm25_score: float
    bm25_rank: int

    def trace_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "chunk_id": self.chunk_id,
            "bm25_score": self.bm25_score,
            "bm25_rank": self.bm25_rank,
        }


@dataclass(frozen=True)
class QueryHits:
    query: RetrievalQuery
    hits: tuple[PerQueryHit, ...]


@dataclass(frozen=True)
class FusedHit:
    chunk: RetrievalChunk
    rrf_score: float
    fused_rank: int
    contributing_hits: tuple[PerQueryHit, ...]

    def trace_dict(self) -> dict[str, object]:
        return {
            **self.chunk.trace_dict(),
            "rrf_score": self.rrf_score,
            "rrf_rank": self.fused_rank,
            "contributing_bm25_hits": [
                hit.trace_dict() for hit in self.contributing_hits
            ],
        }


@dataclass(frozen=True)
class CanonicalOverlap:
    evidence_id: str
    source: str
    start_line: int
    end_line: int

    def model_visible_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "span": {
                "type": "line_range",
                "start_line": self.start_line,
                "end_line": self.end_line,
            },
        }


@dataclass(frozen=True)
class PackedSpan:
    source_kind: SourceKind
    source_path: str
    repository_relative_path: str | None
    start_line: int
    end_line: int
    content: str
    content_sha256: str
    best_retrieval_rank: int
    derived_from_chunk_ids: tuple[str, ...]
    overlapping_canonical_evidence: tuple[CanonicalOverlap, ...]

    def trace_dict(self) -> dict[str, object]:
        document: dict[str, object] = {
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_sha256": self.content_sha256,
            "byte_count": len(self.content.encode("utf-8")),
            "best_retrieval_rank": self.best_retrieval_rank,
            "derived_from_chunk_ids": list(self.derived_from_chunk_ids),
            "overlapping_canonical_evidence_ids": [
                item.evidence_id for item in self.overlapping_canonical_evidence
            ],
        }
        if self.repository_relative_path is not None:
            document["repository_relative_path"] = self.repository_relative_path
        return document

    def model_visible_dict(self) -> dict[str, object]:
        document: dict[str, object] = {
            "kind": self.source_kind,
            "path": self.source_path,
            "span": {
                "type": "line_range",
                "start_line": self.start_line,
                "end_line": self.end_line,
            },
            "content": self.content,
            "overlapping_canonical_evidence": [
                item.model_visible_dict()
                for item in self.overlapping_canonical_evidence
            ],
        }
        if self.repository_relative_path is not None:
            document["repository_relative_path"] = self.repository_relative_path
        return document
