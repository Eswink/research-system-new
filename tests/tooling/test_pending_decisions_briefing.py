"""EC-03 判据：待拍板决策简报必须齐、非空壳、且与 GOAL 的人工面**双向对齐**。

判据口径（GOAL-015 EC-03；GOAL-018 EC-03 扩展）：

- 简报条目数 ≥ 9；
- 每一条必须六要素齐全且非空壳（要决定什么 / 选项 / 影响与代价 / 证据出处 / 不做会怎样 / 建议）；
- GOAL「不进入循环 / 需人工拍板」节的**每条编号项**都必须在简报的对齐表里出现；
- 对齐表里标「待拍板」的行必须指向一个真实存在的简报条目；
- 简报条目与对齐表之间**双向无孤儿**（有条目就必须在表里被引用，被引用就必须真有条目）；
- **（GOAL-018 EC-03 新增）** 13 项 `D-NN` 的**终态表**必须齐：`D-01…D-13` 各一行、
  终态取自四值词汇表（已实施 / 部分实施 / 已拍板为维持现状 / 未授权待拍板）、依据非空壳；
- **（GOAL-018 EC-03 新增）** 终态表与 GOAL-018 人工面里的
  ``**D-NN 终态 = <状态>**`` 声明**逐条同词**（两向：不缺不余），
  即「简报 ↔ GOAL-015」与「简报 ↔ GOAL-018」两条对齐面同时成立；
- **（GOAL-018 EC-03 新增）** 对齐表的状态列必须取自**封闭词汇表**
  （终态四值 + `待拍板` / `标准禁令` / `已了结`），不得出现自由表述。

「删一项 / 空一格 / 删一行 / 改模糊 / 两侧不一致」的反证做成对文本的变体检查
（``_problems`` / ``_mutated_problems``），而不是只对现状断言
—— 否则这条判据在被删空之后仍然会绿。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOAL_FILE = ROOT / ".cursor/plans/goals/GOAL-20260925-015-gate-trustworthiness.md"
GOAL018_FILE = ROOT / (
    ".cursor/plans/goals/GOAL-20260926-018-residual-closeout-and-decision-register.md"
)
BRIEFING_FILE = ROOT / "docs/roadmap/OPEN_DECISIONS_BRIEFING.md"

ELEMENTS = ("要决定什么", "选项", "影响与代价", "证据出处", "不做会怎样", "建议")
MIN_ITEMS = 9
MIN_ELEMENT_CHARS = 8

#: 13 项决策的唯一编号集合（`D-01` … `D-13`）。
DECISION_IDS = tuple(f"D-{index:02d}" for index in range(1, 14))
#: 终态词汇表：每一项 `D-NN` 只能取其中之一（`未授权待拍板` 为「尚无定论」类）。
TERMINAL_STATES = ("已实施", "部分实施", "已拍板为维持现状", "未授权待拍板")
#: 对齐表状态列的封闭词汇表 = 终态四值 + 三类**非决策**标记。
ALIGNMENT_STATE_PREFIXES = TERMINAL_STATES + ("待拍板", "标准禁令", "已了结")

TERMINAL_TABLE_MARKER = "## 13 项 `D-NN` 终态表"

_ITEM_HEADING = re.compile(r"^#{2,3} (D-\d\d)｜(.+?)$", re.M)
_ELEMENT = re.compile(r"^- \*\*(" + "|".join(ELEMENTS) + r")\*\*：(.+?)$", re.M)
_GOAL_SECTION = re.compile(r"^## .*不进入循环.*?^## ", re.M | re.S)
_GOAL_NUMBERED = re.compile(r"^(\d+)\. \*\*", re.M)
_ALIGNMENT_ROW = re.compile(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", re.M)
_INT_ID = re.compile(r"^\d+$")
_D_REF = re.compile(r"D-\d\d")
_ALIGNMENT_MARKER = "## 对齐表"
#: 终态表的一行：`| D-01 | 主题 | 终态 | 依据 |`。
_TERMINAL_ROW = re.compile(r"^\| (D-\d\d) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", re.M)
#: GOAL 侧的终态声明：`**D-05 终态 = 已拍板为维持现状**`（`*` 之外的状态文本由正则吃定）。
_GOAL_DECL = re.compile(r"\*\*(D-\d\d) 终态 = ([^*]+?)\*\*")

# 「本 GOAL 特有的待拍板项」在 GOAL 里是无编号要点，用可核对的短语钉住覆盖关系。
REQUIRED_GOAL_TOPICS = (
    "路径 (B) 的 5 条重设计项",
    "`W-A` 之外的策略面放宽",
    "门禁 scoping 的自我修正",
    "`M-1`",
    "live 判据的开门条件",
    "CI 资源阈值型判据的负载敏感性",
)
EXPECTED_STRAY_IDS = {"特-1", "特-2", "特-3", "特-4", "特-5", "残-1"}

Row = tuple[str, str, str, str]


def _plain(value: str) -> str:
    """去掉反引号与强调号并压掉空白：让「状态」可做**词汇表**比较而非字面比较。"""
    return value.replace("`", "").replace("*", "").strip()


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
            continue
        # GOAL-018 EC-03：状态列改由**封闭词汇表**约束（「待拍板」只是其中一个取值），
        # 于是「已拍板」的行也必须继续把它的 `D-NN` 计入 `referenced`
        # ——引用收集与状态解耦，否则任何一项一旦结案就会立刻被判成孤儿。
        plain_state = _plain(state)
        if _INT_ID.match(row_id.strip()) or row_id.strip().startswith(("特-", "残-")):
            if not plain_state.startswith(ALIGNMENT_STATE_PREFIXES):
                problems.append(
                    f"对齐表第 {row_id} 行（{topic}）的状态列不在词汇表内：{plain_state!r}"
                )
        refs = _D_REF.findall(target)
        if "待拍板" in state and not refs:
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


def _terminal_block(briefing: str) -> str:
    """终态表的文本块（从标记到下一个 `##`）——**按压必须只在这个块内生效**。

    简报里还有一张同形状的**索引**表（也以 `| D-05 | …` 开头），
    所以「按行号/按行首删一行」的按压会命中错的那张表、看着变红其实没动判据
    这正是本仓 `MEM` 记过的「判据自身恒真」那一类坑。
    """
    start = briefing.find(TERMINAL_TABLE_MARKER)
    assert start >= 0, f"简报里找不到「{TERMINAL_TABLE_MARKER}」"
    end = briefing.find("\n## ", start + len(TERMINAL_TABLE_MARKER))
    return briefing[start:end] if end > 0 else briefing[start:]


def _terminal_mutation(pattern: str, replacement: str) -> object:
    """构造一个**只在终态表块内**生效的替换（块内未命中即断言失败）。"""

    def mutate(text: str) -> str:
        block = _terminal_block(text)
        mutated = re.sub(pattern, replacement, block, count=1, flags=re.M)
        assert mutated != block, f"终态表块内未命中：{pattern!r}"
        return text.replace(block, mutated, 1)

    return mutate


def _terminal_rows(briefing: str) -> list[Row]:
    if briefing.find(TERMINAL_TABLE_MARKER) < 0:
        return []
    return _TERMINAL_ROW.findall(_terminal_block(briefing))


def _goal_declarations(goal_text: str) -> dict[str, str]:
    section = _GOAL_SECTION.search(goal_text)
    if section is None:
        return {}
    return {item_id: _plain(state) for item_id, state in _GOAL_DECL.findall(section.group(0))}


def _terminal_row_problems(rows: list[Row]) -> tuple[dict[str, str], list[str]]:
    """终态表逐行检查：编号不重复、终态取自**词汇表**、依据非空壳。"""
    problems: list[str] = []
    table: dict[str, str] = {}
    for item_id, _topic, state, evidence in rows:
        plain_state = _plain(state)
        if item_id in table:
            problems.append(f"终态表重复列出 {item_id}")
        table[item_id] = plain_state
        if plain_state not in TERMINAL_STATES:
            problems.append(f"终态表 {item_id} 的终态不在词汇表内：{plain_state!r}")
        if len(_plain(evidence)) < MIN_ELEMENT_CHARS:
            problems.append(f"终态表 {item_id} 的依据是空壳（{evidence.strip()!r}）")
    return table, problems


def _terminal_problems(briefing: str, goal018_text: str) -> list[str]:
    """13 项 `D-NN` 终态表 ↔ GOAL-018 人工面声明的**逐条同词**对照。"""
    rows = _terminal_rows(briefing)
    if not rows:
        return [f"简报里找不到可解析的「{TERMINAL_TABLE_MARKER}」终态表"]

    table, problems = _terminal_row_problems(rows)
    missing_ids = sorted(set(DECISION_IDS) - set(table))
    if missing_ids:
        problems.append(f"终态表缺决策项：{missing_ids}")
    extra_ids = sorted(set(table) - set(DECISION_IDS))
    if extra_ids:
        problems.append(f"终态表出现词表外的决策项：{extra_ids}")

    declared = _goal_declarations(goal018_text)
    if sorted(declared) != sorted(DECISION_IDS):
        problems.append(f"GOAL 人工面的终态声明不是 13 条：{sorted(declared)}")
    problems += [
        f"{item_id} 的终态在简报与 GOAL 之间不一致：{table[item_id]!r} != {declared[item_id]!r}"
        for item_id in DECISION_IDS
        if item_id in table and item_id in declared and table[item_id] != declared[item_id]
    ]
    return problems


def _problems(goal_text: str, briefing_text: str, goal018_text: str) -> list[str]:
    sections = _split_sections(briefing_text)
    numbered, problems = _numbered_goal_items(goal_text)
    rows = _alignment_rows(briefing_text)
    if not rows:
        return problems + ["简报里找不到可解析的「对齐表」节"]
    problems += _element_problems(sections)
    problems += _alignment_problems(rows, numbered, sections)
    problems += _terminal_problems(briefing_text, goal018_text)
    # GOAL-018 的人工面走**同一套**对齐口径（GOAL-018 EC-03：口径同步，不是另立一套）。
    numbered018, problems018 = _numbered_goal_items(goal018_text)
    problems += [f"[GOAL-018] {problem}" for problem in problems018]
    problems += [
        f"[GOAL-018] {problem}" for problem in _alignment_problems(rows, numbered018, sections)
    ]
    problems += [
        f"对齐表没有覆盖 GOAL 特有项：{topic}"
        for topic in REQUIRED_GOAL_TOPICS
        if topic not in briefing_text
    ]
    return problems


def _current_problems() -> list[str]:
    return _problems(
        GOAL_FILE.read_text(encoding="utf-8"),
        BRIEFING_FILE.read_text(encoding="utf-8"),
        GOAL018_FILE.read_text(encoding="utf-8"),
    )


def _mutated_problems(mutate: object, expect: str, goal018_mutate: object = None) -> list[str]:
    briefing = BRIEFING_FILE.read_text(encoding="utf-8")
    goal018 = GOAL018_FILE.read_text(encoding="utf-8")
    mutated = mutate(briefing)  # type: ignore[operator]
    mutated_goal018 = goal018_mutate(goal018) if goal018_mutate else goal018  # type: ignore[operator]
    assert (mutated, mutated_goal018) != (briefing, goal018), "变体构造失败：没有改动任何内容"
    problems = _problems(GOAL_FILE.read_text(encoding="utf-8"), mutated, mutated_goal018)
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


def test_missing_terminal_row_is_red() -> None:
    _mutated_problems(
        _terminal_mutation(r"^\| D-05 \|.*?$", ""),
        "终态表缺决策项",
    )


def test_blank_terminal_state_is_red() -> None:
    """状态格「空壳」（归一化后为空）必须判红——而不是被当成缺行放过。"""
    _mutated_problems(
        _terminal_mutation(r"^\| (D-07) \| ([^|]*)\| [^|]*\|", r"| \1 | \2| ** |"),
        "终态不在词汇表内",
    )


def test_malformed_terminal_row_is_red() -> None:
    """行形状坏掉（少一格）不得让该决策项静默消失——必须报「缺决策项」。"""
    _mutated_problems(
        _terminal_mutation(r"^\| (D-08) \| ([^|]*)\| [^|]*\| [^|]*\|", r"| \1 | \2| 已实施 |"),
        "终态表缺决策项",
    )


def test_vague_terminal_state_is_red() -> None:
    _mutated_problems(
        _terminal_mutation(r"^\| (D-09) \| ([^|]*)\| [^|]*\|", r"| \1 | \2| 待定 |"),
        "终态不在词汇表内",
    )


def test_unsupported_terminal_evidence_is_red() -> None:
    _mutated_problems(
        _terminal_mutation(r"^\| (D-11) \| ([^|]*)\| ([^|]*)\| [^|]*\|", r"| \1 | \2| \3| 待补 |"),
        "依据是空壳",
    )


def test_vague_alignment_state_is_red() -> None:
    _mutated_problems(
        lambda text: re.sub(
            r"^\| 5 \| (依赖 pin 升级[^|]*)\| [^|]*\|",
            r"| 5 | \1| 待定 |",
            text,
            count=1,
            flags=re.M,
        ),
        "状态列不在词汇表内",
    )


def test_goal_terminal_disagreement_is_red() -> None:
    _mutated_problems(
        lambda text: text,
        "终态在简报与 GOAL 之间不一致",
        goal018_mutate=lambda text: re.sub(
            r"\*\*D-13 终态 = [^*]+\*\*", "**D-13 终态 = 未授权待拍板**", text, count=1
        ),
    )


def test_missing_goal_terminal_declaration_is_red() -> None:
    _mutated_problems(
        lambda text: text,
        "终态声明不是 13 条",
        goal018_mutate=lambda text: re.sub(r"⇒ \*\*D-08 终态 = [^*]+\*\*。", "", text, count=1),
    )


def test_uncovered_goal018_item_is_red() -> None:
    """GOAL-018 的编号项必须**全部**被对齐表覆盖——多出一条没人认领的即判红。"""
    _mutated_problems(
        lambda text: text,
        "[GOAL-018] 对齐表缺 GOAL 编号项",
        goal018_mutate=lambda text: re.sub(
            r"(    ⇒ \*\*D-09 终态 = 已实施\*\*。\n)",
            r"\1\n14. **多出的编号项（按压用）**——对齐表里没有对应行。\n",
            text,
            count=1,
        ),
    )
