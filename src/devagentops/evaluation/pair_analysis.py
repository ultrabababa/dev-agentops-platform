from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


PRIMARY_METRICS = (
    "failure_type_exact_match",
    "report_evidence_hit_rate",
    "protocol_validity_rate",
)
AUXILIARY_METRICS = ("required_fields_completeness", "execution_coverage")


class PairAnalysisError(RuntimeError):
    pass


def analyze_oracle_agent_pair(
    *,
    oracle_path: Path,
    agent_path: Path,
    output_dir: Path,
    agent_database: Path | None = None,
) -> dict[str, Any]:
    oracle = _load(oracle_path)
    agent = _load(agent_path)
    identity = _validate(oracle, agent)
    trajectories = (
        _load_trajectories(agent_database, agent["run_id"])
        if agent_database is not None
        else {}
    )
    document = _build(oracle, agent, identity, trajectories)
    paths = _write(output_dir, document)
    return {
        "status": "completed",
        "oracle_run_id": oracle["run_id"],
        "agent_run_id": agent["run_id"],
        "case_count": len(document["cases"]),
        "detailed_review_case_count": sum(
            row["detailed_review_required"] for row in document["cases"]
        ),
        "trajectory_available": bool(trajectories),
        "artifacts": paths,
    }


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PairAnalysisError(f"cannot read evaluation artifact {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PairAnalysisError("evaluation artifact must be a JSON object")
    return data


def _validate(oracle: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    om = oracle.get("manifest", {})
    am = agent.get("manifest", {})
    if om.get("run_kind") != "formal_full_suite" or am.get("run_kind") != "formal_full_suite":
        raise PairAnalysisError("pair analysis requires two formal_full_suite artifacts")
    if om.get("runtime_variant") != "model_one_shot":
        raise PairAnalysisError("oracle artifact must use model_one_shot")
    if am.get("runtime_variant") == "model_one_shot":
        raise PairAnalysisError("agent artifact must use a non-Oracle runtime")

    osuite = om.get("evaluation_suite", {})
    asuite = am.get("evaluation_suite", {})
    if osuite.get("suite_fingerprint") != asuite.get("suite_fingerprint"):
        raise PairAnalysisError("suite fingerprints differ")
    oracle_model = _model(om)
    agent_model = _model(am)
    if not oracle_model or not agent_model:
        raise PairAnalysisError("model name is missing")
    if oracle_model != agent_model:
        raise PairAnalysisError("model names differ")
    if om.get("evaluation_method") != am.get("evaluation_method"):
        raise PairAnalysisError("evaluation methods differ")
    if om.get("structured_report_schema_version") != am.get(
        "structured_report_schema_version"
    ):
        raise PairAnalysisError("report schema versions differ")
    if _case_identity(osuite) != _case_identity(asuite):
        raise PairAnalysisError("Case identities differ")

    return {
        "suite_id": osuite.get("suite_id"),
        "suite_version": osuite.get("suite_version"),
        "suite_fingerprint": osuite.get("suite_fingerprint"),
        "model": oracle_model,
        "evaluation_method": om.get("evaluation_method"),
        "structured_report_schema_version": om.get("structured_report_schema_version"),
        "oracle_runtime_variant": om.get("runtime_variant"),
        "agent_runtime_variant": am.get("runtime_variant"),
    }


def _model(manifest: dict[str, Any]) -> str | None:
    config = manifest.get("model_configuration")
    if isinstance(config, dict):
        return config.get("model")
    treatment = manifest.get("treatment")
    return treatment.get("model") if isinstance(treatment, dict) else None


def _case_identity(suite: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    return {
        item["case_id"]: (
            item.get("case_fingerprint"),
            item.get("case_schema_version"),
            item.get("weight"),
        )
        for item in suite.get("cases", [])
    }


def _build(
    oracle: dict[str, Any],
    agent: dict[str, Any],
    identity: dict[str, Any],
    trajectories: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, Any]:
    ocases = {row["case_id"]: row for row in oracle["case_aggregates"]}
    acases = {row["case_id"]: row for row in agent["case_aggregates"]}
    if ocases.keys() != acases.keys():
        raise PairAnalysisError("case aggregate sets differ")

    osamples = _group_samples(oracle)
    asamples = _group_samples(agent)
    cases = []
    for row in oracle["case_aggregates"]:
        case_id = row["case_id"]
        primary = _compare(row, acases[case_id], PRIMARY_METRICS)
        auxiliary = _compare(row, acases[case_id], AUXILIARY_METRICS)
        protocol = primary["protocol_validity_rate"]
        execution = auxiliary["execution_coverage"]
        detailed = (
            any(_nonzero(item["gap"]) for item in primary.values())
            or any(
                value is not None and value < 1.0
                for value in (protocol["oracle"], protocol["agent"])
            )
            or any(
                value is not None and value < 1.0
                for value in (execution["oracle"], execution["agent"])
            )
        )
        cases.append(
            {
                "case_id": case_id,
                "failure_type": row["failure_type"],
                "primary_metrics": primary,
                "auxiliary_metrics": auxiliary,
                "detailed_review_required": detailed,
                "oracle": {
                    "aggregate": row,
                    "repeats": [_sample(s) for s in osamples.get(case_id, [])],
                },
                "agent": {
                    "aggregate": acases[case_id],
                    "repeats": [
                        _sample(
                            s,
                            trajectories.get((case_id, s["repeat_index"])),
                        )
                        for s in asamples.get(case_id, [])
                    ],
                },
            }
        )

    otypes = {row["failure_type"]: row for row in oracle["failure_type_aggregates"]}
    atypes = {row["failure_type"]: row for row in agent["failure_type_aggregates"]}
    if otypes.keys() != atypes.keys():
        raise PairAnalysisError("failure-type aggregate sets differ")
    failure_types = [
        {
            "failure_type": row["failure_type"],
            "primary_metrics": _compare(
                row, atypes[row["failure_type"]], PRIMARY_METRICS
            ),
            "auxiliary_metrics": _compare(
                row, atypes[row["failure_type"]], AUXILIARY_METRICS
            ),
        }
        for row in oracle["failure_type_aggregates"]
    ]

    return {
        "artifact_schema_version": "1",
        "analysis_type": "oracle_agent_pair",
        "gap_definition": "oracle_minus_agent",
        "primary_metrics": list(PRIMARY_METRICS),
        "auxiliary_metrics": list(AUXILIARY_METRICS),
        "identity": identity,
        "oracle_run_id": oracle["run_id"],
        "agent_run_id": agent["run_id"],
        "suite": {
            "primary_metrics": _compare(
                oracle["suite_aggregate"], agent["suite_aggregate"], PRIMARY_METRICS
            ),
            "auxiliary_metrics": _compare(
                oracle["suite_aggregate"], agent["suite_aggregate"], AUXILIARY_METRICS
            ),
        },
        "failure_types": failure_types,
        "cases": cases,
    }


def _group_samples(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for sample in document.get("sample_results", []):
        grouped.setdefault(sample["case_id"], []).append(sample)
    for samples in grouped.values():
        samples.sort(key=lambda item: item["repeat_index"])
    return grouped


def _compare(
    oracle: dict[str, Any],
    agent: dict[str, Any],
    metrics: tuple[str, ...],
) -> dict[str, dict[str, float | None]]:
    return {
        metric: _pair(_value(oracle, metric), _value(agent, metric))
        for metric in metrics
    }


def _value(aggregate: dict[str, Any], metric: str) -> float | None:
    if metric in {"protocol_validity_rate", "execution_coverage"}:
        value = aggregate.get(metric)
    else:
        vector = aggregate.get("metric_vector")
        value = vector.get(metric) if isinstance(vector, dict) else None
    return None if value is None else float(value)


def _pair(oracle: float | None, agent: float | None) -> dict[str, float | None]:
    return {
        "oracle": oracle,
        "agent": agent,
        "gap": None if oracle is None or agent is None else oracle - agent,
    }


def _sample(
    sample: dict[str, Any],
    trajectory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = {
        "repeat_index": sample["repeat_index"],
        "outcome": sample["outcome"],
        "quality_metrics": sample.get("quality_metrics"),
        "validation": sample.get("validation"),
        "evidence_diagnostics": sample.get("evidence_diagnostics"),
        "candidate_document": sample.get("candidate_document"),
        "terminal_reason": sample.get("terminal_reason"),
        "agent_steps": sample.get("agent_steps"),
    }
    if trajectory is not None:
        result["trajectory"] = trajectory
        result["trajectory_summary"] = _trajectory_summary(trajectory)
    return result


def _trajectory_summary(messages: list[dict[str, Any]]) -> dict[str, Any]:
    tool_calls: Counter[str] = Counter()
    tool_errors = 0
    for message in messages:
        if message.get("role") == "assistant":
            for block in message.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_call":
                    tool_calls[str(block.get("name"))] += 1
        elif message.get("role") == "tool_result" and message.get("is_error"):
            tool_errors += 1
    return {
        "message_count": len(messages),
        "tool_calls": sum(tool_calls.values()),
        "tool_errors": tool_errors,
        "tools": dict(sorted(tool_calls.items())),
    }


def _load_trajectories(
    database_path: Path,
    run_id: str,
) -> dict[tuple[str, int], list[dict[str, Any]]]:
    path = database_path.expanduser()
    if not path.exists():
        raise PairAnalysisError(f"agent database does not exist: {path}")
    try:
        with sqlite3.connect(path) as connection:
            exists = connection.execute(
                "SELECT 1 FROM evaluation_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if exists is None:
                raise PairAnalysisError(f"agent database does not contain run {run_id}")
            rows = connection.execute(
                "SELECT case_id, repeat_index, message_json "
                "FROM evaluation_sample_trajectory_messages "
                "WHERE run_id = ? ORDER BY case_id, repeat_index, message_index",
                (run_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        raise PairAnalysisError(f"cannot read agent trajectories: {exc}") from exc

    result: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for case_id, repeat_index, message_json in rows:
        result.setdefault((case_id, repeat_index), []).append(json.loads(message_json))
    return result


def _write(output_dir: Path, document: dict[str, Any]) -> dict[str, str]:
    root = output_dir.expanduser().resolve(strict=False)
    try:
        root.mkdir(parents=True, exist_ok=True)
        json_path = root / "pair-analysis.json"
        md_path = root / "pair-analysis.md"
        json_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(_markdown(document), encoding="utf-8")
    except OSError as exc:
        raise PairAnalysisError(f"cannot write pair-analysis artifacts: {exc}") from exc
    return {"json": str(json_path), "markdown": str(md_path)}


def _markdown(document: dict[str, Any]) -> str:
    identity = document["identity"]
    lines = [
        "# Oracle ↔ Agent Pair Analysis",
        "",
        "## Pair Identity",
        "",
        f"- Oracle run: `{document['oracle_run_id']}`",
        f"- Agent run: `{document['agent_run_id']}`",
        f"- Suite: `{identity['suite_id']}` version `{identity['suite_version']}`",
        f"- Model: `{identity['model']}`",
        "- Gap: `Oracle - Agent`",
        "",
        "## Suite Realization Gap",
        "",
        _metric_table(document["suite"]["primary_metrics"]),
        "",
        "### Auxiliary observations",
        "",
        _metric_table(document["suite"]["auxiliary_metrics"]),
        "",
        "## By Failure Type",
        "",
        "| Failure Type | Taxonomy Gap | Evidence Gap | Protocol Gap |",
        "|---|---:|---:|---:|",
    ]
    for item in document["failure_types"]:
        metrics = item["primary_metrics"]
        lines.append(
            "| `{}` | {} | {} | {} |".format(
                item["failure_type"],
                _fmt(metrics["failure_type_exact_match"]["gap"]),
                _fmt(metrics["report_evidence_hit_rate"]["gap"]),
                _fmt(metrics["protocol_validity_rate"]["gap"]),
            )
        )

    lines += [
        "",
        "## All Cases",
        "",
        "| Case | Failure Type | Taxonomy O→A (Gap) | Evidence O→A (Gap) | "
        "Protocol O→A (Gap) | Execution O/A | Detail |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for case in document["cases"]:
        p, a = case["primary_metrics"], case["auxiliary_metrics"]
        lines.append(
            "| `{}` | `{}` | {} | {} | {} | {}/{} | {} |".format(
                case["case_id"],
                case["failure_type"],
                _transition(p["failure_type_exact_match"]),
                _transition(p["report_evidence_hit_rate"]),
                _transition(p["protocol_validity_rate"]),
                _fmt(a["execution_coverage"]["oracle"]),
                _fmt(a["execution_coverage"]["agent"]),
                "yes" if case["detailed_review_required"] else "no",
            )
        )

    lines += ["", "## Detailed Review", ""]
    detailed = [case for case in document["cases"] if case["detailed_review_required"]]
    if not detailed:
        lines.append("No Case requires detailed review.")
    for case in detailed:
        lines += [
            f"### `{case['case_id']}`",
            "",
            _metric_table({**case["primary_metrics"], **case["auxiliary_metrics"]}),
            "",
            "#### Oracle repeats",
            "",
            *_repeat_lines(case["oracle"]["repeats"]),
            "",
            "#### Agent repeats",
            "",
            *_repeat_lines(case["agent"]["repeats"], include_trajectory=True),
            "",
            "#### Human / AI analysis",
            "",
            "_Pending causal analysis._",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _repeat_lines(
    repeats: list[dict[str, Any]],
    *,
    include_trajectory: bool = False,
) -> list[str]:
    lines: list[str] = []
    for repeat in repeats:
        metrics = repeat.get("quality_metrics") or {}
        validation = repeat.get("validation") or {}
        lines.append(
            "- r{}: outcome=`{}`, taxonomy={}, evidence={}, protocol_valid={}".format(
                repeat["repeat_index"],
                repeat["outcome"].get("status"),
                _fmt(metrics.get("failure_type_exact_match")),
                _fmt(metrics.get("report_evidence_hit_rate")),
                validation.get("valid"),
            )
        )
        candidate = repeat.get("candidate_document")
        if isinstance(candidate, dict):
            if candidate.get("root_cause"):
                lines.append(f"  - Root cause: {candidate['root_cause']}")
            evidence = [
                ref["evidence_id"]
                for ref in candidate.get("evidence_references", [])
                if isinstance(ref, dict) and ref.get("evidence_id")
            ]
            if evidence:
                lines.append("  - Evidence: " + ", ".join(f"`{x}`" for x in evidence))
        if validation.get("errors"):
            lines.append(
                "  - Validation: `"
                + json.dumps(validation["errors"], ensure_ascii=False, sort_keys=True)
                + "`"
            )
        if include_trajectory and repeat.get("trajectory_summary"):
            lines.append(
                "  - Trajectory: `"
                + json.dumps(
                    repeat["trajectory_summary"], ensure_ascii=False, sort_keys=True
                )
                + "`"
            )
    return lines or ["- No repeat observations."]


def _metric_table(metrics: dict[str, dict[str, float | None]]) -> str:
    rows = ["| Metric | Oracle | Agent | Gap |", "|---|---:|---:|---:|"]
    rows += [
        f"| `{name}` | {_fmt(pair['oracle'])} | {_fmt(pair['agent'])} | "
        f"{_fmt(pair['gap'])} |"
        for name, pair in metrics.items()
    ]
    return "\n".join(rows)


def _transition(pair: dict[str, float | None]) -> str:
    return f"{_fmt(pair['oracle'])}→{_fmt(pair['agent'])} ({_fmt(pair['gap'])})"


def _nonzero(value: float | None) -> bool:
    return value is not None and abs(value) > 1e-12


def _fmt(value: Any) -> str:
    return "n/a" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)
