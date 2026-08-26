from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ExplorerArtifactError(RuntimeError):
    """Raised when a machine-readable milestone is missing or malformed."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExplorerArtifactError(f"failed to load milestone artifact {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("milestone_id"), str):
        raise ExplorerArtifactError(f"invalid milestone artifact: {path}")
    return value


class MilestoneArtifacts:
    def __init__(self, paths: dict[str, Path]):
        self._documents = {name: _load(path) for name, path in paths.items()}

    def canonicalization_finding(self) -> dict[str, Any]:
        document = self._documents["canonicalization"]
        replay = document["offline_replay"]
        return {
            "artifact_id": document["milestone_id"],
            "authority": "fixed_output_offline_replay",
            "l4": {
                "protocol_validity_before": replay["l4"]["metrics_before"]["protocol_validity_rate"],
                "protocol_validity_after": replay["l4"]["metrics_after"]["protocol_validity_rate"],
                "unknown_evidence_ids_before": replay["l4"]["unknown_evidence_ids_before"],
                "unknown_evidence_ids_after": replay["l4"]["unknown_evidence_ids_after"],
                "failure_type_exact_match_before": replay["l4"]["metrics_before"]["failure_type_exact_match"],
                "failure_type_exact_match_after": replay["l4"]["metrics_after"]["failure_type_exact_match"],
            },
        }

    def runtime_optimization_finding(self) -> dict[str, Any]:
        document = self._documents["runtime_optimization"]
        replication = document["replication"]
        reference = replication["single_sequential"]
        treatment = replication["batch_parallel"]
        return {
            "artifact_id": document["milestone_id"],
            "authority": "formal_trace_metrics_and_replication",
            "run_ids": [reference["run_id"], treatment["run_id"]],
            "model_decisions": [
                reference["runtime_mechanism"]["successful_model_decisions"],
                treatment["runtime_mechanism"]["successful_model_decisions"],
            ],
            "executed_tool_calls": [
                reference["runtime_mechanism"]["tool_calls_started"],
                treatment["runtime_mechanism"]["tool_calls_started"],
            ],
            "run_wall_seconds": [
                reference["latency"]["run_wall_seconds"],
                treatment["latency"]["run_wall_seconds"],
            ],
            "interpretation": "efficiency_reproduced_no_reproducible_material_quality_regression_demonstrated",
        }

    def retrieval_attribution_finding(self) -> dict[str, Any]:
        document = self._documents["retrieval_attribution"]
        diagnostic = document["acquisition_diagnostic"]
        return {
            "artifact_id": document["milestone_id"],
            "authority": "formal_l3_result_snapshot",
            "run_id": document["run"]["run_id"],
            "retrieval_acquisition_recall": diagnostic["retrieval_acquisition_recall"],
            "acquired_required_evidence_utilization": diagnostic[
                "acquired_required_evidence_utilization"
            ],
            "report_evidence_hit_rate": diagnostic["report_evidence_hit_rate"],
            "report_evidence_improvement_over_l1_l2": document["decision"][
                "report_evidence_improvement_over_l1_l2"
            ],
        }

    def featured_findings(self) -> dict[str, dict[str, Any]]:
        return {
            "canonicalization": self.canonicalization_finding(),
            "runtime_optimization": self.runtime_optimization_finding(),
            "retrieval_attribution": self.retrieval_attribution_finding(),
        }
