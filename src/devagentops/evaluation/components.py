from __future__ import annotations

import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ComponentRegistryError(RuntimeError):
    pass


COMPONENT_TYPES = frozenset(
    {
        "prompt",
        "tool_registry",
        "retriever_config",
        "tool_policy",
        "mcp_server_set",
        "skill_registry",
    }
)
MATRIX_COMPONENT_TYPES = {
    "prompt": "prompt",
    "tool_registry": "tool_registry",
    "retriever": "retriever_config",
    "retriever_config": "retriever_config",
    "tool_policy": "tool_policy",
    "mcp_server_set": "mcp_server_set",
    "skill_registry": "skill_registry",
}
MANIFEST_FIELDS = {
    "schema_version",
    "component_type",
    "component_version",
    "behavior",
    "metadata",
}
REQUIRED_MANIFEST_FIELDS = MANIFEST_FIELDS - {"component_version", "metadata"}
REGISTRY_FIELDS = {"schema_version", "components"}
REGISTRY_RECORD_FIELDS = {"manifest", "fingerprint", "frozen_at", "metadata"}
VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
BEHAVIOR_REQUIRED_FIELDS = {
    "prompt": {"template"},
    "tool_registry": {"tools"},
    "retriever_config": {"strategy", "settings"},
    "tool_policy": {"rules"},
    "mcp_server_set": {"servers"},
    "skill_registry": {"skills"},
}
BEHAVIOR_ALLOWED_FIELDS = {
    "prompt": {"template", "variables"},
    "tool_registry": {"tools"},
    "retriever_config": {"strategy", "settings"},
    "tool_policy": {"rules", "default_action"},
    "mcp_server_set": {"servers"},
    "skill_registry": {"skills"},
}


@dataclass(frozen=True)
class ComponentManifest:
    schema_version: str
    component_type: str
    component_version: str | None
    behavior: dict[str, Any]
    metadata: dict[str, Any]
    path: Path

    def as_dict(self, *, component_version: str | None = None) -> dict[str, Any]:
        document = {
            "schema_version": self.schema_version,
            "component_type": self.component_type,
            "behavior": self.behavior,
            "metadata": self.metadata,
        }
        effective_version = component_version or self.component_version
        if effective_version is not None:
            document["component_version"] = effective_version
        return document

    def validation_result(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "component_type": self.component_type,
            "fingerprint": component_fingerprint(self),
        }


@dataclass(frozen=True)
class FrozenComponent:
    component_type: str
    component_version: str
    manifest: str
    fingerprint: str
    frozen_at: str
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "component_type": self.component_type,
            "component_version": self.component_version,
            "manifest": self.manifest,
            "fingerprint": self.fingerprint,
            "frozen_at": self.frozen_at,
            "metadata": self.metadata,
        }


