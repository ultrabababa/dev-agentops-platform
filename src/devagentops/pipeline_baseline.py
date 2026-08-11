from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from devagentops.evaluation_suite import OfflineCasePackage, PublicCaseView


PIPELINE_VERSION = "deterministic_pytest_assertion_v1"


class PipelineBaselineError(RuntimeError):
    """Raised when the bounded deterministic tracer-bullet rule cannot run."""


@dataclass(frozen=True)
class RuntimeCanonicalCoordinate:
    evidence_id: str
    source: str


@dataclass(frozen=True)
class RuntimeCaseWorkspace:
    case: PublicCaseView
    package_root: Path
    repository_members: tuple[str, ...]
    canonical_coordinates: tuple[RuntimeCanonicalCoordinate, ...]

    @classmethod
    def from_package(cls, package: OfflineCasePackage) -> RuntimeCaseWorkspace:
        return cls(
            case=package.public_view(),
            package_root=package.manifest_path.parent,
            repository_members=tuple(
                item.path for item in package.repository_snapshot.files
            ),
            canonical_coordinates=tuple(
                RuntimeCanonicalCoordinate(
                    evidence_id=unit.evidence_id,
                    source=unit.source,
                )
                for unit in package.canonical_evidence_units
            ),
        )

    def read_raw_log(self) -> str:
        return self._read_controlled_file(self.case.raw_log_path)

    def list_repository_files(self) -> tuple[str, ...]:
        return self.repository_members

    def read_repository_file(self, relative_path: str) -> str:
        if relative_path not in self.repository_members:
            raise PipelineBaselineError(
                f"repository file is outside the frozen workspace: {relative_path}"
            )
        return self._read_controlled_file(
            f"{self.case.repository_root}/{relative_path}"
        )

    def evidence_ids_for_sources(self, sources: set[str]) -> tuple[str, ...]:
        return tuple(
            sorted(
                coordinate.evidence_id
                for coordinate in self.canonical_coordinates
                if coordinate.source in sources
            )
        )

    def _read_controlled_file(self, relative_path: str) -> str:
        path = (self.package_root / relative_path).resolve()
        if not path.is_relative_to(self.package_root.resolve()) or not path.is_file():
            raise PipelineBaselineError(
                f"workspace file is unavailable: {relative_path}"
            )
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise PipelineBaselineError(
                f"workspace file cannot be read as UTF-8: {relative_path}"
            ) from exc


@dataclass(frozen=True)
class PipelineBaselineResult:
    raw_report: dict[str, object]


_TEST_PATH_PATTERN = re.compile(
    r"^(?P<path>[A-Za-z0-9_./-]+\.py)\s+F\s+\[\s*100%\s*\]$",
    re.MULTILINE,
)
_ASSERTION_PATTERN = re.compile(
    r"^E\s+assert\s+(?P<call>(?P<symbol>[A-Za-z_]\w*)\((?P<arguments>[^)]*)\))"
    r"\s*==\s*(?P<expected>[^\s]+)\s*$\n"
    r"^E\s+assert\s+(?P<actual>[^\s]+)\s*==\s*(?P=expected)\s*$",
    re.MULTILINE,
)


def run_pipeline_baseline(
    workspace: RuntimeCaseWorkspace,
) -> PipelineBaselineResult:
    raw_log = workspace.read_raw_log()
    test_match = _TEST_PATH_PATTERN.search(raw_log)
    assertion_match = _ASSERTION_PATTERN.search(raw_log)
    if test_match is None or assertion_match is None:
        raise PipelineBaselineError(
            "deterministic pytest assertion rule did not match the frozen raw log"
        )

    symbol = assertion_match.group("symbol")
    arguments = [
        value.strip()
        for value in assertion_match.group("arguments").split(",")
    ]
    if len(arguments) != 2 or not all(arguments):
        raise PipelineBaselineError(
            "deterministic pytest assertion rule requires exactly two arguments"
        )
    expected = assertion_match.group("expected")
    actual = assertion_match.group("actual")
    call = assertion_match.group("call")

    test_path = test_match.group("path")
    if test_path not in workspace.list_repository_files():
        raise PipelineBaselineError(
            "failed pytest path is not present in the frozen repository snapshot"
        )
    workspace.read_repository_file(test_path)

    definition_pattern = re.compile(
        rf"^def\s+{re.escape(symbol)}\([^)]*\):\s*$\n"
        r"\s+return\s+(?P<expression>[^\n]+)\s*$",
        re.MULTILINE,
    )
    definitions: list[tuple[str, str]] = []
    for repository_path in workspace.list_repository_files():
        content = workspace.read_repository_file(repository_path)
        match = definition_pattern.search(content)
        if match is not None:
            definitions.append((repository_path, match.group("expression").strip()))
    if len(definitions) != 1:
        raise PipelineBaselineError(
            "deterministic pytest assertion rule requires one unique symbol definition"
        )
    definition_path, expression = definitions[0]
    if expression != "left * right":
        raise PipelineBaselineError(
            "deterministic pytest assertion rule found an unsupported implementation"
        )

    sources = {
        workspace.case.raw_log_path,
        f"{workspace.case.repository_root}/{test_path}",
        f"{workspace.case.repository_root}/{definition_path}",
    }
    evidence_ids = workspace.evidence_ids_for_sources(sources)
    if not evidence_ids:
        raise PipelineBaselineError(
            "deterministic pytest assertion rule found no citable Canonical Evidence"
        )

    return PipelineBaselineResult(
        raw_report={
            "schema_version": "1",
            "case_id": workspace.case.case_id,
            "classification_status": "classified",
            "failure_type": "test_assertion_failure",
            "summary": (
                f"Pytest assertion failed: {call} produced {actual} instead of "
                f"{expected}."
            ),
            "root_cause": (
                f"{symbol} returns {expression}, so inputs {arguments[0]} and "
                f"{arguments[1]} produce {actual} while the test expects {expected}."
            ),
            "recommended_action": (
                f"Change {symbol} to return left + right, then rerun the affected test."
            ),
            "confidence": 1.0,
            "evidence_references": [
                {"evidence_id": evidence_id} for evidence_id in evidence_ids
            ],
        }
    )
