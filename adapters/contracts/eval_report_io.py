"""M11 EvalScore 报告文件 I/O 与 schema 校验（adapter 边界）。

写：application 纯序列化 → jsonschema 校验 → UTF-8 文件。
读：UTF-8 文件 → JSON 解析 → jsonschema 校验 → domain 构造
（fail-closed）。
"""

from __future__ import annotations

import json
from pathlib import Path

from adapters.contracts.base import ContractLoadError, load_json_schema, validate_instance
from packages.application.evaluation.report import report_to_canonical_bytes
from packages.domain.eval_report_codec import report_from_dict, report_to_dict
from packages.domain.eval_result import EvalReport

_SCHEMA_NAME = "eval-score.schema.json"


def write_report(path: Path, report: EvalReport) -> None:
    """写报告文件；canonical JSON、UTF-8、schema 校验。"""

    payload = report_to_dict(report)
    validate_instance(load_json_schema(_SCHEMA_NAME), payload, str(path))
    path.write_bytes(report_to_canonical_bytes(report) + b"\n")


def read_report(path: Path) -> EvalReport:
    """读报告文件；schema 校验失败 fail-closed。"""

    try:
        data = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractLoadError(f"report not readable: {path}: {exc}") from exc
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ContractLoadError(f"report not valid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractLoadError(f"report must be a JSON object: {path}")
    validate_instance(load_json_schema(_SCHEMA_NAME), payload, str(path))
    try:
        return report_from_dict(payload)
    except ValueError as exc:
        raise ContractLoadError(f"report invalid at {path}: {exc}") from exc
