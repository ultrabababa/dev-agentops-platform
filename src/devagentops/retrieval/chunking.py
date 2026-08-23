from __future__ import annotations

import hashlib
import json

from devagentops.retrieval.types import RetrievalChunk, SourceKind


def chunk_physical_text(
    text: str,
    *,
    source_kind: SourceKind,
    source_path: str,
    repository_relative_path: str | None = None,
    window_lines: int = 100,
    overlap_lines: int = 20,
) -> tuple[RetrievalChunk, ...]:
    if window_lines < 1:
        raise ValueError("window_lines must be positive")
    if overlap_lines < 0 or overlap_lines >= window_lines:
        raise ValueError("overlap_lines must be non-negative and smaller than window_lines")

    lines = text.splitlines(keepends=True)
    if not lines:
        return ()
    stride = window_lines - overlap_lines
    chunks: list[RetrievalChunk] = []
    for zero_based_start in range(0, len(lines), stride):
        zero_based_end = min(zero_based_start + window_lines, len(lines))
        content = "".join(lines[zero_based_start:zero_based_end])
        start_line = zero_based_start + 1
        end_line = zero_based_end
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        identity = json.dumps(
            {
                "version": "fixed_line_window_v1",
                "source_kind": source_kind,
                "source_path": source_path,
                "start_line": start_line,
                "end_line": end_line,
                "content_sha256": content_sha256,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        chunks.append(
            RetrievalChunk(
                chunk_id=f"retrieval-chunk-v1:{hashlib.sha256(identity).hexdigest()}",
                source_kind=source_kind,
                source_path=source_path,
                repository_relative_path=repository_relative_path,
                start_line=start_line,
                end_line=end_line,
                content=content,
                content_sha256=content_sha256,
            )
        )
        if zero_based_end == len(lines):
            break
    return tuple(chunks)
