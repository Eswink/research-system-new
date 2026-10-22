#!/usr/bin/env python3
"""GOAL-20261022-094 收口复检的**本轮特有断言集**（EC-01…EC-04）。

与 GOAL-023…093 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由 `tools/closeout_recheck_assertions.standard_verdicts`
承担；本文件**只写本 GOAL 特有的断言**。

两条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/02/03 的元缺陷面**：跨 GOAL 台账判据**在树**、**按 AST 声明**了它的两个受判原语
   （`ledger_problems` / `_terminal_goals_in_scope`）、**自己遍历** GOAL 文件（不靠清单登记、
   不靠验证器传参）、带祖父条款常量、**按列名**定位 `commits` 列、四种空真形态分别点名；
   GOAL-093 的台账**七行 = 七个提交**（本轮补记的物证）。
2. **EC-04 的报告面**：叙述模块与执行缝**在树**；事实表标题与叙述四键**逐字**在树；
   数字禁令走 `unicodedata` 的 `Nd` 判定；`created_by` 读 `narrative.author`（与元数据同源）；
   `narrator` 是**可选**缝；产品闭包 `narrative_runner` 在树。

**判据规则**（承 GOAL-027…093）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 用例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/tooling/test_goal_ledger_covers_every_commit.py", 8),
    ("tests/application/test_report_narrative.py", 12),
    ("tests/application/test_report_narrative_on_the_product_path.py", 6),
    ("tests/application/test_report_task_narrator_behaviour.py", 8),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_mainline_research_ladder_advances.py",
    "tests/tooling/test_mainline_program_is_intact.py",
    "tests/tooling/test_mainline_archive_is_continuous.py",
    "tests/tooling/test_tooling_scripts_meet_product_gates.py",
    "tests/tooling/test_m0_witness_matches_the_tree.py",
    "tests/tooling/test_python_source_limits.py",
)

#: 落点常量（逐条点名；缺一即判红）。
LEDGER_JUDGE = "tests/tooling/test_goal_ledger_covers_every_commit.py"
NARRATIVE = "packages/application/deliverable/report_narrative.py"
NARRATIVE_TASK = "packages/application/run_orchestration/report_narrative_task.py"
REPORT_TASK = "packages/application/run_orchestration/report_task.py"
REPORT_SUPPORT = "services/api/report_support.py"
REPORT_METADATA = "packages/application/deliverable/research_report.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
#: 本轮的 `tools/` 交付件（**只有**这些要进四道门射程；其余落在 `PRODUCT_ROOTS`）。
TOOL_SCRIPTS: tuple[str, ...] = (
    "tools/verify_goal094_closeout.py",
    "tools/goal094_closeout_assertions.py",
)

GOAL_093 = ".cursor/plans/goals/GOAL-20261022-093-the-review-verdict-drives-the-next-round.md"
GOAL = ".cursor/plans/goals/GOAL-20261022-094-goal-ledger-judge-and-the-model-written-report.md"
CHARTER = ".cursor/plans/goals/MAINLINE.md"
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261022-094-next-round-charter.md"

#: 跨 GOAL 判据必须**按 AST 声明**的两个原语（唯一谓词 + 受判面推导）。
LEDGER_FACE: tuple[str, ...] = ("ledger_problems", "_terminal_goals_in_scope")

#: 祖父条款的两个常量及其取值（改它们 = 改受判面，必须逐条申报）。
CUTOFF_SEQ = 61
CUTOFF_DATE = "2026-10-22"

#: GOAL-093 本轮补记的三个提交（台账与 cycle 行都必须有）。
BACKFILLED: tuple[str, ...] = ("ff7546d7", "c626aced", "2998649d")
#: 补记后 GOAL-093 台账的行数（7 行 = 本轮实际的 7 个提交）。
GOAL_093_LEDGER_ROWS = 7

#: 叙述的四键与事实表标题（**逐字**；判据按它们定位两块面）。
NARRATIVE_KEYS: tuple[str, ...] = ("question", "evidence", "experiment", "review")
FACT_TABLE_HEADING = "## 5. 事实表（数字的唯一来源）"
DIGIT_CATEGORY = '"Nd"'

#: 宪章记账。
LADDER_DOMAIN = "| 报告 |"
LADDER_GOAL = "GOAL-20261022-094"
PROGRAM_SEQ = 62

_CASE_DEF = re.compile(r"^def test_", re.MULTILINE)
_LEDGER_ROW = re.compile(r"^\| `[0-9a-f]{7,8}` \|", re.MULTILINE)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _case_count(text: str) -> int:
    return len(_CASE_DEF.findall(text))


def _ledger_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/02：跨 GOAL 判据在树、自己遍历、带祖父条款、只认 `commits` 列。"""
    judge = _text(root, LEDGER_JUDGE)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-cross-goal-ledger-judge-is-in-the-tree",
            bool(judge.strip()),
            f"跨 GOAL 判据不在树：{LEDGER_JUDGE}",
        )
    ]
    verdicts.extend(
        toolbox.verdict(
            f"ledger-judge-declares-{name}",
            f"def {name}(" in judge,
            f"`{LEDGER_JUDGE}` 没有声明 `{name}`（唯一谓词 / 受判面推导）",
        )
        for name in LEDGER_FACE
    )
    verdicts.extend([
        toolbox.verdict(
            "the-judge-walks-the-goal-directory-itself",
            'glob("GOAL-*.md")' in judge,
            "判据必须**自己遍历** GOAL 文件（不靠清单登记、不靠验证器传参）—— 那正是失效点",
        ),
        toolbox.verdict(
            "the-grandfather-cutoff-is-declared",
            f"_CUTOFF_SEQ = {CUTOFF_SEQ}" in judge and f'_CUTOFF_DATE = "{CUTOFF_DATE}"' in judge,
            f"祖父条款必须是显式常量（序 {CUTOFF_SEQ} / {CUTOFF_DATE}）",
        ),
        toolbox.verdict(
            "the-judge-only-counts-the-commits-column",
            '_column(header, "commits"' in judge,
            "判据必须按**列名**定位 `commits` 列（同一行别格出现不算收录）",
        ),
        toolbox.verdict(
            "the-empty-cases-are-named-separately",
            all(
                needle in judge
                for needle in ("一个提交都没有", "没有反引号包裹的提交哈希", "没有数据行")
            ),
            "空台账 / 台账行没写提交 / 日志无数据行必须**分别**点名（空真不算通过）",
        ),
    ])
    return verdicts


