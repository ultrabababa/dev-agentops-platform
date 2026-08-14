from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


METADATA_TABLE = "devagentops_metadata"


class StorageError(RuntimeError):
    """Raised when local SQLite storage cannot be inspected or initialized."""


@dataclass(frozen=True)
class StorageStatus:
    path: str
    exists: bool
    initialized: bool
    schema_version: str | None
    table_count: int
    tables: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["tables"] = list(self.tables)
        return result


def _resolved_path(database_path: Path) -> Path:
    path = database_path.expanduser().resolve(strict=False)
    if path.exists() and not path.is_file():
        raise StorageError(f"SQLite path is not a file: {path}")

    parent = path.parent
    if parent.exists() and not parent.is_dir():
        raise StorageError(f"SQLite parent path is not a directory: {parent}")
    return path


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def create_database_engine(database_path: Path) -> Engine:
    path = _resolved_path(database_path)
    engine = create_engine(_sqlite_url(path))

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _alembic_config(path: Path) -> Config:
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().with_name("migrations")),
    )
    config.set_main_option("sqlalchemy.url", _sqlite_url(path))
    return config


def initialize_database(database_path: Path) -> StorageStatus:
    path = _resolved_path(database_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        command.upgrade(_alembic_config(path), "head")
    except Exception as exc:
        raise StorageError(f"Failed to initialize SQLite database at {path}: {exc}") from exc
    return inspect_database(path)


def inspect_database(database_path: Path) -> StorageStatus:
    path = _resolved_path(database_path)
    if not path.exists():
        return StorageStatus(
            path=str(path),
            exists=False,
            initialized=False,
            schema_version=None,
            table_count=0,
            tables=(),
        )

    engine = create_database_engine(path)
    try:
        with engine.connect() as connection:
            table_names = tuple(sorted(inspect(connection).get_table_names()))
            schema_version = None
            if METADATA_TABLE in table_names:
                schema_version = connection.execute(
                    text(
                        "SELECT value FROM devagentops_metadata "
                        "WHERE key = 'schema_version'"
                    )
                ).scalar_one_or_none()
    except (OSError, SQLAlchemyError) as exc:
        raise StorageError(f"Failed to inspect SQLite database at {path}: {exc}") from exc
    finally:
        engine.dispose()

    return StorageStatus(
        path=str(path),
        exists=True,
        initialized=METADATA_TABLE in table_names and schema_version is not None,
        schema_version=schema_version,
        table_count=len(table_names),
        tables=table_names,
    )
