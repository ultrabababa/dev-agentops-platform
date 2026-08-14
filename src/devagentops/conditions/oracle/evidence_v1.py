from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from devagentops.evaluation.suite import (
    CanonicalEvidenceUnit,
    OfflineCasePackage,
)


ORACLE_EVIDENCE_PACK_VERSION = "oracle_evidence_pack_v1"

# Intentionally answer-neutral and condition-neutral because this value is
# model-visible. The model should receive selected source evidence without
# being told that the selection came from an Oracle / Required-Evidence path.
ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION = "selected_evidence_runtime_input_v1"

ORACLE_EVIDENCE_DELIVERY_ID = "oracle_required_evidence_delivery"
ORACLE_EVIDENCE_DELIVERY_VERSION = "1"


class OracleEvidenceError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OracleEvidenceItem:
    evidence_id: str
    source: str
    start_line: int
    end_line: int
    content_sha256: str
    content: str

    def model_visible_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "span": {
                "type": "line_range",
                "start_line": self.start_line,
                "end_line": self.end_line,
            },
            "content_sha256": self.content_sha256,
            "content": self.content,
        }


@dataclass(frozen=True)
class OracleEvidencePack:
    pack_version: str
    case_id: str
    case_schema_version: str
    case_fingerprint: str
    forbidden_actions: tuple[str, ...]
    items: tuple[OracleEvidenceItem, ...]

    def model_visible_document(self) -> dict[str, Any]:
        return {
            "runtime_input_serialization_version": (
                ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION
            ),
            "case": {
                "case_id": self.case_id,
                "case_schema_version": self.case_schema_version,
                "case_fingerprint": self.case_fingerprint,
                "forbidden_actions": list(self.forbidden_actions),
            },
            "evidence_items": [
                item.model_visible_dict()
                for item in self.items
            ],
        }


@dataclass(frozen=True)
class OracleRuntimeInputSerialization:
    version: str
    text: str
    sha256: str
    byte_count: int


def oracle_evidence_delivery_contract() -> dict[str, str]:
    """
    Return the behavior-affecting Oracle evidence-delivery identity.

    This object is evaluator/runtime metadata. It is intended to enter the
    future Matrix-v2 Treatment identity and Run Manifest, not the model-visible
    runtime input.
    """
    return {
        "id": ORACLE_EVIDENCE_DELIVERY_ID,
        "version": ORACLE_EVIDENCE_DELIVERY_VERSION,
        "pack_version": ORACLE_EVIDENCE_PACK_VERSION,
        "runtime_input_serialization_version": (
            ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION
        ),
        "selection": "required_evidence_ids_as_set",
        "ordering": "canonical_source_start_end_evidence_id",
        "source_resolution": "canonical_line_range_exact_bytes_v1",
        "integrity": "sha256_verified",
    }


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


ORACLE_EVIDENCE_DELIVERY_FINGERPRINT = _canonical_sha256(
    oracle_evidence_delivery_contract()
)


def resolve_oracle_evidence_pack(
    package: OfflineCasePackage,
) -> OracleEvidencePack:
    """
    Resolve the Human-reviewed Required Evidence set into exact frozen source
    spans.

    Required Evidence IDs are treated as a set. Their evaluator-file ordering
    is not propagated into the model-visible Oracle input.
    """
    if package.case_schema_version != "2":
        raise OracleEvidenceError(
            "Oracle Evidence requires Offline Case Schema V2",
            code="unsupported_oracle_case_schema",
        )

    required_ids = set(
        package.evidence_ground_truth.required_evidence_ids
    )
    if not required_ids:
        raise OracleEvidenceError(
            "Oracle Evidence requires at least one Required Evidence ID",
            code="oracle_required_evidence_empty",
        )

    canonical_by_id = {
        unit.evidence_id: unit
        for unit in package.canonical_evidence_units
    }

    missing = required_ids - set(canonical_by_id)
    if missing:
        raise OracleEvidenceError(
            "Oracle Evidence Ground Truth references an unavailable "
            f"Canonical Evidence ID: {sorted(missing)[0]}",
            code="oracle_required_evidence_missing",
        )

    # Answer-neutral deterministic ordering. This deliberately does not use the
    # order in evaluator/required-evidence.json.
    selected_units = sorted(
        (
            canonical_by_id[evidence_id]
            for evidence_id in required_ids
        ),
        key=lambda unit: (
            unit.source,
            unit.start_line,
            unit.end_line,
            unit.evidence_id,
        ),
    )

    items = tuple(
        _resolve_oracle_evidence_item(
            package,
            unit,
        )
        for unit in selected_units
    )

    return OracleEvidencePack(
        pack_version=ORACLE_EVIDENCE_PACK_VERSION,
        case_id=package.case_id,
        case_schema_version=package.case_schema_version,
        case_fingerprint=package.case_fingerprint,
        forbidden_actions=package.forbidden_actions,
        items=items,
    )


