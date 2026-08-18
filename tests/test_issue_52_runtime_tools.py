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


def test_read_rejects_line_that_cannot_fit_with_progress_envelope() -> None:
    workspace = FakeWorkspace(
        raw_log="x" * (MAX_TOOL_RESULT_BYTES - 20) + "\nnext"
    )

    with pytest.raises(ExpectedToolError) as exc_info:
        execute_read(workspace, path="/raw.log", offset=1, limit=1)

    assert exc_info.value.code == "source_line_too_large"


def test_read_final_line_does_not_reserve_unneeded_continuation_bytes() -> None:
    line = "x" * (MAX_TOOL_RESULT_BYTES - 20)

    result = execute_read(FakeWorkspace(raw_log=line), path="/raw.log")

    assert result.truncated is False
    assert result.metadata["next_offset"] is None
    assert result.content.endswith(line + "\n")
    assert len(result.content.encode("utf-8")) <= MAX_TOOL_RESULT_BYTES


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


def test_grep_utf8_byte_cap_truncates_before_match_count_cap() -> None:
    source_line = "needle " + "界" * 490
    workspace = FakeWorkspace(
        raw_log="\n".join(source_line for _ in range(100))
    )

    result = execute_grep(workspace, pattern="needle", path="/raw.log")

    assert result.metadata["match_count"] == 100
    assert result.truncated is True
    assert "[truncated:" in result.content
    assert len(result.content.encode("utf-8")) <= MAX_TOOL_RESULT_BYTES


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


def test_find_utf8_byte_cap_truncates_before_result_count_cap() -> None:
    workspace = FakeWorkspace(
        files={f"{'界' * 100}-{index:03}.txt": "x" for index in range(600)}
    )

    result = execute_find(workspace, pattern="repository/*")

    assert result.metadata["total_matches"] == 600
    assert result.truncated is True
    emitted_count = len(result.content.splitlines()) - 1
    assert result.metadata["result_count"] == emitted_count
    assert (
        f"[truncated: find returned first {emitted_count} of 600 results]"
        in result.content
    )
    assert emitted_count < 600
    assert len(result.content.encode("utf-8")) <= MAX_TOOL_RESULT_BYTES


def test_ls_utf8_byte_cap_truncates_before_entry_count_cap() -> None:
    workspace = FakeWorkspace(
        files={f"{'界' * 100}-{index:03}.txt": "x" for index in range(400)}
    )

    result = execute_ls(workspace, path="/repository")

    assert result.metadata["total_entries"] == 400
    assert result.truncated is True
    emitted_count = len(result.content.splitlines()) - 1
    assert result.metadata["entry_count"] == emitted_count
    assert (
        f"[truncated: ls returned first {emitted_count} of 400 entries]"
        in result.content
    )
    assert emitted_count < 400
    assert len(result.content.encode("utf-8")) <= MAX_TOOL_RESULT_BYTES
