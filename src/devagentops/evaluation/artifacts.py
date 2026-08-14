from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


class EvaluationArtifactError(RuntimeError):
    """Raised when generated evaluation artifacts cannot be finalized."""


def write_evaluation_artifacts(
    artifacts_dir: Path,
    document: dict[str, Any],
) -> dict[str, str]:
    root = artifacts_dir.expanduser().resolve(strict=False)
    run_directory = root / document["run_id"]
    if run_directory.exists():
        raise EvaluationArtifactError(
            f"evaluation artifact directory already exists: {run_directory}"
        )
    temporary_directory: Path | None = None
    try:
        root.mkdir(parents=True, exist_ok=True)
        temporary_directory = Path(
            tempfile.mkdtemp(prefix=f".{document['run_id']}.", dir=root)
        )
        json_path = temporary_directory / "evaluation.json"
        markdown_path = temporary_directory / "evaluation.md"
        json_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(_render_markdown(document), encoding="utf-8")
        temporary_directory.replace(run_directory)
        temporary_directory = None
    except OSError as exc:
        raise EvaluationArtifactError(
            f"failed to write evaluation artifacts under {root}: {exc}"
        ) from exc
    finally:
        if temporary_directory is not None:
            shutil.rmtree(temporary_directory, ignore_errors=True)
    return {
        "json": str(run_directory / "evaluation.json"),
        "markdown": str(run_directory / "evaluation.md"),
    }


def _render_markdown(document: dict[str, Any]) -> str:
    manifest = document["manifest"]
    if manifest.get("run_kind") == "formal_full_suite":
        return _render_formal_v2_markdown(document)
    if manifest.get("run_kind") == "case_subset_debug":
        return _render_debug_markdown(document)
    if document["status"] == "failed":
        failure = document["failure"]
        trace = "\n".join(
            f"{event['sequence']}. `{event['event_type']}`"
            for event in document["trace"]
        )
        return (
            "# DevAgentOps Evaluation Tracer Bullet\n\n"
            "## Run Summary\n\n"
            f"- Run ID: `{document['run_id']}`\n"
            "- Status: `failed`\n"
            f"- Condition: `{manifest['selected_condition_id']}`\n"
            f"- Runtime: `{manifest['runtime_variant']}`\n"
            f"- Failure code: `{failure['code']}`\n"
            f"- Failure stage: `{failure['stage']}`\n\n"
            "## Failure\n\n"
            f"{failure['message']}\n\n"
            "## Lifecycle Trace\n\n"
            f"{trace}\n"
        )
    result = document["case_results"][0]
    report = result["report"]
    metrics = result["quality_metrics"]
    if report is None:
        evidence = "- No valid evidence references"
        report_section = (
            "- Candidate did not satisfy Structured Triage Report V1.\n\n"
            f"- Validation: `{json.dumps(result['validation'], sort_keys=True)}`\n"
        )
    else:
        evidence = "\n".join(
            f"- `{reference['evidence_id']}`"
            for reference in report["evidence_references"]
        )
        report_section = (
            f"- Case: `{report['case_id']}`\n"
            f"- Failure type: `{report['failure_type']}`\n"
            f"- Confidence: `{report['confidence']}`\n\n"
            f"**Summary:** {report['summary']}\n\n"
            f"**Root cause:** {report['root_cause']}\n\n"
            f"**Recommended action:** {report['recommended_action']}\n"
        )
    trace = "\n".join(
        f"{event['sequence']}. `{event['event_type']}`"
        for event in document["trace"]
    )
    metric_rows = "\n".join(
        f"| `{name}` | {value} |" for name, value in metrics.items()
    )
    return (
        "# DevAgentOps Evaluation Tracer Bullet\n\n"
        "## Run Summary\n\n"
        f"- Run ID: `{document['run_id']}`\n"
        f"- Status: `{document['status']}`\n"
        f"- Condition: `{manifest['selected_condition_id']}`\n"
        f"- Runtime: `{manifest['runtime_variant']}`\n"
        + (
            f"- Pipeline: `{manifest['pipeline_version']}`\n\n"
            if "pipeline_version" in manifest
            else "\n"
        )
        + "## Structured Triage Report\n\n"
        f"{report_section}\n\n"
        "## Evidence References\n\n"
        f"{evidence}\n\n"
        "## Metric Vector\n\n"
        "| Metric | Value |\n"
        "|---|---:|\n"
        f"{metric_rows}\n\n"
        "## Lifecycle Trace\n\n"
        f"{trace}\n"
    )


