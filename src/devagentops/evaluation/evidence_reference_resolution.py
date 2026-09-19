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
    """在启用对应 Output Contract 时，将模型行范围引用转换为冻结 Canonical IDs。

    只处理 evidence_references：精确 ID 保留；可解析的非精确 ID 按相同前缀及
    行范围重叠展开，并按首次出现去重。无法解析的引用保留给 report validator 判错，
    不是猜测答案或丢弃错误引用。输入只有完整坐标集合，不读取 Required/Optional 标签。
    不原地改写原始报告；有变化才返回替换引用列表的新字典，便于保留模型原始输出。"""

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
