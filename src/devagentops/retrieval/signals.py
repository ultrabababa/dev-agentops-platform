from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from devagentops.retrieval.types import RetrievalChunk, RetrievalPool, RetrievalQuery


LOG_SIGNAL_FAMILIES = (
    "failed_test_identifier",
    "exception_or_error",
    "diagnostic",
    "error_or_failure_message",
    "code_reference",
)
REPOSITORY_SIGNAL_FAMILIES = (
    "path_or_filename",
    "symbol",
    "test_identifier",
    "exception_or_error",
    "diagnostic_message",
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_LEADING_TIMESTAMP = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+|\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+"
)
_LEADING_MARKERS = re.compile(
    r"^(?:(?:\[[A-Z][A-Z0-9 _-]*\]|[EFW]>?|>)\s+)+"
)
_PATH = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z0-9_.-]+[/\\])+"
    r"[A-Za-z0-9_.$-]+(?:\.[A-Za-z0-9]+)?(?:[:(][0-9]+(?::[0-9]+)?\)?)?"
)
_FILE_LINE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z0-9_.-]+\.)"
    r"(?:py|java|js|jsx|ts|tsx|c|cc|cpp|h|hpp|go|rs|rb|php|xml|ya?ml|toml|gradle|cfg|ini)"
    r":[0-9]+(?::[0-9]+)?",
    re.IGNORECASE,
)
_TEST_IDENTIFIER = re.compile(
    r"(?:[A-Za-z0-9_./\\-]+::(?:[A-Za-z0-9_.$-]+::)*[A-Za-z0-9_.$-]+"
    r"|\btest_[A-Za-z0-9_]+\b"
    r"|\b[A-Za-z_$][A-Za-z0-9_$]*(?:Test|Tests)(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?\b)"
)
_ERROR_TYPE = re.compile(
    r"\b(?:[A-Za-z_$][A-Za-z0-9_$.]*)(?:Exception|Error)\b"
    r"(?:\s*:\s*[^\n]{1,240})?"
)
_STACK_SYMBOL = re.compile(
    r"\bat\s+([A-Za-z_$][A-Za-z0-9_$.]*\.[A-Za-z_$][A-Za-z0-9_$]*)\s*\("
)
_CALL_SYMBOL = re.compile(
    r"\b([A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+)\s*\("
)
_DIAGNOSTIC_MARKER = re.compile(
    r"(?:\bassert(?:ion)?\b|\berror\s*:|\bwarning\s*:|\bfatal\s*:|"
    r"\btype(?:check| check| error)\b|\blint(?:er|ing)?\b|\bcompiler\b|"
    r"\bexpected\b.+\b(?:actual|found|got)\b)",
    re.IGNORECASE,
)
_FAILURE_MARKER = re.compile(
    r"(?:\bERROR\b|\bFAIL(?:ED|URE)?\b|\bFATAL\b|^E\s+)",
    re.IGNORECASE,
)
_FAILED_TEST_CONTEXT = re.compile(
    r"(?:\bFAILED\b|\bFAILURE\b|\bERROR\b|<<<\s*(?:FAILURE|ERROR)\b|"
    r"(?:^|\s)[FE](?:\s|$|\[))",
    re.IGNORECASE,
)
_GENERIC_FAILURES = {
    "error",
    "failed",
    "failure",
    "build failed",
    "test failed",
    "tests failed",
    "compilation failed",
}


@dataclass(frozen=True)
class _Candidate:
    family: str
    normalized_text: str
    source_path: str
    start_line: int
    end_line: int
    specificity: int


def normalize_signal_text(text: str) -> str:
    normalized = _ANSI_ESCAPE.sub("", text).strip()
    normalized = _LEADING_TIMESTAMP.sub("", normalized)
    normalized = _LEADING_MARKERS.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" :-\t")
    return normalized.casefold()


def extract_log_queries(
    text: str,
    *,
    source_path: str,
    start_line: int = 1,
    per_signal_type_cap: int = 5,
) -> tuple[RetrievalQuery, ...]:
    candidates: list[_Candidate] = []
    for offset, line in enumerate(text.splitlines(), start=start_line):
        normalized_line = normalize_signal_text(line)
        if not normalized_line:
            continue
        if _FAILED_TEST_CONTEXT.search(line):
            for match in _TEST_IDENTIFIER.finditer(line):
                _add(
                    candidates,
                    "failed_test_identifier",
                    match.group(0),
                    source_path,
                    offset,
                    2,
                )
        for match in _ERROR_TYPE.finditer(line):
            _add(candidates, "exception_or_error", match.group(0), source_path, offset, 2)
        if _DIAGNOSTIC_MARKER.search(line):
            _add(candidates, "diagnostic", normalized_line, source_path, offset, 2)
        if _FAILURE_MARKER.search(line):
            specificity = 0 if normalized_line in _GENERIC_FAILURES else 1
            _add(
                candidates,
                "error_or_failure_message",
                normalized_line,
                source_path,
                offset,
                specificity,
            )
        for value in _code_references(line):
            _add(candidates, "code_reference", value, source_path, offset, 2)
    return _select_queries(
        candidates,
        pool="log",
        family_order=LOG_SIGNAL_FAMILIES,
        cap=per_signal_type_cap,
    )


