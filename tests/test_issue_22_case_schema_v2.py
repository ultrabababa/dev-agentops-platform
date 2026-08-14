import hashlib
import json
from pathlib import Path

import pytest

from devagentops.cli import main
from devagentops.evaluation.suite import (
    EvaluationSuiteError,
    calculate_case_fingerprint,
    load_case_package,
)


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_valid_v2_case(tmp_path: Path) -> Path:
    case_root = tmp_path / "constructed-assertion-001"
    raw_log = b"pytest started\nE assert 6 == 5\n1 failed\n"
    calculator = b"def calculate_total(left, right):\n    return left * right\n"
    test_total = b"def test_total():\n    assert calculate_total(2, 3) == 5\n"
    raw_log_path = case_root / "physical-artifacts/raw.log"
    calculator_path = (
        case_root / "physical-artifacts/repository/src/example/calculator.py"
    )
    test_total_path = case_root / "physical-artifacts/repository/tests/test_total.py"
    raw_log_path.parent.mkdir(parents=True, exist_ok=True)
    calculator_path.parent.mkdir(parents=True, exist_ok=True)
    test_total_path.parent.mkdir(parents=True, exist_ok=True)
    raw_log_path.write_bytes(raw_log)
    calculator_path.write_bytes(calculator)
    test_total_path.write_bytes(test_total)

    _write_json(
        case_root / "physical-artifacts/repository-manifest.json",
        {
            "schema_version": "1",
            "upstream_repository": {
                "identity": "project_constructed://issue-22/tiny-fixture",
                "revision_kind": "constructed_snapshot",
                "exact_revision": "fixture-revision-1",
            },
            "files": [
                {
                    "path": "tests/test_total.py",
                    "sha256": _sha256(test_total),
                    "size_bytes": len(test_total),
                },
                {
                    "path": "src/example/calculator.py",
                    "sha256": _sha256(calculator),
                    "size_bytes": len(calculator),
                },
            ],
        },
    )
    _write_json(
        case_root / "canonical-evidence/log-units.json",
        {
            "schema_version": "1",
            "units": [
                {
                    "evidence_id": "log:raw-lines-0002-0002",
                    "source": "physical-artifacts/raw.log",
                    "span": {
                        "type": "line_range",
                        "start_line": 2,
                        "end_line": 2,
                    },
                    "content_sha256": _sha256(b"E assert 6 == 5\n"),
                }
            ],
        },
    )
    _write_json(
        case_root / "canonical-evidence/repository-units.json",
        {
            "schema_version": "1",
            "units": [
                {
                    "evidence_id": "repo:calculator-lines-0001-0002",
                    "source": (
                        "physical-artifacts/repository/src/example/calculator.py"
                    ),
                    "span": {
                        "type": "line_range",
                        "start_line": 1,
                        "end_line": 2,
                    },
                    "content_sha256": _sha256(calculator),
                }
            ],
        },
    )
    _write_json(
        case_root / "evaluator/required-evidence.json",
        {
            "schema_version": "1",
            "required_evidence_ids": [
                "repo:calculator-lines-0001-0002",
                "log:raw-lines-0002-0002",
            ],
            "optional_evidence_ids": [],
        },
    )
    _write_json(
        case_root / "evaluator/expected-answer.json",
        {
            "schema_version": "2",
            "primary_failure_type": "test_assertion_failure",
            "acceptable_failure_types": [],
            "summary": "The calculation assertion failed with a stable mismatch.",
            "root_cause": "The implementation multiplies instead of adding.",
            "recommended_action": "Review calculate_total against its contract.",
        },
    )
    case_path = case_root / "case.json"
    _write_json(
        case_path,
        {
            "case_schema_version": "2",
            "case_id": "constructed-assertion-001",
            "artifacts": {
                "raw_log": "physical-artifacts/raw.log",
                "repository_manifest": "physical-artifacts/repository-manifest.json",
                "repository_root": "physical-artifacts/repository",
                "log_units": "canonical-evidence/log-units.json",
                "repository_units": "canonical-evidence/repository-units.json",
                "required_evidence": "evaluator/required-evidence.json",
                "expected_answer": "evaluator/expected-answer.json",
            },
            "forbidden_actions": [
                "edit_code",
                "rerun_ci",
                "create_pull_request",
                "deploy",
            ],
            "provenance": {
                "source_type": "constructed",
                "source_url_or_construction_note": "Constructed V2 test fixture.",
                "license_or_permission": "project_constructed",
            },
            "curation": {
                "created_by": "DevAgentOps maintainers",
                "review_status": "human_reviewed",
                "reviewed_by": "Human fixture reviewer",
            },
            "sanitization": {
                "status": "reviewed_no_changes",
                "reviewed_by": "Human fixture reviewer",
                "transformations": [],
            },
            "case_fingerprint": "0" * 64,
        },
    )
    return case_path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _refresh_case_fingerprint(case_path: Path) -> str:
    document = _read_json(case_path)
    fingerprint = calculate_case_fingerprint(case_path)
    document["case_fingerprint"] = fingerprint
    _write_json(case_path, document)
    return fingerprint


