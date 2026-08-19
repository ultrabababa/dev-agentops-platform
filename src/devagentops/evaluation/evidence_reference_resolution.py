from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Protocol


EVIDENCE_REFERENCE_RESOLUTION_VERSION = "canonical-line-range-normalization-v1"
_LINE_RANGE_ID = re.compile(
    r"^(?P<prefix>.+):lines-(?P<start>[0-9]+)-(?P<end>[0-9]+)$"
)


class CanonicalEvidenceCoordinate(Protocol):
    evidence_id: str
    start_line: int
    end_line: int


def canonicalize_evidence_references(
    raw_report: Any,
    canonical_coordinates: Iterable[CanonicalEvidenceCoordinate],
) -> Any:
    """Normalize model-authored line-range references into canonical Evidence IDs.

    Only ``evidence_references`` is touched. Exact canonical IDs are preserved.
    A non-canonical ``...:lines-START-END`` reference is expanded to every
    existing canonical ID with the same prefix whose line range overlaps the
    requested range. References that cannot be resolved deterministically are
    preserved for the normal report validator to reject. Duplicate Evidence IDs
    are removed while preserving first occurrence order.
    """

    if not isinstance(raw_report, dict):
        return raw_report

    raw_references = raw_report.get("evidence_references")
    if not isinstance(raw_references, list):
        return raw_report

    coordinates = tuple(canonical_coordinates)
    exact_ids = {coordinate.evidence_id for coordinate in coordinates}
    parsed_coordinates: list[tuple[str, int, int, str]] = []
    for coordinate in coordinates:
        match = _LINE_RANGE_ID.fullmatch(coordinate.evidence_id)
        if match is None:
            continue
        parsed_coordinates.append(
            (
                match.group("prefix"),
                coordinate.start_line,
                coordinate.end_line,
                coordinate.evidence_id,
            )
        )
    parsed_coordinates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    resolved_references: list[Any] = []
    seen_ids: set[str] = set()

    for raw_reference in raw_references:
        if not isinstance(raw_reference, dict):
            resolved_references.append(raw_reference)
            continue

        raw_evidence_id = raw_reference.get("evidence_id")
        if not isinstance(raw_evidence_id, str) or not raw_evidence_id:
            resolved_references.append(raw_reference)
            continue

        if raw_evidence_id in exact_ids:
            replacement_ids = (raw_evidence_id,)
        else:
            match = _LINE_RANGE_ID.fullmatch(raw_evidence_id)
            replacement_ids: tuple[str, ...] = ()
            if match is not None:
                start_line = int(match.group("start"))
                end_line = int(match.group("end"))
                if 0 < start_line <= end_line:
                    prefix = match.group("prefix")
                    replacement_ids = tuple(
                        evidence_id
                        for coordinate_prefix, coordinate_start, coordinate_end, evidence_id
                        in parsed_coordinates
                        if coordinate_prefix == prefix
                        and coordinate_start <= end_line
                        and start_line <= coordinate_end
                    )

            if not replacement_ids:
                replacement_ids = (raw_evidence_id,)

        for evidence_id in replacement_ids:
            if evidence_id in seen_ids:
                continue
            seen_ids.add(evidence_id)
            resolved_references.append(
                {**raw_reference, "evidence_id": evidence_id}
            )

    if resolved_references == raw_references:
        return raw_report

    return {
        **raw_report,
        "evidence_references": resolved_references,
    }
