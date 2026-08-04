"""Lesson 0003: adapt CLI arguments to the storage boundary."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from devagentops.storage import initialize_database, inspect_database, StorageError

DEFAULT_DATABASE_PATH = Path(".devagentops/devagentops.db")


def _database_path(value: str) -> Path:
    """Convert one command-line string into a Path."""
    return Path(value).expanduser()


def build_parser() -> argparse.ArgumentParser:
    """Build this command tree.

    devagentops db init [--database PATH]
    devagentops status  [--database PATH]

    Both subcommand levels must be required. Both leaf commands accept the
    same optional database path and use DEFAULT_DATABASE_PATH by default.
    """
    
    parser = argparse.ArgumentParser()

    subcommands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    db_parser = subcommands.add_parser("db")

    db_subcommands = db_parser.add_subparsers(
        dest="db_command",
        required=True,
    )

    init_parser = db_subcommands.add_parser("init")
    init_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
    )

    status_parser = subcommands.add_parser("status")

    status_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the learning CLI and honor its process contract.

    Success:
      * dispatch to initialize_database() or inspect_database()
      * print one JSON object to stdout
      * return 0

    StorageError:
      * print one JSON object with an ``error`` key to stderr
      * return 2
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "db" and args.db_command == "init":
            status = initialize_database(args.database)
        elif args.command == "status":
            status = inspect_database(args.database)
    except StorageError as exc:
        print(
            json.dumps(
                {"error": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            status.as_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0