def _backfill_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：GOAL-093 在新判据下通过（补记的三个提交 + 台账行数 + cycle 行）。"""
    goal_093 = _text(root, GOAL_093)
    ledger = goal_093.split("## CI 台账", 1)[1] if "## CI 台账" in goal_093 else ""
    rows = len(_LEDGER_ROW.findall(ledger))
    verdicts = [
        toolbox.verdict(
            "goal-093-ledger-has-one-row-per-commit",
            rows == GOAL_093_LEDGER_ROWS,
            f"GOAL-093 的 CI 台账有 {rows} 行，本轮应恰好 {GOAL_093_LEDGER_ROWS} 行",
        )
    ]
    verdicts.extend(
        toolbox.verdict(
            f"goal-093-ledgers-{commit}", commit in ledger, f"`{commit}` 没进 GOAL-093 台账"
        )
        for commit in BACKFILLED
    )
    log = (
        goal_093.split("## 迭代日志", 1)[1].split("\n## ", 1)[0]
        if "## 迭代日志" in goal_093
        else ""
    )
    verdicts.extend(
        toolbox.verdict(
            f"goal-093-cycle-rows-carry-{commit}",
            commit in log,
            f"`{commit}` 没有出现在 GOAL-093 的任何 cycle 行里",
        )
        for commit in BACKFILLED
    )
    return verdicts


def _module_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 的前半：叙述模块 / 执行缝 / 两块面标题 / 数字禁令 / 归因同源。"""
    module = _text(root, NARRATIVE)
    runner = _text(root, NARRATIVE_TASK)
    task = _text(root, REPORT_TASK)
    return [
        toolbox.verdict(
            "the-narrative-module-is-in-the-tree",
            bool(module.strip()),
            f"叙述模块不在树：{NARRATIVE}",
        ),
        toolbox.verdict(
            "the-narrative-execution-seam-is-in-the-tree",
            "def narrate(" in runner and "def llm_narrator(" in runner,
            f"`{NARRATIVE_TASK}` 必须声明 `narrate` / `llm_narrator`",
        ),
        toolbox.verdict(
            "the-fact-table-heading-is-verbatim",
            f'FACT_TABLE_HEADING = "{FACT_TABLE_HEADING}"' in module,
            "事实表标题必须**逐字**在树（判据按它定位两块面）",
        ),
        toolbox.verdict(
            "all-four-narrative-keys-are-declared",
            all(f'"{key}"' in module for key in NARRATIVE_KEYS),
            f"叙述四键必须齐备：{NARRATIVE_KEYS}",
        ),
        toolbox.verdict(
            "the-digit-ban-uses-the-unicode-category",
            f"unicodedata.category(char) == {DIGIT_CATEGORY}" in module,
            "数字禁令必须按 Unicode 类别 `Nd` 判（手写正则数位表会漏全角 / 其他文种数位）",
        ),
        toolbox.verdict(
            "the-narrator-slot-is-optional-and-explicitly-dispatched",
            "narrator: Any | None = None" in task and "narrate(inputs, deps.narrator)" in task,
            "`ReportTaskDeps.narrator` 必须是**可选**缝，且由 `_body` 显式分派（不猜）",
        ),
        toolbox.verdict(
            "the-artifact-author-comes-from-the-admission",
            "narrative.author if narrative is not None" in task,
            "`created_by` 必须读 `narrative.author`（与元数据同源，不各读一份）",
        ),
    ]