def _render_debug_markdown(document: dict[str, Any]) -> str:
    if "sample_results" in document:
        return _render_sample_debug_markdown(document)
    manifest = document["manifest"]
    results = document["case_results"]
    scored_count = sum(
        result["outcome"]["status"] == "scored" for result in results
    )
    failed_count = len(results) - scored_count
    sections = []
    for result in results:
        outcome = result["outcome"]
        lines = [
            f"## Case `{result['case_id']}`",
            "",
            f"- Outcome: `{outcome['status']}`",
            f"- Suite weight: `{result['weight']}`",
            f"- Evaluation Failure Type: `{result['evaluation_failure_type']}`",
        ]
        if outcome["status"] == "execution_failed":
            lines.extend(
                [
                    f"- Failure code: `{outcome['failure_code']}`",
                    f"- Failure stage: `{outcome['failure_stage']}`",
                    "",
                    outcome["failure_message"],
                ]
            )
        else:
            lines.extend(
                [
                    f"- Report valid: `{result['validation']['valid']}`",
                    "",
                    "### Metric Vector",
                    "",
                    "| Metric | Value |",
                    "|---|---:|",
                    *(
                        f"| `{name}` | {value} |"
                        for name, value in result["quality_metrics"].items()
                    ),
                ]
            )
            if manifest.get("manifest_schema_version") == "2":
                observation = result["provider_observation"]
                assessment = result["context_assessment"]
                lines.extend(
                    [
                        "",
                        "### Provider Observation",
                        "",
                        f"- Provider request ID: `{observation['provider_request_id']}`",
                        f"- Returned model: `{observation['returned_model']}`",
                        f"- Usage: `{json.dumps(observation['usage'], sort_keys=True)}`",
                        f"- Finish reason: `{observation['finish_reason']}`",
                        f"- Latency milliseconds: `{observation['latency_ms']}`",
                        f"- Exact local input tokens: `{assessment['input_tokens']}`",
                        f"- Token-count method: `{assessment['method']}`",
                    ]
                )
        sections.append("\n".join(lines))
    trace = "\n".join(
        f"{event['sequence']}. `{event['event_type']}`"
        + (f" — `{event['case_id']}`" if event["case_id"] else "")
        for event in document["trace"]
    )
    preview_section = _render_metric_preview(document["metric_preview"])
    v2_identity = ""
    if manifest.get("manifest_schema_version") == "2":
        v2_identity = (
            f"- Matrix schema: `{manifest['matrix']['schema_version']}`\n"
            f"- Provider: `{manifest['treatment']['provider']['id']}`\n"
            f"- Model: `{manifest['treatment']['model']}`\n"
            f"- Treatment fingerprint: `{manifest['treatment_fingerprint']}`\n"
            f"- Condition fingerprint: `{manifest['condition_fingerprint']}`\n"
            f"- Execution policy fingerprint: "
            f"`{manifest['execution_policy_fingerprint']}`\n"
            f"- Run configuration fingerprint: "
            f"`{manifest['run_configuration_fingerprint']}`\n"
            f"- Code revision: `{manifest['code_revision']}`\n"
            f"- Git dirty: `{str(manifest['git_dirty']).lower()}`\n"
        )
    return (
        "# DevAgentOps Case Subset Debug Run\n\n"
        "## Run Summary\n\n"
        f"- Run ID: `{document['run_id']}`\n"
        f"- Status: `{document['status']}`\n"
        f"- Condition: `{manifest['selected_condition_id']}`\n"
        f"- Runtime: `{manifest['runtime_variant']}`\n"
        + v2_identity
        +
        f"- Selected Cases: `{len(results)}`\n"
        f"- Scored Cases: `{scored_count}`\n"
        f"- Failed Cases: `{failed_count}`\n"
        "- Formal Evaluation: `false`\n"
        "- Quality Gate Qualification: `false`\n\n"
        + preview_section
        + "\n\n"
        + "\n\n".join(sections)
        + "\n\n## Lifecycle Trace\n\n"
        + trace
        + "\n"
    )


