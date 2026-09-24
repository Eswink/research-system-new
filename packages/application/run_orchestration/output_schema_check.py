"""合约声明的 `output_schema` → `SCHEMA_VALID` 的校验回调（GOAL-014 EC-02 / F-11 四维之一）。

为什么落在这一层：`packages/domain/acceptance.py` 把 JSON Schema 校验定义为一个**注入**的
回调（域不读文件、不引依赖），并在那里写明分工——「application 层使用 jsonschema」。
本模块就是那次分工的落实：按**合约自己声明的** `output_schema` 名，从仓内 `schemas/`
读 schema，给出一个 `SchemaCheck`。

三条口径（与 PLAN-20260924-160 的 D-2 / D-3 同文）：

- **同一张名字表**：`schemas/<output_schema>.schema.json` 的拼法是门禁与契约加载器既有的
  约定（`schemas/` 目录 + `.schema.json` 后缀），本模块**不新造第二张映射表**；
- **缺名 / 缺文件 / 读坏 ⇒ `None`**：`SCHEMA_VALID` 于是维持既有的 fail-closed 判词
  `schema validator unavailable`——没有校验器**不等于**这项通过；
- **同名只读一次**（进程内缓存），与 `protocol_authoring` 的 schema 缓存同形。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]

from packages.domain.acceptance import SchemaCheck

_SCHEMA_SUFFIX = ".schema.json"
_DOCUMENT_CACHE: dict[str, dict[str, Any] | None] = {}


def output_schema_check_for(output_schema: str | None) -> SchemaCheck | None:
    """`output_schema` 名 → 校验回调；未声明 / 文件不在 / 不可解析 ⇒ `None`（fail-closed）。"""
    document = _schema_document(output_schema)
    if document is None:
        return None
    return _checker(document)


def _checker(document: dict[str, Any]) -> SchemaCheck:
    """把一份 schema 文档包成回调：通过返回 `None`，否则给出**逐条**的违约说明。"""
    validator = jsonschema.Draft202012Validator(document)

    def check(payload: object) -> str | None:
        errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
        if not errors:
            return None
        return "; ".join(f"{list(error.path)}: {error.message}" for error in errors)

    return check


def _schema_document(output_schema: str | None) -> dict[str, Any] | None:
    name = (output_schema or "").strip()
    if not name:
        return None
    if name not in _DOCUMENT_CACHE:
        _DOCUMENT_CACHE[name] = _read_document(name)
    return _DOCUMENT_CACHE[name]


def _read_document(name: str) -> dict[str, Any] | None:
    path = _schemas_dir() / f"{name}{_SCHEMA_SUFFIX}"
    if not path.is_file():
        return None
    try:
        parsed: Any = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _schemas_dir() -> Path:
    """仓内 `schemas/` 目录；按**标记文件**向上找根，不假定本文件与根的相对深度。"""
    current = Path(__file__).resolve().parent
    while not (current / "pyproject.toml").is_file():
        if current.parent == current:
            return current / "schemas"
        current = current.parent
    return current / "schemas"


__all__ = ["output_schema_check_for"]