def _artifact(case_path: Path, relative_path: str) -> Path:
    return case_path.parent / relative_path


def test_explicit_schema_v1_is_reported_as_unsupported(tmp_path: Path):
    case_path = tmp_path / "case.json"
    _write_json(case_path, {"case_schema_version": "1"})

    with pytest.raises(EvaluationSuiteError) as exc_info:
        load_case_package(case_path)

    assert exc_info.value.code == "unsupported_case_schema_version"


def test_missing_case_schema_version_is_an_invalid_manifest(tmp_path: Path):
    case_path = tmp_path / "case.json"
    _write_json(case_path, {})

    with pytest.raises(EvaluationSuiteError) as exc_info:
        load_case_package(case_path)

    assert exc_info.value.code == "invalid_case_manifest"


def test_non_string_case_schema_version_is_an_invalid_manifest(tmp_path: Path):
    case_path = tmp_path / "case.json"
    _write_json(case_path, {"case_schema_version": 2})

    with pytest.raises(EvaluationSuiteError) as exc_info:
        load_case_package(case_path)

    assert exc_info.value.code == "invalid_case_manifest"


def test_cli_distinguishes_explicit_unsupported_schema_from_invalid_manifest(
    tmp_path: Path,
    capsys,
):
    report_path = tmp_path / "unused-report.json"
    for document, expected_code in [
        ({"case_schema_version": "1"}, "unsupported_case_schema_version"),
        ({}, "invalid_case_manifest"),
        ({"case_schema_version": 2}, "invalid_case_manifest"),
    ]:
        case_path = tmp_path / f"{expected_code}-{len(document)}.json"
        _write_json(case_path, document)

        assert (
            main(
                [
                    "eval",
                    "score",
                    "--case",
                    str(case_path),
                    "--report",
                    str(report_path),
                ]
            )
            == 2
        )
        assert json.loads(capsys.readouterr().err)["code"] == expected_code


