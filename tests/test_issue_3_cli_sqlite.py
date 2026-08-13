import json
import sqlite3
from pathlib import Path

import pytest
from alembic import command

import devagentops.storage as storage
from devagentops.cli import main
from devagentops.storage import StorageError, initialize_database, inspect_database


def test_initialize_database_creates_schema_and_parent_directories(tmp_path: Path):
    database_path = tmp_path / "nested" / "devagentops.db"

    status = initialize_database(database_path)

    assert database_path.is_file()
    assert status.exists is True
    assert status.initialized is True
    assert status.schema_version == "3"
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
    assert metadata_rows == [("schema_version", "3")]


def test_schema_2_database_with_existing_run_upgrades_to_schema_3(tmp_path: Path):
    database_path = tmp_path / "devagentops.db"
    config = storage._alembic_config(database_path)
    command.upgrade(config, "0002")
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO evaluation_runs "
            "(run_id, status, condition_id, runtime_variant, suite_id, "
            "suite_version, condition_fingerprint, code_revision, started_at, "
            "completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000001",
                "completed",
                "existing-condition",
                "full_context_one_shot",
                "existing-suite",
                "1",
                "a" * 64,
                "b" * 40,
                "2026-08-13T00:00:00Z",
                "2026-08-13T00:01:00Z",
            ),
        )

    status = initialize_database(database_path)

    assert status.schema_version == "3"
    assert "evaluation_case_outcomes" in status.tables
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT run_id, status FROM evaluation_runs"
        ).fetchall() == [
            ("00000000-0000-0000-0000-000000000001", "completed")
        ]


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
