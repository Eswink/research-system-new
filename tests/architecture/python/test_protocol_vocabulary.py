"""协议词表同源的结构判据（EC-01 AC-01）。

三处声明必须给出**同一集合**：域枚举 `LLMProtocol`、契约 JSON schema 的 enum、
API DTO 的 `Literal`；执行侧（relay adapter 与 OpenHands llm_factory）**不得**再出现
协议字面量——选路必须走枚举，否则「配了某协议」与「跑的是某形态」会脱钩。

判据用 AST 取字符串常量做**精确相等**比较（不是子串匹配）：`ANTHROPIC_VERSION`
这类常量名/头名不含独立的协议取值，不应误判。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import get_args

from pydantic import BaseModel

from packages.domain.enums import LLMProtocol
from services.api.dto import endpoints as endpoints_dto

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_VALUES = frozenset(member.value for member in LLMProtocol)
EXECUTION_DIRS = (ROOT / "adapters" / "relay", ROOT / "adapters" / "openhands")


def _string_constants(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def test_contract_schema_lists_the_same_protocols() -> None:
    schema = json.loads((ROOT / "schemas" / "llm-endpoint.schema.json").read_text("utf-8"))
    declared = set(schema["properties"]["protocol"]["enum"])
    assert declared == set(PROTOCOL_VALUES)


def test_api_dto_literals_list_the_same_protocols() -> None:
    """凡是以 Literal 声明协议取值的 DTO，其集合必须与域枚举一致。

    Read DTO 的 `protocol` 是普通 `str`（回读值，不构成第二份词表），因此只判
    Literal 形态的字段；同时要求**至少存在一个**这样的字段——否则把词表整体删掉
    也能让本用例变绿。
    """
    checked = 0
    for name, candidate in vars(endpoints_dto).items():
        if not isinstance(candidate, type) or not issubclass(candidate, BaseModel):
            continue
        field = candidate.model_fields.get("protocol")
        if field is None:
            continue
        literal_values = get_args(field.annotation)
        if not literal_values:
            continue
        assert set(literal_values) == set(PROTOCOL_VALUES), name
        checked += 1
    assert checked >= 1, "no DTO declares a protocol Literal vocabulary"


def test_execution_path_uses_the_enum_not_literals() -> None:
    offenders: list[str] = []
    for directory in EXECUTION_DIRS:
        for path in sorted(directory.rglob("*.py")):
            hit = _string_constants(path) & PROTOCOL_VALUES
            if hit:
                offenders.append(f"{path.relative_to(ROOT)}: {sorted(hit)}")
    assert offenders == [], (
        "执行侧出现协议字面量（应改用 domain LLMProtocol）: " + "; ".join(offenders)
    )
