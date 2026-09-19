from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class EvaluationSuiteError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_evaluation_suite",
        public_message: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.public_message = public_message or message


CASE_FIELDS = {
    "case_schema_version",
    "case_id",
    "artifacts",
    "forbidden_actions",
    "provenance",
    "curation",
    "sanitization",
    "case_fingerprint",
}
CASE_ARTIFACT_FIELDS = {
    "raw_log",
    "repository_manifest",
    "repository_root",
    "log_units",
    "repository_units",
    "required_evidence",
    "expected_answer",
}
PROVENANCE_FIELDS = {
    "source_type",
    "source_url_or_construction_note",
    "license_or_permission",
}
CURATION_FIELDS = {"created_by", "review_status", "reviewed_by"}
SANITIZATION_FIELDS = {"status", "reviewed_by", "transformations"}
SANITIZATION_TRANSFORMATION_FIELDS = {
    "artifact_path",
    "description",
    "semantics_preserving",
}
SUITE_FIELDS = {
    "schema_version",
    "suite_id",
    "suite_version",
    "cases",
    "suite_fingerprint",
}
SUITE_CASE_FIELDS = {"case_id", "manifest", "weight"}
REPOSITORY_MANIFEST_FIELDS = {"schema_version", "upstream_repository", "files"}
UPSTREAM_REPOSITORY_FIELDS = {"identity", "revision_kind", "exact_revision"}
REPOSITORY_FILE_FIELDS = {"path", "sha256", "size_bytes"}
CANONICAL_EVIDENCE_FIELDS = {"schema_version", "units"}
CANONICAL_EVIDENCE_UNIT_FIELDS = {
    "evidence_id",
    "source",
    "span",
    "content_sha256",
}
SOURCE_SPAN_FIELDS = {"type", "start_line", "end_line"}
EVIDENCE_GROUND_TRUTH_FIELDS = {
    "schema_version",
    "required_evidence_ids",
    "optional_evidence_ids",
}
EXPECTED_ANSWER_FIELDS = {
    "schema_version",
    "primary_failure_type",
    "acceptable_failure_types",
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
EVIDENCE_ID_PATTERN = re.compile(r"^(log|repo):[a-z0-9][a-z0-9._:-]{0,127}$")
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


@dataclass(frozen=True)
class ExpectedAnswer:
    schema_version: str
    primary_failure_type: str
    acceptable_failure_types: tuple[str, ...]
    summary: str
    root_cause: str
    recommended_action: str

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "primary_failure_type": self.primary_failure_type,
            "acceptable_failure_types": list(self.acceptable_failure_types),
            "summary": self.summary,
            "root_cause": self.root_cause,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class EvidenceGroundTruth:
    schema_version: str
    required_evidence_ids: tuple[str, ...]
    optional_evidence_ids: tuple[str, ...]

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "required_evidence_ids": list(self.required_evidence_ids),
            "optional_evidence_ids": list(self.optional_evidence_ids),
        }


@dataclass(frozen=True)
class RepositorySnapshotFile:
    path: str
    sha256: str
    size_bytes: int

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class RepositorySnapshot:
    identity: str
    revision_kind: str
    exact_revision: str
    files: tuple[RepositorySnapshotFile, ...]

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "upstream_repository": {
                "identity": self.identity,
                "revision_kind": self.revision_kind,
                "exact_revision": self.exact_revision,
            },
            "files": [item.fingerprint_input() for item in self.files],
        }


@dataclass(frozen=True)
class CanonicalEvidenceUnit:
    evidence_id: str
    source: str
    start_line: int
    end_line: int
    content_sha256: str

    def fingerprint_input(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "span": {
                "type": "line_range",
                "start_line": self.start_line,
                "end_line": self.end_line,
            },
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class PublicCaseView:
    case_id: str
    case_schema_version: str
    case_fingerprint: str
    raw_log_path: str
    repository_root: str
    forbidden_actions: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_schema_version": self.case_schema_version,
            "case_fingerprint": self.case_fingerprint,
            "raw_log_path": self.raw_log_path,
            "repository_root": self.repository_root,
            "forbidden_actions": list(self.forbidden_actions),
        }