def _render_formal_v2_markdown(document: dict[str, Any]) -> str:
    manifest = document["manifest"]
    suite = document["suite_aggregate"]
    samples = document["sample_results"]
    failed = [
        sample for sample in samples if sample["outcome"]["status"] == "execution_failed"
    ]
    invalid = [
        sample
        for sample in samples
        if sample["outcome"]["status"] == "scored"
        and not sample["validation"]["valid"]
    ]
    suite_metrics = _metric_table(suite["metric_vector"])
    type_sections = []
    for aggregate in document["failure_type_aggregates"]:
        type_sections.append(
            f"### `{aggregate['failure_type']}`\n\n"
            f"- Cases: `{aggregate['case_count']}`\n"
            f"- Configured Suite weight: `{aggregate['configured_suite_weight']}`\n"
            f"- Execution coverage: `{aggregate['execution_coverage']}`\n"
            f"- Protocol validity: `{aggregate['protocol_validity_rate']}`\n"
            f"- Quality Case coverage: `{aggregate['quality_case_coverage']}`\n"
            f"- Quality status: `{aggregate['quality_status']}`\n\n"
            + _metric_table(aggregate["metric_vector"])
        )
    case_rows = "\n".join(
        "| `{case_id}` | `{failure_type}` | {suite_weight} | {scored}/"
        "{requested} | {execution_coverage} | {protocol_validity_rate} | "
        "`{quality_status}` |".format(
            case_id=item["case_id"],
            failure_type=item["failure_type"],
            suite_weight=item["suite_weight"],
            scored=item["scored_sample_count"],
            requested=item["requested_sample_count"],
            execution_coverage=item["execution_coverage"],
            protocol_validity_rate=item["protocol_validity_rate"],
            quality_status=item["quality_status"],
        )
        for item in document["case_aggregates"]
    )
    case_details = "\n\n".join(
        f"### `{item['case_id']}`\n\n"
        f"- Case fingerprint: `{item['case_fingerprint']}`\n"
        f"- Scored repeat indices: "
        f"`{json.dumps(item['scored_repeat_indices'])}`\n"
        f"- Failed repeat indices: "
        f"`{json.dumps(item['failed_repeat_indices'])}`\n"
        f"- Aggregation: `{item['aggregation_method']}` "
        f"version `{item['aggregation_version']}`\n\n"
        + _metric_table(item["metric_vector"])
        for item in document["case_aggregates"]
    )
    failure_lines = "\n".join(
        f"- Case `{sample['case_id']}` repeat `{sample['repeat_index']}`: "
        f"`{sample['outcome']['failure_code']}` at "
        f"`{sample['outcome']['failure_stage']}`"
        for sample in failed
    ) or "- None"
    invalid_lines = "\n".join(
        f"- Case `{sample['case_id']}` repeat `{sample['repeat_index']}`"
        for sample in invalid
    ) or "- None"
    trace_lines = "\n".join(
        f"{event['sequence']}. `{event['event_type']}`"
        + (f" — `{event['case_id']}`" if event["case_id"] else "")
        + (
            f" repeat `{event['repeat_index']}`"
            if event.get("repeat_index") is not None
            else ""
        )
        for event in document["trace"]
    )
    return (
        "# DevAgentOps Formal L1 Milestone Evaluation\n\n"
        "## Run Identity\n\n"
        f"- Run ID: `{document['run_id']}`\n"
        f"- Status: `{document['status']}`\n"
        f"- Code revision: `{manifest['code_revision']}`\n"
        f"- Git dirty: `{str(manifest['git_dirty']).lower()}`\n"
        f"- Matrix: `{manifest['matrix']['matrix_id']}` "
        f"version `{manifest['matrix']['matrix_version']}`\n"
        f"- Treatment fingerprint: `{manifest['treatment_fingerprint']}`\n"
        f"- Condition fingerprint: `{manifest['condition_fingerprint']}`\n"
        f"- Execution Policy fingerprint: "
        f"`{manifest['execution_policy_fingerprint']}`\n"
        f"- Run Configuration fingerprint: "
        f"`{manifest['run_configuration_fingerprint']}`\n"
        f"- Suite fingerprint: "
        f"`{manifest['evaluation_suite']['suite_fingerprint']}`\n\n"
        "## Sampling\n\n"
        f"- Cases: `{suite['total_case_count']}`\n"
        f"- Repeats per Case: "
        f"`{manifest['execution_policy']['repeat_count']}`\n"
        f"- Planned samples: `{suite['requested_sample_count']}`\n"
        f"- Scored samples: `{suite['scored_sample_count']}`\n"
        f"- Execution-failed samples: "
        f"`{suite['execution_failed_sample_count']}`\n\n"
        "## Coverage\n\n"
        f"- Execution coverage: `{suite['execution_coverage']}`\n"
        f"- Protocol validity: `{suite['protocol_validity_rate']}`\n"
        f"- Quality Case coverage: `{suite['quality_case_coverage']}`\n"
        f"- Quality Suite-weight coverage: "
        f"`{suite['quality_suite_weight_coverage']}`\n"
        f"- Diagnostic quality status: `{suite['quality_status']}`\n\n"
        "## Suite Metric Vector\n\n"
        + suite_metrics
        + "\n\n## By Failure Type\n\n"
        + "\n\n".join(type_sections)
        + "\n\n## Per-Case Aggregates\n\n"
        "| Case | Failure Type | Weight | Scored / Requested | Execution "
        "Coverage | Protocol Validity | Quality |\n"
        "|---|---|---:|---:|---:|---:|---|\n"
        + case_rows
        + "\n\n## Per-Case Diagnostic Detail\n\n"
        + case_details
        + "\n\n## Execution Failures\n\n"
        + failure_lines
        + "\n\n## Protocol-Invalid Observations\n\n"
        + invalid_lines
        + "\n\n## Lifecycle Trace\n\n"
        + trace_lines
        + "\n\n## Experimental Limitations\n\n"
        "This is an L1 development-treatment milestone experiment. It is "
        "not the final frozen L1-L4 benchmark and is not leaderboard-qualified.\n"
    )


