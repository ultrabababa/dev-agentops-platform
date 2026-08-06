from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class EvaluationSuiteError(RuntimeError):
    pass


CASE_FIELDS = {
    "case_schema_version",
    "case_id",
    "raw_log",
    "frozen_log_chunks",
    "frozen_log_chunks_fingerprint",
    "repository_evidence",
    "expected_answer",
    "forbidden_actions",
    "source_type",
    "source_url_or_construction_note",
    "license_or_permission",
    "created_by",
    "reviewed_by",
    "sanitization_status",
    "case_fingerprint",
}
SUITE_FIELDS = {
    "schema_version",
    "suite_id",
    "suite_version",
    "cases",
    "suite_fingerprint",
}
SUITE_CASE_FIELDS = {"case_id", "manifest", "weight"}
LOG_CHUNK_FIELDS = {"evidence_id", "text"}
LOG_CHUNKS_FIELDS = {"schema_version", "chunks"}
REPOSITORY_EVIDENCE_FIELDS = {"schema_version", "items"}
REPOSITORY_EVIDENCE_ITEM_FIELDS = {"evidence_id", "path", "content"}
EXPECTED_ANSWER_FIELDS = {
    "schema_version",
    "primary_failure_type",
    "acceptable_failure_types",
    "required_evidence_ids",
    "optional_evidence_ids",
    "summary",
    "root_cause",
    "recommended_action",
}
SOURCE_TYPES = {"constructed", "public_permitted_source"}
FAILURE_TYPES = {
    "test_assertion_failure",
    "lint_or_type_failure",
    "dependency_or_install_failure",
    "config_or_environment_failure",
    "timeout_or_flaky_failure",
}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExpectedAnswer:
    schema_version: str
    primary_failure_type: str
    acceptable_failure_types: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    optional_evidence_ids: tuple[str, ...]
    summary: str
    root_cause: str
    recommended_action: str

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "primary_failure_type": self.primary_failure_type,
            "acceptable_failure_types": list(self.acceptable_failure_types),
            "required_evidence_ids": list(self.required_evidence_ids),
            "optional_evidence_ids": list(self.optional_evidence_ids),
            "summary": self.summary,
            "root_cause": self.root_cause,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class OfflineCasePackage:
    case_id: str
    case_schema_version: str
    manifest_path: Path
    case_fingerprint: str
    evidence_ids: tuple[str, ...]
    expected_answer: ExpectedAnswer
    fingerprint_input: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_schema_version": self.case_schema_version,
            "case_fingerprint": self.case_fingerprint,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class SuiteCase:
    case_id: str
    manifest: str
    weight: int | float
    package: OfflineCasePackage

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "manifest": self.manifest,
            "weight": self.weight,
            "case_fingerprint": self.package.case_fingerprint,
        }


@dataclass(frozen=True)
class EvaluationSuite:
    schema_version: str
    suite_id: str
    suite_version: str
    manifest_path: Path
    cases: tuple[SuiteCase, ...]
    suite_fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "cases": [case.as_dict() for case in self.cases],
            "suite_fingerprint": self.suite_fingerprint,
        }


