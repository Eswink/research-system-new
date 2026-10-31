"""**期刊选择**的解析与判定（GOAL-20261031-102 EC-04；闭集在 `examples/config/journals.yaml`）。

**它补哪一格**：`target journal` / `journal selection` 在产品三根 0 命中 —— 编辑决定
说「下一步怎么办」，却从不说「投去哪」。本模块给「投去哪」一个**可判的形状**：
`editorial_decision` 的决定块可以多带两个字段（`target_journal` + `selection_rationale`），
取值被**闭集**约束：

1. **选中名 ∈ 闭集**（`journals.yaml` 的 `journals[].name`）—— 闭集是**声明面**：
   不在集里不是「更差的期刊」，是「不可选」（点名集里有什么）；
2. **依据引用该刊 scope_keywords ≥ 1** —— 空依据、或引的是别的刊的关键词 ⇒ 点名；
   「匹配依据」是机械可判的那一面，**语义匹配好坏是人评**，本模块不判；
3. **两个字段同进同出**：只给一个 ⇒ 点名（半个选择没法核）。

**闭集不是评分**：`journals.yaml` 里没有影响因子、没有排名 —— 那是人评的面，本仓
不冒充（`fix_policy.forbidden`：不许把声明面说成评价面）。

**两处声明的镜像判据**：闭集在 `journals.yaml`，模型看见的集合在合约
`editorial_decision` 的 purpose 里 —— 判据逐名核对两处一致（防漂移）。

**零出网 / 零模型 / 零时钟**：输入是声明字节与决定块，输出是已校验的选择或点名异常。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

#: 期刊闭集的声明文件（仓根相对路径）。
JOURNALS_CONFIG = "examples/config/journals.yaml"
#: 决定块里的两个选择字段（**逐字**；合约与判据按它们定位）。
JOURNAL_FIELD = "target_journal"
RATIONALE_FIELD = "selection_rationale"


class JournalSelectionError(RuntimeError):
    """期刊选择不可用（越闭集 / 空依据 / 只给半个）—— **点名**，不回落。"""


@dataclass(frozen=True, slots=True)
class JournalRecord:
    """闭集里的一条声明（名字 + 占位 ISSN + scope 关键词；**没有**任何评分字段）。"""

    name: str
    issn: str
    scope_keywords: tuple[str, ...]


def load_journals(config_path: Path) -> tuple[JournalRecord, ...]:
    """闭集声明 → 逐条记录（重名 / 重 ISSN / 缺关键词 ⇒ 点名；空集 ⇒ 点名）。"""
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    entries = (payload or {}).get("journals")
    if not isinstance(entries, list) or not entries:
        raise JournalSelectionError(f"{config_path.name} declares no journals[] entries")
    records: list[JournalRecord] = []
    names: set[str] = set()
    issns: set[str] = set()
    for entry in entries:
        name = str((entry or {}).get("name") or "").strip()
        issn = str((entry or {}).get("issn") or "").strip()
        keywords = tuple(
            str(item or "").strip()
            for item in (entry or {}).get("scope_keywords") or ()
            if str(item or "").strip()
        )
        if not name or not issn or not keywords:
            raise JournalSelectionError(
                f"journal entry needs name, issn and non-empty scope_keywords: {entry!r}"
            )
        if name in names:
            raise JournalSelectionError(f"duplicate journal name in the closed set: {name!r}")
        if issn in issns:
            raise JournalSelectionError(f"duplicate issn in the closed set: {issn!r}")
        names.add(name)
        issns.add(issn)
        records.append(JournalRecord(name=name, issn=issn, scope_keywords=keywords))
    return tuple(records)


def parse_selection(block: Mapping[str, Any]) -> tuple[str, str] | None:
    """决定块 → `(期刊名, 依据)`（**两字段都没给 ⇒ `None`**；只给一个 ⇒ 点名）。"""
    journal = block.get(JOURNAL_FIELD)
    rationale = block.get(RATIONALE_FIELD)
    if journal is None and rationale is None:
        return None
    name = str(journal or "").strip()
    text = str(rationale or "").strip()
    if not name or not text:
        raise JournalSelectionError(
            f"{JOURNAL_FIELD} and {RATIONALE_FIELD} stand or fall together: a selection "
            "with only one of them cannot be checked against the closed set"
        )
    return name, text


def validate_selection(
    selection: tuple[str, str], journals: tuple[JournalRecord, ...]
) -> JournalRecord:
    """判据①②：选中名 ∈ 闭集，且依据引用该刊 scope_keywords ≥ 1（各自点名）。"""
    name, rationale = selection
    by_name = {record.name: record for record in journals}
    record = by_name.get(name)
    if record is None:
        raise JournalSelectionError(
            f"target journal {name!r} is not in the declared closed set "
            f"({sorted(by_name)}): outside the set is not a worse journal, it is not "
            "selectable"
        )
    cited = [keyword for keyword in record.scope_keywords if keyword.lower() in rationale.lower()]
    if not cited:
        raise JournalSelectionError(
            f"the selection rationale for {name!r} cites none of its scope keywords "
            f"({list(record.scope_keywords)}): a fit claim with no stated basis cannot "
            "be checked"
        )
    return record


def selection_of_decision_payload(payload: Mapping[str, Any]) -> tuple[str, str] | None:
    """决定块（含信封解开后的那份）→ 选择（块里没有选择字段 ⇒ `None`）。"""
    block = payload.get("editorial_decision")
    if not isinstance(block, Mapping):
        return None
    return parse_selection(block)


def selection_from_artifact(content: str) -> tuple[str, str] | None:
    """编辑决定**制品字节** → 选择（信封/直形态都认；不是 JSON ⇒ 点名）。"""
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise JournalSelectionError(
            f"editorial decision artifact is not valid JSON: {error}"
        ) from error
    if not isinstance(parsed, Mapping):
        raise JournalSelectionError("editorial decision artifact must be a JSON object")
    if "editorial_decision" not in parsed:
        from packages.application.run_orchestration.phase_input_material import declared_object

        try:
            parsed = declared_object(parsed, key="editorial_decision")
        except Exception as error:  # noqa: BLE001 - 解不开 ⇒ 点名
            raise JournalSelectionError(
                f"the decision artifact carries no editorial_decision block: {error}"
            ) from error
    return selection_of_decision_payload(parsed)


def contract_mirror_verdict(journals: tuple[JournalRecord, ...], contract_purpose: str) -> None:
    """镜像判据：闭集里每个名字都必须在合约 purpose 里出现（防两处声明漂移）。"""
    missing = [record.name for record in journals if record.name not in contract_purpose]
    if missing:
        raise JournalSelectionError(
            f"the journal closed set and the editorial contract purpose have drifted; "
            f"these names are missing from the contract: {missing}"
        )


__all__ = [
    "JOURNAL_FIELD",
    "JOURNALS_CONFIG",
    "RATIONALE_FIELD",
    "JournalRecord",
    "JournalSelectionError",
    "contract_mirror_verdict",
    "load_journals",
    "parse_selection",
    "selection_from_artifact",
    "selection_of_decision_payload",
    "validate_selection",
]
