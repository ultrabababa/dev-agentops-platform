from __future__ import annotations

import hashlib
import json
from pathlib import Path

from devagentops.conditions.l1.full_context_v1 import (
    STRUCTURED_TRIAGE_REPORT_JSON_SCHEMA,
)


OUTPUT_CONTRACT_ID = "structured-triage-report-json-clarification"
OUTPUT_CONTRACT_VERSION = "development-v1"
OUTPUT_CONTRACT_ASSET_SHA256 = (
    "621391d3d9a93997165105df4a1942b3cbc91e8a50f85bc1766225d5efdf1405"
)
OUTPUT_CONTRACT_ASSET_PATH = (
    Path(__file__).parents[2] / "assets" / "minimax_m3_output_clarification_v1.txt"
)


def output_contract_prompt_suffix() -> str:
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
