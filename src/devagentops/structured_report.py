from __future__ import annotations

import json
import math
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from devagentops.evaluation_suite import FAILURE_TYPES


REPORT_SCHEMA_VERSION = "1"
CLASSIFICATION_STATUSES = {"classified", "inconclusive"}
MIN_RECOMMENDED_ACTION_NON_WHITESPACE_CHARS = 12
REQUIRED_FIELDS_COMPLETENESS_DENOMINATOR = 8
REPORT_FIELDS = {
    "schema_version",
    "case_id",
    "classification_status",
    "failure_type",
    "summary",
    "root_cause",
    "recommended_action",
    "confidence",
    "evidence_references",
}
EVIDENCE_REFERENCE_FIELDS = {"evidence_id"}
_MISSING = object()


class ReportInputError(RuntimeError):
    """An infrastructure error that prevents candidate report evaluation."""


def _reject_non_standard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value}")


def _json_safe_error_value(value: object) -> object:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        if value.bit_length() > 256:
            return {"type": "integer", "bit_length": value.bit_length()}
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            return str(value)
        _, digits, exponent = value.as_tuple()
        if len(digits) > 64 or abs(exponent) > 64:
            return {
                "type": "number",
                "significant_digits": len(digits),
                "exponent": exponent,
            }
        return float(value)
    if isinstance(value, list):
        return [_json_safe_error_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_safe_error_value(item) for key, item in value.items()
        }
    return type(value).__name__


@dataclass(frozen=True)
class ReportValidationError:
    code: str
    field: str
    message: str
    expected: object | None = None
    actual: object | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "code": self.code,
            "field": self.field,
            "message": self.message,
        }
        if self.expected is not None:
            result["expected"] = _json_safe_error_value(self.expected)
        if self.actual is not None:
            result["actual"] = _json_safe_error_value(self.actual)
        return result


@dataclass(frozen=True)
class ReportValidationResult:
    valid: bool
    errors: tuple[ReportValidationError, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": [error.as_dict() for error in self.errors],
        }


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str


@dataclass(frozen=True)
class StructuredTriageReport:
    schema_version: str
    case_id: str
    classification_status: str
    failure_type: str | None
    summary: str
    root_cause: str
    recommended_action: str
    confidence: float
    evidence_references: tuple[EvidenceReference, ...]


@dataclass(frozen=True)
class _CompletenessProjection:
    schema_version: bool
    case_id: bool
    classification: bool
    summary: bool
    root_cause: bool
    recommended_action: bool
    confidence: bool
    evidence_references: bool

    @property
    def filled_count(self) -> int:
        return sum(
            (
                self.schema_version,
                self.case_id,
                self.classification,
                self.summary,
                self.root_cause,
                self.recommended_action,
                self.confidence,
                self.evidence_references,
            )
        )


@dataclass(frozen=True)
class _CandidateReportProjection:
    is_object: bool
    schema_version: str | None
    case_id: str | None
    classification_status: str | None
    failure_type: str | None
    summary: str | None
    root_cause: str | None
    recommended_action: str | None
    confidence: float | None
    evidence_ids: tuple[str, ...]
    has_evidence_reference_list: bool
    case_id_matches: bool
    distinct_unknown_evidence_id_count: int
    duplicate_evidence_reference_count: int
    completeness: _CompletenessProjection


@dataclass(frozen=True)
class CandidateReportAnalysis:
    """Package-level view of candidate validation without exposing raw projection state."""

    validation: ReportValidationResult
    _projection: _CandidateReportProjection

    @property
    def case_id_matches(self) -> bool:
        return self._projection.case_id_matches

    @property
    def classification_status(self) -> str | None:
        return self._projection.classification_status

    @property
    def failure_type(self) -> str | None:
        return self._projection.failure_type

    @property
    def cited_evidence_ids(self) -> tuple[str, ...]:
        return self._projection.evidence_ids

    @property
    def has_evidence_reference_list(self) -> bool:
        return self._projection.has_evidence_reference_list

    @property
    def distinct_unknown_evidence_id_count(self) -> int:
        return self._projection.distinct_unknown_evidence_id_count

    @property
    def duplicate_evidence_reference_count(self) -> int:
        return self._projection.duplicate_evidence_reference_count

    @property
    def completeness_filled_count(self) -> int:
        return self._projection.completeness.filled_count

    def construct_structured_report(self) -> StructuredTriageReport | None:
        if not self.validation.valid:
            return None
        return _construct_valid_report(self._projection)


