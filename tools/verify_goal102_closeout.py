#!/usr/bin/env python3
"""GOAL-20261031-102 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…101 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件只写本 GOAL 特有的**记录面**
（EC 终态、子计划 / 复检在位、阶梯与进展 / 修订记账、残余与「不判什么」逐条明写），
产品面（supersedes / 改稿闭环 / 投稿包 / 期刊闭集 / 登记面）收在
`tools/goal102_closeout_assertions.py`。

**自指**：本验证器**必须加载自己那份**断言集（`goal102_closeout_assertions.py`），
由 `self-loads-its-own-assertions`（按**本文件名**推应载文件名）钉住。

**本轮最重要的一条断言**：`ladder-recheck-next-level-verbatim` —— 阶梯「复检」行的
`下一级` 必须**逐字保持**「判词改写了下一轮的计划/立题」。本轮做的是「**作者按编辑
要求改了稿**」（artifact 父指针让它可判），不是「**判词内容驱动了改什么**」—— 两者
是不同的格，把它改写成已判属于伪造验证证据。

用法：`uv run --frozen --no-sync python -B tools/verify_goal102_closeout.py --root .
--verdict-only`；判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会
（正确地）拒绝）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, cast

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal102_closeout.py"
ASSERTIONS = "tools/goal102_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261031-102-submission-package-and-revision-closure.md"
RECHECK = ".cursor/plans/rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md"
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261031-102-submission-package-and-revision-closure.md",
)
RECHECKS: tuple[str, ...] = (RECHECK,)
ALL_PLAN = ".cursor/plans/ALL_PLAN.md"

#: 本轮残余（GOAL-101 的 W-1…W-6 **逐条处置** + 本轮新发现的 W-7）。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "`W-1`",
    "`W-2`",
    "`W-3`",
    "`W-4`",
    "`W-5`",
    "`W-6`",
    "`W-7`",
)
#: 未覆盖范围（逐条明写）。
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`", "`U-3`")
#: 声称边界（不得宣称的两件事）。
CLAIM_BOUNDARIES: tuple[str, ...] = ("`R-1`", "`R-2`")
#: 必须明写的三件「不粉饰」事实。
HONEST_GAPS: tuple[tuple[str, str], ...] = (
    ("w1-names-the-strong-verdict-as-carried", "承接为长期路线"),
    ("w6-names-the-ledger-rows-as-additions", "不动任何既有行"),
    ("w7-names-the-reorder-as-content-free", "零内容改动"),
)

RECHECK_ID = "RECHECK-20261031-102"
PROGRAM_SEQ = 70
LADDER_GOAL = "GOAL-20261031-102"
LADDER_DOMAIN = "| 复检 |"
#: 本轮在阶梯里写明的推进格（措辞必须逐字在场）。
LADDER_STEP_MARKERS: tuple[str, ...] = ("改稿闭环（artifact 父指针）",)
#: 「复检」行的 `下一级` 必须**逐字保持**（不许改写成已判）。
LADDER_NEXT_LEVEL = "判词改写了下一轮的计划/立题"


def _load_toolbox() -> Any:
    """按路径加载同目录的工具集（`tools/` 不是包 ⇒ 静态 import 不可用）。"""
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal102_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal102_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（按**本文件名**推应载文件名）。"""
    path = Path(__file__).resolve().parent / "goal102_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal102_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal102_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> Any | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal102_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal102_standard"] = module
    spec.loader.exec_module(module)
    return module


def ec_status(goal_text: str, ec_id: str) -> str:
    """从 GOAL 正文取某 EC 的 `status:`（按 EC 块定位，不靠全局搜索）。"""
    marker = f"  - id: {ec_id}\n"
    index = goal_text.find(marker)
    if index == -1:
        return "MISSING"
    tail = goal_text[index:]
    stop = tail.find("\n  - id: ")
    block = tail[: stop if stop != -1 else len(tail)]
    for line in block.splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "MISSING"


