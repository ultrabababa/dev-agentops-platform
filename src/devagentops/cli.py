from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from devagentops.storage import StorageError, initialize_database, inspect_database


DEFAULT_DATABASE_PATH = Path(".devagentops/devagentops.db")


def _database_path(value: str) -> Path:
    return Path(value).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devagentops",
        description="Inspect and initialize the local DevAgentOps foundation.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    db_parser = subcommands.add_parser("db", help="Manage local storage.")
    db_subcommands = db_parser.add_subparsers(dest="db_command", required=True)
    init_parser = db_subcommands.add_parser(
        "init",
        help="Initialize or upgrade the local SQLite schema.",
    )
    init_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite file path (default: {DEFAULT_DATABASE_PATH}).",
    )

    status_parser = subcommands.add_parser(
        "status",
        help="Inspect local SQLite state without creating a database.",
    )
    status_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite file path (default: {DEFAULT_DATABASE_PATH}).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "db" and args.db_command == "init":
            status = initialize_database(args.database)
        elif args.command == "status":
            status = inspect_database(args.database)
        else:  # pragma: no cover - argparse prevents this state.
            parser.error("unsupported command")
    except StorageError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(status.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0