@dataclass(frozen=True)
class OfflineCasePackage:
    case_id: str
    case_schema_version: str
    manifest_path: Path
    case_fingerprint: str
    raw_log_path: str
    repository_root: str
    forbidden_actions: tuple[str, ...]
    repository_snapshot: RepositorySnapshot
    canonical_evidence_units: tuple[CanonicalEvidenceUnit, ...]
    evidence_ids: tuple[str, ...]
    evidence_ground_truth: EvidenceGroundTruth
    expected_answer: ExpectedAnswer
    fingerprint_input: dict[str, Any]

    def public_view(self) -> PublicCaseView:
        """投影普通 Runtime 所需的 Case 身份、物理路径和禁止动作声明。

        不传递 expected_answer、Evidence Ground Truth 或完整 fingerprint_input，
        避免参考答案沿对象序列化进入模型输入。这是字段层面的隔离，不会改变
        文件系统权限；forbidden_actions 在此也只是数据，不是动作拦截器。"""
        return PublicCaseView(
            case_id=self.case_id,
            case_schema_version=self.case_schema_version,
            case_fingerprint=self.case_fingerprint,
            raw_log_path=self.raw_log_path,
            repository_root=self.repository_root,
            forbidden_actions=self.forbidden_actions,
        )


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
    """解析实际文件路径并检查其仍位于包根目录，阻止路径或 symlink 越界。

    这是加载时的路径校验，不是 OS sandbox；不会隔离同进程代码的文件权限，
    也没有锁定校验后的文件。仓库目录的 symlink 另由 _resolve_directory 拒绝。"""
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


