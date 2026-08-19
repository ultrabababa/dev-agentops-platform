from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest

from devagentops.evaluation.pair_analysis import (
    PairAnalysisError,
    analyze_oracle_agent_pair,
)


def _artifact(
    runtime_variant: str,
    run_id: str,
    *,
    exact: float,
    evidence: float,
    protocol: float = 1.0,
    execution: float = 1.0,
) -> dict:
    metric_vector = {
        "failure_type_exact_match": exact,
        "failure_type_reviewed_acceptable_match": 0.0,
        "report_evidence_hit_rate": evidence,
        "required_fields_completeness": 1.0,
    }
    case = {
        "case_id": "case-a",
        "case_fingerprint": "f" * 64,
        "failure_type": "test_assertion_failure",
        "suite_weight": 1.0,
        "requested_sample_count": 3,
        "scored_sample_count": 3,
        "execution_failed_sample_count": 0,
        "execution_coverage": execution,
        "protocol_valid_sample_count": round(protocol * 3),
        "protocol_invalid_sample_count": 3 - round(protocol * 3),
        "protocol_validity_rate": protocol,
        "metric_vector": metric_vector,
    }
    failure_type = {
        "failure_type": "test_assertion_failure",
        "case_count": 1,
        "execution_coverage": execution,
        "protocol_validity_rate": protocol,
        "metric_vector": metric_vector,
    }
    suite = {
        "total_case_count": 1,
        "execution_coverage": execution,
        "protocol_validity_rate": protocol,
        "metric_vector": metric_vector,
    }
    samples = []
    for repeat_index in range(3):
        valid = protocol == 1.0
        samples.append(
            {
                "case_id": "case-a",
                "repeat_index": repeat_index,
                "outcome": {"status": "scored"},
                "quality_metrics": metric_vector,
                "validation": {
                    "valid": valid,
                    "errors": [] if valid else [{"code": "unknown_evidence_id"}],
                },
                "evidence_diagnostics": {
                    "required_evidence_count": 2,
                    "matched_required_evidence_count": 1,
                },
                "candidate_document": {
                    "root_cause": f"root cause from {runtime_variant}",
                    "evidence_references": [{"evidence_id": "evidence:a"}],
                },
                "terminal_reason": "report_submitted",
                "agent_steps": 4 if runtime_variant != "model_one_shot" else None,
            }
        )
    return {
        "artifact_schema_version": "3",
        "run_id": run_id,
        "manifest": {
            "run_kind": "formal_full_suite",
            "runtime_variant": runtime_variant,
            "evaluation_method": "triage-method-v1",
            "structured_report_schema_version": "1",
            "model_configuration": {
                "provider": "minimax-official",
                "model": "MiniMax-M3",
            },
            "evaluation_suite": {
                "suite_id": "triage-suite-v1",
                "suite_version": "1",
                "suite_fingerprint": "s" * 64,
                "cases": [
                    {
                        "case_id": "case-a",
                        "case_schema_version": "2",
                        "case_fingerprint": "f" * 64,
                        "weight": 1.0,
                    }
                ],
            },
        },
        "case_aggregates": [case],
        "failure_type_aggregates": [failure_type],
        "suite_aggregate": suite,
        "sample_results": samples,
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pair_analysis_writes_full_case_table_and_oracle_minus_agent_gap(
    tmp_path: Path,
) -> None:
    oracle = _artifact("model_one_shot", "oracle-run", exact=0.8, evidence=0.9)
    agent = _artifact(
        "self_built_react",
        "agent-run",
        exact=0.7,
        evidence=0.6,
        protocol=2 / 3,
    )
    oracle_path = tmp_path / "oracle.json"
    agent_path = tmp_path / "agent.json"
    _write(oracle_path, oracle)
    _write(agent_path, agent)

    status = analyze_oracle_agent_pair(
        oracle_path=oracle_path,
        agent_path=agent_path,
        output_dir=tmp_path / "pair",
    )

    assert status["status"] == "completed"
    assert status["case_count"] == 1
    assert status["detailed_review_case_count"] == 1
    pair = json.loads((tmp_path / "pair/pair-analysis.json").read_text())
    assert pair["gap_definition"] == "oracle_minus_agent"
    assert pair["suite"]["primary_metrics"]["failure_type_exact_match"]["gap"] == pytest.approx(0.1)
    assert pair["suite"]["primary_metrics"]["report_evidence_hit_rate"]["gap"] == pytest.approx(0.3)
    assert pair["suite"]["primary_metrics"]["protocol_validity_rate"]["gap"] == pytest.approx(1 / 3)
    assert len(pair["cases"]) == 1
    assert len(pair["cases"][0]["oracle"]["repeats"]) == 3
    assert len(pair["cases"][0]["agent"]["repeats"]) == 3
    markdown = (tmp_path / "pair/pair-analysis.md").read_text()
    assert "## All Cases" in markdown
    assert "## Detailed Review" in markdown
    assert "_Pending causal analysis._" in markdown


def test_pair_analysis_rejects_different_suite_or_model(tmp_path: Path) -> None:
    oracle = _artifact("model_one_shot", "oracle-run", exact=1.0, evidence=1.0)
    agent = _artifact("self_built_react", "agent-run", exact=1.0, evidence=1.0)
    agent["manifest"]["evaluation_suite"]["suite_fingerprint"] = "x" * 64
    _write(tmp_path / "oracle.json", oracle)
    _write(tmp_path / "agent.json", agent)

    with pytest.raises(PairAnalysisError, match="suite fingerprints differ"):
        analyze_oracle_agent_pair(
            oracle_path=tmp_path / "oracle.json",
            agent_path=tmp_path / "agent.json",
            output_dir=tmp_path / "pair",
        )

    agent = deepcopy(oracle)
    agent["run_id"] = "agent-run"
    agent["manifest"]["runtime_variant"] = "self_built_react"
    agent["manifest"]["model_configuration"]["model"] = "OtherModel"
    _write(tmp_path / "agent.json", agent)
    with pytest.raises(PairAnalysisError, match="model names differ"):
        analyze_oracle_agent_pair(
            oracle_path=tmp_path / "oracle.json",
            agent_path=tmp_path / "agent.json",
            output_dir=tmp_path / "pair",
        )


def test_optional_agent_database_joins_persisted_trajectory(tmp_path: Path) -> None:
    oracle = _artifact("model_one_shot", "oracle-run", exact=1.0, evidence=1.0)
    agent = _artifact("self_built_react", "agent-run", exact=1.0, evidence=0.5)
    _write(tmp_path / "oracle.json", oracle)
    _write(tmp_path / "agent.json", agent)

    database = tmp_path / "agent.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE evaluation_runs (run_id TEXT, runtime_variant TEXT)"
        )
        connection.execute(
            "CREATE TABLE evaluation_sample_trajectory_messages ("
            "run_id TEXT, case_id TEXT, repeat_index INTEGER, message_index INTEGER, "
            "message_role TEXT, message_json TEXT, message_sha256 TEXT)"
        )
        connection.execute(
            "INSERT INTO evaluation_runs VALUES (?, ?)",
            ("agent-run", "self_built_react"),
        )
        assistant = {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_call",
                    "id": "call-1",
                    "name": "read",
                    "arguments": {"path": "raw-log.txt"},
                    "raw_arguments": None,
                }
            ],
        }
        tool_result = {
            "role": "tool_result",
            "tool_call_id": "call-1",
            "tool_name": "read",
            "content": "failure evidence",
            "is_error": False,
        }
        for index, message in enumerate((assistant, tool_result)):
            connection.execute(
                "INSERT INTO evaluation_sample_trajectory_messages VALUES "
                "(?, ?, ?, ?, ?, ?, ?)",
                (
                    "agent-run",
                    "case-a",
                    0,
                    index,
                    message["role"],
                    json.dumps(message),
                    "hash",
                ),
            )

    status = analyze_oracle_agent_pair(
        oracle_path=tmp_path / "oracle.json",
        agent_path=tmp_path / "agent.json",
        output_dir=tmp_path / "pair",
        agent_database=database,
    )

    assert status["trajectory_available"] is True
    pair = json.loads((tmp_path / "pair/pair-analysis.json").read_text())
    repeat = pair["cases"][0]["agent"]["repeats"][0]
    assert repeat["trajectory_summary"] == {
        "message_count": 2,
        "tool_calls": 1,
        "tool_errors": 0,
        "tools": {"read": 1},
    }
    assert repeat["trajectory"][1]["content"] == "failure evidence"