def _self_loading_verdict() -> Any:
    """自指：本验证器加载的是它自己那份断言集（按本文件名推）。"""
    digits = "".join(ch for ch in Path(__file__).name.split("_")[1] if ch.isdigit())
    expected = f"goal{digits}_closeout_assertions.py"
    source = Path(__file__).read_text(encoding="utf-8")
    loaded_own = f'"{expected}"' in source.split("def _load_assertions")[1]
    return TOOLBOX.verdict(
        "self-loads-its-own-assertions",
        loaded_own,
        "" if loaded_own else f"加载的不是本轮断言集（应为 {expected}）",
    )


def _ladder_verdicts(root: Path) -> list[Any]:
    """阶梯行（收录本 GOAL / 写明改稿闭环 / `下一级` 逐字未动）+ 程序表序 70。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith(LADDER_DOMAIN)]
    recorded = [line for line in rows if LADDER_GOAL in line]
    joined = " ".join(recorded)
    report_rows = [line for line in charter.splitlines() if line.startswith("| 报告 |")]
    report_recorded = [line for line in report_rows if LADDER_GOAL in line]
    return [
        TOOLBOX.verdict(
            "ladder-recheck-row-exists", bool(rows), "宪章阶梯里必须有「复检」域那一行"
        ),
        TOOLBOX.verdict(
            "ladder-recheck-records-this-goal",
            bool(recorded),
            "「复检」域那一行的「依据 GOAL」必须收录本 GOAL",
        ),
        TOOLBOX.verdict(
            "ladder-recheck-names-the-revision-closure",
            all(marker in joined for marker in LADDER_STEP_MARKERS),
            ",".join(marker for marker in LADDER_STEP_MARKERS if marker not in joined),
        ),
        TOOLBOX.verdict(
            "ladder-recheck-next-level-verbatim",
            LADDER_NEXT_LEVEL in joined,
            "`下一级` 必须逐字保持「判词改写了下一轮的计划/立题」—— 本轮是「作者改稿可判」，"
            "不是「判词内容驱动改什么」，改写它属于伪造验证证据",
        ),
        TOOLBOX.verdict(
            "ladder-report-records-this-goal",
            bool(report_recorded),
            "「报告」域那一行也应收录本 GOAL（投稿包五件制品属报告/投稿域）",
        ),
        TOOLBOX.verdict(
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
    ]


def _progress_verdicts(root: Path) -> list[Any]:
    """进展记录的三条（收录本 GOAL / 指向本轮复检 / 插在最上面）。"""
    progress_rows = TOOLBOX.progress_rows(root, LADDER_GOAL)
    progress = TOOLBOX.progress_context(root, LADDER_GOAL)
    return [
        TOOLBOX.verdict(
            "progress-records-this-goal",
            bool(progress_rows),
            "宪章「进展记录」必须有本 GOAL 的一行（EC-06 契约逐字要求）",
        ),
        TOOLBOX.verdict(
            "progress-row-names-the-recheck",
            any(RECHECK_ID in line for line in progress_rows),
            "进展记录那一行的 RECHECK 列必须指向本轮的复检文件",
        ),
        TOOLBOX.verdict(
            "progress-row-is-newest-when-inserted",
            bool(progress_rows) and _rows_above_are_not_older(progress),
            "进展记录必须插在**最上面**（判据取 progress[0]，而该表不按日期排序）",
        ),
    ]


def _rows_above_are_not_older(progress: str) -> bool:
    """本 GOAL 的行**上方**没有更早的行（= 插入时它就在最上面）。"""
    rows: list[tuple[str, str]] = []
    for line in progress.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0].startswith("2026-"):
            rows.append((cells[0], cells[1]))
    for index, (date, goal) in enumerate(rows):
        if goal != LADDER_GOAL:
            continue
        return all(other_date >= date for other_date, _goal in rows[:index])
    return False


def _revision_row_verdicts(root: Path) -> list[Any]:
    """修订记录：本 GOAL 那一行在场（5 格、表内连续由宪章判据另判）。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith("| 2026-11-01 | 70（新增）")]
    ok = bool(rows) and rows[0].strip().startswith("|") and len(rows[0].strip("|").split("|")) == 5
    return [
        TOOLBOX.verdict(
            "revision-row-records-this-goal",
            ok,
            "宪章「修订记录」必须有本 GOAL 的一行（5 格）",
        ),
    ]