def _read_json(path: Path, description: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ComponentRegistryError(f"{description} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ComponentRegistryError(
            f"invalid JSON in {description} {path}: {exc.msg}"
        ) from exc


def load_component_manifest(path: Path) -> ComponentManifest:
    document = _read_json(path, "component manifest")
    if not isinstance(document, dict):
        raise ComponentRegistryError("component manifest must be a JSON object")

    missing_fields = REQUIRED_MANIFEST_FIELDS - set(document)
    if missing_fields:
        field = sorted(missing_fields)[0]
        raise ComponentRegistryError(
            f"component manifest is missing required field {field!r}"
        )
    unknown_fields = set(document) - MANIFEST_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise ComponentRegistryError(
            f"component manifest has unknown field {field!r}; "
            "review-only values belong under 'metadata'"
        )
    if document["schema_version"] != "1":
        raise ComponentRegistryError(
            "unsupported component manifest schema version "
            f"{document['schema_version']!r}"
        )
    if document["component_type"] not in COMPONENT_TYPES:
        raise ComponentRegistryError(
            f"unsupported component type {document['component_type']!r}"
        )
    component_version = document.get("component_version")
    if component_version is not None and (
        not isinstance(component_version, str)
        or not VERSION_PATTERN.fullmatch(component_version)
    ):
        raise ComponentRegistryError("component manifest has invalid component version")
    if not isinstance(document["behavior"], dict):
        raise ComponentRegistryError("component manifest 'behavior' must be an object")
    _validate_behavior(document["component_type"], document["behavior"])
    metadata = document.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ComponentRegistryError("component manifest 'metadata' must be an object")

    return ComponentManifest(
        schema_version=document["schema_version"],
        component_type=document["component_type"],
        component_version=component_version,
        behavior=document["behavior"],
        metadata=metadata,
        path=path,
    )


def _validate_behavior(component_type: str, behavior: dict[str, Any]) -> None:
    missing_fields = BEHAVIOR_REQUIRED_FIELDS[component_type] - set(behavior)
    if missing_fields:
        field = sorted(missing_fields)[0]
        raise ComponentRegistryError(
            f"{component_type} behavior is missing required field {field!r}"
        )
    unknown_fields = set(behavior) - BEHAVIOR_ALLOWED_FIELDS[component_type]
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise ComponentRegistryError(
            f"{component_type} behavior has unknown field {field!r}"
        )

    if component_type == "prompt":
        if not isinstance(behavior["template"], str) or not behavior["template"]:
            raise ComponentRegistryError("prompt behavior 'template' must be a non-empty string")
        variables = behavior.get("variables", [])
        if not isinstance(variables, list) or not all(
            isinstance(variable, str) and variable for variable in variables
        ):
            raise ComponentRegistryError(
                "prompt behavior 'variables' must be a list of non-empty strings"
            )
    elif component_type == "retriever_config":
        if not isinstance(behavior["strategy"], str) or not behavior["strategy"]:
            raise ComponentRegistryError(
                "retriever_config behavior 'strategy' must be a non-empty string"
            )
        if not isinstance(behavior["settings"], dict):
            raise ComponentRegistryError(
                "retriever_config behavior 'settings' must be an object"
            )
    else:
        collection_field = {
            "tool_registry": "tools",
            "tool_policy": "rules",
            "mcp_server_set": "servers",
            "skill_registry": "skills",
        }[component_type]
        entries = behavior[collection_field]
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise ComponentRegistryError(
                f"{component_type} behavior {collection_field!r} "
                "must be a list of objects"
            )
        if component_type == "tool_policy" and "default_action" in behavior:
            if not isinstance(behavior["default_action"], str) or not behavior[
                "default_action"
            ]:
                raise ComponentRegistryError(
                    "tool_policy behavior 'default_action' must be a non-empty string"
                )


def component_fingerprint(manifest: ComponentManifest) -> str:
    canonical = json.dumps( # 把 Python 对象转换成 JSON 字符串
        manifest.behavior,
        ensure_ascii=False, # 表示不要把中文等非 ASCII 字符转成 \uXXXX
        separators=(",", ":"), # 控制 JSON 中元素之间的分隔符, 不会受无关空格影响, 更适合做哈希
        sort_keys=True, # 表示字典的 key 按固定顺序排序
    ).encode("utf-8") # 把 Python 字符串 str 转成字节 bytes, as hashlib.sha256() 要求输入的是 bytes，不是普通字符串
    return hashlib.sha256(canonical).hexdigest() # hashlib.sha256(canonical) 计算 SHA-256 哈希, .hexdigest() 把 SHA-256 结果转换成方便阅读的十六进制字符串


def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": "1",
        "components": {component_type: {} for component_type in sorted(COMPONENT_TYPES)},
    }


def _load_registry(path: Path, *, allow_missing: bool = False) -> dict[str, Any]:
    if allow_missing and not path.exists():
        return _empty_registry()
    document = _read_json(path, "component registry")
    if not isinstance(document, dict):
        raise ComponentRegistryError("component registry must be a JSON object")
    missing_fields = REGISTRY_FIELDS - set(document)
    if missing_fields:
        field = sorted(missing_fields)[0]
        raise ComponentRegistryError(
            f"component registry is missing required field {field!r}"
        )
    unknown_fields = set(document) - REGISTRY_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise ComponentRegistryError(
            f"component registry has unknown field {field!r}"
        )
    if document["schema_version"] != "1":
        raise ComponentRegistryError(
            f"unsupported component registry schema version {document['schema_version']!r}"
        )
    if not isinstance(document["components"], dict):
        raise ComponentRegistryError("component registry 'components' must be an object")
    unknown_types = set(document["components"]) - COMPONENT_TYPES
    if unknown_types:
        component_type = sorted(unknown_types)[0]
        raise ComponentRegistryError(
            f"component registry has unsupported component type {component_type!r}"
        )
    for component_type, versions in document["components"].items():
        if not isinstance(versions, dict):
            raise ComponentRegistryError(
                f"component registry group {component_type!r} must be an object"
            )
    for component_type in COMPONENT_TYPES: # 如果某一种合法 component type 在 JSON 里完全没出现，就自动补成 "某种类型": {}
        document["components"].setdefault(component_type, {})
    return document


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(
                json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            )
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _record_as_frozen_component(
    component_type: str,
    component_version: str,
    record: dict[str, Any],
) -> FrozenComponent:
    return FrozenComponent(
        component_type=component_type,
        component_version=component_version,
        manifest=record["manifest"],
        fingerprint=record["fingerprint"],
        frozen_at=record["frozen_at"],
        metadata=record.get("metadata", {}),
    )


