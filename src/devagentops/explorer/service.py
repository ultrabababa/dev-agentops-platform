from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devagentops.explorer.artifacts import MilestoneArtifacts
from devagentops.explorer.catalog import EvaluationCatalog
from devagentops.explorer.repository import EvaluationRepository
from devagentops.explorer.schemas import (
    TokenUsageDTO,
    ToolCallDTO,
    TraceEventDTO,
    TraceResponseDTO,
    TrajectoryMessageDTO,
    TrajectoryResponseDTO,
)


_SAFE_TRACE_KEYS = {
    "sample_sequence", "step", "steps", "attempt_index", "latency_ms",
    "raw_stop_reason", "returned_model", "stop_reason", "code", "http_status",
    "status", "terminal_reason", "case_count", "failed_sample_count",
    "planned_sample_count", "scored_sample_count", "suite_quality_status",
    "tool_call_id", "tool_name", "truncated", "result_metadata",
    "quality_metrics",
}


class ExplorerService:
    def __init__(self, catalog_path: Path):
        self.catalog = EvaluationCatalog(catalog_path)
        self.repository = EvaluationRepository(self.catalog)
        artifacts = self.catalog.document.get("artifacts", {})
        self.artifacts = MilestoneArtifacts(
            {
                name: self.catalog.resource_path(path)
                for name, path in artifacts.items()
                if isinstance(name, str) and isinstance(path, str)
            }
        )
        self._cases = self._load_cases()

    def _load_cases(self) -> list[dict[str, Any]]:
        suite_config = self.catalog.document.get("suite", {})
        manifest_path = self.catalog.resource_path(suite_config["manifest"])
        suite = json.loads(manifest_path.read_text(encoding="utf-8"))
        failure_types = {
            row["case_id"]: row["failure_type"]
            for row in self.repository.list_run_cases(
                "5dd0f286-ae66-4374-a935-bc6d53e15742"
            )
        }
        cases: list[dict[str, Any]] = []
        for entry in suite["cases"]:
            case_path = (manifest_path.parent / entry["manifest"]).resolve(strict=True)
            case = json.loads(case_path.read_text(encoding="utf-8"))
            provenance = case.get("provenance", {})
            sanitization = case.get("sanitization", {})
            cases.append(
                {
                    "case_id": entry["case_id"],
                    "weight": entry["weight"],
                    "failure_type": failure_types[entry["case_id"]],
                    "case_schema_version": case.get("case_schema_version"),
                    "case_fingerprint": case.get("case_fingerprint"),
                    "provenance": {
                        key: provenance.get(key)
                        for key in (
                            "source_type", "source_url_or_construction_note",
                            "license_or_permission",
                        )
                    },
                    "sanitization": {"status": sanitization.get("status")},
                }
            )
        return cases

    def overview(self) -> dict[str, Any]:
        suite = self.catalog.document["suite"]
        representatives = {
            run.condition_family: {
                "run_id": run.run_id,
                "runtime_variant": run.runtime_variant,
            }
            for run in self.catalog.runs
            if run.representative
        }
        return {
            "benchmark": {
                "case_count": suite["case_count"],
                "repeats_per_case": suite["repeats_per_case"],
                "samples_per_formal_run": suite["samples_per_formal_run"],
                "failure_type_count": suite["failure_type_count"],
            },
            "representative_conditions": representatives,
            "experiment_evolution_endpoint": "/api/experiments/evolution",
            "featured_findings": self.artifacts.featured_findings(),
        }

    def list_conditions(self) -> list[dict[str, Any]]:
        order = ("L1", "L2", "L3", "L4", "Oracle")
        return [self.get_condition(name) for name in order]

    def get_condition(self, condition: str) -> dict[str, Any]:
        normalized = condition.lower()
        run = next(
            (
                item
                for item in self.catalog.runs
                if item.representative and item.condition_family.lower() == normalized
            ),
            None,
        )
        if run is None:
            raise KeyError(condition)
        detail = self.repository.get_run(run.run_id)
        related = [
            item.run_id
            for item in self.catalog.runs
            if item.condition_family == run.condition_family and item.run_id != run.run_id
        ]
        return {
            "condition": run.condition_family,
            "runtime_variant": run.runtime_variant,
            "representative_run": detail,
            "formal_metric_vector": (
                detail["suite_aggregate"]["formal_metric_vector"]
                if detail["suite_aggregate"] is not None
                else None
            ),
            "related_run_ids": related,
            "comparison_group": run.comparison_group,
        }

    def experiment_evolution(self) -> dict[str, Any]:
        findings = self.artifacts.featured_findings()
        stages = []
        for stage, artifact_key in (
            ("baseline", None),
            ("canonicalization", "canonicalization"),
            ("runtime_optimization", "runtime_optimization"),
            ("retrieval_attribution", "retrieval_attribution"),
        ):
            stages.append(
                {
                    "stage": stage,
                    "run_ids": [run.run_id for run in self.catalog.runs if run.stage == stage],
                    "artifact_id": (
                        findings[artifact_key]["artifact_id"] if artifact_key else None
                    ),
                    "key_observation": findings.get(artifact_key) if artifact_key else None,
                }
            )
        return {"stages": stages}

    def list_cases(self) -> list[dict[str, Any]]:
        return list(self._cases)

    def get_case(self, case_id: str) -> dict[str, Any]:
        for case in self._cases:
            if case["case_id"] == case_id:
                return dict(case)
        raise KeyError(case_id)

    def trajectory(self, run_id: str, case_id: str, repeat_index: int) -> TrajectoryResponseDTO:
        self.repository.get_sample(run_id, case_id, repeat_index)
        rows = self.repository.get_trajectory(run_id, case_id, repeat_index)
        messages = [self._trajectory_message(row) for row in rows]
        return TrajectoryResponseDTO(
            run_id=run_id, case_id=case_id, repeat_index=repeat_index, messages=messages
        )

    @staticmethod
    def _trajectory_message(row: dict[str, Any]) -> TrajectoryMessageDTO:
        message = row["message"]
        role = message.get("role", row["message_role"])
        visible_parts: list[str] = []
        tool_calls: list[ToolCallDTO] = []
        content = message.get("content")
        if isinstance(content, str):
            visible_parts.append(content)
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    visible_parts.append(item["text"])
                elif item.get("type") == "tool_call":
                    call_id = item.get("id") or item.get("tool_call_id")
                    name = item.get("name") or item.get("tool_name")
                    if isinstance(call_id, str) and isinstance(name, str):
                        arguments = item.get("arguments")
                        tool_calls.append(
                            ToolCallDTO(
                                tool_call_id=call_id,
                                tool_name=name,
                                arguments=arguments if isinstance(arguments, dict) else None,
                            )
                        )
        usage_value = message.get("usage")
        usage = None
        if isinstance(usage_value, dict):
            usage = TokenUsageDTO(
                **{
                    key: usage_value.get(key)
                    for key in ("input_tokens", "output_tokens", "total_tokens")
                }
            )
        return TrajectoryMessageDTO(
            message_index=row["message_index"],
            role=role,
            visible_content="\n".join(visible_parts) if visible_parts else None,
            tool_calls=tool_calls,
            tool_name=message.get("tool_name") if role == "tool_result" else None,
            tool_call_id=message.get("tool_call_id") if role == "tool_result" else None,
            is_error=message.get("is_error") if role == "tool_result" else None,
            stop_reason=message.get("stop_reason") if role == "assistant" else None,
            raw_stop_reason=message.get("raw_stop_reason") if role == "assistant" else None,
            response_model=message.get("response_model") if role == "assistant" else None,
            usage=usage,
        )

    def trace(self, run_id: str, case_id: str, repeat_index: int) -> TraceResponseDTO:
        self.repository.get_sample(run_id, case_id, repeat_index)
        events = []
        for row in self.repository.get_trace(run_id, case_id, repeat_index):
            payload = {
                key: value
                for key, value in row["payload"].items()
                if key in _SAFE_TRACE_KEYS
            }
            usage = row["payload"].get("usage")
            if isinstance(usage, dict):
                payload["usage"] = {
                    key: usage.get(key)
                    for key in ("input_tokens", "output_tokens", "total_tokens")
                }
            events.append(
                TraceEventDTO(
                    sequence=row["sequence"],
                    event_type=row["event_type"],
                    occurred_at=row["occurred_at"],
                    payload=payload,
                )
            )
        return TraceResponseDTO(
            run_id=run_id, case_id=case_id, repeat_index=repeat_index, events=events
        )

    def comparisons(self) -> list[dict[str, Any]]:
        return list(self.catalog.document.get("comparisons", []))

    def compare(self, run_a: str, run_b: str) -> dict[str, Any]:
        left = self.repository.get_run(run_a)
        right = self.repository.get_run(run_b)
        left_manifest = left["manifest"]
        right_manifest = right["manifest"]
        signals = {
            "same_suite": left["suite_id"] == right["suite_id"] and left["suite_version"] == right["suite_version"],
            "same_suite_fingerprint": left_manifest["suite_fingerprint"] == right_manifest["suite_fingerprint"],
            "same_model_configuration": left_manifest["model_configuration"] == right_manifest["model_configuration"],
            "same_evaluation_method": left_manifest["evaluation_method"] == right_manifest["evaluation_method"],
            "same_output_contract": left_manifest["output_contract"] == right_manifest["output_contract"],
            "same_code_revision": left_manifest["code_revision"] == right_manifest["code_revision"],
            "same_runtime_variant": left["runtime_variant"] == right["runtime_variant"],
            "same_treatment": left_manifest["treatment_fingerprint"] == right_manifest["treatment_fingerprint"],
        }
        preset = next(
            (
                item for item in self.comparisons()
                if {item["run_a"], item["run_b"]} == {run_a, run_b}
            ),
            None,
        )
        if preset is not None:
            category = preset["category"]
        elif "baseline" in {left["catalog"]["stage"], right["catalog"]["stage"]}:
            category = "historical_comparison"
        elif signals["same_suite_fingerprint"]:
            category = "operational_comparison"
        else:
            category = "not_comparable"
        return {
            "run_a": left,
            "run_b": right,
            "compatibility": signals,
            "semantic_category": category,
            "causal_claim_supported": False,
            "causal_reference": "canonicalization_fixed_output_replay" if category != "not_comparable" else None,
        }
