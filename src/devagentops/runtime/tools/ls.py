from __future__ import annotations

from pathlib import PurePosixPath

from devagentops.runtime.tools._common import (
    ExpectedToolError,
    ToolExecutionResult,
    bounded_lines,
    normalize_virtual_path,
    visible_directories,
    visible_files,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_LS_ENTRIES = 500


def execute_ls(
    workspace: RuntimeCaseWorkspace,
    *,
    path: str | None = None,
    limit: int = MAX_LS_ENTRIES,
) -> ToolExecutionResult:
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > MAX_LS_ENTRIES
    ):
        raise ExpectedToolError(
            f"limit must be an integer from 1 to {MAX_LS_ENTRIES}",
            code="invalid_limit",
        )
    base = normalize_virtual_path(path)
    directories = set(visible_directories(workspace))
    if base not in directories:
        raise ExpectedToolError(f"workspace directory does not exist: {base}", code="path_not_found")
    entries: set[str] = set()
    for item in (*visible_files(workspace), *directories):
        if item == base or str(PurePosixPath(item).parent) != base:
            continue
        name = PurePosixPath(item).name
        entries.add(name + ("/" if item in directories else ""))
    ordered = sorted(entries)
    limited = ordered[:limit]
    count_truncated = len(ordered) > len(limited)
    content, byte_truncated, emitted_count = bounded_lines(
        limited,
        truncation_notice=lambda count: (
            f"[truncated: ls returned first {count} of {len(ordered)} entries]"
        ),
        already_truncated=count_truncated,
    )
    truncated = count_truncated or byte_truncated
    return ToolExecutionResult(
        content=content,
        truncated=truncated,
        metadata={
            "entry_count": emitted_count,
            "total_entries": len(ordered),
            "truncation_reason": "count_or_byte_limit" if truncated else None,
        },
    )
