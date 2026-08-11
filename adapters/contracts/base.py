"""契约加载器公共基础设施。

基于已批准依赖 jsonschema 4.26.0 + PyYAML 6.0.3。
示例文件采用“嵌套 map + 扁平化 id”结构（与 system-spec validator 一致）：
```yaml
models:
  research_alpha:
    endpoint: main
    ...
```
加载时对每个子键构造 `{"id": <key>, ...}` 后校验对应 JSON Schema。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "schemas"


class ContractLoadError(ValueError):
    """契约加载或校验失败。"""


def load_yaml(relative_path: str) -> Any:
    """读取 YAML/JSON 文件并解析（UTF-8）。"""
    path = ROOT / relative_path
    if not path.is_file():
        raise ContractLoadError(f"file not found: {relative_path}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContractLoadError(f"invalid YAML at {relative_path}: {exc}") from exc


def load_json_schema(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / name
    if not path.is_file():
        raise ContractLoadError(f"schema not found: {name}")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractLoadError(f"invalid JSON schema {name}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ContractLoadError(f"schema {name} must be a JSON object")
    return schema


def validate_instance(schema: dict[str, Any], instance: Any, source: str) -> None:
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        rendered = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise ContractLoadError(f"contract invalid at {source}: {rendered}")


def mapping_under(data: Any, top_key: str, relative_path: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ContractLoadError(f"{relative_path} must be a mapping")
    section = data.get(top_key)
    if not isinstance(section, dict) or not section:
        raise ContractLoadError(f"{relative_path} must declare non-empty `{top_key}:` mapping")
    return section


def load_flat_collection(
    relative_path: str,
    top_key: str,
    schema_name: str,
    *,
    rename: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """加载嵌套 map，扁平化每条为 `{"id": <key>, ...}` 并逐一校验 schema。"""
    section = mapping_under(load_yaml(relative_path), top_key, relative_path)
    schema = load_json_schema(schema_name)
    result: dict[str, dict[str, Any]] = {}
    for key, body in section.items():
        if not isinstance(body, dict):
            raise ContractLoadError(f"{relative_path}/{key} must be a mapping")
        flat = {**body, "id": key}
        if rename:
            for source, target in rename.items():
                if source in flat:
                    flat[target] = flat.pop(source)
        validate_instance(schema, flat, f"{relative_path}/{key}")
        result[key] = flat
    return result
