from __future__ import annotations

import fnmatch
import re

from devagentops.runtime.tools._common import (
    ExpectedToolError,
    ToolExecutionResult,
    bounded_lines,
    normalize_virtual_path,
    read_virtual_file,
    visible_files,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_GREP_MATCHES = 100
MAX_SOURCE_LINE_CHARS = 500


def execute_grep(
    workspace: RuntimeCaseWorkspace,
    *,
    pattern: str,
    path: str | None = None,
    glob: str | None = None,
    ignore_case: bool = False,
    literal: bool = False,
    context: int = 0,
    limit: int = MAX_GREP_MATCHES,
) -> ToolExecutionResult:
    if not isinstance(pattern, str) or not pattern:
        raise ExpectedToolError("pattern must be a non-empty string", code="invalid_pattern")
    if not isinstance(context, int) or isinstance(context, bool) or context < 0:
        raise ExpectedToolError("context must be an integer >= 0", code="invalid_context")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > MAX_GREP_MATCHES
    ):
        raise ExpectedToolError(
            f"limit must be an integer from 1 to {MAX_GREP_MATCHES}",
            code="invalid_limit",
        )
    flags = re.IGNORECASE if ignore_case else 0
    try:
        expression = re.compile(re.escape(pattern) if literal else pattern, flags)
    except re.error as exc:
        raise ExpectedToolError(f"invalid regular expression: {exc}", code="invalid_pattern") from exc

    base = normalize_virtual_path(path)
    candidates = [
        item
        for item in visible_files(workspace)
        if item == base or item.startswith(base.rstrip("/") + "/")
    ]
    if not candidates:
        raise ExpectedToolError(f"workspace path does not exist: {base}", code="path_not_found")
    if glob is not None:
        if not isinstance(glob, str) or not glob:
            raise ExpectedToolError("glob must be a non-empty string", code="invalid_glob")
        candidates = [item for item in candidates if fnmatch.fnmatch(item.lstrip("/"), glob)]

    output_lines: list[str] = []
    match_count = 0
    match_limit_hit = False
    for file_path in sorted(candidates):
        source_lines = read_virtual_file(workspace, file_path).splitlines()
        emitted_context: set[int] = set()
        for index, source_line in enumerate(source_lines):
            if expression.search(source_line) is None:
                continue
            if match_count >= limit:
                match_limit_hit = True
                break
            start = max(0, index - context)
            end = min(len(source_lines), index + context + 1)
            for context_index in range(start, end):
                if context_index in emitted_context:
                    continue
                emitted_context.add(context_index)
                marker = ":" if context_index == index else "-"
                source = source_lines[context_index]
                if len(source) > MAX_SOURCE_LINE_CHARS:
                    suffix = "[line truncated]"
                    source = source[: MAX_SOURCE_LINE_CHARS - len(suffix)] + suffix
                output_lines.append(
                    f"{file_path}{marker}{context_index + 1}{marker}{source}"
                )
            match_count += 1
        if match_limit_hit:
            break

    notice = (
        f"[truncated: grep returned {match_count} matches; "
        "narrow the query or use a smaller path]"
    )
    content, byte_truncated = bounded_lines(output_lines, truncation_notice=notice)
    truncated = match_limit_hit or byte_truncated
    if match_limit_hit and not byte_truncated:
        content += notice + "\n"
    if not output_lines:
        content = "no matches\n"
    return ToolExecutionResult(
        content=content,
        truncated=truncated,
        metadata={
            "match_count": match_count,
            "truncation_reason": (
                "match_or_byte_limit" if truncated else None
            ),
        },
    )
