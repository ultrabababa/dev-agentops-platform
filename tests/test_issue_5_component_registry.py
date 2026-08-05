import hashlib
import json
from pathlib import Path

import pytest

from devagentops.cli import main
from devagentops.component_registry import (
    COMPONENT_TYPES,
    ComponentRegistryError,
    component_fingerprint,
    freeze_component,
    load_component_manifest,
)

DEFAULT_BEHAVIOR = {
    "prompt": {"template": "Diagnose {log}"},
    "tool_registry": {"tools": []},
    "retriever_config": {"strategy": "none", "settings": {}},
    "tool_policy": {"rules": []},
    "mcp_server_set": {"servers": []},
    "skill_registry": {"skills": []},
}


def _write_manifest(
    path: Path,
    component_type: str,
    *,
    behavior: dict | None = None,
    metadata: dict | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "component_type": component_type,
                "behavior": behavior if behavior is not None else DEFAULT_BEHAVIOR[component_type],
                "metadata": metadata or {"notes": "draft"},
            }
        ),
        encoding="utf-8",
    )


def _write_matrix(path: Path, component_version: str) -> None:
    _write_matrix_with_components(path, {"prompt": component_version})


def _write_matrix_with_components(path: Path, components: dict[str, str]) -> None:
    path.write_text(
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
                        "model": {"provider": "test", "name": "model-v1"},
                        "components": components,
                        "budgets": {"max_steps": 1},
                        "repeats": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("component_type", sorted(COMPONENT_TYPES))
def test_component_validate_accepts_all_v1_manifest_types(
    component_type: str,
    tmp_path: Path,
    capsys,
):
    manifest_path = tmp_path / f"{component_type}.json"
    _write_manifest(manifest_path, component_type)

    assert main(["component", "validate", "--manifest", str(manifest_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["component_type"] == component_type
    assert payload["schema_version"] == "1"
    assert len(payload["fingerprint"]) == 64


def test_component_fingerprint_ignores_metadata_and_json_formatting(tmp_path: Path):
    manifest_path = tmp_path / "prompt.json"
    _write_manifest(
        manifest_path,
        "prompt",
        behavior={"template": "Diagnose {log}", "variables": ["log"]},
        metadata={"author": "first", "notes": "original"},
    )
    original = component_fingerprint(load_component_manifest(manifest_path))
    canonical_behavior = json.dumps(
        {"template": "Diagnose {log}", "variables": ["log"]},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert original == hashlib.sha256(canonical_behavior).hexdigest()

    manifest_path.write_text(
        json.dumps(
            {
                "metadata": {"author": "second", "notes": "edited"},
                "behavior": {
                    "variables": ["log"],
                    "template": "Diagnose {log}",
                },
                "component_type": "prompt",
                "schema_version": "1",
            },
            indent=4,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    assert component_fingerprint(load_component_manifest(manifest_path)) == original


@pytest.mark.parametrize(
    ("document", "message"),
    [
        (
            {"schema_version": "2", "component_type": "prompt", "behavior": {}},
            "schema version",
        ),
        (
            {"schema_version": "1", "component_type": "model", "behavior": {}},
            "component type",
        ),
        (
            {"schema_version": "1", "component_type": "prompt", "metadata": {}},
            "behavior",
        ),
        (
            {
                "schema_version": "1",
                "component_type": "prompt",
                "behavior": {},
                "notes": "metadata must be nested",
            },
            "unknown field",
        ),
    ],
)
def test_component_validate_rejects_invalid_manifest(
    document: dict,
    message: str,
    tmp_path: Path,
):
    manifest_path = tmp_path / "invalid.json"
    manifest_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ComponentRegistryError, match=message):
        load_component_manifest(manifest_path)


@pytest.mark.parametrize(
    ("component_type", "behavior", "message"),
    [
        ("prompt", {"variables": []}, "template"),
        ("tool_registry", {"tools": ["not-an-object"]}, "list of objects"),
        ("retriever_config", {"strategy": "none"}, "settings"),
        ("tool_policy", {"rules": "allow"}, "list of objects"),
        ("mcp_server_set", {"servers": {}}, "list of objects"),
        ("skill_registry", {"skills": [{"name": "x"}], "typo": True}, "unknown"),
    ],
)
def test_component_validate_enforces_type_specific_behavior_schema(
    component_type: str,
    behavior: dict,
    message: str,
    tmp_path: Path,
):
    manifest_path = tmp_path / f"invalid-{component_type}.json"
    _write_manifest(manifest_path, component_type, behavior=behavior)

    with pytest.raises(ComponentRegistryError, match=message):
        load_component_manifest(manifest_path)


def test_component_freeze_records_immutable_version_and_rejects_reuse(
    tmp_path: Path,
    capsys,
):
    manifest_path = tmp_path / "drafts" / "prompt.json"
    manifest_path.parent.mkdir()
    _write_manifest(manifest_path, "prompt", behavior={"template": "Diagnose {log}"})
    registry_path = tmp_path / "components" / "registry.json"
    command = [
        "component",
        "freeze",
        "--manifest",
        str(manifest_path),
        "--registry",
        str(registry_path),
        "--version",
        "triage-prompt-v1",
    ]

    assert main(command) == 0
    frozen = json.loads(capsys.readouterr().out)
    assert frozen["component_type"] == "prompt"
    assert frozen["component_version"] == "triage-prompt-v1"
    assert len(frozen["fingerprint"]) == 64

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    record = registry["components"]["prompt"]["triage-prompt-v1"]
    frozen_path = registry_path.parent / record["manifest"]
    assert frozen_path.is_file()
    assert record["fingerprint"] == frozen["fingerprint"]

    assert main(command) == 0
    assert json.loads(capsys.readouterr().out) == frozen

    _write_manifest(manifest_path, "prompt", behavior={"template": "Changed {log}"})
    assert main(command) == 2
    error = json.loads(capsys.readouterr().err)["error"]
    assert "immutable" in error
    assert "triage-prompt-v1" in error
    assert json.loads(frozen_path.read_text(encoding="utf-8"))["behavior"] == {
        "template": "Diagnose {log}"
    }
    assert json.loads(frozen_path.read_text(encoding="utf-8"))[
        "component_version"
    ] == "triage-prompt-v1"


def test_eval_doctor_validates_frozen_component_references(
    tmp_path: Path,
    capsys,
):
    manifest_path = tmp_path / "prompt.json"
    _write_manifest(manifest_path, "prompt", behavior={"template": "Diagnose {log}"})
    registry_path = tmp_path / "components" / "registry.json"
    freeze_command = [
        "component",
        "freeze",
        "--manifest",
        str(manifest_path),
        "--registry",
        str(registry_path),
        "--version",
        "triage-prompt-v1",
    ]
    assert main(freeze_command) == 0
    frozen_payload = json.loads(capsys.readouterr().out)

    matrix_path = tmp_path / "evaluation-matrix.json"
    doctor_command = [
        "eval",
        "doctor",
        "--matrix",
        str(matrix_path),
        "--registry",
        str(registry_path),
    ]
    _write_matrix(matrix_path, "triage-prompt-v1")
    assert main(doctor_command) == 0
    valid_payload = json.loads(capsys.readouterr().out)
    condition = valid_payload["conditions"][0]
    assert condition["component_fingerprints"] == {
        "prompt": frozen_payload["fingerprint"]
    }
    fingerprint_input = {
        **condition["effective_condition"],
        "component_fingerprints": condition["component_fingerprints"],
    }
    canonical_condition = json.dumps(
        fingerprint_input,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert condition["condition_fingerprint"] == hashlib.sha256(
        canonical_condition
    ).hexdigest()

    _write_matrix(matrix_path, "missing-v1")
    assert main(doctor_command) == 2
    assert "missing" in json.loads(capsys.readouterr().err)["error"]

    _write_matrix(matrix_path, "draft")
    assert main(doctor_command) == 2
    assert "draft" in json.loads(capsys.readouterr().err)["error"]

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    record = registry["components"]["prompt"]["triage-prompt-v1"]
    frozen_path = registry_path.parent / record["manifest"]
    frozen_document = json.loads(frozen_path.read_text(encoding="utf-8"))
    frozen_document["behavior"]["template"] = "Polluted {log}"
    frozen_path.write_text(json.dumps(frozen_document), encoding="utf-8")
    _write_matrix(matrix_path, "triage-prompt-v1")

    assert main(doctor_command) == 2
    error = json.loads(capsys.readouterr().err)["error"]
    assert "version pollution" in error
    assert "triage-prompt-v1" in error


def test_eval_doctor_requires_explicit_formal_or_structural_mode(
    tmp_path: Path,
    capsys,
):
    matrix_path = tmp_path / "evaluation-matrix.json"
    _write_matrix(matrix_path, "missing-v1")

    assert main(["eval", "doctor", "--matrix", str(matrix_path)]) == 2

    error = json.loads(capsys.readouterr().err)["error"]
    assert "requires --registry" in error
    assert "structural-only" in error


def test_component_freeze_recovers_matching_orphaned_frozen_manifest(tmp_path: Path):
    manifest_path = tmp_path / "draft.json"
    _write_manifest(manifest_path, "prompt")
    registry_path = tmp_path / "components" / "registry.json"
    orphaned_path = registry_path.parent / "frozen" / "prompt" / "prompt-v1.json"
    orphaned_path.parent.mkdir(parents=True)
    orphaned_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "component_type": "prompt",
                "component_version": "prompt-v1",
                "behavior": DEFAULT_BEHAVIOR["prompt"],
                "metadata": {"notes": "draft"},
            }
        ),
        encoding="utf-8",
    )

    frozen = freeze_component(manifest_path, registry_path, "prompt-v1")

    assert frozen.manifest == "frozen/prompt/prompt-v1.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["components"]["prompt"]["prompt-v1"]["fingerprint"] == (
        frozen.fingerprint
    )


def test_eval_doctor_resolves_all_six_component_types(
    tmp_path: Path,
    capsys,
):
    matrix_keys = {
        "prompt": "prompt",
        "tool_registry": "tool_registry",
        "retriever_config": "retriever",
        "tool_policy": "tool_policy",
        "mcp_server_set": "mcp_server_set",
        "skill_registry": "skill_registry",
    }
    registry_path = tmp_path / "components" / "registry.json"
    references = {}
    for component_type, matrix_key in matrix_keys.items():
        manifest_path = tmp_path / "drafts" / f"{component_type}.json"
        manifest_path.parent.mkdir(exist_ok=True)
        _write_manifest(manifest_path, component_type)
        version = f"{component_type}-v1"
        freeze_component(manifest_path, registry_path, version)
        references[matrix_key] = version

    matrix_path = tmp_path / "evaluation-matrix.json"
    _write_matrix_with_components(matrix_path, references)

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["conditions"][0]["effective_condition"]["components"] == references


def test_eval_doctor_rejects_retriever_alias_collision(tmp_path: Path, capsys):
    manifest_path = tmp_path / "retriever.json"
    _write_manifest(manifest_path, "retriever_config")
    registry_path = tmp_path / "components" / "registry.json"
    freeze_component(manifest_path, registry_path, "retriever-v1")
    matrix_path = tmp_path / "evaluation-matrix.json"
    _write_matrix_with_components(
        matrix_path,
        {
            "retriever": "retriever-v1",
            "retriever_config": "retriever-v1",
        },
    )

    assert (
        main(
            [
                "eval",
                "doctor",
                "--matrix",
                str(matrix_path),
                "--registry",
                str(registry_path),
            ]
        )
        == 2
    )
    assert "aliases" in json.loads(capsys.readouterr().err)["error"]
