import sqlite3
from pathlib import Path


def inspect_existing_sqlite(database_path: Path) -> dict[str, object]:
    """Inspect an existing SQLite file without creating it.

    Return exactly these keys:
    - path: absolute path string
    - exists: whether the database file exists
    - tables: sorted list of SQLite table names

    Requirements:
    1. A missing path returns exists=False and must remain missing.
    2. A directory path raises ValueError.
    3. An existing database is opened read-only.

    Do not inspect the production implementation before your first attempt.
    """
    # raise NotImplementedError("Complete lesson 0001 before checking the solution")

    resolved_path = database_path.resolve(strict=False)

    if not database_path.exists():
        return {
            "path": str(resolved_path),
            "exists": False,
            "tables": []
        }

    if not database_path.is_file():
        raise ValueError("not a file")

    # build a uri with read-only mode
    database_uri = resolved_path.as_uri() + "?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
        tables = [t[0] for t in rows]
    finally:
        connection.close()

    return {
        "path": str(resolved_path),
        "exists": True,
        "tables": tables
    }