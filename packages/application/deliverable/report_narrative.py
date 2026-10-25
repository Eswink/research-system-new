"""**由模型撰写正文**的研究报告（报告域 L1 → L2；GOAL-20261022-062）。

**它补哪一格**：`research_report.py` 的汇编器是**确定性**的 —— 同一份持久状态 ⇒ 逐字节相同，
但它写不出叙述，报告的「质量」那一面**无人判**。本模块让**模型写正文**，同时保住汇编器
唯一的硬约束：**每个数字可溯源**。

**怎么做到「数字不因模型而脱离来源」**（本模块的核心取舍）：把报告切成**两块互不越界的面**：

1. **事实表**（`## 5. 事实表（数字的唯一来源）`）—— **汇编器**从 canonical 读取并写出，
   每行带来源列（`evidence_id` / `experiment_run_id` / 读面名）。模型**不参与**这一块。
2. **叙述**（第 1…4 节）—— **模型**写的散文。它**不得出现任何数字**（拒绝一切 Unicode
   十进制数位）⇒ 读者在正文里看到的任何量，都必须去事实表取，而事实表的每一行都可复核。

这不是「让模型自觉」：`validate_narrative` 是一条**结构判据** —— 模型写了数字，任务就
**点名拒绝**（不论那个数字对不对）。**为什么不抽掉数字后照用**：静默改写模型输出会让
「报告是谁写的」变得不可判（读者以为整段都是模型说的）。

**与既有四节的关系**：四个二级标题**逐字沿用** `SECTION_HEADINGS` ⇒ 既有「四节齐全」的
判据对本形态**照样成立**；新增的只有第五节的表与抬头里的叙述作者。

**如实边界（本模块不声称的）**：

- 它**不判**叙述的**科学质量**（那需要人评或更强的判据）；它判的是「谁写的」与
  「数字在哪」两件结构事实；
- 它**不重算**任何数字：事实表的值逐字来自 `ReportInputs`（而那是四个既有读面的输出）；
- 模型对事实表内容的**任何说法**都不进报告 —— 它在正文里只能**指称**指标名 / 标识符。
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.deliverable.research_report import (
    SECTION_HEADINGS,
    ReportInputs,
)

#: 事实表的二级标题（**逐字**；判据按它定位，改字 = 改契约）。
FACT_TABLE_HEADING = "## 5. 事实表（数字的唯一来源）"

#: 叙述的四个键（与 `SECTION_HEADINGS` 一一对应；模型必须逐个给出）。
NARRATIVE_KEYS: tuple[str, ...] = ("question", "evidence", "experiment", "review")

#: 事实表的列头（**逐字**）。
FACT_TABLE_COLUMNS: tuple[str, ...] = ("类别", "名称", "值", "来源")


class NarrativeError(RuntimeError):
    """叙述不可用（畸形 / 含数字 / 缺键）—— **点名**，不静默改写也不静默丢弃。"""


@dataclass(frozen=True, slots=True)
class NarrativeAdmission:
    """一次叙述的**归因面**（谁写的 / 写了什么 / 它是不是那个模型写的）。"""

    #: 装配方声明的执行者（`model:<endpoint>/<model>` 形态；与 `Artifact.created_by` 同值）。
    author: str
    #: 供应商**返回**的模型名（与声明名可能不同 —— 同名漂移必须可见，AGENTS.md §4）。
    returned_model: str
    #: 叙述正文的 `sha256`（规范 JSON 文本）—— 报告字节之外的第二份可核对读数。
    digest: str
    #: 四个键的正文（已通过数字禁令）。
    sections: Mapping[str, str]


def _numeral(text: str) -> str | None:
    """正文里的第一个 Unicode 十进制数位（没有 ⇒ `None`）。"""
    for char in text:
        if unicodedata.category(char) == "Nd":
            return char
    return None


def validate_narrative(sections: Mapping[str, str]) -> None:
    """叙述四键齐备且**不含任何数字**（结构判据；违反即点名拒绝）。"""
    missing = [key for key in NARRATIVE_KEYS if not str(sections.get(key) or "").strip()]
    if missing:
        raise NarrativeError(f"narrative is missing these sections: {', '.join(missing)}")
    for key in NARRATIVE_KEYS:
        found = _numeral(str(sections[key]))
        if found is not None:
            raise NarrativeError(
                f"narrative section {key!r} contains the numeral {found!r}: the model must refer "
                "to quantities by name and leave every number to the fact table"
            )


def parse_narrative(content: str | None) -> Mapping[str, str]:
    """模型输出 → 四个键的正文（JSON 对象；畸形即点名，不猜）。"""
    if content is None or not content.strip():
        raise NarrativeError("narrative is empty")
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise NarrativeError(f"narrative is not a JSON object: {error}") from error
    if not isinstance(parsed, Mapping):
        raise NarrativeError(f"narrative must be a JSON object, got {type(parsed).__name__}")
    return {key: str(parsed.get(key) or "") for key in NARRATIVE_KEYS}


def narrative_digest(sections: Mapping[str, str]) -> str:
    """叙述正文的规范摘要（键排序 + `ensure_ascii=False` ⇒ 同一内容同一串）。"""
    payload = json.dumps(
        {key: sections[key] for key in NARRATIVE_KEYS}, ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fact_ledger(inputs: ReportInputs) -> tuple[dict[str, str], ...]:
    """**事实表**的行（值逐字取自 `ReportInputs`；每行带来源列）。

    **这是报告里唯一允许出现数字的地方**。行序是确定性的（类别 → 名称 → 来源），
    因此同一份持久事实 ⇒ 同一张表（与汇编器的确定性同一条纪律）。
    """
    rows: list[dict[str, str]] = []
    for source in inputs.sources:
        rows.append({
            "类别": "来源",
            "名称": str(source.get("identifier", "?")),
            "值": str(source.get("title") or source.get("identifier", "?")),
            "来源": str(source.get("evidence_id", "?")),
        })
    for metric in inputs.metrics:
        rows.append({
            "类别": "指标",
            "名称": str(metric.get("name", "?")),
            "值": str(metric.get("value", "?")),
            "来源": str(metric.get("experiment_run_id") or "experiment"),
        })
    if inputs.verdict:
        verdict = dict(inputs.verdict)
        rows.append({
            "类别": "评审",
            "名称": "decision",
            "值": str(verdict.get("decision", "?")),
            "来源": "review_findings",
        })
        if verdict.get("reason"):
            rows.append({
                "类别": "评审",
                "名称": "reason",
                "值": str(verdict["reason"]),
                "来源": "review_findings",
            })
    return tuple(sorted(rows, key=lambda row: (row["类别"], row["名称"], row["来源"])))


def fact_table_markdown(rows: tuple[dict[str, str], ...]) -> str:
    """事实表 → markdown（空表也写出表头 + 一行「无」的说明，不省略该节）。"""
    lines = ["| " + " | ".join(FACT_TABLE_COLUMNS) + " |", "| --- | --- | --- | --- |"]
    if not rows:
        lines.append("| _（无）_ | 本 run 没有检索来源 / 实验指标 / 评审判词 | — | — |")
    lines += [
        f"| {row['类别']} | `{row['名称']}` | {row['值']} | `{row['来源']}` |" for row in rows
    ]
    return "\n".join(lines)


def narrative_prompt(inputs: ReportInputs, rows: tuple[dict[str, str], ...]) -> str:
    """给模型的任务书（**只给类别计数与指标名** —— 标识符与数值都不发给它）。

    **为什么不发标识符**：来源标识（PMID 之类）**本身是数字串**，而叙述被禁止出现任何
    数字 ⇒ 把它们发给模型是**请它违规**（实测：首版任务书把 `39000001` 发过去，模型仍得
    照禁令不写，但那等于让它知道一个它不能用的东西）。模型要指称来源时写「检索得到的
    记录」，指称指标时用**名字**（名字里若含数字，同样属于拒绝面 —— 见 `validate_narrative`）。
    """
    kinds: dict[str, int] = {}
    for row in rows:
        kinds[row["类别"]] = kinds.get(row["类别"], 0) + 1
    counts = "\n".join(f"- {kind}: {count}" for kind, count in sorted(kinds.items()))
    names = "\n".join(f"- {row['名称']}" for row in rows if row["类别"] == "指标")
    return (
        "Write the narrative body of a research report as a JSON object with exactly these "
        f"keys: {', '.join(NARRATIVE_KEYS)}.\n"
        f"run: {inputs.run_id}\nprotocol: {inputs.protocol_id}\nstate at assembly: {inputs.state}\n"
        "How many facts this report carries (counts only):\n"
        f"{counts or '- (none)'}\n"
        "The measured quantities are named:\n"
        f"{names or '- (none)'}\n"
        "HARD RULE: the narrative must contain NO digits at all (not even inside identifiers) — "
        "every quantity is published in a separate, machine-assembled fact table, and the "
        "narrative must refer to quantities by name only. Do not state, infer or repeat any "
        "number, and do not claim anything the listed facts do not support: if a category is "
        "empty, say what is missing and why it matters."
    )


def build_narrative_report(inputs: ReportInputs, admission: NarrativeAdmission) -> str:
    """事实表（汇编器）+ 叙述（模型）→ 一份报告（同输入同叙述 ⇒ 逐字节相同）。"""
    if not inputs.run_id.strip():
        raise NarrativeError("report requires a non-empty run_id")
    validate_narrative(admission.sections)
    rows = fact_ledger(inputs)
    header = [
        "# 研究报告（模型撰写正文 + 确定性事实表）",
        "",
        f"- **run**: `{inputs.run_id}`",
        f"- **协议**: `{inputs.protocol_id}`",
        f"- **汇编时状态**: `{inputs.state}`",
        f"- **叙述作者**: {admission.author}",
        f"- **供应商返回的模型名**: `{admission.returned_model}`",
        f"- **叙述摘要**: `{admission.digest}`",
    ]
    if inputs.objective:
        # GOAL-20261024-096 EC-03 起，生产路径的 `objective` 来自本 run 自己的
        # `research_question` 制品（与 `research_report._header_lines` 同一口径）。
        header.append(f"- **研究问题（本 run 自提；逐字引用）**: {inputs.objective}")
    body: list[str] = [*header, ""]
    for heading, key in zip(SECTION_HEADINGS, NARRATIVE_KEYS, strict=True):
        body += [heading, "", admission.sections[key].strip(), ""]
    body += [FACT_TABLE_HEADING, "", fact_table_markdown(rows), ""]
    body += [
        "**两块面各自由谁写（如实登记）**：",
        "",
        f"- 第 1…4 节由**模型**撰写（{admission.author}，返回名 `{admission.returned_model}`），"
        "正文**不含任何数字** —— 模型写数字即被**点名拒绝**，不静默改写。",
        "- 第 5 节由**汇编器**撰写：值逐字取自本 run 的持久事实（四个既有读面），"
        "**不重算、不编造**；来源列可逐条复核。",
        "- 报告只覆盖**本 run**；跨 run 的结论不在其中。发现与结论的可靠性取决于上游各 phase "
        "的判据，本报告不重新判定它们，也**不判**叙述的科学质量。",
    ]
    if not inputs.sources:
        body.append("- **本 run 没有真实检索来源** ⇒ 事实表里没有来源行。")
    if not inputs.metrics:
        body.append("- **本 run 没有实测指标** ⇒ 事实表里没有指标行。")
    return "\n".join(body).rstrip("\n") + "\n"


__all__ = [
    "FACT_TABLE_COLUMNS",
    "FACT_TABLE_HEADING",
    "NARRATIVE_KEYS",
    "NarrativeAdmission",
    "NarrativeError",
    "build_narrative_report",
    "fact_ledger",
    "fact_table_markdown",
    "narrative_digest",
    "narrative_prompt",
    "parse_narrative",
    "validate_narrative",
]
