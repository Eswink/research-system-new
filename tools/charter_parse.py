#!/usr/bin/env python3
"""charter 读取的**纯解析原语**（GOAL-20261021-092 EC-01）—— 只读树，不做判断。

**为什么单列**：`tools/next_round_charter.py` 既要解析 GOAL / RECHECK / 宪章，又要渲染骨架，
两件事合起来会撞 450 行硬上限（规模门）。本模块只做**机械动作**：取 frontmatter、切小节、
取表格数据行、把残余节切成逐条原文。它**不含**任何「该不该生成」的判断（那是读取器的事），
也不读时钟、不出网、不加载模型。

**口径与宪章的既有判据同源**（`tests/tooling/test_mainline_program_is_intact.py` 与
`test_mainline_research_ladder_advances.py` 里各自写过一份）：小节取到下一个 `## ` 为止、
表格数据行跳过表头与全 `-:` 分隔行、格内去 Markdown 强调标记。此处**不**去复用那两个判据
里的私有函数（它们住在 `tests/` 且带各自的断言），而是把同一口径**再写一份**并逐条钉住
（`tests/tooling/test_next_round_charter.py` 的 `test_the_parsing_agrees_with_the_charter_judges`
把两份读数逐条比对）—— 两份独立实现对同一输入给出同一读数，才叫口径成立。
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import yaml

#: GOAL 的**终态**取值（与治理契约同源；非终态 ⇒ 拒绝生成）。
TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABORTED"})
#: RECHECK 的**通过**取值（`REVISE` / `BLOCK` ⇒ 上一轮不算收口）。
PASSING = frozenset({"PASS", "PASS_WITH_WARNINGS"})

#: 三个受判小节的标题前缀（标题可带括注，按前缀定位）。
RESIDUAL_HEADING = "## 残余与未覆盖范围"
LADDER_HEADING = "## 科研能力阶梯"
CI_HEADING = "## CI 台账"
#: 残余节的「确实没有残余」写法（其余「空」一律按缺失处理 —— 空节与忘写不可区分）。
EMPTY_MARKERS: tuple[str, ...] = ("无残余", "（无）", "（无未覆盖）")

_W_ITEM = re.compile(r"^- \*\*`W-(\d+)`\*\*")
_OK_CONCLUSION = re.compile(r"\bsuccess\b", re.IGNORECASE)
_RED_CONCLUSION = re.compile(r"\bfailure\b|判红|取消|cancelled", re.IGNORECASE)


class Refusal(Exception):
    """一条**点名**的失败（带稳定的 `code`，便于判据逐条按压）。"""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class Residual:
    """残余节里的一条（`raw` 是**逐字原文**，含续行；不摘要、不改写）。"""

    number: int
    raw: str


@dataclass(frozen=True, slots=True)
class LadderMatch:
    """收录了本 GOAL 的阶梯行里，被审判的两格（`域` / `下一级是什么`）。"""

    domain: str
    next_level: str


@dataclass(frozen=True, slots=True)
class CiSummary:
    """CI 台账的机械读数（逐类行数 + 结论）。"""

    green: int
    no_run: int
    red: int
    unknown: tuple[str, ...]
    last: str

    @property
    def verdict(self) -> str:
        if self.red:
            return f"有判红（{self.red} 行）"
        if self.unknown:
            return f"未能判定（{len(self.unknown)} 行未识别）"
        return "全绿"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frontmatter(text: str) -> dict[str, Any]:
    """取 YAML frontmatter（没有 / 形状不对 ⇒ 空映射，由调用方点名）。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    loaded: object = yaml.safe_load(text[3:end])
    return loaded if isinstance(loaded, dict) else {}


def section_lines(text: str, heading: str) -> list[str] | None:
    """某个二级小节的正文行（到下一个 `## ` 为止）；小节不存在 ⇒ `None`。"""
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith(heading):
            start = index + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def _cells(line: str) -> list[str]:
    return [
        cell.replace("**", "").replace("`", "").strip()
        for cell in line.strip().strip("|").split("|")
    ]


def table_rows(lines: Sequence[str]) -> list[list[str]]:
    """小节里的数据行（跳过表头与分隔行；非表格行不算）。"""
    rows: list[list[str]] = []
    separator_seen = False
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if cells and all(set(cell) <= set("-: ") and cell for cell in cells):
            separator_seen = True
            continue
        if not separator_seen:
            continue
        rows.append(cells)
    return rows