def _read_bytes(path: Path, description: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvaluationSuiteError(f"{description} cannot be read: {exc}") from exc


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _resolve_directory(root: Path, relative_path: str, description: str) -> Path:
    candidate = root / relative_path
    relative = Path(*PurePosixPath(relative_path).parts)
    path_chain = [
        root / Path(*relative.parts[:index])
        for index in range(1, len(relative.parts) + 1)
    ]
    if any(path.is_symlink() for path in path_chain):
        raise EvaluationSuiteError(f"{description} must not use symlinks")
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise EvaluationSuiteError(f"{description} resolves outside its package")
    if not resolved.is_dir():
        raise EvaluationSuiteError(f"{description} does not exist: {relative_path}")
    return resolved


def _load_repository_snapshot(
    manifest_path: Path,
    repository_root_path: Path,
) -> RepositorySnapshot:
    """验证 manifest 声明的仓库快照，并返回按路径排序的文件身份。

    逐个读取真实文件 bytes，核对 size_bytes 和 SHA-256，而非盲信声明摘要；
    再扫描目录拒绝 symlink 和额外文件，防止 Runtime 看见未纳入身份的材料。
    返回对象保留来源/revision、路径、大小及已验证摘要，不保存文件正文。"""
    document = _validate_fields(
        _read_json(manifest_path, "repository manifest"),
        REPOSITORY_MANIFEST_FIELDS,
        "repository manifest",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError("unsupported repository manifest schema version")
    upstream = _validate_fields(
        document["upstream_repository"],
        UPSTREAM_REPOSITORY_FIELDS,
        "repository manifest upstream_repository",
    )
    identity = _non_empty_string(
        upstream["identity"], "repository manifest upstream identity"
    )
    revision_kind = upstream["revision_kind"]
    if revision_kind not in {"git_commit", "constructed_snapshot"}:
        raise EvaluationSuiteError("repository manifest has unsupported revision_kind")
    exact_revision = _non_empty_string(
        upstream["exact_revision"], "repository manifest exact_revision"
    )
    if revision_kind == "git_commit" and not GIT_COMMIT_PATTERN.fullmatch(
        exact_revision
    ):
        raise EvaluationSuiteError(
            "repository manifest git_commit exact_revision must be a 40- or "
            "64-character lowercase hexadecimal commit ID"
        )
    if revision_kind == "constructed_snapshot":
        _identifier(exact_revision, "repository manifest constructed exact_revision")

    raw_files = document["files"]
    if not isinstance(raw_files, list) or not raw_files:
        raise EvaluationSuiteError("repository manifest files must be a non-empty list")
    files: list[RepositorySnapshotFile] = []
    seen_paths: set[str] = set()
    for index, raw_file in enumerate(raw_files):
        item = _validate_fields(
            raw_file,
            REPOSITORY_FILE_FIELDS,
            f"repository manifest file at index {index}",
        )
        relative_path = _controlled_relative_path(
            item["path"], f"repository manifest file {index} path"
        )
        if relative_path in seen_paths:
            raise EvaluationSuiteError(
                "repository manifest files must not contain duplicate paths"
            )
        seen_paths.add(relative_path)
        declared_sha256 = _declared_fingerprint(
            item["sha256"], f"repository manifest file {relative_path!r} sha256"
        )
        size_bytes = item["size_bytes"]
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
            raise EvaluationSuiteError(
                f"repository manifest file {relative_path!r} size_bytes must be a "
                "non-negative integer"
            )
        candidate = repository_root_path / relative_path
        relative_candidate = candidate.relative_to(repository_root_path)
        member_chain = [ # 校验路径链不能经过 symlink
            repository_root_path / Path(*relative_candidate.parts[:index])
            for index in range(1, len(relative_candidate.parts) + 1)
        ]
        if any(member.is_symlink() for member in member_chain):
            raise EvaluationSuiteError(
                f"repository member {relative_path!r} must not use symlinks"
            )
        if not candidate.is_file():
            raise EvaluationSuiteError(
                f"repository manifest member does not exist: {relative_path}"
            )
        content = _read_bytes(candidate, f"repository member {relative_path!r}")
        if len(content) != size_bytes:
            raise EvaluationSuiteError(
                f"repository member {relative_path!r} size does not match manifest"
            )
        if _sha256(content) != declared_sha256:
            raise EvaluationSuiteError(
                f"repository member {relative_path!r} hash does not match manifest"
            )
        files.append(
            RepositorySnapshotFile(
                path=relative_path,
                sha256=declared_sha256,
                size_bytes=size_bytes,
            )
        )

    actual_paths: set[str] = set()
    for directory, directory_names, file_names in os.walk(
        repository_root_path, followlinks=False
    ): # 用于保证真实 repository snapshot 中的文件集合，必须和 repository manifest 声明的文件集合完全一致。否则就可能有未纳入 fingerprint/manifest 管理的“幽灵文件”影响 Agent
        directory_path = Path(directory)
        for directory_name in directory_names:
            if (directory_path / directory_name).is_symlink():
                raise EvaluationSuiteError("repository snapshot must not contain symlinks")
        for file_name in file_names:
            candidate = directory_path / file_name
            if candidate.is_symlink():
                raise EvaluationSuiteError("repository snapshot must not contain symlinks")
            actual_paths.add(candidate.relative_to(repository_root_path).as_posix())
    extra = actual_paths - seen_paths
    if extra:
        raise EvaluationSuiteError(
            f"repository snapshot contains undeclared member {sorted(extra)[0]!r}"
        )
    return RepositorySnapshot(
        identity=identity,
        revision_kind=revision_kind,
        exact_revision=exact_revision,
        files=tuple(sorted(files, key=lambda item: item.path)),
    )


def _line_ranges(content: bytes, description: str) -> list[bytes]:
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvaluationSuiteError(f"{description} is not valid UTF-8") from exc
    lines: list[bytes] = []
    start = 0
    for index, byte in enumerate(content):
        if byte == 0x0A:
            lines.append(content[start : index + 1])
            start = index + 1
    if start < len(content):
        lines.append(content[start:])
    return lines


def _load_canonical_units(
    path: Path,
    *,
    kind: str,
    raw_log_path: str,
    raw_log_content: bytes,
    repository_root: str,
    repository_root_path: Path,
    repository_members: set[str],
) -> tuple[CanonicalEvidenceUnit, ...]:
    """将 Canonical Evidence 坐标核对到真实物理内容，返回按 ID 排序的 units。

    log 使用调用方读取的原始 bytes；repo 从已声明成员重新读取。按 1-based、
    两端包含的行范围拼接 bytes 并核对 content_sha256，越界/未知成员/摘要漂移
    均阻止加载。坐标是引用与评分单位，不是在这里生成的 Retrieval chunks。"""
    description = f"canonical {kind} evidence"
    document = _validate_fields(
        _read_json(path, description),
        CANONICAL_EVIDENCE_FIELDS,
        description,
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError(f"unsupported {description} schema version")
    raw_units = document["units"]
    if not isinstance(raw_units, list):
        raise EvaluationSuiteError(f"{description} units must be a list")
    units: list[CanonicalEvidenceUnit] = []
    seen_ids: set[str] = set()
    expected_prefix = f"{kind}:"
    for index, raw_unit in enumerate(raw_units):
        unit = _validate_fields(
            raw_unit,
            CANONICAL_EVIDENCE_UNIT_FIELDS,
            f"{description} unit at index {index}",
        )
        evidence_id = _non_empty_string(
            unit["evidence_id"], f"{description} unit {index} evidence_id"
        )
        if not EVIDENCE_ID_PATTERN.fullmatch(evidence_id) or not evidence_id.startswith(
            expected_prefix
        ):
            raise EvaluationSuiteError(
                f"{description} unit {index} has invalid evidence_id"
            )
        if evidence_id in seen_ids:
            raise EvaluationSuiteError(f"{description} contains duplicate evidence IDs")
        seen_ids.add(evidence_id)
        source = _controlled_relative_path(
            unit["source"], f"{description} unit {evidence_id!r} source"
        )
        if kind == "log":
            if source != raw_log_path:
                raise EvaluationSuiteError(
                    "canonical log unit source must equal the declared raw log path"
                )
            source_content = raw_log_content
        else:
            prefix = f"{repository_root}/"
            if not source.startswith(prefix):
                raise EvaluationSuiteError(
                    "canonical repository unit source must be inside the declared "
                    "repository root"
                )
            member = source[len(prefix) :]
            if member not in repository_members:
                raise EvaluationSuiteError(
                    "canonical repository unit source must name a manifest-declared member"
                )
            source_content = _read_bytes(
                repository_root_path / member,
                f"canonical repository source {member!r}",
            )
        span = _validate_fields(
            unit["span"],
            SOURCE_SPAN_FIELDS,
            f"{description} unit {evidence_id!r} span",
        )
        if span["type"] != "line_range":
            raise EvaluationSuiteError("canonical source span type must be 'line_range'")
        start_line = span["start_line"]
        end_line = span["end_line"]
        if (
            isinstance(start_line, bool)
            or isinstance(end_line, bool)
            or not isinstance(start_line, int)
            or not isinstance(end_line, int)
            or start_line < 1
            or end_line < start_line
        ):
            raise EvaluationSuiteError(
                "canonical line range must use positive 1-based inclusive bounds"
            )
        lines = _line_ranges(source_content, f"canonical source {source!r}")
        if end_line > len(lines):
            raise EvaluationSuiteError("canonical line range exceeds source EOF")
        resolved = b"".join(lines[start_line - 1 : end_line])
        content_sha256 = _declared_fingerprint(
            unit["content_sha256"],
            f"{description} unit {evidence_id!r} content_sha256",
        )
        if _sha256(resolved) != content_sha256: # 验证读取的实际文件的指定的那些行的sha256是否和canonical-evidence json文件中声明的一致
            raise EvaluationSuiteError(
                f"canonical evidence unit {evidence_id!r} content hash does not match source"
            )
        units.append(
            CanonicalEvidenceUnit(
                evidence_id=evidence_id,
                source=source,
                start_line=start_line,
                end_line=end_line,
                content_sha256=content_sha256,
            )
        )
    return tuple(sorted(units, key=lambda item: item.evidence_id))


def _load_evidence_ground_truth(
    path: Path, evidence_ids: set[str]
) -> EvidenceGroundTruth:
    document = _validate_fields(
        _read_json(path, "evidence ground truth"),
        EVIDENCE_GROUND_TRUTH_FIELDS,
        "evidence ground truth",
    )
    if document["schema_version"] != "1":
        raise EvaluationSuiteError("unsupported evidence ground truth schema version")
    required = _string_list(
        document["required_evidence_ids"],
        "evidence ground truth required_evidence_ids",
        allow_empty=False,
    )
    optional = _string_list(
        document["optional_evidence_ids"],
        "evidence ground truth optional_evidence_ids",
        allow_empty=True,
    )
    overlap = set(required) & set(optional)
    if overlap:
        raise EvaluationSuiteError(
            "evidence ground truth Required and Optional IDs must be disjoint"
        )
    if (set(required) | set(optional)) - evidence_ids:
        raise EvaluationSuiteError(
            "evidence ground truth references an unknown Canonical Evidence ID"
        )
    return EvidenceGroundTruth(
        schema_version="1",
        required_evidence_ids=tuple(sorted(required)),
        optional_evidence_ids=tuple(sorted(optional)),
    )


def _load_expected_answer(path: Path) -> ExpectedAnswer:
    document = _validate_fields(
        _read_json(path, "expected answer"),
        EXPECTED_ANSWER_FIELDS,
        "expected answer",
    )
    if document["schema_version"] != "2":
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
    for field in ("summary", "root_cause", "recommended_action"):
        _non_empty_string(document[field], f"expected answer {field}")
    return ExpectedAnswer(
        schema_version=document["schema_version"],
        primary_failure_type=primary_failure_type,
        acceptable_failure_types=tuple(sorted(acceptable)),
        summary=document["summary"],
        root_cause=document["root_cause"],
        recommended_action=document["recommended_action"],
    )


def _load_sanitization(
    raw_sanitization: Any,
    *,
    physical_sources: set[str],
) -> dict[str, Any]:
    sanitization = _validate_fields(
        raw_sanitization,
        SANITIZATION_FIELDS,
        "case manifest sanitization",
    )
    status = sanitization["status"]
    if status not in {"reviewed_no_changes", "reviewed_sanitized"}:
        raise EvaluationSuiteError("case sanitization has unsupported status")
    reviewed_by = _non_empty_string(
        sanitization["reviewed_by"], "case sanitization reviewed_by"
    )
    raw_transformations = sanitization["transformations"]
    if not isinstance(raw_transformations, list):
        raise EvaluationSuiteError("case sanitization transformations must be a list")
    if status == "reviewed_no_changes" and raw_transformations:
        raise EvaluationSuiteError(
            "reviewed_no_changes sanitization must not declare transformations"
        )
    if status == "reviewed_sanitized" and not raw_transformations:
        raise EvaluationSuiteError(
            "reviewed_sanitized sanitization must declare transformations"
        )
    transformations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_transformation in enumerate(raw_transformations):
        transformation = _validate_fields(
            raw_transformation,
            SANITIZATION_TRANSFORMATION_FIELDS,
            f"case sanitization transformation at index {index}",
        )
        artifact_path = _controlled_relative_path(
            transformation["artifact_path"],
            f"case sanitization transformation {index} artifact_path",
        )
        if artifact_path not in physical_sources:
            raise EvaluationSuiteError(
                "case sanitization transformation must reference a frozen Physical Artifact"
            )
        description = _non_empty_string(
            transformation["description"],
            f"case sanitization transformation {index} description",
        )
        if transformation["semantics_preserving"] is not True:
            raise EvaluationSuiteError(
                "case sanitization transformations must be semantics-preserving"
            )
        identity = (artifact_path, description)
        if identity in seen:
            raise EvaluationSuiteError(
                "case sanitization transformations must not contain duplicates"
            )
        seen.add(identity)
        transformations.append(
            {
                "artifact_path": artifact_path,
                "description": description,
                "semantics_preserving": True,
            }
        )
    return {
        "status": status,
        "reviewed_by": reviewed_by,
        "transformations": sorted(
            transformations,
            key=lambda item: (item["artifact_path"], item["description"]),
        ),
    }


def _load_case_package(
    manifest_path: Path,
    *,
    verify_fingerprint: bool,
) -> OfflineCasePackage:
    """加载仅支持 Schema V2 的 Case，建立经验证的物理/坐标/Ground Truth 身份。

    依次检查目录分层和物理内容、Canonical spans、两份 Ground Truth 及元数据，
    再计算 Case 指纹。返回对象属于可信 Harness/Evaluator，含隐藏答案；
    普通 Runtime 输入应由 public_view/RuntimeCaseWorkspace 投影，不能直接序列化它。
    verify_fingerprint=False 只跳过最终声明值比对，仍执行文件与内容一致性检查。"""
    raw_document = _read_json(manifest_path, "case manifest")
    if isinstance(raw_document, dict):
        if "case_schema_version" not in raw_document:
            raise EvaluationSuiteError(
                "case manifest is missing required field 'case_schema_version'",
                code="invalid_case_manifest",
            )
        schema_version = raw_document.get("case_schema_version")
        if not isinstance(schema_version, str):
            raise EvaluationSuiteError(
                "case manifest case_schema_version must be a string",
                code="invalid_case_manifest",
            )
        if isinstance(schema_version, str) and schema_version != "2":
            raise EvaluationSuiteError(
                "unsupported Offline Case Schema version",
                code="unsupported_case_schema_version",
            )
    document = _validate_fields(
        raw_document,
        CASE_FIELDS,
        "case manifest",
    )
    if document["case_schema_version"] != "2":
        raise EvaluationSuiteError(
            "case manifest case_schema_version must be the string '2'",
            code="invalid_case_manifest",
        )
    case_id = _identifier(document["case_id"], "case manifest case_id")
    artifacts = _validate_fields(
        document["artifacts"], CASE_ARTIFACT_FIELDS, "case manifest artifacts"
    )
    normalized_paths = {
        field: _controlled_relative_path( # 先把 artifacts 里声明的每个路径都经过 _controlled_relative_path() 规范化
            artifacts[field], f"case {case_id!r} artifact {field}"
        )
        for field in CASE_ARTIFACT_FIELDS
    }
    if len(normalized_paths) != len(set(normalized_paths.values())):
        raise EvaluationSuiteError("case artifacts must use distinct paths")
    expected_layers = {
        "raw_log": "physical-artifacts/",
        "repository_manifest": "physical-artifacts/",
        "repository_root": "physical-artifacts/",
        "log_units": "canonical-evidence/",
        "repository_units": "canonical-evidence/",
        "required_evidence": "evaluator/",
        "expected_answer": "evaluator/",
    } # 所有 artifact 都只能引用 Case Package 内部受控路径；每类 artifact 必须待在它应该属于的语义层。
    for field, prefix in expected_layers.items(): # 校验是在强制 Case Package 的物理目录结构与语义层次一致
        if not normalized_paths[field].startswith(prefix):
            raise EvaluationSuiteError(
                f"case artifact {field!r} must be located under {prefix!r}"
            )
    root = manifest_path.parent
    repository_root_path = _resolve_directory(
        root,
        normalized_paths["repository_root"],
        f"case {case_id!r} repository_root",
    )
    artifact_paths = {
        field: _resolve_artifact(
            root, normalized_paths[field], f"case {case_id!r} artifact {field}"
        )
        for field in CASE_ARTIFACT_FIELDS - {"repository_root"}
    }
    raw_log = _read_bytes(artifact_paths["raw_log"], f"case {case_id!r} raw log")
    if not raw_log:
        raise EvaluationSuiteError(f"case {case_id!r} raw log must not be empty")
    _line_ranges(raw_log, f"case {case_id!r} raw log")

    repository_snapshot = _load_repository_snapshot(
        artifact_paths["repository_manifest"], repository_root_path
    )
    repository_members = {item.path for item in repository_snapshot.files}
    log_units = _load_canonical_units(
        artifact_paths["log_units"],
        kind="log",
        raw_log_path=normalized_paths["raw_log"],
        raw_log_content=raw_log,
        repository_root=normalized_paths["repository_root"],
        repository_root_path=repository_root_path,
        repository_members=repository_members,
    )
    repository_units = _load_canonical_units(
        artifact_paths["repository_units"],
        kind="repo",
        raw_log_path=normalized_paths["raw_log"],
        raw_log_content=raw_log,
        repository_root=normalized_paths["repository_root"],
        repository_root_path=repository_root_path,
        repository_members=repository_members,
    )
    canonical_units = log_units + repository_units
    all_evidence_ids = tuple(unit.evidence_id for unit in canonical_units)
    if len(all_evidence_ids) != len(set(all_evidence_ids)):
        raise EvaluationSuiteError(
            f"case {case_id!r} contains duplicate stable evidence IDs across artifacts"
        )
    all_evidence_ids = tuple(sorted(all_evidence_ids))
    evidence_ground_truth = _load_evidence_ground_truth( # 读取 required_evidence_ids 读取 optional_evidence_ids → 两者不能重叠 → 两边引用的 evidence_id 都必须真的存在于前面已经验证过的 canonical evidence 集合里 → 最后构造成 EvidenceGroundTruth
        artifact_paths["required_evidence"], set(all_evidence_ids)
    )
    expected_answer = _load_expected_answer(artifact_paths["expected_answer"])

    forbidden_actions = tuple(
        sorted(
            _string_list(
                document["forbidden_actions"],
                f"case {case_id!r} forbidden_actions",
                allow_empty=False,
            )
        )
    )
    provenance = _validate_fields( # 这个 Case 从哪来、有没有合法来源
        document["provenance"], PROVENANCE_FIELDS, "case manifest provenance"
    )
    source_type = _non_empty_string(
        provenance["source_type"], f"case {case_id!r} provenance source_type"
    )
    if source_type not in SOURCE_TYPES:
        raise EvaluationSuiteError(
            f"case {case_id!r} has unsupported provenance source_type {source_type!r}"
        )
    source_note = _non_empty_string(
        provenance["source_url_or_construction_note"],
        f"case {case_id!r} provenance source_url_or_construction_note",
    )
    permission = _non_empty_string(
        provenance["license_or_permission"],
        f"case {case_id!r} provenance license_or_permission",
    )
    if source_type == "constructed" and permission != "project_constructed":
        raise EvaluationSuiteError(
            f"constructed case {case_id!r} must use license_or_permission "
            "'project_constructed'"
        )
    normalized_provenance = {
        "source_type": source_type,
        "source_url_or_construction_note": source_note,
        "license_or_permission": permission,
    }
    curation = _validate_fields( # 是不是人工审核过
        document["curation"], CURATION_FIELDS, "case manifest curation"
    )
    created_by = _non_empty_string(curation["created_by"], "case curation created_by")
    reviewed_by = _non_empty_string(
        curation["reviewed_by"], "case curation reviewed_by"
    )
    if curation["review_status"] != "human_reviewed":
        raise EvaluationSuiteError(
            "case curation review_status must be 'human_reviewed'"
        )
    normalized_curation = {
        "created_by": created_by,
        "review_status": "human_reviewed",
        "reviewed_by": reviewed_by,
    }
    physical_sources = {normalized_paths["raw_log"]} | {
        f"{normalized_paths['repository_root']}/{member}"
        for member in repository_members
    }
    normalized_sanitization = _load_sanitization( # 有没有对原始 artifact 做脱敏/清洗，以及这些修改是否声明为 semantics_preserving
        document["sanitization"], physical_sources=physical_sources
    )

    declared_case_fingerprint = _declared_fingerprint( # 先读 case package manifest 里冻结时写下来的 fingerprint
        document["case_fingerprint"], f"case {case_id!r} case_fingerprint"
    )
    normalized_manifest = {
        "case_schema_version": "2",
        "case_id": case_id,
        "artifacts": normalized_paths,
        "forbidden_actions": list(forbidden_actions),
        "provenance": normalized_provenance,
        "curation": normalized_curation,
        "sanitization": normalized_sanitization,
    }
    # Case 指纹对规范化 JSON 做 SHA-256，而不是直接拼接各 JSON 文件原文。
    # raw.log 使用实际 bytes 的长度/hash；repo 使用刚校验过的成员路径/大小/hash
    # 与来源 revision；Canonical units 使用坐标和已核对的 span hash。两份 evaluator
    # 文件使用解析后的字段（集合语义列表已排序），不把 JSON 排版当成实验身份。
    # provenance/curation/sanitization 是受校验的声明，hash 不证明声明本身真实，
    # 也不证明人工 Ground Truth 在语义上正确。包目录中任意额外文件并非都进入摘要。
    fingerprint_input = {
        "fingerprint_schema": "devagentops.case-fingerprint.v2",
        "manifest": normalized_manifest,
        "physical_artifacts": {
            "raw_log": {
                "path": normalized_paths["raw_log"],
                "size_bytes": len(raw_log),
                "sha256": _sha256(raw_log),
            },
            "repository_manifest": repository_snapshot.fingerprint_input(),
        },
        "canonical_evidence": {
            "log_units": [unit.fingerprint_input() for unit in log_units],
            "repository_units": [
                unit.fingerprint_input() for unit in repository_units
            ],
        },
        "evaluator": {
            "required_evidence": evidence_ground_truth.fingerprint_input(),
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
        raw_log_path=normalized_paths["raw_log"],
        repository_root=normalized_paths["repository_root"],
        forbidden_actions=forbidden_actions,
        repository_snapshot=repository_snapshot,
        canonical_evidence_units=tuple(
            sorted(canonical_units, key=lambda unit: unit.evidence_id)
        ),
        evidence_ids=all_evidence_ids,
        evidence_ground_truth=evidence_ground_truth,
        expected_answer=expected_answer,
        fingerprint_input=fingerprint_input,
    )


def load_case_package(manifest_path: Path) -> OfflineCasePackage:
    """正式加载并比对 Case 声明指纹；失败时不给下游返回可执行的 Case。

    将 EvaluationSuiteError 的公开消息收敛为通用包错误，避免 CLI 在报错时
    泄露 evaluator 内容；原始诊断仍保留在异常文本和异常链，供可信调用方排查。"""
    try:
        return _load_case_package(manifest_path, verify_fingerprint=True)
    except EvaluationSuiteError as exc:
        code = (
            exc.code
            if exc.code
            in {"invalid_case_manifest", "unsupported_case_schema_version"}
            else "invalid_case_manifest"
        )
        public_message = (
            "unsupported Offline Case Schema version"
            if code == "unsupported_case_schema_version"
            else "invalid Offline Case package"
        )
        raise EvaluationSuiteError(
            str(exc), code=code, public_message=public_message
        ) from exc


def calculate_case_fingerprint(manifest_path: Path) -> str:
    """计算待冻结 Case 的实际指纹，不写文件、不自动修复声明值。

    只关闭最终 Case 指纹相等性检查；声明格式、成员 hash、Canonical span
    和 Ground Truth 等检查仍生效，不能用它绕过损坏数据的验证。"""
    return _load_case_package(
        manifest_path,
        verify_fingerprint=False,
    ).case_fingerprint


def _load_evaluation_suite(
    manifest_path: Path,
    *,
    verify_fingerprint: bool,
) -> EvaluationSuite:
    """加载有序 Case 清单并组合其已验证身份；Suite schema v1 与 Case v2 独立。

    每个条目核对 Case ID、相对路径及正且相等的权重，逐个调用正式 Case loader。
    Suite 指纹包含规范化 manifest 和按清单顺序排列的 Case 指纹；故 Case 变更、
    条目顺序/权重变更都会改变 Suite 身份。这里不强制正式 triage Suite 的 20 Case 配额。"""
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
    """重算 Suite 指纹但仍验证所有 Case 的声明指纹；不写入任何 manifest。"""
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