def _validate_record(
    registry_path: Path,
    component_type: str,
    component_version: str,
    record: Any,
) -> FrozenComponent:
    if not isinstance(record, dict):
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} must be an object"
        )
    missing_fields = (REGISTRY_RECORD_FIELDS - {"metadata"}) - set(record)
    if missing_fields:
        field = sorted(missing_fields)[0]
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} "
            f"is missing required field {field!r}"
        )
    unknown_fields = set(record) - REGISTRY_RECORD_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} "
            f"has unknown field {field!r}"
        )
    if not isinstance(record["manifest"], str) or not record["manifest"]:
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} has invalid manifest path"
        )
    if not isinstance(record["fingerprint"], str) or not FINGERPRINT_PATTERN.fullmatch(
        record["fingerprint"]
    ):
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} has invalid fingerprint"
        )
    if not isinstance(record["frozen_at"], str) or not record["frozen_at"]:
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} has invalid frozen_at"
        )
    if not isinstance(record.get("metadata", {}), dict):
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} has invalid metadata"
        )

    registry_root = registry_path.parent.resolve() # registry.json 所在目录的绝对路径
    manifest_path = (registry_path.parent / record["manifest"]).resolve() # Registry 里 manifest 字段指向的那个具体 manifest 文件的绝对路径
    if not manifest_path.is_relative_to(registry_root): # 检查manifest_path 最终解析出来以后，是否仍然位于 Registry 所在目录之下
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} points outside the registry"
        )
    manifest = load_component_manifest(manifest_path)
    if manifest.component_type != component_type:
        raise ComponentRegistryError(
            f"registry record for {component_type}:{component_version} points to "
            f"a {manifest.component_type!r} manifest"
        )
    if manifest.component_version != component_version:
        raise ComponentRegistryError(
            f"component version pollution detected for {component_type}:{component_version}: "
            f"frozen manifest declares version {manifest.component_version!r}"
        )
    actual_fingerprint = component_fingerprint(manifest)
    if actual_fingerprint != record["fingerprint"]:
        raise ComponentRegistryError(
            f"component version pollution detected for {component_type}:{component_version}: "
            f"registered fingerprint {record['fingerprint']} differs from "
            f"manifest fingerprint {actual_fingerprint}"
        )
    return _record_as_frozen_component(component_type, component_version, record)


def freeze_component(
    manifest_path: Path,
    registry_path: Path,
    component_version: str,
) -> FrozenComponent:
    if not VERSION_PATTERN.fullmatch(component_version):
        raise ComponentRegistryError(
            "component version must start with an alphanumeric character and contain only "
            "letters, digits, '.', '_', or '-'"
        )
    if _is_draft_version(component_version):
        raise ComponentRegistryError("a frozen component version cannot be named 'draft'")

    manifest = load_component_manifest(manifest_path)
    if (
        manifest.component_version is not None
        and not _is_draft_version(manifest.component_version)
        and manifest.component_version != component_version
    ):
        raise ComponentRegistryError(
            f"component manifest declares version {manifest.component_version!r}, "
            f"not requested version {component_version!r}"
        )
    fingerprint = component_fingerprint(manifest)
    registry = _load_registry(registry_path, allow_missing=True)
    versions = registry["components"][manifest.component_type]
    existing = versions.get(component_version)
    if existing is not None:
        frozen = _validate_record(
            registry_path,
            manifest.component_type,
            component_version,
            existing,
        )
        if frozen.fingerprint != fingerprint:
            raise ComponentRegistryError(
                f"component version {manifest.component_type}:{component_version} is immutable; "
                "freeze changed behavior under a new version"
            )
        return frozen

    frozen_relative_path = Path("frozen") / manifest.component_type / f"{component_version}.json"
    frozen_path = registry_path.parent / frozen_relative_path
    frozen_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    record = {
        "manifest": frozen_relative_path.as_posix(),
        "fingerprint": fingerprint,
        "frozen_at": frozen_at,
        "metadata": manifest.metadata,
    }
    frozen_was_created = False
    if frozen_path.exists():
        orphaned_manifest = load_component_manifest(frozen_path)
        if (
            orphaned_manifest.component_type != manifest.component_type
            or orphaned_manifest.component_version != component_version
            or component_fingerprint(orphaned_manifest) != fingerprint
        ):
            raise ComponentRegistryError(
                f"unregistered frozen manifest conflicts with requested freeze: {frozen_path}"
            )
    else:
        try:
            _write_json(
                frozen_path,
                manifest.as_dict(component_version=component_version),
            )
            frozen_was_created = True
        except OSError as exc:
            raise ComponentRegistryError(
                f"could not write frozen component manifest {frozen_path}: {exc}"
            ) from exc
    versions[component_version] = record
    try:
        _write_json(registry_path, registry)
    except OSError as exc:
        if frozen_was_created:
            frozen_path.unlink(missing_ok=True)
        raise ComponentRegistryError(
            f"could not write component registry {registry_path}: {exc}"
        ) from exc
    return _record_as_frozen_component(
        manifest.component_type,
        component_version,
        record,
    )