def _metric_table(metric_vector: dict[str, float] | None) -> str:
    if metric_vector is None:
        return (
            "Diagnostic quality is unavailable because at least one Case has "
            "no scored sample."
        )
    rows = "\n".join(
        f"| `{name}` | {value} |" for name, value in metric_vector.items()
    )
    return "| Metric | Value |\n|---|---:|\n" + rows


def _render_sample_debug_markdown(document: dict[str, Any]) -> str:
    manifest = document["manifest"]
    results = document["sample_results"]
    scored_count = sum(
        result["outcome"]["status"] == "scored" for result in results
    )
    failed_count = len(results) - scored_count
    sections: list[str] = []
    for result in results:
        outcome = result["outcome"]
        lines = [
            (
                f"## Sample `{result['sample_sequence']}` — Case "
                f"`{result['case_id']}` Repeat `{result['repeat_index']}`"
            ),
            "",
            f"- Outcome: `{outcome['status']}`",
            f"- Suite weight: `{result['weight']}`",
            f"- Evaluation Failure Type: `{result['evaluation_failure_type']}`",
        ]
        if outcome["status"] == "execution_failed":
            lines.extend(
                [
                    f"- Failure code: `{outcome['failure_code']}`",
                    f"- Failure stage: `{outcome['failure_stage']}`",
                    "",
                    outcome["failure_message"],
                ]
            )
        else:
            observation = result["provider_observation"]
            assessment = result["context_assessment"]
            lines.extend(
                [
                    f"- Report valid: `{result['validation']['valid']}`",
                    "",
                    "### Sample Metric Vector",
                    "",
                    "| Metric | Value |",
                    "|---|---:|",
                    *(
                        f"| `{name}` | {value} |"
                        for name, value in result["quality_metrics"].items()
                    ),
                    "",
                    "### Provider Observation",
                    "",
                    f"- Provider request ID: `{observation['provider_request_id']}`",
                    f"- Returned model: `{observation['returned_model']}`",
                    f"- Usage: `{json.dumps(observation['usage'], sort_keys=True)}`",
                    f"- Finish reason: `{observation['finish_reason']}`",
                    f"- Latency milliseconds: `{observation['latency_ms']}`",
                    f"- Exact local input tokens: `{assessment['input_tokens']}`",
                    f"- Token-count method: `{assessment['method']}`",
                    "- Reasoning metadata: "
                    f"`{json.dumps(observation['reasoning'], sort_keys=True)}`",
                ]
            )
        sections.append("\n".join(lines))
    trace = "\n".join(
        f"{event['sequence']}. `{event['event_type']}`"
        + (f" — `{event['case_id']}`" if event["case_id"] else "")
        + (
            f" repeat `{event['repeat_index']}`"
            if event.get("repeat_index") is not None
            else ""
        )
        for event in document["trace"]
    )
    preview = document["metric_preview"]
    coverage = preview["coverage"]
    return (
        "# DevAgentOps Repeated Sample Debug Run\n\n"
        "## Run Summary\n\n"
        f"- Run ID: `{document['run_id']}`\n"
        f"- Status: `{document['status']}`\n"
        f"- Condition: `{manifest['selected_condition_id']}`\n"
        f"- Runtime: `{manifest['runtime_variant']}`\n"
        f"- Matrix schema: `{manifest['matrix']['schema_version']}`\n"
        f"- Provider: `{manifest['treatment']['provider']['id']}`\n"
        f"- Model: `{manifest['treatment']['model']}`\n"
        f"- Treatment fingerprint: `{manifest['treatment_fingerprint']}`\n"
        f"- Condition fingerprint: `{manifest['condition_fingerprint']}`\n"
        f"- Execution policy fingerprint: "
        f"`{manifest['execution_policy_fingerprint']}`\n"
        f"- Run configuration fingerprint: "
        f"`{manifest['run_configuration_fingerprint']}`\n"
        f"- Code revision: `{manifest['code_revision']}`\n"
        f"- Git dirty: `{str(manifest['git_dirty']).lower()}`\n"
        f"- Selected Cases: `{len(manifest['case_selection']['case_ids'])}`\n"
        f"- Planned Samples: `{coverage['planned_sample_count']}`\n"
        f"- Scored Samples: `{scored_count}`\n"
        f"- Failed Samples: `{failed_count}`\n"
        "- Formal Evaluation: `false`\n"
        "- Quality Gate Qualification: `false`\n\n"
        "## Aggregation\n\n"
        f"- Status: `{preview['status']}`\n"
        f"- Scope: `{preview['scope']}`\n"
        f"- Reason: {preview['reason']}\n\n"
        + "\n\n".join(sections)
        + "\n\n## Lifecycle Trace\n\n"
        + trace
        + "\n"
    )


