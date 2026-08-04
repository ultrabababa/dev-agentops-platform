"""Executable contract for Lesson 0003."""

import json
from pathlib import Path

from learning_exercises.lesson_0003_cli_contract import build_parser, main


def test_parser_maps_nested_commands_and_database_path():
    args = build_parser().parse_args(
        ["db", "init", "--database", "somewhere/devagentops.db"]
    )

    assert args.command == "db"
    assert args.db_command == "init"
    assert args.database == Path("somewhere/devagentops.db")


def test_init_then_status_emit_the_same_json_state(tmp_path: Path, capsys):
    database_path = tmp_path / "devagentops.db"

    assert main(["db", "init", "--database", str(database_path)]) == 0
    init_payload = json.loads(capsys.readouterr().out)

    assert main(["status", "--database", str(database_path)]) == 0
    status_payload = json.loads(capsys.readouterr().out)

    assert init_payload["initialized"] is True
    assert status_payload == init_payload


def test_storage_error_goes_to_stderr_and_returns_two(tmp_path: Path, capsys):
    assert main(["db", "init", "--database", str(tmp_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not a file" in json.loads(captured.err)["error"]
