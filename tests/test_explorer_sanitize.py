from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from devagentops.explorer.sanitize import (
    SanitizationError,
    sanitize_database,
    validate_public_database,
)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _source_database(path, *, schema_version: str = "6", invalid_json: bool = False):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE devagentops_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE evaluation_runs (run_id TEXT PRIMARY KEY);
        CREATE TABLE evaluation_sample_outcomes (
            run_id TEXT NOT NULL, case_id TEXT NOT NULL, repeat_index INTEGER NOT NULL,
            PRIMARY KEY (run_id,case_id,repeat_index),
            FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
        );
        CREATE TABLE evaluation_trace_events (
            run_id TEXT NOT NULL, sequence INTEGER NOT NULL, payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id,sequence),
            FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
        );
        """
    )
    if schema_version == "6":
        connection.execute(
            "CREATE TABLE evaluation_sample_trajectory_messages ("
            "run_id TEXT NOT NULL,case_id TEXT NOT NULL,repeat_index INTEGER NOT NULL,"
            "message_index INTEGER NOT NULL,message_role TEXT NOT NULL,"
            "message_json TEXT NOT NULL,message_sha256 TEXT NOT NULL,"
            "PRIMARY KEY(run_id,case_id,repeat_index,message_index),"
            "FOREIGN KEY(run_id,case_id,repeat_index) REFERENCES "
            "evaluation_sample_outcomes(run_id,case_id,repeat_index) ON DELETE CASCADE)"
        )
    connection.execute(
        "INSERT INTO devagentops_metadata VALUES ('schema_version',?)", (schema_version,)
    )
    for run_id in ("keep", "remove"):
        connection.execute("INSERT INTO evaluation_runs VALUES (?)", (run_id,))
        connection.execute(
            "INSERT INTO evaluation_sample_outcomes VALUES (?,?,0)", (run_id, "case")
        )
        trace = {
            "step": 1,
            "response_id": "provider-response-private",
            "usage": {"input_tokens": 3, "provider_fields": {"cached": 2}},
            "nested": {
                "reasoning_content": "trace secret thought",
                "provider_state": "opaque",
            },
        }
        connection.execute(
            "INSERT INTO evaluation_trace_events VALUES (?,?,?)",
            (run_id, 1, _canonical(trace)),
        )
        if schema_version == "6":
            message = {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "private chain of thought"},
                    {"type": "text", "text": "public conclusion"},
                    {
                        "type": "tool_call",
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "README.md"},
                        "raw_arguments": "provider-private duplicate",
                    },
                ],
                "response_id": "private-response-id",
                "response_model": "model-v1",
                "usage": {
                    "input_tokens": 11,
                    "output_tokens": 7,
                    "total_tokens": 18,
                    "provider_fields": {"reasoning_tokens": 5},
                },
                "stop_reason": "tool_use",
                "raw_stop_reason": "tool_calls",
                "provider_fields": {"reasoning_details": [{"text": "private"}]},
            }
            raw = "{" if invalid_json and run_id == "keep" else _canonical(message)
            connection.execute(
                "INSERT INTO evaluation_sample_trajectory_messages VALUES "
                "(?,?,0,0,'assistant',?,?)",
                (run_id, "case", raw, "0" * 64),
            )
    connection.commit()
    connection.close()


def test_sanitizer_preserves_public_trajectory_and_source_and_filters_trace(tmp_path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "public.sqlite3"
    _source_database(source)
    source_before = hashlib.sha256(source.read_bytes()).hexdigest()

    report = sanitize_database(source, destination, run_ids=["keep"])

    assert destination.is_file()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_before
    assert report.retained_run_ids == ("keep",)
    with sqlite3.connect(destination) as connection:
        assert connection.execute("SELECT run_id FROM evaluation_runs").fetchall() == [("keep",)]
        message_json, message_sha256 = connection.execute(
            "SELECT message_json,message_sha256 FROM evaluation_sample_trajectory_messages"
        ).fetchone()
        message = json.loads(message_json)
        assert message == {
            "content": [
                {"text": "public conclusion", "type": "text"},
                {
                    "arguments": {"path": "README.md"},
                    "id": "call-1",
                    "name": "read_file",
                    "type": "tool_call",
                },
            ],
            "raw_stop_reason": "tool_calls",
            "response_model": "model-v1",
            "role": "assistant",
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18},
        }
        assert message_sha256 == hashlib.sha256(message_json.encode()).hexdigest()
        trace = json.loads(
            connection.execute("SELECT payload_json FROM evaluation_trace_events").fetchone()[0]
        )
        assert trace == {"nested": {}, "step": 1, "usage": {"input_tokens": 3}}
    assert validate_public_database(destination).forbidden_key_count == 0


def test_sanitizer_accepts_schema_v5_without_trajectory_and_is_deterministic(tmp_path):
    source = tmp_path / "v5.sqlite3"
    first = tmp_path / "first.sqlite3"
    second = tmp_path / "second.sqlite3"
    _source_database(source, schema_version="5")

    first_report = sanitize_database(source, first)
    second_report = sanitize_database(source, second)

    assert first_report.trajectory_rows_sanitized == 0
    assert second_report.trajectory_rows_sanitized == 0
    assert first.read_bytes() == second.read_bytes()


def test_sanitizer_fails_explicitly_for_invalid_json_and_removes_partial_output(tmp_path):
    source = tmp_path / "invalid.sqlite3"
    destination = tmp_path / "public.sqlite3"
    _source_database(source, invalid_json=True)

    with pytest.raises(SanitizationError, match="invalid JSON.*keep/case/0/0"):
        sanitize_database(source, destination)

    assert not destination.exists()


def test_validator_reports_locations_without_sensitive_values(tmp_path):
    database = tmp_path / "leaky.sqlite3"
    _source_database(database)

    with pytest.raises(SanitizationError) as caught:
        validate_public_database(database)

    text = str(caught.value)
    assert "evaluation_sample_trajectory_messages row keep/case/0/0" in text
    assert "thinking" in text
    assert "private chain of thought" not in text
    assert "trace secret thought" not in text


def test_sanitizer_requires_new_destination_and_known_run_subset(tmp_path):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "existing.sqlite3"
    _source_database(source)
    destination.write_bytes(b"owned")
    with pytest.raises(FileExistsError):
        sanitize_database(source, destination)
    assert destination.read_bytes() == b"owned"

    unknown_destination = tmp_path / "unknown.sqlite3"
    with pytest.raises(SanitizationError, match="requested Run ID is absent"):
        sanitize_database(source, unknown_destination, run_ids=["missing"])
    assert not unknown_destination.exists()


def test_validator_scans_credential_like_content_across_all_text_columns(tmp_path):
    source = tmp_path / "credential.sqlite3"
    destination = tmp_path / "public.sqlite3"
    _source_database(source, schema_version="5")
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE operator_notes (note TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO operator_notes VALUES (?)",
            ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz",),
        )

    with pytest.raises(SanitizationError, match="credential_matches=") as caught:
        sanitize_database(source, destination)

    assert "abcdefghijklmnopqrstuvwxyz" not in str(caught.value)
    assert not destination.exists()


def test_validator_rejects_forbidden_key_in_another_json_column(tmp_path):
    database = tmp_path / "diagnostics.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE evaluation_diagnostics (diagnostics_json TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO evaluation_diagnostics VALUES (?)",
            (
                _canonical(
                    {"public": {"nested": {"provider_fields": {"opaque": True}}}}
                ),
            ),
        )

    with pytest.raises(SanitizationError, match="forbidden_keys=1") as caught:
        validate_public_database(database)

    assert "evaluation_diagnostics row 1 key provider_fields" in str(caught.value)


def test_sanitizer_filters_run_manifest_private_keys_and_recomputes_hash(tmp_path):
    source = tmp_path / "manifest.sqlite3"
    destination = tmp_path / "public.sqlite3"
    _source_database(source, schema_version="5")
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE evaluation_run_manifests ("
            "manifest_json TEXT NOT NULL,manifest_sha256 TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO evaluation_run_manifests VALUES (?,?)",
            (
                _canonical(
                    {
                        "condition": {"reasoning": {"thinking": {"type": "enabled"}}},
                        "public": "retained",
                    }
                ),
                "0" * 64,
            ),
        )

    sanitize_database(source, destination)

    with sqlite3.connect(destination) as connection:
        manifest_json, manifest_sha256 = connection.execute(
            "SELECT manifest_json,manifest_sha256 FROM evaluation_run_manifests"
        ).fetchone()
    assert json.loads(manifest_json) == {"condition": {}, "public": "retained"}
    assert manifest_sha256 == hashlib.sha256(manifest_json.encode()).hexdigest()
    validate_public_database(destination)


def test_sanitizer_redacts_credential_like_report_text_and_recomputes_hash(tmp_path):
    source = tmp_path / "report.sqlite3"
    destination = tmp_path / "public.sqlite3"
    _source_database(source, schema_version="5")
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE evaluation_sample_reports ("
            "report_json TEXT NOT NULL,validation_json TEXT NOT NULL,"
            "report_sha256 TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO evaluation_sample_reports VALUES (?,?,?)",
            (
                _canonical(
                    {
                        "summary": "Request used Authorization: Bearer abcdefghijklmnopqrstuvwxyz and failed",
                    }
                ),
                _canonical({"valid": True}),
                "0" * 64,
            ),
        )

    sanitize_database(source, destination)

    with sqlite3.connect(destination) as connection:
        report_json, report_sha256 = connection.execute(
            "SELECT report_json,report_sha256 FROM evaluation_sample_reports"
        ).fetchone()
    assert "abcdefghijklmnopqrstuvwxyz" not in report_json
    assert "[REDACTED]" in report_json
    assert report_sha256 == hashlib.sha256(report_json.encode()).hexdigest()
