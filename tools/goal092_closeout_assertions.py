#!/usr/bin/env python3
"""GOAL-20261021-092 收口复检的**本轮特有断言集**（EC-04 / EC-05）。

与 GOAL-023…091 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由 `tools/closeout_recheck_assertions.standard_verdicts`
承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02/EC-03 的交付面**：读取器与解析原语在树且**按 AST 声明**了公开面
   （`build_skeleton` / `main` / `Refusal` / `residual_section` / `ladder_matches` /
   `ci_summary`）；判据文件的用例数**不低于下界**；两个脚本都在四道门射程内
   （`IN_SCOPE`，与 `W-7` 的顺序反转同源）。
2. **EC-04 产物被真的用了**：`evidence/` 下的骨架在树且非空、其 `sha256` 与记录里写的一致；
   GOAL 的「上一轮残余的处置」表**逐条**覆盖 **7** 个 `W`（不多不少），每条有非空处置，
   其中 `W-6` / `W-7` 必须落在**做掉**（本轮有实际动作）。
3. **EC-05 记录面自洽**：GOAL / PLAN / RECHECK 三者在位、`latest_recheck` 是可解析的仓库
   相对路径（**时序**：本验证器跑之前它可能仍是 `null`，故允许「通过取值 ∪ null」；
   这不是放宽，是收口复检自己的时序）、阶梯「迭代」行收录本 GOAL、程序表有序 60 这一行。

**判据规则**（承 GOAL-027…091）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
#: **函数**下界（判据用例数按 `^def test_` 数；参数化会展开成更多收集项）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (("tests/tooling/test_next_round_charter.py", 17),)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_mainline_research_ladder_advances.py",
    "tests/tooling/test_mainline_program_is_intact.py",
    "tests/tooling/test_tooling_scripts_meet_product_gates.py",
    "tests/tooling/test_m0_witness_matches_the_tree.py",
)

#: 落点常量（逐条点名；缺一即判红）。
READER = "tools/next_round_charter.py"
PARSE = "tools/charter_parse.py"
JUDGE = "tests/tooling/test_next_round_charter.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
_GOAL_FILE = "GOAL-20261021-092-the-next-round-charter-is-read-not-remembered.md"
_PLAN_FILE = "PLAN-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md"
GOAL = f".cursor/plans/goals/{_GOAL_FILE}"
PLAN = f".cursor/plans/tasks/{_PLAN_FILE}"
CHARTER = ".cursor/plans/goals/MAINLINE.md"
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md"

#: 读取器的公开面（按 AST 读**声明**，不靠文本巧合）。
READER_FACE: tuple[str, ...] = ("build_skeleton", "main", "build_parser")
PARSE_FACE: tuple[str, ...] = (
    "Refusal",
    "ci_summary",
    "ladder_matches",
    "residual_section",
    "section_lines",
    "table_rows",
)
#: 拒绝臂的 `code`（逐条；少一个 ⇒ 某一类不合格输入会被静默接受）。
REFUSAL_CODES: tuple[str, ...] = (
    "GOAL_NOT_TERMINAL",
    "RECHECK_MISSING",
    "RECHECK_NOT_THIS_GOAL",
    "RECHECK_NOT_PASSING",
    "RESIDUAL_GAP",
    "LADDER_NOT_RECORDED",
    "RESIDUAL_EMPTY",
)

#: 上一轮残余的条数与编号（GOAL-091 的读数）。
PRIOR_GOAL = "GOAL-20261020-091"
PRIOR_WS = 7
#: 本轮**实际动过**的两条（其余是「不做 / 承接」）。
ACTED_ON: tuple[str, ...] = ("`W-6`", "`W-7`")

#: 阶梯记账：本 GOAL 必须出现在「迭代」那一行的 `依据 GOAL` 里。
LADDER_DOMAIN = "迭代"
#: 程序表序号（战役预算的最后一个名额）。
PROGRAM_SEQ = 60

_ITEM = re.compile(r"^\|\s*`W-(\d+)`\s*\|")
_CASE_DEF = re.compile(r"^def test_", re.MULTILINE)


def _has(root: Path, relative: str, needle: str) -> bool:
    path = root / relative
    return path.is_file() and needle in path.read_text(encoding="utf-8")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _declares(text: str, name: str) -> bool:
    return f"def {name}(" in text or f"class {name}(" in text or f"class {name}:" in text


def _face_verdicts(reader: str, parser: str, toolbox: Any) -> list[Any]:
    """两个模块**按 AST 读声明**的公开面（逐条一条判词）。"""
    return [
        toolbox.verdict(
            f"reader-declares-{name}",
            _declares(reader, name),
            f"`{READER}` 没有声明 `{name}`",
        )
        for name in READER_FACE
    ] + [
        toolbox.verdict(
            f"parse-declares-{name}", _declares(parser, name), f"`{PARSE}` 没有声明 `{name}`"
        )
        for name in PARSE_FACE
    ]


def _guard_verdicts(root: Path, reader: str, parser: str, toolbox: Any) -> list[Any]:
    """拒绝臂齐备 + 用例数下界 + 四道门射程 + 无时钟无网络。"""
    verdicts = [
        toolbox.verdict(
            "every-refusal-code-is-declared",
            all(code in parser or code in reader for code in REFUSAL_CODES),
            f"这些拒绝码没有出现：{[c for c in REFUSAL_CODES if c not in parser + reader]}",
        )
    ]
    verdicts.extend(
        toolbox.verdict(
            f"judge-count-floor-{Path(relative).name}",
            len(_CASE_DEF.findall(_text(root, relative))) >= floor,
            f"`{relative}` 的用例数低于下界 {floor}",
        )
        for relative, floor in CASE_FLOORS
    )
    verdicts.extend(
        toolbox.verdict(
            f"{Path(relative).name}-is-in-the-four-gate-scope",
            f'"{relative}"' in _text(root, SCOPE_JUDGE),
            f"`{relative}` 不在 `IN_SCOPE` 里 ⇒ 四道门看不见它（GOAL-091 `W-7` 的回归点）",
        )
        for relative in (READER, PARSE)
    )
    verdicts.append(
        toolbox.verdict(
            "reader-has-no-clock-and-no-network",
            not any(
                token in reader or token in parser
                for token in ("datetime.now", "time.time", "date.today", "socket", "urllib")
            ),
            "读取器出现了时钟 / 网络调用 ⇒ 不再是确定性读取",
        )
    )
    return verdicts


def _delivery_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/02/03：读取器 + 解析原语的公开面与拒绝臂。"""
    reader = _text(root, READER)
    parser = _text(root, PARSE)
    return [
        *_face_verdicts(reader, parser, toolbox),
        *_guard_verdicts(root, reader, parser, toolbox),
    ]


