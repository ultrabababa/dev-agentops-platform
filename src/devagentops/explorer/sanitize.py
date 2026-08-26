from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "thinking",
        "reasoning_content",
        "reasoning_details",
        "reasoning",
        "encrypted_content",
        "continuation_state",
        "provider_state",
        "provider_fields",
        "response_id",
        "provider_request_id",
    }
)

_CREDENTIAL_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "access_token",
        "refresh_token",
        "client_secret",
        "password",
        "passwd",
        "private_key",
        "secret",
        "token",
        "cookie",
        "set_cookie",
    }
)
_CREDENTIAL_PATTERNS = (
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)"
        r"\s*[:=]\s*[^\s,;]{8,}"
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class SanitizationError(RuntimeError):
    """A public snapshot could not be safely and completely produced."""


@dataclass(frozen=True)
class ValidationReport:
    database: str
    trajectory_rows: int
    trace_rows: int
    forbidden_key_count: int = 0
    credential_match_count: int = 0


@dataclass(frozen=True)
class SanitizationReport:
    source: str
    destination: str
    retained_run_ids: tuple[str, ...]
    trajectory_rows_sanitized: int
    trace_rows_sanitized: int
    validation: ValidationReport


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _readonly_connection(path: Path) -> sqlite3.Connection:
    resolved = path.resolve(strict=True)
    connection = sqlite3.connect(
        f"file:{quote(str(resolved), safe='/')}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _normalized_key(key: str) -> str:
    return key.casefold().replace("-", "_").replace(" ", "_")


def _looks_like_credential(value: str) -> bool:
    return any(pattern.search(value) for pattern in _CREDENTIAL_PATTERNS)


def _redact_credential_text(value: str) -> str:
    redacted = value
    for pattern in _CREDENTIAL_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sanitize_public_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                continue
            key = _normalized_key(raw_key)
            if key in FORBIDDEN_PUBLIC_KEYS or key in _CREDENTIAL_KEYS:
                continue
            sanitized[raw_key] = _sanitize_public_value(child)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_public_value(item) for item in value]
    if isinstance(value, str):
        return _redact_credential_text(value)
    return value


def _safe_content(value: Any) -> Any:
    if isinstance(value, (str, type(None))):
        return _sanitize_public_value(value)
    if not isinstance(value, list):
        return None
    blocks: list[Any] = []
    for block in value:
        if isinstance(block, str):
            blocks.append(_sanitize_public_value(block))
            continue
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type in {"thinking", "reasoning"}:
            continue
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str):
                blocks.append({"type": "text", "text": _sanitize_public_value(text)})
        elif block_type in {"tool_call", "function_call"}:
            safe: dict[str, Any] = {"type": block_type}
            for key in ("id", "name"):
                if isinstance(block.get(key), str):
                    safe[key] = block[key]
            if "arguments" in block:
                safe["arguments"] = _sanitize_public_value(block["arguments"])
            blocks.append(safe)
    return blocks


def _safe_tool_calls(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    calls: list[dict[str, Any]] = []
    for call in value:
        if not isinstance(call, dict):
            continue
        safe: dict[str, Any] = {}
        for key in ("id", "name", "type"):
            if isinstance(call.get(key), str):
                safe[key] = call[key]
        function = call.get("function")
        if isinstance(function, dict):
            safe_function: dict[str, Any] = {}
            if isinstance(function.get("name"), str):
                safe_function["name"] = function["name"]
            if "arguments" in function:
                safe_function["arguments"] = _sanitize_public_value(
                    function["arguments"]
                )
            safe["function"] = safe_function
        if "arguments" in call:
            safe["arguments"] = _sanitize_public_value(call["arguments"])
        calls.append(safe)
    return calls


def sanitize_trajectory_message(message: Any) -> dict[str, Any]:
    """Return a role-specific, explicit public allowlist for one message."""
    if not isinstance(message, dict):
        raise SanitizationError("trajectory message JSON must be an object")
    role = message.get("role")
    if role not in {"user", "assistant", "tool_result"}:
        raise SanitizationError("trajectory message has an unsupported role")

    safe: dict[str, Any] = {"role": role}
    if "content" in message:
        content = _safe_content(message["content"])
        if content is not None:
            safe["content"] = content

    if role == "assistant":
        tool_calls = _safe_tool_calls(message.get("tool_calls"))
        if tool_calls is not None:
            safe["tool_calls"] = tool_calls
        for key in ("stop_reason", "raw_stop_reason", "response_model"):
            value = message.get(key)
            if value is None or isinstance(value, str):
                if key in message:
                    safe[key] = value
        usage = message.get("usage")
        if isinstance(usage, dict):
            safe["usage"] = {
                key: usage[key]
                for key in ("input_tokens", "output_tokens", "total_tokens")
                if usage.get(key) is None
                or (isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool))
            }
    elif role == "tool_result":
        for key in ("tool_call_id", "tool_name"):
            if isinstance(message.get(key), str):
                safe[key] = message[key]
        if isinstance(message.get("is_error"), bool):
            safe["is_error"] = message["is_error"]
    return safe


