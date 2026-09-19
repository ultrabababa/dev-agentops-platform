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
    """按 UTF-8 byte 上限截断可恢复错误文本，并显式附加 truncation notice。"""
    encoded = content.encode("utf-8")
    if len(encoded) <= MAX_TOOL_RESULT_BYTES:
        return content, False
    notice = TOOL_RESULT_TRUNCATION_NOTICE.encode("utf-8")
    prefix = encoded[: MAX_TOOL_RESULT_BYTES - len(notice)]
    return prefix.decode("utf-8", errors="ignore") + TOOL_RESULT_TRUNCATION_NOTICE, True


def normalize_virtual_path(path: str | None, *, default: str = "/") -> str:
    """规范化 Agent-visible POSIX 路径并拒绝 ``.``/``..`` traversal。

    返回值属于虚拟 namespace，不直接用作宿主机任意路径；后续读取仍必须经过
    ``read_virtual_file`` 的固定根与 workspace 成员白名单。
    """
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
    """构造完整虚拟文件成员：固定 ``/raw.log`` 加冻结 repo manifest 成员。"""
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
    """将虚拟路径映射到 workspace 的受控读取 API，不暴露 package 其他目录。

    evaluator、canonical-evidence 和 repository manifest 没有虚拟路径分支，因此
    read/grep 无法通过正常工具接口读取它们；这仍是 API allowlist，不是 OS sandbox。
    """
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
    """在 50 KiB envelope 内输出完整行，并为未输出内容预留 notice 空间。

    先预留提示字节可以保证返回值不会在最后才越界；函数不切开 UTF-8 字符或
    单行。调用方同时获得 truncated 标志与实际输出行数，用于 Trace metadata。
    """
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
