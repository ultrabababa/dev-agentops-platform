import json
import sqlite3
from pathlib import Path

import pytest
from alembic import command

import devagentops.storage.database as storage
from devagentops.cli import main
from devagentops.storage.database import StorageError, initialize_database, inspect_database


def test_initialize_database_creates_schema_and_parent_directories(tmp_path: Path):
    database_path = tmp_path / "nested" / "devagentops.db"

    status = initialize_database(database_path)

    assert database_path.is_file()
    assert status.exists is True
    assert status.initialized is True
    assert status.schema_version == "4"
    assert "alembic_version" in status.tables
    assert "devagentops_metadata" in status.tables
    assert {
        "evaluation_case_outcomes",
        "evaluation_reports",
        "evaluation_case_scores",
        "evaluation_sample_outcomes",
        "evaluation_sample_reports",
        "evaluation_sample_scores",
        "evaluation_trace_events",
    } <= set(status.tables)


def test_initialize_database_is_idempotent(tmp_path: Path):
    database_path = tmp_path / "devagentops.db"

    first_status = initialize_database(database_path)
    second_status = initialize_database(database_path)

    assert second_status == first_status
    with sqlite3.connect(database_path) as connection:
        metadata_rows = connection.execute(
            "SELECT key, value FROM devagentops_metadata"
        ).fetchall()
    assert metadata_rows == [("schema_version", "4")]


def test_schema_2_database_with_existing_run_upgrades_to_schema_4(tmp_path: Path):
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

    assert status.schema_version == "4"
    assert {
        "evaluation_case_outcomes",
        "evaluation_sample_outcomes",
        "evaluation_sample_reports",
        "evaluation_sample_scores",
    } <= set(status.tables)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT run_id, status FROM evaluation_runs"
        ).fetchall() == [
            ("00000000-0000-0000-0000-000000000001", "completed")
        ]


def test_schema_3_database_with_existing_case_outcome_upgrades_to_schema_4(
    tmp_path: Path,
):
    database_path = tmp_path / "devagentops.db"
    config = storage._alembic_config(database_path)
    command.upgrade(config, "0003")
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO evaluation_runs "
            "(run_id, status, condition_id, runtime_variant, suite_id, "
            "suite_version, condition_fingerprint, code_revision, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000004",
                "completed_with_case_failures",
                "existing-condition",
                "full_context_one_shot",
                "existing-suite",
                "1",
                "a" * 64,
                "b" * 40,
                "2026-08-13T00:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_case_outcomes "
            "(run_id, case_id, sequence, suite_weight, status, failure_code, "
            "failure_stage, failure_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000004",
                "existing-case",
                1,
                1.0,
                "execution_failed",
                "provider_error",
                "model_provider",
                "historical failure",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_trace_events "
            "(run_id, sequence, event_type, case_id, occurred_at, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000004",
                1,
                "case_failed",
                "existing-case",
                "2026-08-13T00:00:01Z",
                "{}",
            ),
        )

    status = initialize_database(database_path)

    assert status.schema_version == "4"
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT run_id, status FROM evaluation_runs"
        ).fetchall() == [
            (
                "00000000-0000-0000-0000-000000000004",
                "completed_with_case_failures",
            )
        ]
        assert connection.execute(
            "SELECT run_id, case_id, status FROM evaluation_case_outcomes"
        ).fetchall() == [
            (
                "00000000-0000-0000-0000-000000000004",
                "existing-case",
                "execution_failed",
            )
        ]
        assert connection.execute(
            "SELECT event_type, repeat_index FROM evaluation_trace_events"
        ).fetchall() == [("case_failed", None)]
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name LIKE 'evaluation_sample_%' ORDER BY name"
        ).fetchall() == [
            ("evaluation_sample_outcomes",),
            ("evaluation_sample_reports",),
            ("evaluation_sample_scores",),
        ]