def sanitize_trace_payload(payload: Any) -> Any:
    """Remove provider-private state and credential material from Trace JSON."""
    return _sanitize_public_value(payload)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def _load_json(raw: str, *, table: str, identity: str) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SanitizationError(f"invalid JSON in {table} row {identity}") from exc


def _sanitize_json_tables(connection: sqlite3.Connection) -> tuple[int, int]:
    trajectory_count = 0
    if _table_exists(connection, "evaluation_sample_trajectory_messages"):
        rows = connection.execute(
            "SELECT run_id,case_id,repeat_index,message_index,message_role,message_json "
            "FROM evaluation_sample_trajectory_messages "
            "ORDER BY run_id,case_id,repeat_index,message_index"
        ).fetchall()
        for row in rows:
            identity = (
                f"{row['run_id']}/{row['case_id']}/"
                f"{row['repeat_index']}/{row['message_index']}"
            )
            message = _load_json(
                row["message_json"],
                table="evaluation_sample_trajectory_messages",
                identity=identity,
            )
            if isinstance(message, dict) and message.get("role") != row["message_role"]:
                raise SanitizationError(
                    "trajectory role mismatch in "
                    f"evaluation_sample_trajectory_messages row {identity}"
                )
            safe = sanitize_trajectory_message(message)
            connection.execute(
                "UPDATE evaluation_sample_trajectory_messages "
                "SET message_json=?,message_sha256=? "
                "WHERE run_id=? AND case_id=? AND repeat_index=? AND message_index=?",
                (
                    _canonical_json(safe),
                    _canonical_sha256(safe),
                    row["run_id"],
                    row["case_id"],
                    row["repeat_index"],
                    row["message_index"],
                ),
            )
            trajectory_count += 1

    trace_count = 0
    if _table_exists(connection, "evaluation_trace_events"):
        rows = connection.execute(
            "SELECT run_id,sequence,payload_json FROM evaluation_trace_events "
            "ORDER BY run_id,sequence"
        ).fetchall()
        for row in rows:
            identity = f"{row['run_id']}/{row['sequence']}"
            payload = _load_json(
                row["payload_json"],
                table="evaluation_trace_events",
                identity=identity,
            )
            safe = sanitize_trace_payload(payload)
            connection.execute(
                "UPDATE evaluation_trace_events SET payload_json=? "
                "WHERE run_id=? AND sequence=?",
                (_canonical_json(safe), row["run_id"], row["sequence"]),
            )
            trace_count += 1
    return trajectory_count, trace_count