def _surface_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 的后半：元数据块 / 产品闭包 / 四道门射程 / 用例下界 / 既有判据在位。"""
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-metadata-carries-the-narrative-block",
            '"narrative"' in _text(root, REPORT_METADATA),
            "元数据必须带 `narrative` 块（作者 / 返回名 / 摘要）",
        ),
        toolbox.verdict(
            "the-product-closure-is-declared",
            "def narrative_runner(" in _text(root, REPORT_SUPPORT),
            f"`{REPORT_SUPPORT}` 必须声明产品闭包 `narrative_runner`",
        ),
    ]
    for relative, floor in CASE_FLOORS:
        count = _case_count(_text(root, relative))
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}",
                count >= floor,
                f"{relative} 的判据用例数 {count} 低于下界 {floor}",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(
                f"prior-judge-{Path(relative).stem}",
                (root / relative).is_file(),
                f"本轮引用的既有判据必须仍在树：{relative}",
            )
        )
    # **只对 `tools/` 下的脚本**断言四道门射程：`packages/` 与 `tests/` 本就在
    # `PRODUCT_ROOTS` 里（`test_python_source_limits` 与 m0 的产品门直接覆盖），
    # 把它们也要求进 `IN_SCOPE` 是**范畴错误**（`IN_SCOPE` 的定义就是「补 `tools/` 的洞」）。
    scope = _text(root, SCOPE_JUDGE)
    for relative in TOOL_SCRIPTS:
        verdicts.append(
            toolbox.verdict(
                f"{Path(relative).name}-is-in-the-four-gate-scope",
                f'"{relative}"' in scope,
                f"`{relative}` 不在 `IN_SCOPE` 里 ⇒ 四道门看不见它（GOAL-092 `W-7` 的回归点）",
            )
        )
    return verdicts


def _record_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05 的记录面：阶梯「报告」行收录本 GOAL、程序表有序 62、读取器产物在树。"""
    charter = _text(root, CHARTER)
    goal = _text(root, GOAL)
    return [
        toolbox.verdict(
            "the-ladder-report-row-records-this-goal",
            any(
                line.startswith(LADDER_DOMAIN) and LADDER_GOAL in line
                for line in charter.splitlines()
            ),
            "阶梯「报告」行的 `依据 GOAL` 没有收录本 GOAL（每轮必须更近科研）",
        ),
        toolbox.verdict(
            "the-program-table-has-row-sixty-two",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
        toolbox.verdict(
            "the-evidence-skeleton-is-in-the-tree",
            bool(_text(root, EVIDENCE).strip()),
            f"读取器产物不在树：{EVIDENCE}",
        ),
        toolbox.verdict(
            "the-goal-names-the-skeleton",
            "GOAL-20261022-094-next-round-charter" in goal,
            "GOAL 必须点名读取器产物（自举的物证）",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """全部本轮特有断言（收口验证器只调这一个入口）。"""
    return [
        *_ledger_verdicts(root, toolbox),
        *_backfill_verdicts(root, toolbox),
        *_module_verdicts(root, toolbox),
        *_surface_verdicts(root, toolbox),
        *_record_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
