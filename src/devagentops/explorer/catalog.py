from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


class ExplorerCatalogError(RuntimeError):
    """Raised when the frozen public catalog is missing or inconsistent."""


@dataclass(frozen=True)
class CatalogRun:
    run_id: str
    database: str
    stage: str
    role: str
    condition_family: str
    runtime_variant: str
    representative: bool
    comparison_group: str | None


def connect_readonly(path: Path) -> sqlite3.Connection:
    resolved = path.resolve(strict=False)
    if not resolved.is_file():
        raise ExplorerCatalogError(f"public evaluation database is missing: {resolved}")
    connection = sqlite3.connect(
        f"file:{quote(str(resolved))}?mode=ro&immutable=1",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


class EvaluationCatalog:
    """Validated Run-to-database index over immutable public SQLite snapshots."""

    def __init__(self, catalog_path: Path):
        self.path = catalog_path.resolve(strict=False)
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ExplorerCatalogError(f"failed to load Explorer catalog: {exc}") from exc
        if document.get("schema_version") != "1":
            raise ExplorerCatalogError("unsupported Explorer catalog schema_version")
        self.document: dict[str, Any] = document
        self.root = self.path.parent
        self.databases = self._load_databases(document.get("databases"))
        self.runs = self._load_runs(document.get("runs"))
        self.run_index = self._build_run_index()

    def _load_databases(self, value: object) -> dict[str, Path]:
        if not isinstance(value, list) or not value:
            raise ExplorerCatalogError("catalog databases must be a non-empty list")
        databases: dict[str, Path] = {}
        database_root = (self.root / "databases").resolve(strict=False)
        for item in value:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ExplorerCatalogError("catalog database entry is invalid")
            database_id = item["id"]
            if database_id in databases:
                raise ExplorerCatalogError(f"duplicate catalog database id: {database_id}")
            raw_path = item.get("path")
            if not isinstance(raw_path, str):
                raise ExplorerCatalogError(f"database path is invalid: {database_id}")
            path = (self.root / raw_path).resolve(strict=False)
            if path.parent != database_root:
                raise ExplorerCatalogError(f"database path escapes public database root: {raw_path}")
            if not path.is_file():
                raise ExplorerCatalogError(f"public evaluation database is missing: {path}")
            databases[database_id] = path
        return databases

    def _load_runs(self, value: object) -> tuple[CatalogRun, ...]:
        if not isinstance(value, list) or not value:
            raise ExplorerCatalogError("catalog runs must be a non-empty list")
        runs: list[CatalogRun] = []
        seen: set[str] = set()
        required = {
            "run_id", "database", "stage", "role", "condition_family",
            "runtime_variant", "representative",
        }
        for item in value:
            if not isinstance(item, dict) or not required.issubset(item):
                raise ExplorerCatalogError("catalog run entry is invalid")
            run_id = item["run_id"]
            if not isinstance(run_id, str) or run_id in seen:
                raise ExplorerCatalogError(f"duplicate catalog run id: {run_id}")
            if item["database"] not in self.databases:
                raise ExplorerCatalogError(f"unknown catalog database: {item['database']}")
            seen.add(run_id)
            runs.append(CatalogRun(**{key: item.get(key) for key in CatalogRun.__dataclass_fields__}))
        return tuple(runs)

    def _build_run_index(self) -> dict[str, Path]:
        physical: dict[str, Path] = {}
        for path in self.databases.values():
            try:
                with connect_readonly(path) as connection:
                    rows = connection.execute(
                        "SELECT run_id FROM evaluation_runs ORDER BY run_id"
                    ).fetchall()
            except sqlite3.Error as exc:
                raise ExplorerCatalogError(f"failed to inspect public database {path}: {exc}") from exc
            for row in rows:
                run_id = str(row["run_id"])
                if run_id in physical:
                    raise ExplorerCatalogError(f"duplicate Run ID across public databases: {run_id}")
                physical[run_id] = path

        expected = {run.run_id for run in self.runs}
        missing = sorted(expected - physical.keys())
        unexpected = sorted(physical.keys() - expected)
        if missing:
            raise ExplorerCatalogError(f"catalog Run ID not found in public databases: {missing[0]}")
        if unexpected:
            raise ExplorerCatalogError(f"uncataloged Run ID found in public databases: {unexpected[0]}")
        for run in self.runs:
            if physical[run.run_id] != self.databases[run.database]:
                raise ExplorerCatalogError(f"catalog Run database mismatch: {run.run_id}")
        return physical

    def path_for_run(self, run_id: str) -> Path:
        try:
            return self.run_index[run_id]
        except KeyError as exc:
            raise KeyError(run_id) from exc

    def metadata_for_run(self, run_id: str) -> CatalogRun:
        for run in self.runs:
            if run.run_id == run_id:
                return run
        raise KeyError(run_id)

    def resource_path(self, value: str) -> Path:
        return (self.root / value).resolve(strict=False)