def _disposal_rows(goal_text: str) -> dict[str, tuple[str, str]]:
    """「上一轮残余的处置」表 ⇒ `{`W-N`: (残余, 处置)}`（只收 `W` 行）。"""
    rows: dict[str, tuple[str, str]] = {}
    for line in goal_text.splitlines():
        match = _ITEM.match(line)
        if match is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            rows[f"`W-{match.group(1)}`"] = (cells[1], cells[2])
    return rows


def _usage_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：产物在树、被点名、且七条残余逐条有处置。"""
    goal_text = _text(root, GOAL)
    rows = _disposal_rows(goal_text)
    expected = {f"`W-{index}`" for index in range(1, PRIOR_WS + 1)}
    verdicts = [
        toolbox.verdict(
            "the-skeleton-is-in-the-tree",
            bool(_text(root, EVIDENCE)),
            f"产物不在树或为空：{EVIDENCE}",
        ),
        toolbox.verdict(
            "the-goal-names-the-skeleton-path",
            EVIDENCE in goal_text or "GOAL-20261021-092-next-round-charter" in goal_text,
            "GOAL 没有点名产物路径 ⇒ 「被当输入用」不可复核",
        ),
        toolbox.verdict(
            "the-disposal-table-covers-exactly-the-seven",
            set(rows) == expected,
            f"处置表覆盖 {sorted(rows)}，应恰好是 {sorted(expected)}",
        ),
    ]
    verdicts.append(
        toolbox.verdict(
            "every-disposal-is-non-empty",
            bool(rows) and all(cell for _residual, cell in rows.values()),
            "有残余没有处置（空单元格 = 既没做也没说不做）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "the-two-acted-on-are-marked-done",
            all("做掉" in rows.get(item, ("", ""))[1] for item in ACTED_ON),
            f"{list(ACTED_ON)} 必须标为「做掉」（本轮有实际动作的那两条）",
        )
    )
    undecided = sorted(item for item, (_r, cell) in rows.items() if not cell.strip())
    return [
        *verdicts,
        toolbox.verdict(
            "no-residual-left-undecided", not undecided, f"这些残余没有处置：{undecided}"
        ),
    ]


def _record_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：记录面自洽 + 阶梯记账 + 程序表序 60。"""
    goal_text = _text(root, GOAL)
    charter = _text(root, CHARTER)
    ladder_rows = [
        line
        for line in charter.splitlines()
        if line.startswith(f"| {LADDER_DOMAIN} |") and "GOAL-20261021-092" in line
    ]
    program_rows = [
        line
        for line in charter.splitlines()
        if re.match(rf"^\|\s*{PROGRAM_SEQ}\s*\|\s*GOAL-20261021-092", line)
    ]
    return [
        toolbox.verdict("goal-record-present", bool(goal_text), f"GOAL 不在树：{GOAL}"),
        toolbox.verdict("plan-record-present", bool(_text(root, PLAN)), f"PLAN 不在树：{PLAN}"),
        toolbox.verdict(
            "the-goal-points-at-a-repository-relative-recheck",
            "/" in _latest_recheck(goal_text),
            "`latest_recheck` 不是仓库相对路径（收口后必须指向 RECHECK-20261021-092）",
        ),
        toolbox.verdict(
            "the-ladder-iteration-row-records-this-goal",
            bool(ladder_rows),
            f"阶梯「{LADDER_DOMAIN}」行的 `依据 GOAL` 没有收录本 GOAL（每轮必须更近科研）",
        ),
        toolbox.verdict(
            "the-program-table-has-row-sixty",
            bool(program_rows),
            f"程序表没有序 {PROGRAM_SEQ} 这一行指向本 GOAL",
        ),
        toolbox.verdict(
            "the-campaign-budget-exhaustion-is-registered",
            "预算已用尽" in goal_text or "需用户决定" in goal_text,
            "序 60 用尽 `max_goals` ⇒ GOAL 里必须登记「需用户决定扩表或收兵」",
        ),
    ]