def load_candidate_report_json(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ReportInputError(f"report file does not exist: {path}") from exc
    except OSError as exc:
        raise ReportInputError(f"report file cannot be read: {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ReportInputError(f"report file is not valid UTF-8: {path}") from exc
    try:
        return json.loads(
            raw,
            parse_constant=_reject_non_standard_json_constant,
            parse_int=Decimal,
            parse_float=Decimal,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        message = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
        raise ReportInputError(
            f"invalid JSON in report file {path}: {message}"
        ) from exc


def _type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    return type(value).__name__


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_field(
    document: dict[str, Any],
    field: str,
    errors: list[ReportValidationError],
) -> str | None:
    value = document.get(field, _MISSING)
    if value is _MISSING:
        errors.append(
            ReportValidationError(
                code="missing_required_field",
                field=field,
                message="Required report field is missing",
            )
        )
        return None
    if not isinstance(value, str):
        errors.append(
            ReportValidationError(
                code="invalid_field_type",
                field=field,
                expected="non-empty string",
                actual=_type_name(value),
                message="Report field must be a non-empty string",
            )
        )
        return None
    if not value.strip():
        errors.append(
            ReportValidationError(
                code="empty_required_field",
                field=field,
                message="Required report field must not be empty",
            )
        )
        return None
    return value


def _validate_candidate_report(
    raw_report: Any,
    *,
    case_id: str,
    evidence_ids: tuple[str, ...],
) -> tuple[ReportValidationResult, _CandidateReportProjection]:
    if not isinstance(raw_report, dict):
        error = ReportValidationError(
            code="invalid_report_type",
            field="$",
            expected="object",
            actual=_type_name(raw_report),
            message="Structured Triage Report must be a JSON object",
        )
        empty_completeness = _CompletenessProjection(
            False, False, False, False, False, False, False, False
        )
        return (
            ReportValidationResult(valid=False, errors=(error,)),
            _CandidateReportProjection(
                is_object=False,
                schema_version=None,
                case_id=None,
                classification_status=None,
                failure_type=None,
                summary=None,
                root_cause=None,
                recommended_action=None,
                confidence=None,
                evidence_ids=(),
                has_evidence_reference_list=False,
                case_id_matches=False,
                distinct_unknown_evidence_id_count=0,
                duplicate_evidence_reference_count=0,
                completeness=empty_completeness,
            ),
        )

    document = raw_report
    errors: list[ReportValidationError] = []

    schema_version = _text_field(document, "schema_version", errors)
    if schema_version is not None and schema_version != REPORT_SCHEMA_VERSION:
        errors.append(
            ReportValidationError(
                code="unknown_schema_version",
                field="schema_version",
                expected=REPORT_SCHEMA_VERSION,
                actual=schema_version,
                message="Structured Triage Report schema version is not supported",
            )
        )

    candidate_case_id = _text_field(document, "case_id", errors)
    case_id_matches = candidate_case_id == case_id
    if candidate_case_id is not None and not case_id_matches:
        errors.append(
            ReportValidationError(
                code="case_id_mismatch",
                field="case_id",
                expected=case_id,
                actual=candidate_case_id,
                message="Report case ID does not match the evaluated case",
            )
        )

    classification_status = _text_field(
        document, "classification_status", errors
    )
    if (
        classification_status is not None
        and classification_status not in CLASSIFICATION_STATUSES
    ):
        errors.append(
            ReportValidationError(
                code="invalid_classification_status",
                field="classification_status",
                expected=sorted(CLASSIFICATION_STATUSES),
                actual=classification_status,
                message="Classification status is not supported by Schema V1",
            )
        )

    raw_failure_type = document.get("failure_type", _MISSING)
    failure_type: str | None = None
    if classification_status == "classified":
        if raw_failure_type is _MISSING:
            errors.append(
                ReportValidationError(
                    code="missing_required_field",
                    field="failure_type",
                    message="Classified reports must include failure_type",
                )
            )
        elif raw_failure_type is None:
            errors.append(
                ReportValidationError(
                    code="null_failure_type_for_classified",
                    field="failure_type",
                    actual="null",
                    message="Classified reports must include a non-null failure_type",
                )
            )
        elif not isinstance(raw_failure_type, str):
            errors.append(
                ReportValidationError(
                    code="invalid_field_type",
                    field="failure_type",
                    expected="non-empty string",
                    actual=_type_name(raw_failure_type),
                    message="Failure type must be a non-empty string",
                )
            )
        elif not raw_failure_type.strip():
            errors.append(
                ReportValidationError(
                    code="empty_required_field",
                    field="failure_type",
                    message="Classified reports must include a non-empty failure_type",
                )
            )
        else:
            failure_type = raw_failure_type
            if failure_type not in FAILURE_TYPES:
                errors.append(
                    ReportValidationError(
                        code="invalid_failure_type",
                        field="failure_type",
                        expected=sorted(FAILURE_TYPES),
                        actual=failure_type,
                        message="Failure type is not part of the V1 taxonomy",
                    )
                )
    elif classification_status == "inconclusive":
        if raw_failure_type not in (_MISSING, None):
            if isinstance(raw_failure_type, str):
                failure_type = raw_failure_type if raw_failure_type.strip() else None
            errors.append(
                ReportValidationError(
                    code="failure_type_not_allowed_for_inconclusive",
                    field="failure_type",
                    expected="null or omitted",
                    actual=raw_failure_type,
                    message="Inconclusive reports must not select a failure type",
                )
            )
    elif raw_failure_type not in (_MISSING, None):
        if isinstance(raw_failure_type, str) and raw_failure_type.strip():
            failure_type = raw_failure_type
        elif not isinstance(raw_failure_type, str):
            errors.append(
                ReportValidationError(
                    code="invalid_field_type",
                    field="failure_type",
                    expected="non-empty string or null",
                    actual=_type_name(raw_failure_type),
                    message="Failure type must be a non-empty string or null",
                )
            )

    summary = _text_field(document, "summary", errors)
    root_cause = _text_field(document, "root_cause", errors)
    recommended_action = _text_field(document, "recommended_action", errors)
    if recommended_action is not None:
        non_whitespace_chars = sum(
            1 for character in recommended_action if not character.isspace()
        )
        if non_whitespace_chars < MIN_RECOMMENDED_ACTION_NON_WHITESPACE_CHARS:
            errors.append(
                ReportValidationError(
                    code="recommended_action_too_short",
                    field="recommended_action",
                    expected={
                        "minimum_non_whitespace_characters": (
                            MIN_RECOMMENDED_ACTION_NON_WHITESPACE_CHARS
                        )
                    },
                    actual={"non_whitespace_characters": non_whitespace_chars},
                    message=(
                        "Recommended action does not meet the V1 minimum structural "
                        "specificity proxy"
                    ),
                )
            )

    raw_confidence = document.get("confidence", _MISSING)
    confidence: float | None = None
    if raw_confidence is _MISSING:
        errors.append(
            ReportValidationError(
                code="missing_required_field",
                field="confidence",
                message="Required report field is missing",
            )
        )
    elif isinstance(raw_confidence, bool) or not isinstance(
        raw_confidence, (int, float, Decimal)
    ):
        errors.append(
            ReportValidationError(
                code="invalid_field_type",
                field="confidence",
                expected="number from 0 to 1",
                actual=_type_name(raw_confidence),
                message="Confidence must be a number from 0 to 1",
            )
        )
    else:
        finite = (
            raw_confidence.is_finite()
            if isinstance(raw_confidence, Decimal)
            else not isinstance(raw_confidence, float)
            or math.isfinite(raw_confidence)
        )
        if not finite:
            errors.append(
                ReportValidationError(
                    code="non_finite_confidence",
                    field="confidence",
                    actual=raw_confidence,
                    message="Confidence must be finite",
                )
            )
        elif not 0 <= raw_confidence <= 1:
            errors.append(
                ReportValidationError(
                    code="confidence_out_of_range",
                    field="confidence",
                    expected={"minimum": 0.0, "maximum": 1.0},
                    actual=raw_confidence,
                    message="Confidence must be between 0 and 1 inclusive",
                )
            )
        else:
            try:
                confidence = float(raw_confidence)
            except OverflowError:
                errors.append(
                    ReportValidationError(
                        code="confidence_out_of_range",
                        field="confidence",
                        expected={"minimum": 0.0, "maximum": 1.0},
                        actual=raw_confidence,
                        message="Confidence must be between 0 and 1 inclusive",
                    )
                )

    raw_references = document.get("evidence_references", _MISSING)
    parsed_evidence_ids: list[str] = []
    seen_evidence_ids: set[str] = set()
    unknown_evidence_ids: set[str] = set()
    duplicate_count = 0
    has_reference_list = isinstance(raw_references, list)
    if raw_references is _MISSING:
        errors.append(
            ReportValidationError(
                code="missing_required_field",
                field="evidence_references",
                message="Required report field is missing",
            )
        )
    elif not isinstance(raw_references, list):
        errors.append(
            ReportValidationError(
                code="invalid_field_type",
                field="evidence_references",
                expected="non-empty array",
                actual=_type_name(raw_references),
                message="Evidence references must be a non-empty array",
            )
        )
    elif not raw_references:
        errors.append(
            ReportValidationError(
                code="empty_required_field",
                field="evidence_references",
                message="Evidence references must not be empty",
            )
        )
    else:
        stable_ids = set(evidence_ids)
        for index, raw_reference in enumerate(raw_references):
            reference_field = f"evidence_references[{index}]"
            if not isinstance(raw_reference, dict):
                errors.append(
                    ReportValidationError(
                        code="invalid_evidence_reference_type",
                        field=reference_field,
                        expected="object",
                        actual=_type_name(raw_reference),
                        message="Evidence Reference must be a JSON object",
                    )
                )
                continue
            raw_evidence_id = raw_reference.get("evidence_id", _MISSING)
            evidence_id: str | None = None
            if raw_evidence_id is _MISSING:
                errors.append(
                    ReportValidationError(
                        code="missing_required_field",
                        field=f"{reference_field}.evidence_id",
                        message="Evidence Reference is missing evidence_id",
                    )
                )
            elif not isinstance(raw_evidence_id, str):
                errors.append(
                    ReportValidationError(
                        code="invalid_field_type",
                        field=f"{reference_field}.evidence_id",
                        expected="non-empty string",
                        actual=_type_name(raw_evidence_id),
                        message="Evidence ID must be a non-empty string",
                    )
                )
            elif not raw_evidence_id.strip():
                errors.append(
                    ReportValidationError(
                        code="empty_required_field",
                        field=f"{reference_field}.evidence_id",
                        message="Evidence ID must not be empty",
                    )
                )
            else:
                evidence_id = raw_evidence_id
                parsed_evidence_ids.append(evidence_id)
                if evidence_id in seen_evidence_ids:
                    duplicate_count += 1
                    errors.append(
                        ReportValidationError(
                            code="duplicate_evidence_reference",
                            field=f"{reference_field}.evidence_id",
                            actual=evidence_id,
                            message="Evidence ID is cited more than once",
                        )
                    )
                else:
                    seen_evidence_ids.add(evidence_id)
                if evidence_id not in stable_ids:
                    unknown_evidence_ids.add(evidence_id)
                    errors.append(
                        ReportValidationError(
                            code="unknown_evidence_id",
                            field=f"{reference_field}.evidence_id",
                            actual=evidence_id,
                            message="Evidence ID does not exist in the evaluated case",
                        )
                    )
            for unknown_field in sorted(
                set(raw_reference) - EVIDENCE_REFERENCE_FIELDS
            ):
                errors.append(
                    ReportValidationError(
                        code="unknown_evidence_reference_field",
                        field=f"{reference_field}.{unknown_field}",
                        actual=unknown_field,
                        message="Evidence Reference contains an unknown field",
                    )
                )

    for unknown_field in sorted(set(document) - REPORT_FIELDS):
        errors.append(
            ReportValidationError(
                code="unknown_report_field",
                field=unknown_field,
                actual=unknown_field,
                message="Structured Triage Report contains an unknown field",
            )
        )

    raw_status = document.get("classification_status", _MISSING)
    raw_type = document.get("failure_type", _MISSING)
    classification_filled = _non_empty_text(raw_status) and (
        raw_status == "inconclusive" or _non_empty_text(raw_type)
    )
    completeness = _CompletenessProjection(
        schema_version=_non_empty_text(document.get("schema_version", _MISSING)),
        case_id=_non_empty_text(document.get("case_id", _MISSING)),
        classification=classification_filled,
        summary=_non_empty_text(document.get("summary", _MISSING)),
        root_cause=_non_empty_text(document.get("root_cause", _MISSING)),
        recommended_action=_non_empty_text(
            document.get("recommended_action", _MISSING)
        ),
        confidence=(
            not isinstance(raw_confidence, bool)
            and isinstance(raw_confidence, (int, float, Decimal))
        ),
        evidence_references=(
            isinstance(raw_references, list) and bool(raw_references)
        ),
    )
    projection = _CandidateReportProjection(
        is_object=True,
        schema_version=schema_version,
        case_id=candidate_case_id,
        classification_status=classification_status,
        failure_type=failure_type,
        summary=summary,
        root_cause=root_cause,
        recommended_action=recommended_action,
        confidence=confidence,
        evidence_ids=tuple(parsed_evidence_ids),
        has_evidence_reference_list=has_reference_list,
        case_id_matches=case_id_matches,
        distinct_unknown_evidence_id_count=len(unknown_evidence_ids),
        duplicate_evidence_reference_count=duplicate_count,
        completeness=completeness,
    )
    return ReportValidationResult(valid=not errors, errors=tuple(errors)), projection


def analyze_candidate_report(
    raw_report: Any,
    *,
    case_id: str,
    evidence_ids: tuple[str, ...],
) -> CandidateReportAnalysis:
    validation, projection = _validate_candidate_report(
        raw_report,
        case_id=case_id,
        evidence_ids=evidence_ids,
    )
    return CandidateReportAnalysis(validation=validation, _projection=projection)


def _construct_valid_report(
    projection: _CandidateReportProjection,
) -> StructuredTriageReport:
    # This helper is called only after validation has proven every assertion below.
    assert projection.schema_version is not None
    assert projection.case_id is not None
    assert projection.classification_status is not None
    assert projection.summary is not None
    assert projection.root_cause is not None
    assert projection.recommended_action is not None
    assert projection.confidence is not None
    return StructuredTriageReport(
        schema_version=projection.schema_version,
        case_id=projection.case_id,
        classification_status=projection.classification_status,
        failure_type=(
            None
            if projection.classification_status == "inconclusive"
            else projection.failure_type
        ),
        summary=projection.summary,
        root_cause=projection.root_cause,
        recommended_action=projection.recommended_action,
        confidence=projection.confidence,
        evidence_references=tuple(
            EvidenceReference(evidence_id=evidence_id)
            for evidence_id in projection.evidence_ids
        ),
    )