def _canonical_fingerprint(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_json(path: Path, description: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationSuiteError(f"{description} does not exist: {path}") from exc
    except OSError as exc:
        raise EvaluationSuiteError(
            f"{description} cannot be read: {path}: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise EvaluationSuiteError(f"{description} is not valid UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationSuiteError(
            f"invalid JSON in {description} {path}: {exc.msg}"
        ) from exc


def _validate_fields(
    document: Any,
    fields: set[str],
    description: str,
    *,
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise EvaluationSuiteError(f"{description} must be a JSON object")
    missing = (fields - (optional or set())) - set(document)
    if missing:
        field = sorted(missing)[0]
        raise EvaluationSuiteError(
            f"{description} is missing required field {field!r}"
        )
    unknown = set(document) - fields
    if unknown:
        field = sorted(unknown)[0]
        raise EvaluationSuiteError(f"{description} has unknown field {field!r}")
    return document


def _non_empty_string(value: Any, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationSuiteError(f"{description} must be a non-empty string")
    return value


def _identifier(value: Any, description: str) -> str:
    identifier = _non_empty_string(value, description)
    if not IDENTIFIER_PATTERN.fullmatch(identifier):
        raise EvaluationSuiteError(
            f"{description} must start with an alphanumeric character and contain only "
            "letters, digits, '.', '_', ':', or '-'"
        )
    return identifier


def _declared_fingerprint(value: Any, description: str) -> str:
    if not isinstance(value, str) or not FINGERPRINT_PATTERN.fullmatch(value):
        raise EvaluationSuiteError(
            f"{description} must be a 64-character lowercase SHA-256 fingerprint"
        )
    return value


def _controlled_relative_path(value: Any, description: str) -> str:
    raw = _non_empty_string(value, description)
    if "\\" in raw:
        raise EvaluationSuiteError(
            f"{description} must use normalized POSIX relative path separators"
        )
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise EvaluationSuiteError(
            f"{description} must be a controlled relative path without '..'"
        )
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise EvaluationSuiteError(f"{description} must reference a file")
    return normalized


def _resolve_artifact(root: Path, relative_path: str, description: str) -> Path:
    resolved_root = root.resolve()
    resolved = (root / relative_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise EvaluationSuiteError(f"{description} resolves outside its package")
    if not resolved.is_file():
        raise EvaluationSuiteError(f"{description} does not exist: {relative_path}")
    return resolved


def _string_list(value: Any, description: str, *, allow_empty: bool) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise EvaluationSuiteError(
            f"{description} must be a list of non-empty strings"
        )
    if not allow_empty and not value:
        raise EvaluationSuiteError(f"{description} must not be empty")
    if len(value) != len(set(value)):
        raise EvaluationSuiteError(f"{description} must not contain duplicates")
    return value


def _load_log_chunks(path: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    document = _validate_fields(
        _read_json(path, "frozen log chunks"),
        LOG_CHUNKS_FIELDS,
        "frozen log chunks",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError(
            "unsupported frozen log chunks schema version "
            f"{document['schema_version']!r}"
        )
    chunks = document["chunks"]
    if not isinstance(chunks, list) or not chunks:
        raise EvaluationSuiteError("frozen log chunks 'chunks' must be a non-empty list")
    evidence_ids: list[str] = []
    for index, raw_chunk in enumerate(chunks):
        chunk = _validate_fields(
            raw_chunk,
            LOG_CHUNK_FIELDS,
            f"frozen log chunk at index {index}",
        )
        evidence_ids.append(
            _identifier(chunk["evidence_id"], f"frozen log chunk {index} evidence_id")
        )
        _non_empty_string(chunk["text"], f"frozen log chunk {index} text")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise EvaluationSuiteError("frozen log chunks contain duplicate evidence IDs")
    return document, tuple(evidence_ids)


def _load_repository_evidence(
    path: Path,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    document = _validate_fields(
        _read_json(path, "repository evidence snapshot"),
        REPOSITORY_EVIDENCE_FIELDS,
        "repository evidence snapshot",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError(
            "unsupported repository evidence schema version "
            f"{document['schema_version']!r}"
        )
    items = document["items"]
    if not isinstance(items, list) or not items:
        raise EvaluationSuiteError(
            "repository evidence snapshot 'items' must be a non-empty list"
        )
    evidence_ids: list[str] = []
    for index, raw_item in enumerate(items):
        item = _validate_fields(
            raw_item,
            REPOSITORY_EVIDENCE_ITEM_FIELDS,
            f"repository evidence item at index {index}",
        )
        evidence_ids.append(
            _identifier(
                item["evidence_id"],
                f"repository evidence item {index} evidence_id",
            )
        )
        item["path"] = _controlled_relative_path(
            item["path"], f"repository evidence item {index} path"
        )
        _non_empty_string(
            item["content"], f"repository evidence item {index} content"
        )
    if len(evidence_ids) != len(set(evidence_ids)):
        raise EvaluationSuiteError(
            "repository evidence snapshot contains duplicate evidence IDs"
        )
    return document, tuple(evidence_ids)


def _load_expected_answer(path: Path, evidence_ids: set[str]) -> ExpectedAnswer:
    document = _validate_fields(
        _read_json(path, "expected answer"),
        EXPECTED_ANSWER_FIELDS,
        "expected answer",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError(
            f"unsupported expected answer schema version {document['schema_version']!r}"
        )
    primary_failure_type = _non_empty_string(
        document["primary_failure_type"],
        "expected answer primary_failure_type",
    )
    if primary_failure_type not in FAILURE_TYPES:
        raise EvaluationSuiteError(
            "expected answer has unsupported primary_failure_type "
            f"{primary_failure_type!r}"
        )
    acceptable = _string_list(
        document["acceptable_failure_types"],
        "expected answer acceptable_failure_types",
        allow_empty=True,
    )
    unsupported = set(acceptable) - FAILURE_TYPES
    if unsupported:
        raise EvaluationSuiteError(
            "expected answer has unsupported acceptable failure type "
            f"{sorted(unsupported)[0]!r}"
        )
    if primary_failure_type in acceptable:
        raise EvaluationSuiteError(
            "expected answer primary_failure_type must not appear in "
            "acceptable_failure_types"
        )
    required = _string_list(
        document["required_evidence_ids"],
        "expected answer required_evidence_ids",
        allow_empty=False,
    )
    optional = _string_list(
        document["optional_evidence_ids"],
        "expected answer optional_evidence_ids",
        allow_empty=True,
    )
    overlap = set(required) & set(optional)
    if overlap:
        raise EvaluationSuiteError(
            f"expected answer evidence ID {sorted(overlap)[0]!r} is both required and optional"
        )
    missing = (set(required) | set(optional)) - evidence_ids
    if missing:
        raise EvaluationSuiteError(
            f"expected answer references unknown evidence ID {sorted(missing)[0]!r}"
        )
    for field in ("summary", "root_cause", "recommended_action"):
        _non_empty_string(document[field], f"expected answer {field}")
    return ExpectedAnswer(
        schema_version=document["schema_version"],
        primary_failure_type=primary_failure_type,
        acceptable_failure_types=tuple(acceptable),
        required_evidence_ids=tuple(required),
        optional_evidence_ids=tuple(optional),
        summary=document["summary"],
        root_cause=document["root_cause"],
        recommended_action=document["recommended_action"],
    )


def _load_case_package(
    manifest_path: Path,
    *,
    verify_fingerprint: bool,
) -> OfflineCasePackage:
    document = _validate_fields(
        _read_json(manifest_path, "case manifest"),
        CASE_FIELDS,
        "case manifest",
    )
    if document["case_schema_version"] != "1":
        raise EvaluationSuiteError(
            "unsupported case schema version "
            f"{document['case_schema_version']!r}"
        )
    case_id = _identifier(document["case_id"], "case manifest case_id")

    normalized_paths = {
        field: _controlled_relative_path(
            document[field], f"case {case_id!r} {field}"
        )
        for field in (
            "raw_log",
            "frozen_log_chunks",
            "repository_evidence",
            "expected_answer",
        )
    }
    if len(set(normalized_paths.values())) != len(normalized_paths):
        raise EvaluationSuiteError(
            f"case {case_id!r} artifact paths must reference distinct files"
        )
    root = manifest_path.parent
    artifact_paths = {
        field: _resolve_artifact(root, relative_path, f"case {case_id!r} {field}")
        for field, relative_path in normalized_paths.items()
    }
    try:
        raw_log = artifact_paths["raw_log"].read_text(encoding="utf-8")
    except OSError as exc:
        raise EvaluationSuiteError(
            f"case {case_id!r} raw log cannot be read: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise EvaluationSuiteError(f"case {case_id!r} raw log is not valid UTF-8") from exc
    if not raw_log:
        raise EvaluationSuiteError(f"case {case_id!r} raw log must not be empty")

    log_chunks, log_evidence_ids = _load_log_chunks(
        artifact_paths["frozen_log_chunks"]
    )
    actual_chunks_fingerprint = _canonical_fingerprint(log_chunks)
    declared_chunks_fingerprint = _declared_fingerprint(
        document["frozen_log_chunks_fingerprint"],
        f"case {case_id!r} frozen_log_chunks_fingerprint",
    )
    if declared_chunks_fingerprint != actual_chunks_fingerprint:
        raise EvaluationSuiteError(
            f"case {case_id!r} frozen log chunks fingerprint changed: declared "
            f"{declared_chunks_fingerprint}, actual {actual_chunks_fingerprint}"
        )

    repository_evidence, repository_evidence_ids = _load_repository_evidence(
        artifact_paths["repository_evidence"]
    )
    all_evidence_ids = log_evidence_ids + repository_evidence_ids
    if len(all_evidence_ids) != len(set(all_evidence_ids)):
        raise EvaluationSuiteError(
            f"case {case_id!r} contains duplicate stable evidence IDs across artifacts"
        )
    expected_answer = _load_expected_answer(
        artifact_paths["expected_answer"], set(all_evidence_ids)
    )

    _string_list(
        document["forbidden_actions"],
        f"case {case_id!r} forbidden_actions",
        allow_empty=False,
    )
    source_type = _non_empty_string(
        document["source_type"], f"case {case_id!r} provenance source_type"
    )
    if source_type not in SOURCE_TYPES:
        raise EvaluationSuiteError(
            f"case {case_id!r} has unsupported provenance source_type "
            f"{source_type!r}"
        )
    for field in (
        "source_url_or_construction_note",
        "license_or_permission",
        "created_by",
        "reviewed_by",
    ):
        _non_empty_string(document[field], f"case {case_id!r} provenance {field}")
    if (
        source_type == "constructed"
        and document["license_or_permission"] != "project_constructed"
    ):
        raise EvaluationSuiteError(
            f"constructed case {case_id!r} must use license_or_permission "
            "'project_constructed'"
        )
    if document["sanitization_status"] != "reviewed_sanitized":
        raise EvaluationSuiteError(
            f"case {case_id!r} is not eligible for formal evaluation: "
            "sanitization_status must be 'reviewed_sanitized'"
        )

    declared_case_fingerprint = _declared_fingerprint(
        document["case_fingerprint"], f"case {case_id!r} case_fingerprint"
    )
    normalized_manifest = {
        key: value
        for key, value in document.items()
        if key != "case_fingerprint"
    }
    normalized_manifest.update(normalized_paths)
    fingerprint_input = {
        "manifest": normalized_manifest,
        "artifacts": {
            "raw_log": raw_log,
            "frozen_log_chunks": log_chunks,
            "repository_evidence": repository_evidence,
            "expected_answer": expected_answer.fingerprint_input(),
        },
    }
    actual_case_fingerprint = _canonical_fingerprint(fingerprint_input)
    if verify_fingerprint and declared_case_fingerprint != actual_case_fingerprint:
        raise EvaluationSuiteError(
            f"case {case_id!r} fingerprint changed: declared "
            f"{declared_case_fingerprint}, actual {actual_case_fingerprint}"
        )
    return OfflineCasePackage(
        case_id=case_id,
        case_schema_version=document["case_schema_version"],
        manifest_path=manifest_path,
        case_fingerprint=actual_case_fingerprint,
        evidence_ids=tuple(sorted(all_evidence_ids)),
        expected_answer=expected_answer,
        fingerprint_input=fingerprint_input,
    )


def load_case_package(manifest_path: Path) -> OfflineCasePackage:
    return _load_case_package(manifest_path, verify_fingerprint=True)


def calculate_case_fingerprint(manifest_path: Path) -> str:
    return _load_case_package(
        manifest_path,
        verify_fingerprint=False,
    ).case_fingerprint


def _load_evaluation_suite(
    manifest_path: Path,
    *,
    verify_fingerprint: bool,
) -> EvaluationSuite:
    document = _validate_fields(
        _read_json(manifest_path, "suite manifest"),
        SUITE_FIELDS,
        "suite manifest",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError(
            f"unsupported suite schema version {document['schema_version']!r}"
        )
    suite_id = _identifier(document["suite_id"], "suite manifest suite_id")
    suite_version = _identifier(
        document["suite_version"], "suite manifest suite_version"
    )
    raw_cases = document["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise EvaluationSuiteError("suite manifest 'cases' must be a non-empty list")

    suite_root = manifest_path.parent
    cases: list[SuiteCase] = []
    normalized_entries: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for index, raw_entry in enumerate(raw_cases):
        entry = _validate_fields(
            raw_entry,
            SUITE_CASE_FIELDS,
            f"suite case at index {index}",
        )
        case_id = _identifier(entry["case_id"], f"suite case {index} case_id")
        if case_id in seen_case_ids:
            raise EvaluationSuiteError(
                f"suite manifest contains duplicate case ID {case_id!r}"
            )
        seen_case_ids.add(case_id)
        relative_manifest = _controlled_relative_path(
            entry["manifest"], f"suite case {case_id!r} manifest"
        )
        case_manifest_path = _resolve_artifact(
            suite_root,
            relative_manifest,
            f"suite case {case_id!r} manifest",
        )
        weight = entry["weight"]
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight <= 0
        ):
            raise EvaluationSuiteError(
                f"suite case {case_id!r} weight must be a positive finite number"
            )
        package = load_case_package(case_manifest_path)
        if package.case_id != case_id:
            raise EvaluationSuiteError(
                f"suite case ID {case_id!r} does not match case manifest ID "
                f"{package.case_id!r}"
            )
        cases.append(
            SuiteCase(
                case_id=case_id,
                manifest=relative_manifest,
                weight=weight,
                package=package,
            )
        )
        normalized_entries.append(
            {
                "case_id": case_id,
                "manifest": relative_manifest,
                "weight": weight,
            }
        )
    if len({case.weight for case in cases}) != 1:
        raise EvaluationSuiteError(
            "V1 formal evaluation suites require equal case weights"
        )

    declared_suite_fingerprint = _declared_fingerprint(
        document["suite_fingerprint"], "suite manifest suite_fingerprint"
    )
    normalized_manifest = {
        key: value
        for key, value in document.items()
        if key != "suite_fingerprint"
    }
    normalized_manifest["cases"] = normalized_entries
    fingerprint_input = {
        "manifest": normalized_manifest,
        "case_fingerprints": [
            {
                "case_id": case.case_id,
                "case_fingerprint": case.package.case_fingerprint,
            }
            for case in cases
        ],
    }
    actual_suite_fingerprint = _canonical_fingerprint(fingerprint_input)
    if verify_fingerprint and declared_suite_fingerprint != actual_suite_fingerprint:
        raise EvaluationSuiteError(
            f"suite {suite_id!r} fingerprint changed: declared "
            f"{declared_suite_fingerprint}, actual {actual_suite_fingerprint}"
        )
    return EvaluationSuite(
        schema_version=document["schema_version"],
        suite_id=suite_id,
        suite_version=suite_version,
        manifest_path=manifest_path,
        cases=tuple(cases),
        suite_fingerprint=actual_suite_fingerprint,
    )


def load_evaluation_suite(manifest_path: Path) -> EvaluationSuite:
    return _load_evaluation_suite(manifest_path, verify_fingerprint=True)


def calculate_suite_fingerprint(manifest_path: Path) -> str:
    return _load_evaluation_suite(
        manifest_path,
        verify_fingerprint=False,
    ).suite_fingerprint


def validate_matrix_suite_references(matrix: Any, suite: EvaluationSuite) -> None:
    for condition in matrix.conditions:
        referenced_suite = condition.effective_condition["suite"]
        if referenced_suite != suite.suite_id:
            raise EvaluationSuiteError(
                f"condition {condition.condition_id!r} references suite "
                f"{referenced_suite!r}, but formal preflight loaded {suite.suite_id!r}"
            )
