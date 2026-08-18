from __future__ import annotations

from sqlalchemy import text

from devagentops.storage.database import (
    create_database_engine,
    initialize_database,
)
from devagentops.evaluation.persistence import persist_finalizing_sample_run


def test_migration_adds_sample_scoped_trajectory_table(tmp_path) -> None:
    database = tmp_path / "trajectory.db"
    status = initialize_database(database)
    assert status.schema_version == "6"
    assert "evaluation_sample_trajectory_messages" in status.tables

    engine = create_database_engine(database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs "
                    "(run_id,status,condition_id,runtime_variant,suite_id,suite_version,"
                    "condition_fingerprint,code_revision,started_at) VALUES "
                    "('run','finalizing','l4','self_built_react','suite','1',"
                    ":fingerprint,:revision,'now')"
                ),
                {"fingerprint": "a" * 64, "revision": "b" * 40},
            )
            connection.execute(
                text(
                    "INSERT INTO evaluation_sample_outcomes "
                    "(run_id,case_id,repeat_index,sample_sequence,suite_weight,"
                    "evaluation_failure_type,status,failure_code,failure_stage,failure_message) "
                    "VALUES ('run','case',0,1,1.0,NULL,'scored',NULL,NULL,NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO evaluation_sample_trajectory_messages "
                    "(run_id,case_id,repeat_index,message_index,message_role,"
                    "message_json,message_sha256) VALUES "
                    "('run','case',0,0,'user','{}',:sha)"
                ),
                {"sha": "c" * 64},
            )
            row = connection.execute(
                text(
                    "SELECT message_index,message_role,message_json FROM "
                    "evaluation_sample_trajectory_messages"
                )
            ).one()
            assert tuple(row) == (0, "user", "{}")
    finally:
        engine.dispose()


def test_sample_persistence_writes_exact_trajectory_separately_from_trace(tmp_path) -> None:
    database = tmp_path / "persisted-trajectory.db"
    initialize_database(database)
    manifest = {
        "run_id": "run-52",
        "selected_condition_id": "l4",
        "runtime_variant": "self_built_react",
        "evaluation_suite": {
            "suite_id": "suite",
            "suite_version": "1",
            "cases": [{"case_id": "case", "weight": 1.0}],
        },
        "condition_fingerprint": "a" * 64,
        "code_revision": "b" * 40,
        "manifest_schema_version": "2",
        "structured_report_schema_version": "1",
        "evaluation_method": "triage-method-v1",
    }
    sample = {
        "case_id": "case",
        "repeat_index": 0,
        "sample_sequence": 1,
        "weight": 1.0,
        "evaluation_failure_type": "test_assertion_failure",
        "outcome": {"status": "scored"},
        "report": {"schema_version": "1"},
        "candidate_document": {"schema_version": "1"},
        "validation": {"valid": True, "errors": []},
        "quality_metrics": {"metric": 1.0},
        "evidence_diagnostics": {"observed": True},
    }
    trajectory = (
        {"role": "user", "content": "initial"},
        {
            "role": "assistant",
            "content": [{"type": "thinking", "thinking": "private"}],
            "provider_fields": {"reasoning_details": [{"text": "private"}]},
        },
    )
    persist_finalizing_sample_run(
        database,
        manifest=manifest,
        trace_events=[],
        sample_results=[sample],
        started_at="now",
        sample_trajectories={("case", 0): trajectory},
    )
    engine = create_database_engine(database)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT message_role,message_json,message_sha256 FROM "
                    "evaluation_sample_trajectory_messages ORDER BY message_index"
                )
            ).all()
            assert [row.message_role for row in rows] == ["user", "assistant"]
            assert '"thinking":"private"' in rows[1].message_json
            assert all(len(row.message_sha256) == 64 for row in rows)
            assert connection.execute(
                text("SELECT COUNT(*) FROM evaluation_trace_events")
            ).scalar_one() == 0
    finally:
        engine.dispose()
