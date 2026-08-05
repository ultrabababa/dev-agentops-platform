from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from devagentops.component_registry import (
    ComponentRegistryError,
    freeze_component,
    load_component_manifest,
)
from devagentops.config import DEFAULT_DATABASE_PATH
from devagentops.evaluation_matrix import (
    EvaluationMatrixError,
    load_evaluation_matrix,
)
from devagentops.evaluation_suite import (
    EvaluationSuiteError,
    load_evaluation_suite,
    validate_matrix_suite_references,
)
from devagentops.storage import StorageError, initialize_database, inspect_database


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

    eval_parser = subcommands.add_parser(
        "eval",
        help="Validate and run repository-defined evaluations.",
    )
    eval_subcommands = eval_parser.add_subparsers(
        dest="eval_command",
        required=True,
    )
    doctor_parser = eval_subcommands.add_parser(
        "doctor",
        help="Validate evaluation inputs without calling a model.",
    )
    doctor_parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to a repository-defined evaluation matrix JSON file.",
    )
    doctor_parser.add_argument(
        "--registry",
        type=Path,
        help="Path to the repository component registry used for formal preflight.",
    )
    doctor_parser.add_argument(
        "--suite",
        type=Path,
        help="Path to the explicit evaluation suite manifest used for formal preflight.",
    )
    doctor_parser.add_argument(
        "--structural-only",
        action="store_true",
        help="Run legacy matrix structure checks without formal component validation.",
    )

    component_parser = subcommands.add_parser(
        "component",
        help="Validate and freeze behavior-affecting agent components.",
    )
    component_subcommands = component_parser.add_subparsers(
        dest="component_command",
        required=True,
    )
    validate_parser = component_subcommands.add_parser(
        "validate",
        help="Validate a draft component manifest and print its canonical fingerprint.",
    )
    validate_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to a draft component manifest JSON file.",
    )
    freeze_parser = component_subcommands.add_parser(
        "freeze",
        help="Freeze a validated manifest as an immutable component version.",
    )
    freeze_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to a draft component manifest JSON file.",
    )
    freeze_parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Path to the repository component registry JSON file.",
    )
    freeze_parser.add_argument(
        "--version",
        required=True,
        help="New immutable component version.",
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
        elif args.command == "eval" and args.eval_command == "doctor":
            if args.structural_only and (
                args.registry is not None or args.suite is not None
            ):
                raise EvaluationMatrixError(
                    "eval doctor --structural-only validates only the Evaluation Matrix "
                    "and cannot be combined with --registry or --suite"
                )
            if not args.structural_only and (
                args.registry is None or args.suite is None
            ):
                raise EvaluationMatrixError(
                    "formal eval doctor requires both --registry and --suite; "
                    "use --structural-only only for Matrix structure validation"
                )
            if args.structural_only:
                status = load_evaluation_matrix(args.matrix)
            else:
                matrix = load_evaluation_matrix(args.matrix, args.registry)
                suite = load_evaluation_suite(args.suite)
                validate_matrix_suite_references(matrix, suite)
                status = {
                    **matrix.as_dict(),
                    "evaluation_suite": suite.as_dict(),
                }
        elif args.command == "component" and args.component_command == "validate":
            status = load_component_manifest(args.manifest).validation_result()
        elif args.command == "component" and args.component_command == "freeze":
            status = freeze_component(args.manifest, args.registry, args.version)
        else:  # pragma: no cover - argparse prevents this state.
            parser.error("unsupported command")
    except (
        ComponentRegistryError,
        EvaluationMatrixError,
        EvaluationSuiteError,
        StorageError,
    ) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    payload = status if isinstance(status, dict) else status.as_dict()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0
