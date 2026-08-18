from __future__ import annotations

import pytest

from devagentops.runtime.tools import (
    MAX_TOOL_RESULT_BYTES,
    ExpectedToolError,
    execute_find,
    execute_grep,
    execute_ls,
    execute_read,
)


class FakeWorkspace:
    def __init__(self, *, raw_log: str = "failure\nstack\n", files=None) -> None:
        self.raw_log = raw_log
        self.files = files or {
            ".hidden": "secret marker\n",
            "src/a.py": "alpha\nneedle value\nomega\n",
            "src/nested/b.py": "needle other\n",
        }

    def read_raw_log(self) -> str:
        return self.raw_log

    def list_repository_files(self) -> tuple[str, ...]:
        return tuple(sorted(self.files))

    def read_repository_file(self, relative_path: str) -> str:
        if relative_path not in self.files:
            raise AssertionError("tool escaped frozen membership")
        return self.files[relative_path]


def test_read_is_one_based_bounded_and_exposes_continuation() -> None:
    workspace = FakeWorkspace(raw_log="\n".join(str(index) for index in range(1, 6)))
    result = execute_read(workspace, path="/raw.log", offset=2, limit=2)
    assert result.content == (
        "lines 2-3 of 5\n2: 2\n3: 3\n[truncated: continue with offset=4]\n"
    )
    assert result.truncated is True
    assert result.metadata["next_offset"] == 4


def test_read_rejects_traversal_and_oversized_single_line() -> None:
    with pytest.raises(ExpectedToolError, match="traversal"):
        execute_read(FakeWorkspace(), path="/repository/../raw.log")
    workspace = FakeWorkspace(raw_log="x" * MAX_TOOL_RESULT_BYTES)
    with pytest.raises(ExpectedToolError) as exc_info:
        execute_read(workspace, path="/raw.log")
    assert exc_info.value.code == "source_line_too_large"


def test_grep_is_deterministic_marks_context_and_caps_source_lines() -> None:
    workspace = FakeWorkspace(
        files={"z.py": "before\nneedle " + "x" * 800 + "\nafter\n"}
    )
    result = execute_grep(
        workspace,
        pattern="needle",
        path="/repository",
        context=1,
    )
    lines = result.content.splitlines()
    assert lines[0] == "/repository/z.py-1-before"
    assert lines[1].startswith("/repository/z.py:2:needle ")
    assert lines[1].endswith("[line truncated]")
    assert len(lines[1].split(":", 2)[2]) == 500
    assert lines[2] == "/repository/z.py-3-after"


def test_grep_match_limit_is_visible_and_metadata_records_truncation() -> None:
    workspace = FakeWorkspace(raw_log="needle\nneedle\nneedle\n")
    result = execute_grep(workspace, pattern="needle", path="/raw.log", limit=2)
    assert result.truncated is True
    assert "[truncated:" in result.content
    assert result.metadata["match_count"] == 2


def test_find_and_ls_include_dotfiles_without_gitignore_filtering() -> None:
    workspace = FakeWorkspace()
    found = execute_find(workspace, pattern="repository/**")
    assert "/repository/.hidden" in found.content
    assert "/repository/src/nested/b.py" in found.content

    root = execute_ls(workspace)
    assert root.content == "raw.log\nrepository/\n"
    repository = execute_ls(workspace, path="/repository")
    assert repository.content == ".hidden\nsrc/\n"


def test_find_and_ls_count_truncation_is_visible() -> None:
    workspace = FakeWorkspace(files={f"f{index:04}.txt": "x" for index in range(600)})
    found = execute_find(workspace, pattern="repository/*", limit=3)
    listed = execute_ls(workspace, path="/repository", limit=3)
    assert found.truncated and "first 3" in found.content
    assert listed.truncated and "first 3" in listed.content