def _sanitize_public_text_records(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "evaluation_run_manifests"):
        rows = connection.execute(
            "SELECT rowid,manifest_json FROM evaluation_run_manifests ORDER BY rowid"
        ).fetchall()
        for row in rows:
            manifest = _load_json(
                row["manifest_json"],
                table="evaluation_run_manifests",
                identity=str(row["rowid"]),
            )
            safe_manifest = _sanitize_public_value(manifest)
            connection.execute(
                "UPDATE evaluation_run_manifests "
                "SET manifest_json=?,manifest_sha256=? WHERE rowid=?",
                (
                    _canonical_json(safe_manifest),
                    _canonical_sha256(safe_manifest),
                    row["rowid"],
                ),
            )

    report_tables = (
        "evaluation_reports",
        "evaluation_sample_reports",
    )
    for table in report_tables:
        if not _table_exists(connection, table):
            continue
        rows = connection.execute(
            f"SELECT rowid,report_json,validation_json FROM {table} ORDER BY rowid"
        ).fetchall()
        for row in rows:
            report = _load_json(
                row["report_json"], table=table, identity=str(row["rowid"])
            )
            validation = _load_json(
                row["validation_json"], table=table, identity=str(row["rowid"])
            )
            safe_report = _sanitize_public_value(report)
            safe_validation = _sanitize_public_value(validation)
            connection.execute(
                f"UPDATE {table} SET report_json=?,validation_json=?,report_sha256=? "
                "WHERE rowid=?",
                (
                    _canonical_json(safe_report),
                    _canonical_json(safe_validation),
                    _canonical_sha256(safe_report),
                    row["rowid"],
                ),
            )

    for table in (
        "evaluation_runs",
        "evaluation_case_outcomes",
        "evaluation_sample_outcomes",
    ):
        if not _table_exists(connection, table):
            continue
        columns = {
            str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if "failure_message" not in columns:
            continue
        rows = connection.execute(
            f"SELECT rowid,failure_message FROM {table} WHERE failure_message IS NOT NULL"
        ).fetchall()
        for row in rows:
            redacted = _redact_credential_text(str(row["failure_message"]))
            if redacted != row["failure_message"]:
                connection.execute(
                    f"UPDATE {table} SET failure_message=? WHERE rowid=?",
                    (redacted, row["rowid"]),
                )


def _walk_public_json(value: Any) -> Iterable[tuple[str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk_public_json(child)
    elif isinstance(value, list):
        for child in value:
            yield None, child
            yield from _walk_public_json(child)


def validate_public_database(database: Path | str) -> ValidationReport:
    """Validate public JSON and text fields without exposing their values."""
    path = Path(database)
    forbidden: list[tuple[str, str, str]] = []
    credentials: list[tuple[str, str, str]] = []
    counts = {"evaluation_sample_trajectory_messages": 0, "evaluation_trace_events": 0}
    with _readonly_connection(path) as connection:
        specs = (
            (
                "evaluation_sample_trajectory_messages",
                "message_json",
                "run_id || '/' || case_id || '/' || repeat_index || '/' || message_index",
            ),
            ("evaluation_trace_events", "payload_json", "run_id || '/' || sequence"),
        )
        for table, column, identity_sql in specs:
            if not _table_exists(connection, table):
                continue
            rows = connection.execute(
                f"SELECT {identity_sql} AS identity,{column} AS document FROM {table}"
            ).fetchall()
            counts[table] = len(rows)
            for row in rows:
                document = _load_json(row["document"], table=table, identity=row["identity"])
                for key, value in _walk_public_json(document):
                    normalized = _normalized_key(key) if key is not None else None
                    if normalized in FORBIDDEN_PUBLIC_KEYS:
                        forbidden.append((table, row["identity"], str(key)))
                    if normalized in _CREDENTIAL_KEYS:
                        credentials.append((table, row["identity"], str(key)))
                    if isinstance(value, str) and _looks_like_credential(value):
                        credentials.append((table, row["identity"], key or "<array>"))

        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for table_row in tables:
            table = str(table_row[0])
            quoted_table = '"' + table.replace('"', '""') + '"'
            columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
            for column_row in columns:
                column = str(column_row[1])
                declared_type = str(column_row[2]).upper()
                if not any(token in declared_type for token in ("TEXT", "CHAR", "CLOB")):
                    continue
                quoted_column = '"' + column.replace('"', '""') + '"'
                rows = connection.execute(
                    f"SELECT rowid,{quoted_column} FROM {quoted_table} "
                    f"WHERE {quoted_column} IS NOT NULL"
                ).fetchall()
                for row in rows:
                    value = row[1]
                    if not isinstance(value, str):
                        continue
                    values_to_scan: list[str] = [value]
                    if column.endswith("_json"):
                        try:
                            parsed = json.loads(value)
                        except json.JSONDecodeError:
                            parsed = None
                        if parsed is not None:
                            walked = list(_walk_public_json(parsed))
                            if (table, column) not in {
                                (
                                    "evaluation_sample_trajectory_messages",
                                    "message_json",
                                ),
                                ("evaluation_trace_events", "payload_json"),
                            }:
                                for key, _ in walked:
                                    normalized = (
                                        _normalized_key(key) if key is not None else None
                                    )
                                    if normalized in FORBIDDEN_PUBLIC_KEYS:
                                        forbidden.append((table, str(row[0]), str(key)))
                                    if normalized in _CREDENTIAL_KEYS:
                                        credentials.append((table, str(row[0]), str(key)))
                            values_to_scan = (
                                [parsed] if isinstance(parsed, str) else []
                            ) + [
                                child for _, child in walked if isinstance(child, str)
                            ]
                    if any(_looks_like_credential(item) for item in values_to_scan):
                        credentials.append((table, str(row[0]), column))

    report = ValidationReport(
        database=str(path.resolve(strict=False)),
        trajectory_rows=counts["evaluation_sample_trajectory_messages"],
        trace_rows=counts["evaluation_trace_events"],
        forbidden_key_count=len(forbidden),
        credential_match_count=len(credentials),
    )
    if forbidden or credentials:
        details = [
            f"{table} row {identity} key {key}"
            for table, identity, key in (*forbidden, *credentials)
        ]
        raise SanitizationError(
            "public leakage validation failed "
            f"(forbidden_keys={len(forbidden)}, credential_matches={len(credentials)}): "
            + "; ".join(details)
        )
    return report


def sanitize_database(
    source: Path | str,
    destination: Path | str,
    *,
    run_ids: Iterable[str] | None = None,
) -> SanitizationReport:
    """Create and validate a deterministic public SQLite snapshot."""
    try:
        source_path = Path(source).resolve(strict=True)
    except OSError as exc:
        raise SanitizationError(f"source database is unavailable: {source}") from exc
    destination_path = Path(destination).resolve(strict=False)
    if destination_path.exists():
        raise FileExistsError(f"destination already exists: {destination_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    requested = None if run_ids is None else tuple(dict.fromkeys(run_ids))

    source_connection: sqlite3.Connection | None = None
    destination_connection: sqlite3.Connection | None = None
    try:
        source_connection = _readonly_connection(source_path)
        destination_connection = sqlite3.connect(destination_path)
        destination_connection.row_factory = sqlite3.Row
        source_connection.backup(destination_connection)
        destination_connection.execute("PRAGMA foreign_keys=ON")

        if not _table_exists(destination_connection, "evaluation_runs"):
            raise SanitizationError("source database has no evaluation_runs table")
        available = {
            str(row[0])
            for row in destination_connection.execute("SELECT run_id FROM evaluation_runs")
        }
        if requested is not None:
            unknown = sorted(set(requested) - available)
            if unknown:
                raise SanitizationError(f"requested Run ID is absent from source: {unknown[0]}")
            if requested:
                placeholders = ",".join("?" for _ in requested)
                destination_connection.execute(
                    f"DELETE FROM evaluation_runs WHERE run_id NOT IN ({placeholders})",
                    requested,
                )
            else:
                destination_connection.execute("DELETE FROM evaluation_runs")

        _sanitize_public_text_records(destination_connection)
        trajectory_count, trace_count = _sanitize_json_tables(destination_connection)
        violations = destination_connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise SanitizationError(
                f"destination foreign-key validation failed (count={len(violations)})"
            )
        destination_connection.commit()
        destination_connection.execute("PRAGMA journal_mode=DELETE")
        destination_connection.execute("VACUUM")
        retained = tuple(
            str(row[0])
            for row in destination_connection.execute(
                "SELECT run_id FROM evaluation_runs ORDER BY run_id"
            )
        )
        destination_connection.close()
        destination_connection = None
        validation = validate_public_database(destination_path)
        return SanitizationReport(
            source=str(source_path),
            destination=str(destination_path),
            retained_run_ids=retained,
            trajectory_rows_sanitized=trajectory_count,
            trace_rows_sanitized=trace_count,
            validation=validation,
        )
    except (sqlite3.Error, OSError) as exc:
        raise SanitizationError(f"failed to sanitize SQLite database: {exc}") from exc
    finally:
        if destination_connection is not None:
            destination_connection.close()
        if source_connection is not None:
            source_connection.close()
        if sys.exc_info()[0] is not None and destination_path.exists():
            destination_path.unlink()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a deterministic public-safe evaluation SQLite snapshot."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--run-id", action="append", dest="run_ids")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = sanitize_database(args.source, args.destination, run_ids=args.run_ids)
    except (FileExistsError, SanitizationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
