from __future__ import annotations

from dataclasses import dataclass

from devagentops.conditions.l1.development_output_contract import (
    CANONICALIZING_OUTPUT_CONTRACT_VERSION,
    OUTPUT_CONTRACT_VERSION,
    evidence_reference_resolution_enabled,
    output_contract_identity,
)
from devagentops.evaluation.evidence_reference_resolution import (
    EVIDENCE_REFERENCE_RESOLUTION_VERSION,
    canonicalize_evidence_references,
)


@dataclass(frozen=True)
class _Coordinate:
    evidence_id: str
    start_line: int
    end_line: int


def _coordinates() -> tuple[_Coordinate, ...]:
    return (
        _Coordinate("repo:foo-java:lines-0001-0100", 1, 100),
        _Coordinate("repo:foo-java:lines-0101-0200", 101, 200),
        _Coordinate("repo:foo-java:lines-0201-0300", 201, 300),
        _Coordinate("repo:bar-java:lines-0001-0100", 1, 100),
    )


def test_exact_canonical_id_is_preserved() -> None:
    report = {
        "summary": "unchanged",
        "evidence_references": [
            {"evidence_id": "repo:foo-java:lines-0101-0200"}
        ],
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved is report


def test_crossing_range_expands_to_every_overlapping_canonical_id() -> None:
    report = {
        "summary": "unchanged",
        "evidence_references": [
            {"evidence_id": "repo:foo-java:lines-0080-0250"}
        ],
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved["summary"] == "unchanged"
    assert resolved["evidence_references"] == [
        {"evidence_id": "repo:foo-java:lines-0001-0100"},
        {"evidence_id": "repo:foo-java:lines-0101-0200"},
        {"evidence_id": "repo:foo-java:lines-0201-0300"},
    ]


def test_range_101_to_200_resolves_to_101_to_200_unit() -> None:
    report = {
        "evidence_references": [
            {"evidence_id": "repo:foo-java:lines-101-200"}
        ]
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved["evidence_references"] == [
        {"evidence_id": "repo:foo-java:lines-0101-0200"}
    ]


def test_resolution_deduplicates_while_preserving_first_occurrence() -> None:
    report = {
        "evidence_references": [
            {"evidence_id": "repo:foo-java:lines-0001-0200"},
            {"evidence_id": "repo:foo-java:lines-0101-0200"},
            {"evidence_id": "repo:bar-java:lines-0001-0100"},
        ]
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved["evidence_references"] == [
        {"evidence_id": "repo:foo-java:lines-0001-0100"},
        {"evidence_id": "repo:foo-java:lines-0101-0200"},
        {"evidence_id": "repo:bar-java:lines-0001-0100"},
    ]


def test_unresolvable_reference_is_preserved_for_normal_validation() -> None:
    report = {
        "evidence_references": [
            {"evidence_id": "repo:not-real:lines-0001-0100"}
        ]
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved is report


def test_only_evidence_references_are_changed() -> None:
    report = {
        "case_id": "case-1",
        "failure_type": "test_assertion_failure",
        "extra_field": "validator should still see this",
        "evidence_references": [
            {
                "evidence_id": "repo:foo-java:lines-0050-0150",
                "extra_reference_field": "also preserved",
            }
        ],
    }

    resolved = canonicalize_evidence_references(report, _coordinates())

    assert resolved["case_id"] == report["case_id"]
    assert resolved["failure_type"] == report["failure_type"]
    assert resolved["extra_field"] == report["extra_field"]
    assert resolved["evidence_references"] == [
        {
            "evidence_id": "repo:foo-java:lines-0001-0100",
            "extra_reference_field": "also preserved",
        },
        {
            "evidence_id": "repo:foo-java:lines-0101-0200",
            "extra_reference_field": "also preserved",
        },
    ]


def test_output_contract_v2_explicitly_identifies_resolution_behavior() -> None:
    assert evidence_reference_resolution_enabled(OUTPUT_CONTRACT_VERSION) is False
    assert (
        evidence_reference_resolution_enabled(CANONICALIZING_OUTPUT_CONTRACT_VERSION)
        is True
    )
    assert output_contract_identity(CANONICALIZING_OUTPUT_CONTRACT_VERSION)[
        "evidence_reference_resolution"
    ] == EVIDENCE_REFERENCE_RESOLUTION_VERSION