def _ec_status_verdicts(goal: str) -> list[Any]:
    """EC 终态：六条全 PASS（收口复检跑时六件交付都已在树）。"""
    verdicts: list[Any] = []
    for index in range(1, 7):
        status = ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    return verdicts


def _scope_verdicts(goal: str) -> list[Any]:
    """残余 / 未覆盖 / 声称边界逐条明写 + 三件「不粉饰」的事实。"""
    verdicts: list[Any] = []
    missing_uncovered = [item for item in UNCOVERED_MARKERS if item not in goal]
    verdicts.append(
        TOOLBOX.verdict(
            "uncovered-scope-enumerated", not missing_uncovered, ",".join(missing_uncovered)
        )
    )
    missing_residual = [item for item in RESIDUAL_MARKERS if item not in goal]
    verdicts.append(
        TOOLBOX.verdict("residuals-enumerated", not missing_residual, ",".join(missing_residual))
    )
    missing_claims = [item for item in CLAIM_BOUNDARIES if item not in goal]
    verdicts.append(
        TOOLBOX.verdict("claim-boundaries-enumerated", not missing_claims, ",".join(missing_claims))
    )
    for name, marker in HONEST_GAPS:
        verdicts.append(
            TOOLBOX.verdict(
                name,
                marker in goal,
                f"残余节必须明写「{marker}」（不粉饰是判据的一部分）",
            )
        )
    return verdicts


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、阶梯 / 进展 / 修订记账、残余逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict(
            "goal-declares-six-ecs",
            all(f"id: EC-0{n}" in goal for n in range(1, 7)),
        ),
        _self_loading_verdict(),
        *_ladder_verdicts(root),
        *_progress_verdicts(root),
        *_revision_row_verdicts(root),
        *_ec_status_verdicts(goal),
    ]
    for relative in (*CHILD_PLANS, *RECHECKS, ALL_PLAN):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    all_plan = TOOLBOX.text(root, ALL_PLAN)
    verdicts.append(
        TOOLBOX.verdict(
            "child-plan-registered-in-all-plan",
            "PLAN-20261031-102" in all_plan,
            "子计划必须登记进 ALL_PLAN.md 的 Active 表",
        )
    )
    verdicts.append(
        TOOLBOX.verdict(
            "goal-latest-recheck-resolves",
            RECHECK in goal and TOOLBOX.tree(root, RECHECK).is_file(),
            "GOAL frontmatter 的 latest_recheck 必须指向本轮复检文件且它在树",
        )
    )
    verdicts.extend(_scope_verdicts(goal))
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261031-102 closeout recheck")
    parser.add_argument("--root", default=".", help="tree root to verify")
    parser.add_argument("--verdict-only", action="store_true", help="print verdicts only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    standard = load_standard(root)
    verdicts: list[Any] = []
    if standard is None:
        verdicts.append(TOOLBOX.verdict("standard-assertions-present", False, f"{STANDARD} 不在树"))
    else:
        standard_verdicts = getattr(standard, "standard_verdicts", None)
        assert callable(standard_verdicts), "标准断言集缺少 standard_verdicts"
        cast("Callable[[Path], Iterable[Any]]", standard_verdicts)
        verdicts.extend(standard_verdicts(root))
    verdicts.extend(_load_assertions().assertion_verdicts(root, TOOLBOX))
    verdicts.extend(record_verdicts(root))
    failures = [verdict for verdict in verdicts if not verdict.ok]
    for verdict in verdicts:
        if verdict.ok:
            print(f"PASS {verdict.name}")
        else:
            print(f"FAIL {verdict.name} -> {verdict.detail}")
    if not args.verdict_only:
        print(f"SUMMARY total={len(verdicts)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
