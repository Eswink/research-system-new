"""EC-03 判据：待拍板决策简报必须齐、非空壳、且与 GOAL 的人工面**双向对齐**。

判据口径（对应 GOAL-015 EC-03）：

- 简报条目数 ≥ 9；
- 每一条必须六要素齐全且非空壳（要决定什么 / 选项 / 影响与代价 / 证据出处 / 不做会怎样 / 建议）；
- GOAL-015「不进入循环 / 需人工拍板」节的**每条编号项**都必须在简报的对齐表里出现；
- 对齐表里标「待拍板」的行必须指向一个真实存在的简报条目；
- 简报条目与对齐表之间**双向无孤儿**（有条目就必须在表里被引用，被引用就必须真有条目）。

「删一项 / 空一格 / 删一行」的反证做成对文本的变体检查（``_problems``），而不是只对现状断言
—— 否则这条判据在被删空之后仍然会绿。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOAL_FILE = ROOT / ".cursor/plans/goals/GOAL-20260925-015-gate-trustworthiness.md"
BRIEFING_FILE = ROOT / "docs/roadmap/OPEN_DECISIONS_BRIEFING.md"

ELEMENTS = ("要决定什么", "选项", "影响与代价", "证据出处", "不做会怎样", "建议")
MIN_ITEMS = 9
MIN_ELEMENT_CHARS = 8

_ITEM_HEADING = re.compile(r"^#{2,3} (D-\d\d)｜(.+?)$", re.M)
_ELEMENT = re.compile(r"^- \*\*(" + "|".join(ELEMENTS) + r")\*\*：(.+?)$", re.M)
_GOAL_SECTION = re.compile(r"^## .*不进入循环.*?^## ", re.M | re.S)
_GOAL_NUMBERED = re.compile(r"^(\d+)\. \*\*", re.M)
_ALIGNMENT_ROW = re.compile(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", re.M)
_INT_ID = re.compile(r"^\d+$")
_D_REF = re.compile(r"D-\d\d")
_ALIGNMENT_MARKER = "## 对齐表"

# 「本 GOAL 特有的待拍板项」在 GOAL 里是无编号要点，用可核对的短语钉住覆盖关系。
REQUIRED_GOAL_TOPICS = (
    "路径 (B) 的 5 条重设计项",
    "`W-A` 之外的策略面放宽",
    "门禁 scoping 的自我修正",
    "`M-1`",
    "live 判据的开门条件",
)
EXPECTED_STRAY_IDS = {"特-1", "特-2", "特-3", "特-4", "残-1"}

Row = tuple[str, str, str, str]


def _split_sections(briefing: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(_ITEM_HEADING.finditer(briefing))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(briefing)
        sections[match.group(1)] = briefing[match.end() : end]
    return sections


def _element_problems(sections: dict[str, str]) -> list[str]:
    problems: list[str] = []
    if len(sections) < MIN_ITEMS:
        problems.append(f"简报条目只有 {len(sections)} 条，少于 {MIN_ITEMS} 条")
    for item_id, body in sections.items():
        labels = {label: value.strip() for label, value in _ELEMENT.findall(body)}
        for element in ELEMENTS:
            value = labels.get(element)
            if value is None:
                problems.append(f"{item_id} 缺要素「{element}」")
            elif len(value) < MIN_ELEMENT_CHARS:
                problems.append(f"{item_id} 的「{element}」是空壳（{value!r}）")
    return problems


def _numbered_goal_items(goal_text: str) -> tuple[set[int], list[str]]:
    section = _GOAL_SECTION.search(goal_text)
    if section is None:
        return set(), ["GOAL 里找不到「不进入循环 / 需人工拍板」节"]
    numbered = {int(number) for number in _GOAL_NUMBERED.findall(section.group(0))}
    if len(numbered) < 10:
        return numbered, [f"GOAL 人工面只解析到 {len(numbered)} 条编号项，疑似格式被改"]
    return numbered, []


def _alignment_rows(briefing: str) -> list[Row]:
    start = briefing.find(_ALIGNMENT_MARKER)
    if start < 0:
        return []
    return [row for row in _ALIGNMENT_ROW.findall(briefing[start:]) if not row[0].startswith("---")]


def _alignment_problems(rows: list[Row], numbered: set[int], sections: dict[str, str]) -> list[str]:
    problems: list[str] = []
    numbered_rows = {int(row[0]): row for row in rows if _INT_ID.match(row[0].strip())}
    missing = sorted(numbered - set(numbered_rows))
    if missing:
        problems.append(f"对齐表缺 GOAL 编号项：{missing}")

    referenced: set[str] = set()
    for row_id, topic, state, target in rows:
        if not state.strip():
            problems.append(f"对齐表第 {row_id} 行（{topic}）的状态列为空")
        if "待拍板" not in state:
            continue
        refs = _D_REF.findall(target)
        if not refs:
            problems.append(f"对齐表第 {row_id} 行（{topic}）标为待拍板却没有指向任何 D-NN")
        referenced.update(refs)
    return problems + _orphan_problems(rows, sections, referenced)


def _orphan_problems(rows: list[Row], sections: dict[str, str], referenced: set[str]) -> list[str]:
    problems: list[str] = []
    orphan_refs = sorted(referenced - set(sections))
    if orphan_refs:
        problems.append(f"对齐表引用了不存在的简报条目：{orphan_refs}")
    orphan_items = sorted(set(sections) - referenced)
    if orphan_items:
        problems.append(f"简报条目没有被对齐表引用（孤儿）：{orphan_items}")
    stray = {row[0] for row in rows if row[0].startswith(("特-", "残-"))}
    if stray != EXPECTED_STRAY_IDS:
        problems.append(f"对齐表的非编号行不是预期集合：{sorted(stray)}")
    return problems


def _problems(goal_text: str, briefing_text: str) -> list[str]:
    sections = _split_sections(briefing_text)
    numbered, problems = _numbered_goal_items(goal_text)
    rows = _alignment_rows(briefing_text)
    if not rows:
        return problems + ["简报里找不到可解析的「对齐表」节"]
    problems += _element_problems(sections)
    problems += _alignment_problems(rows, numbered, sections)
    problems += [
        f"对齐表没有覆盖 GOAL 特有项：{topic}"
        for topic in REQUIRED_GOAL_TOPICS
        if topic not in briefing_text
    ]
    return problems


def _current_problems() -> list[str]:
    return _problems(
        GOAL_FILE.read_text(encoding="utf-8"), BRIEFING_FILE.read_text(encoding="utf-8")
    )


def _mutated_problems(mutate: object, expect: str) -> list[str]:
    briefing = BRIEFING_FILE.read_text(encoding="utf-8")
    mutated = mutate(briefing)  # type: ignore[operator]
    assert mutated != briefing, "变体构造失败：没有改动任何内容"
    problems = _problems(GOAL_FILE.read_text(encoding="utf-8"), mutated)
    assert problems, f"变体未被判红（期望含「{expect}」）"
    assert any(expect in problem for problem in problems), problems
    return problems


def test_briefing_is_complete_and_aligned() -> None:
    problems = _current_problems()
    assert problems == [], "决策简报不满足 EC-03 判据：" + "；".join(problems)


def test_missing_item_is_red() -> None:
    _mutated_problems(
        lambda text: re.sub(r"^## D-11｜.*?(?=^## D-12｜)", "", text, flags=re.M | re.S),
        "不存在的简报条目",
    )


def test_empty_element_is_red() -> None:
    _mutated_problems(
        lambda text: re.sub(
            r"^- \*\*证据出处\*\*：.*?$", "- **证据出处**：待补", text, count=1, flags=re.M
        ),
        "空壳",
    )


def test_uncovered_goal_item_is_red() -> None:
    _mutated_problems(
        lambda text: re.sub(r"^\| 5 \| 依赖 pin 升级.*?$", "", text, flags=re.M),
        "对齐表缺 GOAL 编号项",
    )


def test_missing_goal_topic_row_is_red() -> None:
    _mutated_problems(
        lambda text: re.sub(r"^\| 残-1 \|.*?$", "", text, flags=re.M),
        "非编号行不是预期集合",
    )