def _is_draft_version(component_version: str) -> bool:
    normalized = component_version.casefold()
    return (
        normalized == "draft"
        or normalized.startswith(("draft-", "draft_", "draft."))
        or normalized.endswith(("-draft", "_draft", ".draft"))
    )


def validate_component_references(
    components: Any,
    registry_path: Path,
    *,
    condition_id: str,
) -> dict[str, str]:
    if not isinstance(components, dict):
        raise ComponentRegistryError(
            f"condition {condition_id!r} components must be an object"
        )
    registry = _load_registry(registry_path)
    fingerprints: dict[str, str] = {} # Matrix 里引用的 component → Registry 中实际验证出来的 fingerprint
    matrix_keys_by_type: dict[str, str] = {} # 防止同一个 component type 被两个不同别名重复声明
    for matrix_key, component_version in components.items():
        component_type = MATRIX_COMPONENT_TYPES.get(matrix_key) # Matrix 里的名字和 Registry 里的正式 component type 不一定完全相同, 比如 retriever -> retriever_config
        if component_type is None:
            raise ComponentRegistryError(
                f"condition {condition_id!r} references unsupported component "
                f"{matrix_key!r}"
            )
        previous_key = matrix_keys_by_type.get(component_type)
        if previous_key is not None: # 用来保证一个 condition 对同一种 component type 只能声明一次，不能通过两个不同 alias 重复引用。比如retriever、retriever_config在同一个condition里面不能同时存在
            raise ComponentRegistryError(
                f"condition {condition_id!r} declares aliases {previous_key!r} and "
                f"{matrix_key!r} for component type {component_type!r}"
            )
        matrix_keys_by_type[component_type] = matrix_key
        if not isinstance(component_version, str) or not component_version:
            raise ComponentRegistryError(
                f"condition {condition_id!r} component {matrix_key!r} "
                "must reference a component version string"
            )
        if _is_draft_version(component_version): # Formal evaluation 不允许引用 draft 版本，只允许引用已经 frozen 的版本
            raise ComponentRegistryError(
                f"condition {condition_id!r} references draft component "
                f"{matrix_key}:{component_version}; formal evaluation requires frozen versions"
            )
        record = registry["components"][component_type].get(component_version)
        if record is None:
            raise ComponentRegistryError(
                f"condition {condition_id!r} references missing frozen component "
                f"{component_type}:{component_version}"
            )
        frozen = _validate_record( # 把“已经验证为合法、未污染的 frozen component 记录”变成一个更明确的 Python 对象
            registry_path,
            component_type,
            component_version,
            record,
        )
        fingerprints[matrix_key] = frozen.fingerprint
    return fingerprints


def resolve_frozen_component_manifest(
    registry_path: Path,
    component_type: str,
    component_version: str,
) -> ComponentManifest:
    """Resolve one already-validated frozen Registry record to its manifest."""
    registry = _load_registry(registry_path)
    if component_type not in COMPONENT_TYPES:
        raise ComponentRegistryError(
            f"unsupported component type {component_type!r}"
        )
    record = registry["components"][component_type].get(component_version)
    if record is None:
        raise ComponentRegistryError(
            f"missing frozen component {component_type}:{component_version}"
        )
    frozen = _validate_record(
        registry_path,
        component_type,
        component_version,
        record,
    )
    return load_component_manifest(registry_path.parent / frozen.manifest)
