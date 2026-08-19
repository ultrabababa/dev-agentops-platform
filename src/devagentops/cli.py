from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from devagentops.evaluation.components import (
    ComponentRegistryError,
    freeze_component,
    load_component_manifest,
)
from devagentops.config import DEFAULT_DATABASE_PATH
from devagentops.evaluation.matrix import (
    EvaluationMatrixError,
    load_evaluation_matrix,
)
from devagentops.evaluation.debug import run_case_subset_debug
from devagentops.evaluation.pair_analysis import (
    PairAnalysisError,
    analyze_oracle_agent_pair,
)
from devagentops.evaluation.preflight import run_formal_eval_doctor
from devagentops.evaluation.run import EvaluationRunError, run_evaluation
from devagentops.evaluation.suite import (
    EvaluationSuiteError,
    load_case_package,
)
from devagentops.scoring.case import evaluate_case_report
from devagentops.storage.database import (
    StorageError,
    initialize_database,
    inspect_database,
)
from devagentops.scoring.report import ReportInputError, load_candidate_report_json


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
    score_parser = eval_subcommands.add_parser(
        "score",
        help="Validate and deterministically score one candidate report against a case.",
    )
    score_parser.add_argument(
        "--case",
        type=Path,
        required=True,
        help="Path to a verified Offline Case Package manifest.",
    )
    score_parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to a candidate Structured Triage Report JSON file.",
    )
    run_parser = eval_subcommands.add_parser(
        "run",
        help="Run one repository-defined evaluation after complete formal preflight.",
    )
    run_parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to a repository-defined evaluation matrix JSON file.",
    )
    run_parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Path to the repository component registry used for formal preflight.",
    )
    run_parser.add_argument(
        "--suite",
        type=Path,
        required=True,
        help="Path to the explicit evaluation suite manifest.",
    )
    run_parser.add_argument(
        "--condition",
        required=True,
        help="ID of the resolved evaluation condition to run.",
    )
    run_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite file path (default: {DEFAULT_DATABASE_PATH}).",
    )
    run_parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path(".devagentops/evaluation-artifacts"),
        help="Ignored directory for generated JSON and Markdown artifacts.",
    )
    debug_parser = eval_subcommands.add_parser(
        "debug",
        help="Run an explicit L1 Case subset for exploratory diagnosis.",
    )
    debug_parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to a repository-defined L1 debug matrix JSON file.",
    )
    debug_parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Path to the repository component registry used for formal preflight.",
    )
    debug_parser.add_argument(
        "--suite",
        type=Path,
        required=True,
        help="Path to the explicit evaluation suite manifest.",
    )
    debug_parser.add_argument(
        "--condition",
        required=True,
        help="ID of the resolved L1 debug condition to run.",
    )
    debug_parser.add_argument(
        "--case",
        dest="case_ids",
        action="append",
        default=[],
        help="Case ID to include; repeat for an explicit subset.",
    )
    debug_parser.add_argument(
        "--database",
        type=_database_path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite file path (default: {DEFAULT_DATABASE_PATH}).",
    )
    debug_parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path(".devagentops/evaluation-artifacts"),
        help="Ignored directory for generated JSON and Markdown artifacts.",
    )
    pair_parser = eval_subcommands.add_parser(
        "pair",
        help="Compare one Oracle formal artifact with one Agent formal artifact.",
    )
    pair_parser.add_argument(
        "--oracle",
        type=Path,
        required=True,
        help="Path to the Oracle evaluation.json artifact.",
    )
    pair_parser.add_argument(
        "--agent",
        type=Path,
        required=True,
        help="Path to the Agent evaluation.json artifact.",
    )
    pair_parser.add_argument(
        "--agent-database",
        type=_database_path,
        help="Optional SQLite database containing persisted Agent trajectories.",
    )
    pair_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".devagentops/pair-analysis"),
        help="Directory for pair-analysis.json and pair-analysis.md.",
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
    exit_code = 0

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
                status = run_formal_eval_doctor(
                    args.matrix,
                    args.registry,
                    args.suite,
                )
        elif args.command == "eval" and args.eval_command == "score":
            package = load_case_package(args.case)
            raw_report = load_candidate_report_json(args.report)
            status = evaluate_case_report(raw_report, package)
        elif args.command == "eval" and args.eval_command == "run":
            status = run_evaluation(
                matrix_path=args.matrix,
                registry_path=args.registry,
                suite_path=args.suite,
                condition_id=args.condition,
                database_path=args.database,
                artifacts_dir=args.artifacts_dir,
            )
            if status["status"] == "completed_with_sample_failures":
                exit_code = 1
        elif args.command == "eval" and args.eval_command == "debug":
            status = run_case_subset_debug(
                matrix_path=args.matrix,
                registry_path=args.registry,
                suite_path=args.suite,
                condition_id=args.condition,
                case_ids=args.case_ids,
                database_path=args.database,
                artifacts_dir=args.artifacts_dir,
            )
            if status["status"] in {
                "completed_with_case_failures",
                "completed_with_sample_failures",
            }:
                exit_code = 1
        elif args.command == "eval" and args.eval_command == "pair":
            status = analyze_oracle_agent_pair(
                oracle_path=args.oracle,
                agent_path=args.agent,
                agent_database=args.agent_database,
                output_dir=args.output_dir,
            )
        elif args.command == "component" and args.component_command == "validate":
            status = load_component_manifest(args.manifest).validation_result()
        elif args.command == "component" and args.component_command == "freeze":
            status = freeze_component(args.manifest, args.registry, args.version)
        else:  # pragma: no cover - argparse prevents this state.
            parser.error("unsupported command")
    except EvaluationSuiteError as exc:
        print(
            json.dumps(
                {"error": exc.public_message, "code": exc.code},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    except (
        ComponentRegistryError,
        EvaluationMatrixError,
        PairAnalysisError,
        ReportInputError,
        StorageError,
    ) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except EvaluationRunError as exc:
        print(
            json.dumps(
                {"error": str(exc), "code": exc.code},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    payload = status if isinstance(status, dict) else status.as_dict()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return exit_code
