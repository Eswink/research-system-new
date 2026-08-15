"""M11 EvalScore 报告纯序列化（无 I/O、无 schema 校验、无 adapter 依赖）。

文件写入与 JSON Schema 校验在 adapters/contracts/eval_report_io.py
（依赖方向 adapter → application → domain）。
"""

from __future__ import annotations

import json

from packages.domain.eval_report_codec import report_from_dict, report_to_dict
from packages.domain.eval_result import EvalReport
from packages.domain.serialization import canonical_json_bytes


def report_to_canonical_bytes(report: EvalReport) -> bytes:
    """canonical JSON 字节（UTF-8、无多余空白）。"""

    return canonical_json_bytes(report_to_dict(report))


def report_from_json_text(text: str) -> EvalReport:
    """从 JSON 文本重建报告；JSON 解析失败抛 ValueError（fail-closed）。"""

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"report is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("report must be a JSON object")
    return report_from_dict(payload)