def test_schema_4_sample_tables_are_queryable_without_changing_historical_tables(
    tmp_path: Path,
):
    database_path = tmp_path / "devagentops.db"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO evaluation_runs "
            "(run_id, status, condition_id, runtime_variant, suite_id, "
            "suite_version, condition_fingerprint, code_revision, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                "completed_with_sample_failures",
                "condition",
                "full_context_one_shot",
                "suite",
                "1",
                "a" * 64,
                "b" * 40,
                "2026-08-13T00:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_sample_outcomes "
            "(run_id, case_id, repeat_index, sample_sequence, suite_weight, "
            "evaluation_failure_type, status, failure_code, failure_stage, "
            "failure_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                "case-a",
                1,
                2,
                1.0,
                "provider",
                "execution_failed",
                "provider_error",
                "model_provider",
                "sanitized",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_sample_outcomes "
            "(run_id, case_id, repeat_index, sample_sequence, suite_weight, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                "case-b",
                0,
                1,
                2.0,
                "scored",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_sample_reports "
            "(run_id, case_id, repeat_index, schema_version, valid, report_json, "
            "validation_json, report_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                "case-b",
                0,
                "1",
                1,
                "{}",
                "{}",
                "c" * 64,
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_sample_scores "
            "(run_id, case_id, repeat_index, evaluation_method, metrics_json, "
            "diagnostics_json) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                "case-b",
                0,
                "structured_report_v1",
                "{}",
                "{}",
            ),
        )
        connection.execute(
            "INSERT INTO evaluation_trace_events "
            "(run_id, sequence, event_type, case_id, repeat_index, occurred_at, "
            "payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000002",
                1,
                "sample_failed",
                "case-a",
                1,
                "2026-08-13T00:00:01Z",
                "{}",
            ),
        )
        assert connection.execute(
            "SELECT case_id, repeat_index, status FROM evaluation_sample_outcomes "
            "WHERE run_id = ? ORDER BY sample_sequence",
            ("00000000-0000-0000-0000-000000000002",),
        ).fetchall() == [
            ("case-b", 0, "scored"),
            ("case-a", 1, "execution_failed"),
        ]
        assert connection.execute(
            "SELECT case_id, repeat_index FROM evaluation_sample_reports"
        ).fetchall() == [("case-b", 0)]
        assert connection.execute(
            "SELECT case_id, repeat_index FROM evaluation_sample_scores"
        ).fetchall() == [("case-b", 0)]
        assert connection.execute(
            "SELECT case_id, repeat_index FROM evaluation_trace_events"
        ).fetchall() == [("case-a", 1)]
        assert connection.execute(
            "SELECT run_id, case_id FROM evaluation_case_outcomes"
        ).fetchall() == []


def test_schema_4_downgrade_removes_sample_columns_and_tables(tmp_path: Path):
    database_path = tmp_path / "devagentops.db"
    initialize_database(database_path)
    config = storage._alembic_config(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO evaluation_runs "
            "(run_id, status, condition_id, runtime_variant, suite_id, "
            "suite_version, condition_fingerprint, code_revision, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "00000000-0000-0000-0000-000000000003",
                "completed_with_sample_failures",
                "condition",
                "full_context_one_shot",
                "suite",
                "1",
                "a" * 64,
                "b" * 40,
                "2026-08-13T00:00:00Z",
            ),
        )

    command.downgrade(config, "0003")

    status = inspect_database(database_path)
    assert status.schema_version == "3"
    assert "evaluation_sample_outcomes" not in status.tables
    assert "evaluation_sample_reports" not in status.tables
    assert "evaluation_sample_scores" not in status.tables
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT status FROM evaluation_runs WHERE run_id = ?",
            ("00000000-0000-0000-0000-000000000003",),
        ).fetchone() == ("failed",)
        trace_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(evaluation_trace_events)"
            )
        }
    assert "repeat_index" not in trace_columns


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