def _render_metric_preview(preview: dict[str, Any]) -> str:
    coverage = preview["coverage"]

    def metric_table(metric_vector: dict[str, Any] | None) -> str:
        if metric_vector is None:
            return "No scored Cases are available for this preview."
        rows = "\n".join(
            f"| `{name}` | {value} |" for name, value in metric_vector.items()
        )
        return "| Metric | Value |\n|---|---:|\n" + rows

    groups = []
    for group in preview["by_failure_type"]:
        group_coverage = group["coverage"]
        groups.append(
            f"### Failure Type `{group['failure_type']}`\n\n"
            f"- Selected Cases: `{group_coverage['selected_case_count']}`\n"
            f"- Scored Cases: `{group_coverage['scored_case_count']}`\n"
            f"- Failed Cases: `{group_coverage['failed_case_count']}`\n"
            f"- Selected Weight: `{group_coverage['selected_weight']}`\n"
            f"- Scored Weight: `{group_coverage['scored_weight']}`\n"
            f"- Failed Weight: `{group_coverage['failed_weight']}`\n\n"
            + metric_table(group["metric_vector"])
        )
    return (
        "## Metric Vector Preview\n\n"
        f"- Status: `{preview['status']}`\n"
        f"- Selected Cases: `{coverage['selected_case_count']}`\n"
        f"- Scored Cases: `{coverage['scored_case_count']}`\n"
        f"- Failed Cases: `{coverage['failed_case_count']}`\n"
        f"- Selected Weight: `{coverage['selected_weight']}`\n"
        f"- Scored Weight: `{coverage['scored_weight']}`\n"
        f"- Failed Weight: `{coverage['failed_weight']}`\n"
        "- Scope: `debug-only metric preview`\n\n"
        "### Overall\n\n"
        + metric_table(preview["overall"]["metric_vector"])
        + "\n\n"
        + "\n\n".join(groups)
    )