def test_loads_one_complete_schema_v2_case(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    _refresh_case_fingerprint(case_path)

    package = load_case_package(case_path)

    assert package.case_id == "constructed-assertion-001"
    assert package.case_schema_version == "2"
    assert len(package.evidence_ids) == 2


@pytest.mark.parametrize(
    ("artifact_name", "source", "message"),
    [
        (
            "log_units",
            "physical-artifacts/repository/src/example/calculator.py",
            "must equal the declared raw log path",
        ),
        (
            "repository_units",
            "physical-artifacts/raw.log",
            "inside the declared repository root",
        ),
        (
            "repository_units",
            "physical-artifacts/repository/src/example/unfrozen.py",
            "manifest-declared member",
        ),
    ],
)
def test_canonical_units_are_owned_by_their_declared_physical_artifact_type(
    artifact_name: str,
    source: str,
    message: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    case = _read_json(case_path)
    units_path = _artifact(case_path, case["artifacts"][artifact_name])
    units = _read_json(units_path)
    units["units"][0]["source"] = source
    _write_json(units_path, units)

    with pytest.raises(EvaluationSuiteError, match=message):
        calculate_case_fingerprint(case_path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("extra", "undeclared member"),
        ("missing", "manifest member does not exist"),
        ("duplicate", "duplicate paths"),
        ("size", "size does not match"),
        ("hash", "hash does not match"),
    ],
)
def test_repository_snapshot_membership_and_integrity_are_manifest_driven(
    mutation: str,
    message: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    manifest_path = _artifact(
        case_path, "physical-artifacts/repository-manifest.json"
    )
    manifest = _read_json(manifest_path)
    repository_root = _artifact(case_path, "physical-artifacts/repository")
    if mutation == "extra":
        extra = repository_root / "src/example/unfrozen.py"
        extra.write_bytes(b"unfrozen = True\n")
    elif mutation == "missing":
        (repository_root / manifest["files"][0]["path"]).unlink()
    elif mutation == "duplicate":
        manifest["files"].append(dict(manifest["files"][0]))
        _write_json(manifest_path, manifest)
    elif mutation == "size":
        manifest["files"][0]["size_bytes"] += 1
        _write_json(manifest_path, manifest)
    else:
        manifest["files"][0]["sha256"] = "f" * 64
        _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationSuiteError, match=message):
        calculate_case_fingerprint(case_path)


@pytest.mark.parametrize(
    ("revision_kind", "exact_revision"),
    [
        ("git_commit", "a" * 40),
        ("constructed_snapshot", "fixture-revision-2026-08-09"),
    ],
)
def test_repository_manifest_accepts_supported_exact_revision_identities(
    revision_kind: str,
    exact_revision: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    manifest_path = _artifact(
        case_path, "physical-artifacts/repository-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["upstream_repository"]["revision_kind"] = revision_kind
    manifest["upstream_repository"]["exact_revision"] = exact_revision
    _write_json(manifest_path, manifest)

    _refresh_case_fingerprint(case_path)

    snapshot = load_case_package(case_path).repository_snapshot
    assert snapshot.revision_kind == revision_kind
    assert snapshot.exact_revision == exact_revision


@pytest.mark.parametrize("malformed_revision", ["abc123", "A" * 40, "g" * 40])
def test_repository_manifest_rejects_malformed_git_commit_revision(
    malformed_revision: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    manifest_path = _artifact(
        case_path, "physical-artifacts/repository-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["upstream_repository"]["revision_kind"] = "git_commit"
    manifest["upstream_repository"]["exact_revision"] = malformed_revision
    _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationSuiteError, match="git_commit exact_revision"):
        calculate_case_fingerprint(case_path)


def test_repository_snapshot_rejects_member_symlinks(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    member = _artifact(
        case_path, "physical-artifacts/repository/src/example/calculator.py"
    )
    outside = tmp_path / "outside.py"
    outside.write_bytes(member.read_bytes())
    member.unlink()
    member.symlink_to(outside)

    with pytest.raises(EvaluationSuiteError, match="must not use symlinks"):
        calculate_case_fingerprint(case_path)


def test_repository_root_rejects_symlinked_parent_components(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    physical = case_path.parent / "physical-artifacts"
    frozen_physical = case_path.parent / "frozen-physical-artifacts"
    physical.rename(frozen_physical)
    physical.symlink_to(frozen_physical, target_is_directory=True)

    with pytest.raises(EvaluationSuiteError, match="must not use symlinks"):
        calculate_case_fingerprint(case_path)


def test_line_ranges_hash_exact_crlf_bytes_and_final_non_lf_line(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    raw_log_path = _artifact(case_path, "physical-artifacts/raw.log")
    raw_log_path.write_bytes(b"first\r\nsecond\r\nfinal")
    units_path = _artifact(case_path, "canonical-evidence/log-units.json")
    units = _read_json(units_path)
    units["units"] = [
        {
            "evidence_id": "log:crlf-line",
            "source": "physical-artifacts/raw.log",
            "span": {"type": "line_range", "start_line": 2, "end_line": 2},
            "content_sha256": _sha256(b"second\r\n"),
        },
        {
            "evidence_id": "log:final-line",
            "source": "physical-artifacts/raw.log",
            "span": {"type": "line_range", "start_line": 3, "end_line": 3},
            "content_sha256": _sha256(b"final"),
        },
    ]
    _write_json(units_path, units)
    ground_truth_path = _artifact(case_path, "evaluator/required-evidence.json")
    ground_truth = _read_json(ground_truth_path)
    ground_truth["required_evidence_ids"] = [
        "log:crlf-line",
        "repo:calculator-lines-0001-0002",
    ]
    ground_truth["optional_evidence_ids"] = ["log:final-line"]
    _write_json(ground_truth_path, ground_truth)

    _refresh_case_fingerprint(case_path)
    package = load_case_package(case_path)

    assert package.evidence_ids == (
        "log:crlf-line",
        "log:final-line",
        "repo:calculator-lines-0001-0002",
    )


@pytest.mark.parametrize(
    ("start_line", "end_line", "message"),
    [
        (0, 1, "positive 1-based inclusive"),
        (2, 1, "positive 1-based inclusive"),
        (1, 99, "exceeds source EOF"),
    ],
)
def test_invalid_or_empty_line_ranges_are_rejected(
    start_line: int,
    end_line: int,
    message: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    units_path = _artifact(case_path, "canonical-evidence/log-units.json")
    units = _read_json(units_path)
    units["units"][0]["span"]["start_line"] = start_line
    units["units"][0]["span"]["end_line"] = end_line
    _write_json(units_path, units)

    with pytest.raises(EvaluationSuiteError, match=message):
        calculate_case_fingerprint(case_path)


def test_set_like_list_order_does_not_change_case_fingerprint(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    original = calculate_case_fingerprint(case_path)
    manifest_path = _artifact(
        case_path, "physical-artifacts/repository-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["files"].reverse()
    _write_json(manifest_path, manifest)
    ground_truth_path = _artifact(case_path, "evaluator/required-evidence.json")
    ground_truth = _read_json(ground_truth_path)
    ground_truth["required_evidence_ids"].reverse()
    _write_json(ground_truth_path, ground_truth)
    case = _read_json(case_path)
    case["forbidden_actions"].reverse()
    _write_json(case_path, case)

    assert calculate_case_fingerprint(case_path) == original


def test_expected_answer_cannot_reabsorb_evidence_ground_truth(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    expected_path = _artifact(case_path, "evaluator/expected-answer.json")
    expected = _read_json(expected_path)
    expected["required_evidence_ids"] = ["log:raw-lines-0002-0002"]
    _write_json(expected_path, expected)

    with pytest.raises(EvaluationSuiteError, match="unknown field"):
        calculate_case_fingerprint(case_path)


def test_sanitization_records_are_strict_without_freezing_a_kind_taxonomy(
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    case = _read_json(case_path)
    case["sanitization"] = {
        "status": "reviewed_sanitized",
        "reviewed_by": "Human fixture reviewer",
        "transformations": [
            {
                "artifact_path": "physical-artifacts/raw.log",
                "description": "Replaced one private token with a neutral placeholder.",
                "semantics_preserving": True,
            }
        ],
    }
    _write_json(case_path, case)

    _refresh_case_fingerprint(case_path)
    assert load_case_package(case_path).case_fingerprint


def test_reviewed_sanitized_rejects_non_semantics_preserving_transformation(
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    case = _read_json(case_path)
    case["sanitization"] = {
        "status": "reviewed_sanitized",
        "reviewed_by": "Human fixture reviewer",
        "transformations": [
            {
                "artifact_path": "physical-artifacts/raw.log",
                "description": "Changed one frozen artifact.",
                "semantics_preserving": False,
            }
        ],
    }
    _write_json(case_path, case)

    with pytest.raises(EvaluationSuiteError, match="semantics-preserving"):
        calculate_case_fingerprint(case_path)


def test_structured_answer_neutral_evidence_ids_may_contain_colons_in_suffix(
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    log_id = "log:ci-lines-0572-0601:maven-antrun-verify"
    repo_id = "repo:equals-avoid-null-check.java:lines-0401-0500"
    log_units_path = _artifact(case_path, "canonical-evidence/log-units.json")
    log_units = _read_json(log_units_path)
    log_units["units"][0]["evidence_id"] = log_id
    _write_json(log_units_path, log_units)
    repository_units_path = _artifact(
        case_path, "canonical-evidence/repository-units.json"
    )
    repository_units = _read_json(repository_units_path)
    repository_units["units"][0]["evidence_id"] = repo_id
    _write_json(repository_units_path, repository_units)
    ground_truth_path = _artifact(case_path, "evaluator/required-evidence.json")
    ground_truth = _read_json(ground_truth_path)
    ground_truth["required_evidence_ids"] = [repo_id, log_id]
    _write_json(ground_truth_path, ground_truth)

    _refresh_case_fingerprint(case_path)

    assert load_case_package(case_path).evidence_ids == (log_id, repo_id)


def test_public_case_view_recursively_excludes_evaluator_data(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    _refresh_case_fingerprint(case_path)
    package = load_case_package(case_path)

    encoded = json.dumps(package.public_view().as_dict(), sort_keys=True)

    assert "expected_answer" not in encoded
    assert "required_evidence" not in encoded
    assert "primary_failure_type" not in encoded
    assert package.expected_answer.root_cause not in encoded
    assert package.evidence_ground_truth.required_evidence_ids[0] not in encoded


def test_cli_redacts_evaluator_values_and_reports_stable_case_error_code(
    tmp_path: Path,
    capsys,
):
    case_path = _write_valid_v2_case(tmp_path)
    expected_path = _artifact(case_path, "evaluator/expected-answer.json")
    expected = _read_json(expected_path)
    sentinel = "EVALUATOR_ONLY_SENTINEL"
    expected["primary_failure_type"] = sentinel
    _write_json(expected_path, expected)

    exit_code = main(
        [
            "eval",
            "score",
            "--case",
            str(case_path),
            "--report",
            str(tmp_path / "not-read.json"),
        ]
    )
    payload = json.loads(capsys.readouterr().err)

    assert exit_code == 2
    assert payload == {
        "error": "invalid Offline Case package",
        "code": "invalid_case_manifest",
    }
    assert sentinel not in json.dumps(payload)


@pytest.mark.parametrize(
    ("relative_path", "message"),
    [
        ("physical-artifacts/raw.log", "does not exist"),
        ("physical-artifacts/repository-manifest.json", "does not exist"),
    ],
)
def test_required_physical_artifacts_must_exist(
    relative_path: str,
    message: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    _artifact(case_path, relative_path).unlink()

    with pytest.raises(EvaluationSuiteError, match=message):
        calculate_case_fingerprint(case_path)


def test_case_manifest_rejects_unknown_fields(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    case = _read_json(case_path)
    case["future_field"] = True
    _write_json(case_path, case)

    with pytest.raises(EvaluationSuiteError, match="unknown field"):
        calculate_case_fingerprint(case_path)


def test_case_manifest_artifact_paths_must_be_distinct(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    case = _read_json(case_path)
    case["artifacts"]["repository_units"] = case["artifacts"]["log_units"]
    _write_json(case_path, case)

    with pytest.raises(EvaluationSuiteError, match="distinct paths"):
        calculate_case_fingerprint(case_path)


@pytest.mark.parametrize("unsafe_path", ["../escape.py", "/tmp/escape.py", "bad\\path.py"])
def test_repository_manifest_member_paths_are_controlled(
    unsafe_path: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    manifest_path = _artifact(
        case_path, "physical-artifacts/repository-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["files"][0]["path"] = unsafe_path
    _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationSuiteError, match="relative path|POSIX"):
        calculate_case_fingerprint(case_path)


def test_raw_log_and_canonical_sources_must_be_utf8(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)
    _artifact(case_path, "physical-artifacts/raw.log").write_bytes(b"valid\n\xff")

    with pytest.raises(EvaluationSuiteError, match="not valid UTF-8"):
        calculate_case_fingerprint(case_path)


def test_canonical_resolved_content_hash_must_match_exact_selected_bytes(
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    units_path = _artifact(case_path, "canonical-evidence/log-units.json")
    units = _read_json(units_path)
    units["units"][0]["content_sha256"] = "f" * 64
    _write_json(units_path, units)

    with pytest.raises(EvaluationSuiteError, match="content hash does not match"):
        calculate_case_fingerprint(case_path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("required_empty", "required_evidence_ids must not be empty"),
        ("required_duplicate", "required_evidence_ids must not contain duplicates"),
        ("optional_duplicate", "optional_evidence_ids must not contain duplicates"),
        ("overlap", "must be disjoint"),
        ("unknown", "unknown Canonical Evidence ID"),
    ],
)
def test_evidence_ground_truth_set_integrity(
    mutation: str,
    message: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    ground_truth_path = _artifact(case_path, "evaluator/required-evidence.json")
    ground_truth = _read_json(ground_truth_path)
    if mutation == "required_empty":
        ground_truth["required_evidence_ids"] = []
    elif mutation == "required_duplicate":
        ground_truth["required_evidence_ids"].append(
            ground_truth["required_evidence_ids"][0]
        )
    elif mutation == "optional_duplicate":
        ground_truth["optional_evidence_ids"] = [
            "repo:calculator-lines-0001-0002",
            "repo:calculator-lines-0001-0002",
        ]
        ground_truth["required_evidence_ids"] = ["log:raw-lines-0002-0002"]
    elif mutation == "overlap":
        ground_truth["optional_evidence_ids"] = [
            ground_truth["required_evidence_ids"][0]
        ]
    else:
        ground_truth["required_evidence_ids"].append("repo:unknown-member")
    _write_json(ground_truth_path, ground_truth)

    with pytest.raises(EvaluationSuiteError, match=message):
        calculate_case_fingerprint(case_path)


def test_optional_evidence_ground_truth_may_be_empty(tmp_path: Path):
    case_path = _write_valid_v2_case(tmp_path)

    _refresh_case_fingerprint(case_path)

    assert load_case_package(case_path).evidence_ground_truth.optional_evidence_ids == ()


@pytest.mark.parametrize("kind", ["log", "repository"])
def test_each_canonical_artifact_rejects_duplicate_evidence_ids(
    kind: str,
    tmp_path: Path,
):
    case_path = _write_valid_v2_case(tmp_path)
    relative_path = (
        "canonical-evidence/log-units.json"
        if kind == "log"
        else "canonical-evidence/repository-units.json"
    )
    units_path = _artifact(case_path, relative_path)
    units = _read_json(units_path)
    units["units"].append(dict(units["units"][0]))
    _write_json(units_path, units)

    with pytest.raises(EvaluationSuiteError, match="duplicate evidence IDs"):
        calculate_case_fingerprint(case_path)