def serialize_oracle_evidence_pack(
    pack: OracleEvidencePack,
) -> OracleRuntimeInputSerialization:
    """
    Serialize only the allowlisted model-visible Oracle data.

    Evaluator-only selection metadata, Expected Answer, optional-evidence
    labels, curator reasoning, and Oracle identity are intentionally absent.
    """
    if pack.pack_version != ORACLE_EVIDENCE_PACK_VERSION:
        raise OracleEvidenceError(
            f"unsupported Oracle Evidence Pack version {pack.pack_version!r}",
            code="unsupported_oracle_pack_version",
        )

    text = json.dumps(
        pack.model_visible_document(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    encoded = text.encode("utf-8")

    return OracleRuntimeInputSerialization(
        version=ORACLE_RUNTIME_INPUT_SERIALIZATION_VERSION,
        text=text,
        sha256=hashlib.sha256(encoded).hexdigest(),
        byte_count=len(encoded),
    )


def _resolve_oracle_evidence_item(
    package: OfflineCasePackage,
    unit: CanonicalEvidenceUnit,
) -> OracleEvidenceItem:
    _validate_selected_physical_source(package, unit)

    if (
        unit.start_line < 1
        or unit.end_line < unit.start_line
    ):
        raise OracleEvidenceError(
            f"Oracle source span is invalid for Evidence ID "
            f"{unit.evidence_id!r}",
            code="oracle_source_span_invalid",
        )

    source_bytes = _read_controlled_source(
        package.manifest_path.parent,
        unit.source,
    )
    lines = _line_ranges(
        source_bytes,
        unit.source,
    )

    if unit.end_line > len(lines):
        raise OracleEvidenceError(
            f"Oracle source span exceeds EOF for Evidence ID "
            f"{unit.evidence_id!r}",
            code="oracle_source_span_out_of_bounds",
        )

    resolved = b"".join(
        lines[unit.start_line - 1 : unit.end_line]
    )
    actual_sha256 = hashlib.sha256(resolved).hexdigest()

    if actual_sha256 != unit.content_sha256:
        raise OracleEvidenceError(
            f"Oracle source content hash mismatch for Evidence ID "
            f"{unit.evidence_id!r}",
            code="oracle_evidence_hash_mismatch",
        )

    try:
        content = resolved.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OracleEvidenceError(
            f"Oracle Evidence source is not valid UTF-8 for Evidence ID "
            f"{unit.evidence_id!r}",
            code="oracle_source_not_utf8",
        ) from exc

    return OracleEvidenceItem(
        evidence_id=unit.evidence_id,
        source=unit.source,
        start_line=unit.start_line,
        end_line=unit.end_line,
        content_sha256=unit.content_sha256,
        content=content,
    )


def _validate_selected_physical_source(
    package: OfflineCasePackage,
    unit: CanonicalEvidenceUnit,
) -> None:
    """
    Enforce the Trusted Builder allowlist independently of Case loading.

    Oracle-visible content may come only from the frozen raw log or a
    manifest-declared repository member. Evaluator artifacts and other
    package-local files are never valid Oracle Evidence sources.
    """
    if unit.source == package.raw_log_path:
        if not unit.evidence_id.startswith("log:"):
            raise OracleEvidenceError(
                f"Oracle log source has incompatible Evidence ID "
                f"{unit.evidence_id!r}",
                code="oracle_evidence_source_kind_mismatch",
            )
        return

    repository_prefix = f"{package.repository_root}/"
    repository_members = {
        item.path
        for item in package.repository_snapshot.files
    }

    if unit.source.startswith(repository_prefix):
        member = unit.source[len(repository_prefix) :]
        if (
            member in repository_members
            and unit.evidence_id.startswith("repo:")
        ):
            return

        if member in repository_members:
            raise OracleEvidenceError(
                f"Oracle repository source has incompatible Evidence ID "
                f"{unit.evidence_id!r}",
                code="oracle_evidence_source_kind_mismatch",
            )

    raise OracleEvidenceError(
        f"Oracle Evidence source is outside the frozen Physical Evidence "
        f"Universe for Evidence ID {unit.evidence_id!r}: {unit.source!r}",
        code="oracle_source_not_physical_artifact",
    )


def _read_controlled_source(
    package_root: Path,
    source: str,
) -> bytes:
    if "\\" in source:
        raise OracleEvidenceError(
            f"Oracle Evidence source must use POSIX separators: {source!r}",
            code="oracle_source_path_invalid",
        )

    relative = PurePosixPath(source)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() in {"", "."}
    ):
        raise OracleEvidenceError(
            f"Oracle Evidence source is not a controlled relative path: "
            f"{source!r}",
            code="oracle_source_path_invalid",
        )

    root = package_root.resolve()
    candidate = package_root.joinpath(*relative.parts)

    # Do not permit a source to escape the frozen package through a symlink.
    path_chain = [
        package_root.joinpath(*relative.parts[:index])
        for index in range(1, len(relative.parts) + 1)
    ]
    if any(path.is_symlink() for path in path_chain):
        raise OracleEvidenceError(
            f"Oracle Evidence source must not use symlinks: {source!r}",
            code="oracle_source_symlink",
        )

    resolved = candidate.resolve()
    if (
        not resolved.is_relative_to(root)
        or not resolved.is_file()
    ):
        raise OracleEvidenceError(
            f"Oracle Evidence source is unavailable: {source!r}",
            code="oracle_source_unavailable",
        )

    try:
        return resolved.read_bytes()
    except OSError as exc:
        raise OracleEvidenceError(
            f"Oracle Evidence source cannot be read: {source!r}",
            code="oracle_source_unavailable",
        ) from exc


def _line_ranges(
    content: bytes,
    source: str,
) -> list[bytes]:
    """
    Preserve the exact Canonical Evidence line semantics:

    - UTF-8 source
    - LF terminator remains part of its line
    - CRLF therefore remains exact bytes
    - final non-LF line remains present
    """
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OracleEvidenceError(
            f"Oracle Evidence source is not valid UTF-8: {source!r}",
            code="oracle_source_not_utf8",
        ) from exc

    lines: list[bytes] = []
    start = 0

    for index, byte in enumerate(content):
        if byte == 0x0A:
            lines.append(content[start : index + 1])
            start = index + 1

    if start < len(content):
        lines.append(content[start:])

    return lines
