from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_TOOL_RESULT_BYTES = 50 * 1024
TOOL_RESULT_TRUNCATION_NOTICE = "\n[truncated: ToolResult exceeded 50 KiB]\n"


class ExpectedToolError(RuntimeError):
    """A valid tool invocation failed in an Agent-recoverable way."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ToolExecutionResult:
    content: str
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def bound_tool_result_text(content: str) -> tuple[str, bool]:
    encoded = content.encode("utf-8")
    if len(encoded) <= MAX_TOOL_RESULT_BYTES:
        return content, False
    notice = TOOL_RESULT_TRUNCATION_NOTICE.encode("utf-8")
    prefix = encoded[: MAX_TOOL_RESULT_BYTES - len(notice)]
    return prefix.decode("utf-8", errors="ignore") + TOOL_RESULT_TRUNCATION_NOTICE, True


def normalize_virtual_path(path: str | None, *, default: str = "/") -> str:
    if path is None or path == "":
        path = default
    if not isinstance(path, str):
        raise ExpectedToolError("path must be a string", code="invalid_path")
    candidate = "/" + path.lstrip("/")
    if any(part in {".", ".."} for part in candidate.split("/")):
        raise ExpectedToolError(
            "path traversal is not allowed", code="path_outside_workspace"
        )
    normalized = str(PurePosixPath(candidate))
    return normalized if normalized != "." else "/"


def visible_files(workspace: RuntimeCaseWorkspace) -> tuple[str, ...]:
    return (
        "/raw.log",
        *(f"/repository/{path}" for path in workspace.list_repository_files()),
    )


def visible_directories(workspace: RuntimeCaseWorkspace) -> tuple[str, ...]:
    directories = {"/", "/repository"}
    for file_path in visible_files(workspace):
        parent = PurePosixPath(file_path).parent
        while str(parent) != "/":
            directories.add(str(parent))
            parent = parent.parent
    return tuple(sorted(directories))


def read_virtual_file(workspace: RuntimeCaseWorkspace, path: str) -> str:
    normalized = normalize_virtual_path(path)
    if normalized == "/raw.log":
        return workspace.read_raw_log()
    prefix = "/repository/"
    if normalized.startswith(prefix):
        relative_path = normalized[len(prefix) :]
        if relative_path not in workspace.list_repository_files():
            raise ExpectedToolError(
                f"workspace file does not exist: {normalized}",
                code="path_not_found",
            )
        return workspace.read_repository_file(relative_path)
    raise ExpectedToolError(
        f"workspace file does not exist: {normalized}", code="path_not_found"
    )


def bounded_lines(
    lines: Iterable[str],
    *,
    truncation_notice: str | Callable[[int], str],
    already_truncated: bool = False,
) -> tuple[str, bool, int]:
    source_lines = tuple(lines)
    emitted: list[str] = []
    emitted_bytes = 0

    def notice_for(count: int) -> str:
        value = truncation_notice(count) if callable(truncation_notice) else truncation_notice
        return value + "\n"

    for index, line in enumerate(source_lines):
        rendered = line + "\n"
        encoded_size = len(rendered.encode("utf-8"))
        has_unemitted_content = index < len(source_lines) - 1 or already_truncated
        reserved_notice_bytes = (
            len(notice_for(len(emitted) + 1).encode("utf-8"))
            if has_unemitted_content
            else 0
        )
        if (
            emitted_bytes + encoded_size + reserved_notice_bytes
            > MAX_TOOL_RESULT_BYTES
        ):
            content = "".join(item + "\n" for item in emitted)
            return content + notice_for(len(emitted)), True, len(emitted)
        emitted.append(line)
        emitted_bytes += encoded_size
    content = "".join(item + "\n" for item in emitted)
    if already_truncated:
        content += notice_for(len(emitted))
    return content, already_truncated, len(emitted)
