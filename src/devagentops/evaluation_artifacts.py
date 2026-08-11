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
