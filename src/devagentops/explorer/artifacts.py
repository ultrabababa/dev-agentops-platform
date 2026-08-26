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

    def runtime_optimization_comparison(
        self, run_a: str, run_b: str
    ) -> dict[str, Any] | None:
        document = self._documents["runtime_optimization"]
        replication = document["replication"]
        reference = replication["single_sequential"]
        treatment = replication["batch_parallel"]
        by_run = {
            reference["run_id"]: reference,
            treatment["run_id"]: treatment,
        }
        if {run_a, run_b} != set(by_run):
            return None

        def values(path: tuple[str, ...]) -> dict[str, Any]:
            def read(run_id: str) -> Any:
                value: Any = by_run[run_id]
                for key in path:
                    value = value[key]
                return value

            return {"a": read(run_a), "b": read(run_b)}

        return {
            "artifact_id": document["milestone_id"],
            "authority": "milestone_artifact",
            "interpretation": (
                "efficiency_reproduced_no_reproducible_material_quality_"
                "regression_demonstrated"
            ),
            "metrics": {
                "model_decisions": values(
                    ("runtime_mechanism", "successful_model_decisions")
                ),
                "executed_tool_calls": values(
                    ("runtime_mechanism", "tool_calls_started")
                ),
                "input_tokens": values(("provider_usage", "input_tokens")),
                "output_tokens": values(("provider_usage", "output_tokens")),
                "total_tokens": values(("provider_usage", "total_tokens")),
                "run_wall_time_seconds": values(("latency", "run_wall_seconds")),
                "mean_sample_latency_seconds": values(
                    ("latency", "sample_duration_seconds", "mean")
                ),
                "p50_sample_latency_seconds": values(
                    ("latency", "sample_duration_seconds", "p50")
                ),
                "p95_sample_latency_seconds": values(
                    ("latency", "sample_duration_seconds", "p95")
                ),
            },
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
