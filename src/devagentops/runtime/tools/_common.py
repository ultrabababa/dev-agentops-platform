from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Iterable

from devagentops.runtime.workspace import RuntimeCaseWorkspace


MAX_TOOL_RESULT_BYTES = 50 * 1024


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
    truncation_notice: str,
) -> tuple[str, bool]:
    emitted: list[str] = []
    notice_bytes = len((truncation_notice + "\n").encode("utf-8"))
    for line in lines:
        rendered = line + "\n"
        encoded_size = len(rendered.encode("utf-8"))
        if encoded_size + notice_bytes > MAX_TOOL_RESULT_BYTES:
            emitted.append(truncation_notice)
            return "\n".join(emitted) + "\n", True
        emitted.append(line)
    return ("\n".join(emitted) + ("\n" if emitted else "")), False