def extract_repository_queries(
    selected_log_chunks: tuple[RetrievalChunk, ...],
    *,
    per_signal_type_cap: int = 5,
) -> tuple[RetrievalQuery, ...]:
    candidates: list[_Candidate] = []
    for chunk in sorted(
        selected_log_chunks,
        key=lambda item: (item.source_path, item.start_line, item.end_line, item.chunk_id),
    ):
        for offset, line in enumerate(
            chunk.content.splitlines(), start=chunk.start_line
        ):
            normalized_line = normalize_signal_text(line)
            if not normalized_line:
                continue
            for match in (*_PATH.finditer(line), *_FILE_LINE.finditer(line)):
                _add(
                    candidates,
                    "path_or_filename",
                    _path_without_line(match.group(0)),
                    chunk.source_path,
                    offset,
                    2,
                )
            for match in _TEST_IDENTIFIER.finditer(line):
                _add(candidates, "test_identifier", match.group(0), chunk.source_path, offset, 2)
            for match in _ERROR_TYPE.finditer(line):
                _add(candidates, "exception_or_error", match.group(0), chunk.source_path, offset, 2)
            for value in _symbols(line):
                _add(candidates, "symbol", value, chunk.source_path, offset, 2)
            if _DIAGNOSTIC_MARKER.search(line) or _FAILURE_MARKER.search(line):
                specificity = 0 if normalized_line in _GENERIC_FAILURES else 1
                _add(
                    candidates,
                    "diagnostic_message",
                    normalized_line,
                    chunk.source_path,
                    offset,
                    specificity,
                )
    return _select_queries(
        candidates,
        pool="repository",
        family_order=REPOSITORY_SIGNAL_FAMILIES,
        cap=per_signal_type_cap,
    )


def _add(
    candidates: list[_Candidate],
    family: str,
    text: str,
    source_path: str,
    line: int,
    specificity: int,
) -> None:
    normalized = normalize_signal_text(text)
    if normalized:
        candidates.append(
            _Candidate(family, normalized, source_path, line, line, specificity)
        )


def _select_queries(
    candidates: list[_Candidate],
    *,
    pool: RetrievalPool,
    family_order: tuple[str, ...],
    cap: int,
) -> tuple[RetrievalQuery, ...]:
    if cap < 1:
        raise ValueError("per-signal-family cap must be positive")
    latest_by_identity: dict[tuple[str, str], _Candidate] = {}
    for candidate in candidates:
        key = (candidate.family, candidate.normalized_text)
        current = latest_by_identity.get(key)
        if current is None or (
            candidate.start_line,
            candidate.source_path,
        ) >= (
            current.start_line,
            current.source_path,
        ):
            latest_by_identity[key] = candidate

    selected: list[RetrievalQuery] = []
    for family in family_order:
        family_candidates = sorted(
            (
                item for item in latest_by_identity.values()
                if item.family == family
            ),
            key=lambda item: (
                -item.specificity,
                -item.start_line,
                item.source_path,
                item.normalized_text,
            ),
        )[:cap]
        for item in family_candidates:
            identity = json.dumps(
                {
                    "version": "failure_signal_query_v1",
                    "pool": pool,
                    "family": item.family,
                    "text": item.normalized_text,
                    "source_path": item.source_path,
                    "start_line": item.start_line,
                    "end_line": item.end_line,
                },
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            selected.append(
                RetrievalQuery(
                    query_id=f"retrieval-query-v1:{hashlib.sha256(identity).hexdigest()}",
                    pool=pool,
                    signal_family=item.family,
                    normalized_text=item.normalized_text,
                    source_path=item.source_path,
                    start_line=item.start_line,
                    end_line=item.end_line,
                    specificity=item.specificity,
                )
            )
    return tuple(selected)


def _path_without_line(value: str) -> str:
    return re.sub(r"[:(][0-9]+(?::[0-9]+)?\)?$", "", value)


def _code_references(line: str) -> tuple[str, ...]:
    values = [match.group(0) for match in _PATH.finditer(line)]
    values.extend(match.group(0) for match in _FILE_LINE.finditer(line))
    values.extend(_symbols(line))
    return tuple(values)


def _symbols(line: str) -> tuple[str, ...]:
    values = [match.group(1) for match in _STACK_SYMBOL.finditer(line)]
    values.extend(match.group(1) for match in _CALL_SYMBOL.finditer(line))
    return tuple(values)
