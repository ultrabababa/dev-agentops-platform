import json
import sqlite3
from pathlib import Path

import pytest

from devagentops.cli import main
from devagentops.storage import StorageError, initialize_database, inspect_database


def test_initialize_database_creates_schema_and_parent_directories(tmp_path: Path):
    database_path = tmp_path / "nested" / "devagentops.db"

    status = initialize_database(database_path)

    assert database_path.is_file()
    assert status.exists is True
    assert status.initialized is True
    assert status.schema_version == "1"
    assert "alembic_version" in status.tables
    assert "devagentops_metadata" in status.tables


def test_initialize_database_is_idempotent(tmp_path: Path):
    database_path = tmp_path / "devagentops.db"

    first_status = initialize_database(database_path)
    second_status = initialize_database(database_path)

    assert second_status == first_status
    with sqlite3.connect(database_path) as connection:
        metadata_rows = connection.execute(
            "SELECT key, value FROM devagentops_metadata"
        ).fetchall()
    assert metadata_rows == [("schema_version", "1")]


def test_database_directory_is_rejected_as_an_invalid_path(tmp_path: Path):
    with pytest.raises(StorageError, match="not a file"):
        initialize_database(tmp_path)


def test_inspect_empty_sqlite_database_reports_uninitialized(tmp_path: Path):
    database_path = tmp_path / "empty.db"
    with sqlite3.connect(database_path):
        pass

    status = inspect_database(database_path)

    assert status.exists is True
    assert status.initialized is False
    assert status.schema_version is None
    assert status.table_count == 0
    assert status.tables == ()


def test_status_for_missing_database_is_read_only(tmp_path: Path):
    database_path = tmp_path / "missing" / "devagentops.db"

    status = inspect_database(database_path)

    assert status.exists is False
    assert status.initialized is False
    assert database_path.exists() is False
    assert database_path.parent.exists() is False


def test_cli_init_and_status_emit_machine_readable_json(tmp_path: Path, capsys):
    database_path = tmp_path / "devagentops.db"

    assert main(["db", "init", "--database", str(database_path)]) == 0
    init_payload = json.loads(capsys.readouterr().out)
    assert init_payload["initialized"] is True

    assert main(["status", "--database", str(database_path)]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload == init_payload


def test_cli_invalid_path_returns_nonzero_and_json_error(tmp_path: Path, capsys):
    assert main(["db", "init", "--database", str(tmp_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not a file" in json.loads(captured.err)["error"]