def residuals(lines: Sequence[str]) -> tuple[Residual, ...]:
    """把残余节切成逐条原文（一条 = 一个 `- **`W-N`**` 起头 + 其缩进续行）。"""
    items: list[Residual] = []
    current: list[str] = []
    number = 0
    for line in [*lines, ""]:
        match = _W_ITEM.match(line)
        if match is not None:
            if current:
                items.append(Residual(number, "\n".join(current)))
            number = int(match.group(1))
            current = [line]
        elif current and line[:1] in (" ", "\t") and line.strip():
            current.append(line)
        elif current:
            items.append(Residual(number, "\n".join(current)))
            current = []
    return tuple(items)


def check_residuals(items: Sequence[Residual]) -> None:
    """编号必须是 `W-1…W-N` 的**连续**序列（断号 ⇒ 有人删/漏了一条）。"""
    numbers = [item.number for item in items]
    if not numbers:
        raise Refusal("RESIDUAL_EMPTY", "残余节里没有任何 `W-NN` 条目（也没有「无残余」标记）")
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise Refusal(
            "RESIDUAL_GAP",
            f"`W` 编号不连续：读到 {numbers}，应是 {expected}（断号 = 有残余被删或漏写）",
        )


def residual_section(goal_text: str) -> tuple[Residual, ...]:
    """GOAL 的残余节 ⇒ 逐条原文（节缺失 / 空而无标记 / 断号都点名拒绝）。"""
    body = section_lines(goal_text, RESIDUAL_HEADING)
    if body is None:
        raise Refusal("RESIDUAL_SECTION_MISSING", f"GOAL 缺少小节 {RESIDUAL_HEADING!r}")
    first = next((line.strip() for line in body if line.strip()), "")
    if any(marker in first for marker in EMPTY_MARKERS):
        return ()
    items = residuals(body)
    check_residuals(items)
    return items


def ladder_matches(charter: str, goal_id: str) -> tuple[LadderMatch, ...]:
    """阶梯里 `依据 GOAL` 收录本 GOAL 的行 ⇒ `(域, 下一级是什么)`（原文）。"""
    body = section_lines(charter, LADDER_HEADING)
    if body is None:
        raise Refusal("LADDER_SECTION_MISSING", f"宪章缺少小节 {LADDER_HEADING!r}")
    matches = [
        LadderMatch(row[0], row[3])
        for row in table_rows(body)
        if len(row) >= 4 and goal_id in re.findall(r"GOAL-\d{8}-\d{3}", row[2])
    ]
    if not matches:
        raise Refusal(
            "LADDER_NOT_RECORDED",
            f"宪章阶梯没有任何域的 `依据 GOAL` 收录 {goal_id} ⇒ 这一轮没有被记为科研进展",
        )
    return tuple(matches)


def ci_summary(text: str) -> CiSummary:
    """CI 台账的逐行分类（`success` / 无 run / 判红 / 未识别）。"""
    body = section_lines(text, CI_HEADING)
    if body is None:
        raise Refusal("CI_SECTION_MISSING", f"GOAL 缺少小节 {CI_HEADING!r}")
    green = no_run = red = 0
    unknown: list[str] = []
    last = ""
    for row in table_rows(body):
        if len(row) < 3:
            continue
        conclusion = row[2]
        if _RED_CONCLUSION.search(conclusion):
            red += 1
        elif _OK_CONCLUSION.search(conclusion):
            green += 1
        elif conclusion in ("—", "-", ""):
            no_run += 1
        else:
            unknown.append(f"{row[0]} ⇒ {conclusion}")
        last = f"{row[0]} ⇒ {conclusion}"
    if not last:
        raise Refusal("CI_SECTION_MISSING", f"{CI_HEADING} 里没有任何数据行 ⇒ 台账只是标题")
    return CiSummary(green, no_run, red, tuple(unknown), last)


__all__ = [
    "CI_HEADING",
    "EMPTY_MARKERS",
    "LADDER_HEADING",
    "PASSING",
    "RESIDUAL_HEADING",
    "TERMINAL",
    "CiSummary",
    "LadderMatch",
    "Refusal",
    "Residual",
    "check_residuals",
    "ci_summary",
    "frontmatter",
    "ladder_matches",
    "residual_section",
    "residuals",
    "section_lines",
    "sha256_text",
    "table_rows",
]
