import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from learning_exercises.lesson_0001_read_only_status import inspect_existing_sqlite


class ReadOnlyStatusExerciseTest(unittest.TestCase):
    def test_missing_database_is_not_created(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "missing" / "database.db"

            status = inspect_existing_sqlite(database_path)

            self.assertEqual(
                status,
                {
                    "path": str(database_path.resolve()),
                    "exists": False,
                    "tables": [],
                },
            )
            self.assertFalse(database_path.exists())
            self.assertFalse(database_path.parent.exists())

    def test_directory_is_rejected(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "not a file"):
                inspect_existing_sqlite(Path(directory))

    def test_existing_database_tables_are_sorted(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "database.db"
            with sqlite3.connect(database_path) as connection:
                connection.execute("CREATE TABLE zebra (id INTEGER PRIMARY KEY)")
                connection.execute("CREATE TABLE alpha (id INTEGER PRIMARY KEY)")

            status = inspect_existing_sqlite(database_path)

            self.assertEqual(status["exists"], True)
            self.assertEqual(status["tables"], ["alpha", "zebra"])


if __name__ == "__main__":
    unittest.main()
