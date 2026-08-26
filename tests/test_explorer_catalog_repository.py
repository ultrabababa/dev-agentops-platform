from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from devagentops.explorer.catalog import (
    EvaluationCatalog,
    ExplorerCatalogError,
    connect_readonly,
)
from devagentops.explorer.repository import EvaluationRepository


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CATALOG = ROOT / "showcase-data" / "catalog.json"
EXPECTED_RUN_IDS = {
    "de1809aa-3506-4e04-843b-099f4be00df4",
    "82372eec-204f-4223-b87e-0f26a9ae3fb5",
    "388dc6a6-6483-4e11-9b4a-5c935929bd5a",
    "dd8ca829-5051-43b6-a0c2-b3c2889acae0",
    "5dd0f286-ae66-4374-a935-bc6d53e15742",
    "345b08a2-1a9a-4b7e-be19-4c17721786a9",
    "023d5960-c450-42e1-a516-a874106673f4",
    "d6fee1ba-ddd2-4ed3-ae2f-625603de5fef",
    "010e9a75-8ca8-44b5-8445-d82d188d11f3",
    "b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8",
    "d76ac5ca-22a3-4c67-acf3-c33bba68f0d5",
    "a9d5bce2-d635-4573-baf1-d26c391fedf8",
}


def _minimal_database(path: Path, *run_ids: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE evaluation_runs (run_id TEXT PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO evaluation_runs (run_id) VALUES (?)",
            [(run_id,) for run_id in run_ids],
        )


def _catalog_document(database_entries, runs):
    return {
        "schema_version": "1",
        "suite": {},
        "artifacts": {},
        "databases": database_entries,
        "runs": [
            {
                "run_id": run_id,
                "database": database,
                "stage": "baseline",
                "role": "historical_baseline",
                "condition_family": "L1",
                "runtime_variant": "full_context_one_shot",
                "representative": False,
                "comparison_group": None,
            }
            for run_id, database in runs
        ],
        "comparisons": [],
    }


def test_checked_in_catalog_resolves_exactly_twelve_formal_runs() -> None:
    catalog = EvaluationCatalog(PUBLIC_CATALOG)

    assert {run.run_id for run in catalog.runs} == EXPECTED_RUN_IDS
    assert set(catalog.run_index) == EXPECTED_RUN_IDS
    assert len(catalog.databases) == 9


def test_catalog_fails_clearly_for_missing_database(tmp_path: Path) -> None:
    document = _catalog_document(
        [{"id": "missing", "path": "databases/missing.sqlite3"}],
        [("run-1", "missing")],
    )
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ExplorerCatalogError, match="database is missing"):
        EvaluationCatalog(path)


def test_catalog_rejects_duplicate_physical_run_id(tmp_path: Path) -> None:
    _minimal_database(tmp_path / "databases" / "a.sqlite3", "run-1")
    _minimal_database(tmp_path / "databases" / "b.sqlite3", "run-1")
    document = _catalog_document(
        [
            {"id": "a", "path": "databases/a.sqlite3"},
            {"id": "b", "path": "databases/b.sqlite3"},
        ],
        [("run-1", "a")],
    )
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ExplorerCatalogError, match="duplicate Run ID"):
        EvaluationCatalog(path)


def test_catalog_rejects_unknown_catalog_run(tmp_path: Path) -> None:
    _minimal_database(tmp_path / "databases" / "a.sqlite3", "different-run")
    document = _catalog_document(
        [{"id": "a", "path": "databases/a.sqlite3"}],
        [("run-1", "a")],
    )
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ExplorerCatalogError, match="catalog Run ID not found"):
        EvaluationCatalog(path)


def test_repository_lists_and_fetches_runs_across_databases() -> None:
    repository = EvaluationRepository(EvaluationCatalog(PUBLIC_CATALOG))

    runs = repository.list_runs()
    l3 = repository.get_run("a9d5bce2-d635-4573-baf1-d26c391fedf8")

    assert {run["run_id"] for run in runs} == EXPECTED_RUN_IDS
    assert l3["runtime_variant"] == "static_retrieval"
    assert l3["planned_samples"] == 60
    assert len(l3["failure_type_aggregates"]) == 5


def test_repository_fetches_sample_trajectory_and_trace() -> None:
    repository = EvaluationRepository(EvaluationCatalog(PUBLIC_CATALOG))
    run_id = "d6fee1ba-ddd2-4ed3-ae2f-625603de5fef"
    case_id = "bugswarm-traccar-170287308"

    sample = repository.get_sample(run_id, case_id, 0)
    trajectory = repository.get_trajectory(run_id, case_id, 0)
    trace = repository.get_trace(run_id, case_id, 0)

    assert sample["trajectory_available"] is True
    assert sample["trace_available"] is True
    assert trajectory == sorted(trajectory, key=lambda item: item["message_index"])
    assert trace == sorted(trace, key=lambda item: item["sequence"])


def test_repository_keeps_invalid_report_type_as_validation_without_raw_report() -> None:
    repository = EvaluationRepository(EvaluationCatalog(PUBLIC_CATALOG))
    sample = repository.get_sample(
        "b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8",
        "bugswarm-mypy-237548392",
        0,
    )

    assert sample["report"] is None
    assert sample["validation"]["valid"] is False
    assert sample["validation"]["errors"][0]["code"] == "invalid_report_type"


def test_public_database_connection_is_query_only() -> None:
    catalog = EvaluationCatalog(PUBLIC_CATALOG)
    path = catalog.path_for_run("a9d5bce2-d635-4573-baf1-d26c391fedf8")

    with connect_readonly(path) as connection:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE forbidden_write (value TEXT)")
