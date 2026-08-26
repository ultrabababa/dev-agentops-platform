from __future__ import annotations

import json
from pathlib import Path

from devagentops.explorer.artifacts import MilestoneArtifacts


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_featured_findings_are_read_from_milestone_artifacts(tmp_path: Path) -> None:
    artifacts = MilestoneArtifacts(
        {
            "canonicalization": _write(
                tmp_path / "canonicalization.json",
                {
                    "milestone_id": "canonical-sentinel",
                    "offline_replay": {
                        "l4": {
                            "metrics_before": {"protocol_validity_rate": 0.11, "failure_type_exact_match": 0.33},
                            "metrics_after": {"protocol_validity_rate": 0.22, "failure_type_exact_match": 0.33},
                            "unknown_evidence_ids_before": 7,
                            "unknown_evidence_ids_after": 1,
                        }
                    },
                },
            ),
            "runtime_optimization": _write(
                tmp_path / "runtime.json",
                {
                    "milestone_id": "runtime-sentinel",
                    "replication": {
                        "single_sequential": {
                            "run_id": "a", "runtime_mechanism": {"successful_model_decisions": 9, "tool_calls_started": 8}, "latency": {"run_wall_seconds": 7}
                        },
                        "batch_parallel": {
                            "run_id": "b", "runtime_mechanism": {"successful_model_decisions": 6, "tool_calls_started": 5}, "latency": {"run_wall_seconds": 4}
                        },
                    },
                },
            ),
            "retrieval_attribution": _write(
                tmp_path / "retrieval.json",
                {
                    "milestone_id": "retrieval-sentinel",
                    "run": {"run_id": "c"},
                    "acquisition_diagnostic": {
                        "retrieval_acquisition_recall": 0.44,
                        "acquired_required_evidence_utilization": 0.55,
                        "report_evidence_hit_rate": 0.66,
                    },
                    "decision": {"report_evidence_improvement_over_l1_l2": "not_demonstrated"},
                },
            ),
        }
    )

    findings = artifacts.featured_findings()

    assert findings["canonicalization"]["l4"]["protocol_validity_before"] == 0.11
    assert findings["runtime_optimization"]["model_decisions"] == [9, 6]
    assert findings["retrieval_attribution"]["retrieval_acquisition_recall"] == 0.44
