#!/usr/bin/env python3
"""GOAL-20261030-101 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…100 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件只写本 GOAL 特有的**记录面**
（EC 终态、子计划 / 复检在位、阶梯与进展记账、残余与「不判什么」逐条明写），产品面
（三条品质判据 / 负判扫描补主文件 / run 归属校验器 / 两条方法纪律）收在
`tools/goal101_closeout_assertions.py`。

**自指**：本验证器**必须加载自己那份**断言集（`goal101_closeout_assertions.py`），
由 `self-loads-its-own-assertions`（按**本文件名**推应载文件名）钉住 —— GOAL-078 曾自洽地
加载上一轮那份，自有断言从未运行。

**时间口径**：`EC-05` 在**本收口复检跑之前**仍是待办（它的判词就是本文件产出的），
所以 EC-05 那条断言接受「达成 ∪ 待办」两种取值 —— **不是**放宽，是**时序**。

**本轮最重要的一条断言**：`ladder-report-does-not-claim-the-strong-verdict`
—— 阶梯「报告」行的 `下一级` 必须**逐字保持**「叙述质量与事实一致性可判」。本轮落地的
只是**弱口径**（三条必要不充分判据）；把它改写成已达成属于伪造验证证据。

用法：`uv run --frozen --no-sync python -B tools/verify_goal101_closeout.py
--root . --verdict-only`；
判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, cast


def _load_toolbox() -> object:
    """按**路径**加载同目录的工具集（`tools/` 不是包 ⇒ 静态 import 不可用）。"""
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal101_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal101_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal101_closeout.py"
ASSERTIONS = "tools/goal101_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261030-101-narrative-quality-and-verifier-coverage.md"
RECHECK = (
    ".cursor/plans/rechecks/"
    "RECHECK-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md"
)
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md",
)
RECHECKS: tuple[str, ...] = (RECHECK,)
ALL_PLAN = ".cursor/plans/ALL_PLAN.md"

README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
    ALL_PLAN,
)

#: 本轮残余（逐条明写）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-2`", "`W-3`", "`W-4`", "`W-5`", "`W-6`")
#: 未覆盖范围（逐条明写）。
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`", "`U-3`")
#: 声称边界（不得宣称的两件事）。
CLAIM_BOUNDARIES: tuple[str, ...] = ("`R-1`", "`R-2`")
#: 必须明写为「弱口径」的那件事（本轮最容易夸大的一处）。
HONEST_GAPS: tuple[tuple[str, str], ...] = (
    ("w-1-names-the-strong-verdict-as-unjudged", "叙述质量的强口径仍未判"),
    ("w-4-names-the-ledger-findings-unchanged", "本轮不改写历史台账"),
    ("r-3-names-the-criteria-as-weak", "三条判据是弱判据"),
)

RECHECK_ID = "RECHECK-20261030-101"
PROGRAM_SEQ = 69
LADDER_GOAL = "GOAL-20261030-101"
LADDER_DOMAIN = "| 报告 |"
#: 本轮在阶梯里写明的推进格（弱口径 —— 措辞必须逐字在场）。
LADDER_STEP_MARKERS: tuple[str, ...] = ("叙述质量弱口径成立", "引用不是无关", "节非空洞")
#: `下一级` 必须**逐字保持**（不许改写成已达成）。
LADDER_NEXT_LEVEL = "叙述质量与事实一致性可判"


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（`tools/` 不是包 ⇒ 静态 import 不行）。"""
    path = Path(__file__).resolve().parent / "goal101_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal101_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal101_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal101_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal101_standard"] = module
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
    """自指：本验证器**加载的是它自己那份**断言集（按**本文件名**推，不写死）。"""
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
    """阶梯行（存在 / 收录本 GOAL / 写明弱口径 / `下一级` 未冒认）+ 进展记录行。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith(LADDER_DOMAIN)]
    recorded = [line for line in rows if LADDER_GOAL in line]
    joined = " ".join(recorded)
    verdicts: list[Any] = [
        TOOLBOX.verdict("ladder-report-row-exists", bool(rows), "宪章阶梯里必须有「报告」域那一行"),
        TOOLBOX.verdict(
            "ladder-report-records-this-goal",
            bool(recorded),
            "「报告」域那一行的「依据 GOAL」必须收录本 GOAL（每轮必须更近科研）",
        ),
        TOOLBOX.verdict(
            "ladder-report-names-the-weak-verdict",
            all(marker in joined for marker in LADDER_STEP_MARKERS),
            ",".join(marker for marker in LADDER_STEP_MARKERS if marker not in joined),
        ),
        TOOLBOX.verdict(
            "ladder-report-does-not-claim-the-strong-verdict",
            LADDER_NEXT_LEVEL in joined,
            "`下一级` 必须逐字保持「叙述质量与事实一致性可判」—— 本轮只做了弱口径，"
            "把它改写成已达成属于伪造验证证据",
        ),
    ]
    verdicts.extend(_progress_verdicts(root))
    return verdicts


def _progress_verdicts(root: Path) -> list[Any]:
    """进展记录的三条（收录本 GOAL / 指向本轮复检 / 插在最上面）。"""
    # **活跃面或归档**（本 GOAL 自己修的读取面：共享 helper）。
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


def _progress_rows(progress: str) -> list[tuple[str, str]]:
    """进展记录表 → `[(日期, GOAL)]`（按表内顺序）。"""
    rows: list[tuple[str, str]] = []
    for line in progress.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0].startswith("2026-"):
            rows.append((cells[0], cells[1]))
    return rows


def _rows_above_are_not_older(progress: str) -> bool:
    """本 GOAL 的行**上方**没有更早的行（= 插入时它就在最上面）。

    **不是**「它永远是第一行」：之后每一轮都会在它上面插自己的行 ⇒ 断言「永久居首」等于
    要求后续 GOAL 不许记账。真正的机械含义是：它上方每一行的日期都不早于它。
    """
    rows = _progress_rows(progress)
    for index, (date, goal) in enumerate(rows):
        if goal != LADDER_GOAL:
            continue
        return all(other_date >= date for other_date, _goal in rows[:index])
    return False


def _ec_status_verdicts(goal: str) -> list[Any]:
    """EC 终态：除 EC-05 外**逐条必须 PASS**（EC-05 是时序，见模块 docstring）。"""
    verdicts: list[Any] = []
    for index in (1, 2, 3, 4, 6):
        status = ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    ec05 = ec_status(goal, "EC-05")
    verdicts.append(TOOLBOX.verdict("goal-ec05-status", ec05 in {"PASS", "PENDING"}, ec05))
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
    """记录面：EC 终态、子计划 / 复检在位、阶梯记账、残余与未覆盖逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    verdicts: list[Any] = [
        TOOLBOX.verdict(
            # 本 GOAL 声明**六个** EC（EC-01…EC-06）；GOAL-023…100 的验证器写的是 `range(1, 8)`
            # 七条 —— 那是当时的契约，此处**照本 GOAL 的实际条数**判（多写一条会恒红）。
            "goal-declares-six-ecs",
            all(f"id: EC-0{n}" in goal for n in range(1, 7)),
        ),
        _self_loading_verdict(),
        *_ladder_verdicts(root),
        TOOLBOX.verdict(
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
        *_ec_status_verdicts(goal),
    ]
    for relative in (*CHILD_PLANS, *RECHECKS, *README_AND_PRIOR):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    verdicts.extend(_scope_verdicts(goal))
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261030-101 closeout recheck")
    parser.add_argument("--root", default=".", help="tree root to verify")
    parser.add_argument("--verdict-only", action="store_true", help="print verdicts only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    standard = load_standard(root)
    verdicts: list[Any] = []
    if standard is None:
        verdicts.append(TOOLBOX.verdict("standard-assertions-present", False, f"{STANDARD} 不在树"))
    else:
        standard_verdicts = getattr(standard, "standard_verdicts", None)
        assert callable(standard_verdicts), "标准断言集缺少 standard_verdicts"
        cast(Callable[[Path], Iterable[Any]], standard_verdicts)
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