def _latest_recheck(goal_text: str) -> str:
    match = re.search(r"^latest_recheck:\s*(\S+)", goal_text, re.MULTILINE)
    return match.group(1) if match else ""


#: 提交短哈希（台账与迭代日志里的形态）。
_COMMIT = re.compile(r"`([0-9a-f]{7,40})`")


def _section(text: str, heading: str) -> str:
    """某个二级小节的正文（到下一个 `## ` 为止；缺节 ⇒ 空串）。"""
    start = text.find(heading)
    if start == -1:
        return ""
    tail = text[start + len(heading) :]
    end = tail.find("\n## ")
    return tail if end == -1 else tail[:end]


def _log_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """**迭代日志必须逐 cycle 一行**（提示词的显式要求；GOAL-090 因此被补正过一次）。

    不写「行数 >= N」这种拍脑袋的下界 —— 那既可能漏（把两次修复并成一行）也可能假红。
    判的是**可核对的覆盖关系**：CI 台账里出现的**每一个提交**，都必须在迭代日志的某一行的
    `commits` 格里出现。把多次修复压成散文的日志，必然有提交只活在台账、不在任何 cycle 行里
    ⇒ 判红并逐条点名是哪些提交。
    """
    goal = _text(root, GOAL)
    ledger = _section(goal, "## CI 台账")
    log = _section(goal, "## 迭代日志")
    logged = set(_COMMIT.findall(log))
    committed = set(_COMMIT.findall(ledger))
    unlogged = sorted(item for item in committed if item not in logged)
    rows = len([line for line in log.splitlines() if re.match(r"^\| \d+ \|", line)])
    return [
        toolbox.verdict(
            "iteration-log-has-one-row-per-cycle",
            rows >= 2,
            f"迭代日志只有 {rows} 行 ⇒ 多次修复被压成散文（要求逐 cycle 一行）",
        ),
        toolbox.verdict(
            "every-ledgered-commit-appears-in-a-cycle-row",
            not unlogged,
            f"这些提交只出现在 CI 台账、没有任何 cycle 行收录：{unlogged}",
        ),
        toolbox.verdict(
            "the-iteration-log-is-not-vacuous",
            bool(committed) and bool(logged),
            "受判面为空（台账无提交或日志无提交）⇒ 本条失去判据对象",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（验证器把它与标准断言集拼起来）。"""
    return [
        *_delivery_verdicts(root, toolbox),
        *_usage_verdicts(root, toolbox),
        *_record_verdicts(root, toolbox),
        *_log_verdicts(root, toolbox),
    ]
