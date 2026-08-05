import json
from pathlib import Path

from devagentops.cli import main


def test_eval_doctor_prints_effective_condition_with_stable_fingerprint(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "pipeline-anchor-v1",
                        "type": "anchor",
                        "runtime_variant": "pipeline",
                        "suite": "triage-v1",
                        "evaluation_method": "triage-method-v1",
                        "model": {
                            "provider": "openai-compatible",
                            "name": "test-model",
                            "temperature": 0,
                        },
                        "components": {
                            "prompt": "triage-prompt-v1",
                            "retriever": "none",
                            "skill_registry": "none",
                        },
                        "budgets": {"max_steps": 1, "max_tokens": 1024},
                        "repeats": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["matrix_id"] == "v1-baseline"
    assert payload["matrix_version"] == "1"
    assert payload["schema_version"] == "1"
    assert payload["conditions"] == [
        {
            "condition_id": "pipeline-anchor-v1",
            "effective_condition": {
                "type": "anchor",
                "runtime_variant": "pipeline",
                "suite": "triage-v1",
                "evaluation_method": "triage-method-v1",
                "model": {
                    "provider": "openai-compatible",
                    "name": "test-model",
                    "temperature": 0,
                },
                "components": {
                    "prompt": "triage-prompt-v1",
                    "retriever": "none",
                    "skill_registry": "none",
                },
                "budgets": {"max_steps": 1, "max_tokens": 1024},
                "repeats": 1,
            },
            "condition_fingerprint": payload["conditions"][0][
                "condition_fingerprint"
            ],
        }
    ]
    fingerprint = payload["conditions"][0]["condition_fingerprint"]
    assert len(fingerprint) == 64

    formatted_path = tmp_path / "formatted-evaluation-matrix.json"
    formatted_path.write_text(
        json.dumps(
            json.loads(matrix_path.read_text(encoding="utf-8")),
            ensure_ascii=False,
            indent=4,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    assert main(["eval", "doctor", "--matrix", str(formatted_path)]) == 0
    formatted_payload = json.loads(capsys.readouterr().out)
    assert formatted_payload["conditions"][0]["condition_fingerprint"] == fingerprint


def test_eval_doctor_resolves_defaults_into_each_effective_condition(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "defaults": {
                    "suite": "triage-v1",
                    "evaluation_method": "triage-method-v1",
                    "model": {
                        "provider": "openai-compatible",
                        "name": "test-model",
                        "temperature": 0,
                    },
                    "components": {"prompt": "triage-prompt-v1"},
                    "budgets": {"max_steps": 8, "max_tokens": 4096},
                    "repeats": 1,
                },
                "conditions": [
                    {
                        "id": "pipeline-anchor-v1",
                        "type": "anchor",
                        "runtime_variant": "pipeline",
                        "budgets": {"max_steps": 1},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["conditions"][0]["effective_condition"] == {
        "type": "anchor",
        "runtime_variant": "pipeline",
        "suite": "triage-v1",
        "evaluation_method": "triage-method-v1",
        "model": {
            "provider": "openai-compatible",
            "name": "test-model",
            "temperature": 0,
        },
        "components": {"prompt": "triage-prompt-v1"},
        "budgets": {"max_steps": 1, "max_tokens": 4096},
        "repeats": 1,
    }


def test_eval_doctor_resolves_one_level_condition_extension(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "defaults": {
                    "suite": "triage-v1",
                    "evaluation_method": "triage-method-v1",
                    "model": {"provider": "test", "name": "model-v1"},
                    "components": {
                        "prompt": "triage-prompt-v1",
                        "retriever": "none",
                    },
                    "budgets": {"max_steps": 8},
                    "repeats": 1,
                },
                "conditions": [
                    {
                        "id": "react-anchor-v1",
                        "type": "anchor",
                        "runtime_variant": "react",
                    },
                    {
                        "id": "react-retrieval-ablation-v1",
                        "extends": "react-anchor-v1",
                        "type": "ablation",
                        "components": {"retriever": "hybrid-v1"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["conditions"][1]["effective_condition"] == {
        "type": "ablation",
        "runtime_variant": "react",
        "suite": "triage-v1",
        "evaluation_method": "triage-method-v1",
        "model": {"provider": "test", "name": "model-v1"},
        "components": {
            "prompt": "triage-prompt-v1",
            "retriever": "hybrid-v1",
        },
        "budgets": {"max_steps": 8},
        "repeats": 1,
    }


def test_eval_doctor_rejects_missing_extension_reference(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "broken-ablation-v1",
                        "extends": "missing-anchor-v1",
                        "type": "ablation",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "missing-anchor-v1" in json.loads(captured.err)["error"]


def test_eval_doctor_rejects_deeper_condition_extension(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {"id": "anchor-v1", "type": "anchor"},
                    {
                        "id": "ablation-v1",
                        "extends": "anchor-v1",
                        "type": "ablation",
                    },
                    {
                        "id": "candidate-v1",
                        "extends": "ablation-v1",
                        "type": "candidate",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "one level" in error
    assert "ablation-v1" in error


def test_eval_doctor_rejects_condition_extension_cycle(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "condition-a",
                        "extends": "condition-b",
                        "type": "anchor",
                    },
                    {
                        "id": "condition-b",
                        "extends": "condition-a",
                        "type": "ablation",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "cycle" in error
    assert "condition-a" in error


def test_eval_doctor_rejects_unknown_condition_field(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "pipeline-anchor-v1",
                        "type": "anchor",
                        "runtime_variant": "pipeline",
                        "runtime_varient": "typo",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "unknown field" in error
    assert "runtime_varient" in error


def test_eval_doctor_rejects_unknown_condition_type(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "invalid-condition-v1",
                        "type": "experiment",
                        "runtime_variant": "pipeline",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "condition type" in error
    assert "experiment" in error


def test_eval_doctor_rejects_incomplete_effective_condition(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [
                    {
                        "id": "pipeline-anchor-v1",
                        "type": "anchor",
                        "runtime_variant": "pipeline",
                        "evaluation_method": "triage-method-v1",
                        "model": {"provider": "test", "name": "model-v1"},
                        "components": {"prompt": "triage-prompt-v1"},
                        "budgets": {"max_steps": 1},
                        "repeats": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "missing required field" in error
    assert "suite" in error


def test_eval_doctor_rejects_unknown_matrix_field(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "matrix_verzion": "typo",
                "conditions": [],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "unknown field" in error
    assert "matrix_verzion" in error


def test_eval_doctor_rejects_unknown_defaults_field(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "defaults": {"evalution_method": "typo"},
                "conditions": [],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "unknown field" in error
    assert "evalution_method" in error


def test_eval_doctor_reports_missing_matrix_metadata(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "missing required field" in error
    assert "matrix_id" in error


def test_eval_doctor_reports_invalid_json(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text("{not-json", encoding="utf-8")

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "invalid JSON" in error
    assert str(matrix_path) in error


def test_eval_doctor_rejects_duplicate_condition_ids(
    tmp_path: Path,
    capsys,
):
    condition = {
        "id": "pipeline-anchor-v1",
        "type": "anchor",
        "runtime_variant": "pipeline",
        "suite": "triage-v1",
        "evaluation_method": "triage-method-v1",
        "model": {"provider": "test", "name": "model-v1"},
        "components": {"prompt": "triage-prompt-v1"},
        "budgets": {"max_steps": 1},
        "repeats": 1,
    }
    matrix_path = tmp_path / "evaluation-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_id": "v1-baseline",
                "matrix_version": "1",
                "schema_version": "1",
                "conditions": [condition, condition],
            }
        ),
        encoding="utf-8",
    )

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "duplicate condition id" in error
    assert "pipeline-anchor-v1" in error
