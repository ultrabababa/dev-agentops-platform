from __future__ import annotations

import fnmatch

from devagentops.runtime.tools._common import (
    ExpectedToolError,
    ToolExecutionResult,
    bounded_lines,
    normalize_virtual_path,
    visible_directories,
    visible_files,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_FIND_RESULTS = 1000


def execute_find(
    workspace: RuntimeCaseWorkspace,
    *,
    pattern: str,
    path: str | None = None,
    limit: int = MAX_FIND_RESULTS,
) -> ToolExecutionResult:
    if not isinstance(pattern, str) or not pattern:
        raise ExpectedToolError("pattern must be a non-empty glob", code="invalid_pattern")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > MAX_FIND_RESULTS
    ):
        raise ExpectedToolError(
            f"limit must be an integer from 1 to {MAX_FIND_RESULTS}",
            code="invalid_limit",
        )
    base = normalize_virtual_path(path)
    members = sorted({*visible_files(workspace), *visible_directories(workspace)})
    in_scope = [
        item for item in members if item == base or item.startswith(base.rstrip("/") + "/")
    ]
    if not in_scope:
        raise ExpectedToolError(f"workspace path does not exist: {base}", code="path_not_found")
    matches = [item for item in in_scope if fnmatch.fnmatch(item.lstrip("/"), pattern)]
    limited = matches[:limit]
    count_truncated = len(matches) > len(limited)
    content, byte_truncated, emitted_count = bounded_lines(
        limited,
        truncation_notice=lambda count: (
            f"[truncated: find returned first {count} of {len(matches)} results]"
        ),
        already_truncated=count_truncated,
    )
    if not limited:
        content = "no results\n"
    truncated = count_truncated or byte_truncated
    return ToolExecutionResult(
        content=content,
        truncated=truncated,
        metadata={
            "result_count": emitted_count,
            "total_matches": len(matches),
            "truncation_reason": "count_or_byte_limit" if truncated else None,
        },
    )
