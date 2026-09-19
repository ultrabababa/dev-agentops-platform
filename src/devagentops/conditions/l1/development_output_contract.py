from __future__ import annotations

import hashlib
import json
from pathlib import Path

from devagentops.conditions.l1.full_context_v1 import (
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
)
from devagentops.evaluation.evidence_reference_resolution import (
    EVIDENCE_REFERENCE_RESOLUTION_VERSION,
)


OUTPUT_CONTRACT_ID = "structured-triage-report-json-clarification"
OUTPUT_CONTRACT_VERSION = "development-v1"
CANONICALIZING_OUTPUT_CONTRACT_VERSION = "development-v2"
OUTPUT_CONTRACT_ASSET_SHA256 = (
    "621391d3d9a93997165105df4a1942b3cbc91e8a50f85bc1766225d5efdf1405"
)
OUTPUT_CONTRACT_ASSET_PATH = (
    Path(__file__).parents[2] / "assets" / "minimax_m3_output_clarification_v1.txt"
)


def output_contract_prompt_suffix() -> str:
    """读取冻结的报告格式提示并在使用前核对内容 hash。

    各 Runtime 把返回文本约束为 Structured Triage Report JSON；hash 防止本地 asset
    被静默修改后仍沿用旧 Treatment identity。这里不生成报告字段，也不修复模型输出。
    """
    content = OUTPUT_CONTRACT_ASSET_PATH.read_text(encoding="utf-8")
    actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if actual != OUTPUT_CONTRACT_ASSET_SHA256:
        raise ValueError("MiniMax development output-contract asset changed")
    return content


OUTPUT_CONTRACT_PROMPT_SHA256 = hashlib.sha256(
    output_contract_prompt_suffix().encode("utf-8")
).hexdigest()
OUTPUT_SCHEMA_SHA256 = hashlib.sha256(
    json.dumps(
        STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA["json_schema"]["schema"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


def output_contract_identity(version: str) -> dict[str, str]:
    """返回 Output Contract 身份；v2 额外声明确定性 Evidence Mapping 版本。

    v1/v2 共享同一 prompt suffix 与 Report Schema，差异仅是模型输出后是否执行
    canonical line-range normalization，便于将格式修复与模型原始诊断分开归因。
    """
    identity = {
        "id": OUTPUT_CONTRACT_ID,
        "version": version,
        "prompt_suffix_sha256": OUTPUT_CONTRACT_PROMPT_SHA256,
        "schema_version": "1",
        "schema_sha256": OUTPUT_SCHEMA_SHA256,
    }
    if version == CANONICALIZING_OUTPUT_CONTRACT_VERSION:
        identity["evidence_reference_resolution"] = (
            EVIDENCE_REFERENCE_RESOLUTION_VERSION
        )
    elif version != OUTPUT_CONTRACT_VERSION:
        raise ValueError(f"unsupported output contract version: {version}")
    return identity


def evidence_reference_resolution_enabled(version: str) -> bool:
    """把冻结 Output Contract version 精确映射为引用规范化开关。"""
    if version == CANONICALIZING_OUTPUT_CONTRACT_VERSION:
        return True
    if version == OUTPUT_CONTRACT_VERSION:
        return False
    raise ValueError(f"unsupported output contract version: {version}")
