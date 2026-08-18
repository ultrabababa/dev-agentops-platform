from __future__ import annotations

from devagentops.runtime.tools._common import (
    MAX_TOOL_RESULT_BYTES,
    ExpectedToolError,
    ToolExecutionResult,
    read_virtual_file,
)
from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_READ_LINES = 2000


def execute_read(
    workspace: RuntimeCaseWorkspace,
    *,
    path: str,
    offset: int = 1,
    limit: int = MAX_READ_LINES,
) -> ToolExecutionResult:
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 1:
        raise ExpectedToolError("offset must be an integer >= 1", code="invalid_offset")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > MAX_READ_LINES
    ):
        raise ExpectedToolError(
            f"limit must be an integer from 1 to {MAX_READ_LINES}",
            code="invalid_limit",
        )
    content = read_virtual_file(workspace, path)
    lines = content.splitlines()
    total_lines = len(lines)
    if offset > total_lines + 1:
        raise ExpectedToolError(
            f"offset {offset} is beyond total line count {total_lines}",
            code="offset_out_of_range",
        )
    selected = lines[offset - 1 : offset - 1 + limit]
    if any(len((line + "\n").encode("utf-8")) > MAX_TOOL_RESULT_BYTES for line in selected):
        raise ExpectedToolError(
            "a requested source line exceeds the 50 KiB ToolResult bound",
            code="source_line_too_large",
        )

    header = f"lines {offset}-{offset + len(selected) - 1} of {total_lines}"
    rendered = [header]
    truncated = False
    next_offset: int | None = None
    emitted_count = 0
    for line_number, line in enumerate(selected, start=offset):
        candidate = f"{line_number}: {line}"
        projected_parts = [*rendered, candidate]
        if line_number < total_lines:
            projected_parts.append(
                f"[truncated: continue with offset={line_number + 1}]"
            )
        projected = "\n".join(projected_parts) + "\n"
        if len(projected.encode("utf-8")) > MAX_TOOL_RESULT_BYTES:
            if emitted_count == 0:
                raise ExpectedToolError(
                    "a requested source line cannot fit inside the 50 KiB "
                    "ToolResult envelope",
                    code="source_line_too_large",
                )
            truncated = True
            next_offset = line_number
            break
        rendered.append(candidate)
        emitted_count += 1
    else:
        if offset - 1 + len(selected) < total_lines:
            truncated = True
            next_offset = offset + len(selected)

    if next_offset is not None:
        rendered.append(f"[truncated: continue with offset={next_offset}]")
    output = "\n".join(rendered) + "\n"
    return ToolExecutionResult(
        content=output,
        truncated=truncated,
        metadata={
            "returned_start": offset,
            "returned_end": offset + emitted_count - 1,
            "total_lines": total_lines,
            "next_offset": next_offset,
            "truncation_reason": (
                "byte_or_line_limit" if truncated else None
            ),
        },
    )
