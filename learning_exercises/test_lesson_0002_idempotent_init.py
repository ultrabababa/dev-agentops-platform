"""Lesson 0002: prove that repeated initialization preserves existing data."""

import sqlite3
from pathlib import Path

from devagentops.storage.database import initialize_database


def test_repeated_initialization_preserves_existing_data(tmp_path: Path):
    database_path = tmp_path / "devagentops.db"

    # TODO 1: initialize the database for the first time.
    # TODO 2: insert a marker row into devagentops_metadata and commit it.
    # TODO 3: initialize the same database for the second time.
    # TODO 4: query the marker row and Alembic revision.
    # TODO 5: assert that the marker survived and the revision is still 0001.
    # raise NotImplementedError("Complete the five TODOs without reading the production test")
    status = initialize_database(database_path)

    connection = sqlite3.connect(status.path)
    try:
        connection.execute(
        """
            INSERT INTO devagentops_metadata (key, value)
            VALUES (?, ?)
            """,
            ("learning_marker", "must_survive"),)
        connection.commit()

        old_version = connection.execute("""
        SELECT version_num FROM alembic_version
        """).fetchone()[0]
    finally:
        connection.close()

    status = initialize_database(database_path)

    connection = sqlite3.connect(status.path)
    try:
        new_version = connection.execute("""
        SELECT version_num FROM alembic_version
        """).fetchone()[0]
        marker_value = connection.execute("""
        SELECT value FROM devagentops_metadata WHERE key = ?
        """, ("learning_marker",)).fetchone()[0]
    finally:
        connection.close()

    assert old_version == "0001"
    assert new_version == "0001"
    assert marker_value == "must_survive"
