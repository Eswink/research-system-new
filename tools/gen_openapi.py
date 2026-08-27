"""导出 Control Plane OpenAPI schema（docs/api/openapi.m13.json）。

用途：前端以 OpenAPI 为类型单一真相源（生成 TS types），CI 经
tests/contracts/test_openapi_snapshot.py 校验 schema 未漂移。

确定性：Pydantic 生成的 object schema 默认允许额外属性，validators 要求
显式 `additionalProperties: false`（契约资产约束），故导出时统一补写，
保证生成结果确定（sort_keys + 固定格式）。
运行：uv run --frozen --no-sync python -B tools/gen_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.api.app import create_app

_TARGET = Path(__file__).resolve().parents[1] / "docs" / "api" / "openapi.m13.json"


def _finalize(schema: dict[str, object]) -> dict[str, object]:
    """统一补写 additionalProperties: false（object schema 显式闭包，含嵌套 inline）。"""
    components = schema.get("components")
    if not isinstance(components, dict):
        return schema
    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        return schema
    for body in schemas.values():
        if not isinstance(body, dict):
            continue
        _close_object_schemas(body)
    return schema


def _close_object_schemas(node: object) -> None:
    """递归为 object schema 补写/改写 additionalProperties: false。"""
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
        for value in node.values():
            _close_object_schemas(value)
    elif isinstance(node, list):
        for item in node:
            _close_object_schemas(item)


def main() -> int:
    app = create_app()
    schema = _finalize(app.openapi())
    schema["$id"] = "https://research-os.local/schemas/openapi.m13.json"
    _TARGET.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {_TARGET} ({len(json.dumps(schema))} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
