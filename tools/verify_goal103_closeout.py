#!/usr/bin/env python3
"""GOAL-20261101-103 收口复检（EC-07）：**标准断言集 + 本轮断言集 + 记录面**。

与 GOAL-023…102 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`。本文件只写本 GOAL 特有的
**记录面**（八条 EC 终态、子计划 / 复检在位、阶梯与进展 / 修订记账、残余与未覆盖逐条
明写）；产品面（相级事件 / 读面补字段 / 前端两件 / retmax / §7 论证 / 早期一代射程）
收在 `tools/goal103_closeout_assertions.py`。

**自指**：本验证器**必须加载自己那份**断言集（`goal103_closeout_assertions.py`），
由 `self-loads-its-own-assertions`（按**本文件名**推应载文件名）钉住。

**本轮最重要的一条断言**：`ladder-next-level-not-claimed` —— §7 的论证**不**等于
强口径已判。阶梯对应行的 `下一级` 若被改写成「叙述质量已可判」，本验证器判红：
论证给出的是「三项只能人评 + 两项可机械判但未实现」，把它写成已判属于**伪造验证证据**。

用法：`uv run --frozen --no-sync python -B tools/verify_goal103_closeout.py --root .
--verdict-only`；判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, cast

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal103_closeout.py"
ASSERTIONS = "tools/goal103_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261101-103-phase-events-and-frontend-visible-chain.md"
RECHECK = ".cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md"
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261101-103-phase-events-and-frontend-visible-chain.md",
)
RECHECKS: tuple[str, ...] = (RECHECK,)
ALL_PLAN = ".cursor/plans/ALL_PLAN.md"

#: 本轮残余（**没做到**的那部分，逐条明写；不得留空）。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "`W-1`",
    "`W-2`",
    "`W-3`",
    "`W-4`",
    "`W-5`",
)
#: 未覆盖范围（逐条明写）。
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`", "`U-3`")
#: 声称边界（不得宣称的两件事）。
CLAIM_BOUNDARIES: tuple[str, ...] = ("`R-1`", "`R-2`")

RECHECK_ID = "RECHECK-20261101-103"
PROGRAM_SEQ = 71
LADDER_GOAL = "GOAL-20261101-103"
#: 阶梯行以「域」开头（`| 复检 |`）—— 用于把射程精确到**阶梯行**而不是所有提到本 GOAL 的行。
LADDER_DOMAIN = "| 复检 |"
#: 本轮在阶梯里写明的推进格（措辞必须逐字在场）。**相级进度**是「复检/报告」两域共同的
#: 可读性推进：链已在，进度此前不可见。
LADDER_STEP_MARKERS: tuple[str, ...] = ("相级进度可见",)
#: 阶梯里**不得出现**的过度声称（出现在本轮新增措辞里即判红）。
FORBIDDEN_LADDER_CLAIMS: tuple[str, ...] = ("叙述质量已可判", "强口径已判")


def _load_toolbox() -> Any:
    """按路径加载同目录的工具集（`tools/` 不是包 ⇒ 静态 import 不可用）。"""
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal103_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal103_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（按**本文件名**推应载文件名）。"""
    path = Path(__file__).resolve().parent / "goal103_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal103_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal103_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> Any | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal103_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal103_standard"] = module
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
    """阶梯行（收录本 GOAL / 写明相级进度 / 不过度声称）+ 程序表序 71。

    **射程精确到阶梯行本身**（本轮实测的坑）：判「不得过度声称」时若扫**所有**提到本
    GOAL 的行，会连修订记录里那句「把 X 写进去属于伪造」一起扫到 —— 那正是**禁止**的
    措辞被引用来说明它被禁止。所以三条阶梯判据都只看 `| ` 开头且**本 GOAL 出现在
    阶梯行**的那几行（程序表与修订记录另判）。
    """
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    ladder_rows = [
        line
        for line in charter.splitlines()
        if line.startswith(LADDER_DOMAIN) and LADDER_GOAL in line
    ]
    joined = " ".join(ladder_rows)
    return [
        TOOLBOX.verdict(
            "ladder-records-this-goal",
            bool(ladder_rows),
            f"宪章阶梯的「{LADDER_DOMAIN}」行必须收录本 GOAL",
        ),
        TOOLBOX.verdict(
            "ladder-names-the-phase-progress",
            all(marker in joined for marker in LADDER_STEP_MARKERS),
            ",".join(marker for marker in LADDER_STEP_MARKERS if marker not in joined),
        ),
        TOOLBOX.verdict(
            "ladder-next-level-not-claimed",
            bool(ladder_rows) and not any(claim in joined for claim in FORBIDDEN_LADDER_CLAIMS),
            "本轮只做**论证**：阶梯行写「叙述质量已可判 / 强口径已判」属于伪造验证证据"
            f"（禁词：{','.join(FORBIDDEN_LADDER_CLAIMS)}）",
        ),
        TOOLBOX.verdict(
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
    ]


def _progress_verdicts(root: Path) -> list[Any]:
    """进展记录（收录本 GOAL / 指向本轮复检 / 插在最上面）。"""
    rows = TOOLBOX.progress_rows(root, LADDER_GOAL)
    context = TOOLBOX.progress_context(root, LADDER_GOAL)
    return [
        TOOLBOX.verdict(
            "progress-records-this-goal",
            bool(rows),
            "宪章「进展记录」必须有本 GOAL 的一行（EC-08 契约逐字要求）",
        ),
        TOOLBOX.verdict(
            "progress-row-names-the-recheck",
            any(RECHECK_ID in line for line in rows),
            "进展记录那一行的 RECHECK 列必须指向本轮的复检文件",
        ),
        TOOLBOX.verdict(
            "progress-row-is-newest-when-inserted",
            bool(rows) and _rows_above_are_not_older(context),
            "进展记录必须插在**最上面**（该表不按日期排序，判据取第一行）",
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
    """修订记录：本 GOAL 那一行在场且 5 格（表内连续由宪章判据另判）。

    **活跃面或归档均可**（序 74 归档轮实测）：宪章只保留最近三条，本 GOAL 的修订行
    （序 71）在本轮被移进 `archive/MAINLINE-2026-11-04-revisions-71-only.md`。断言问的是
    「当初有没有写这一行、写成了几格」，不是「它现在还在活跃面吗」—— 后者是归档惯例的
    正常结果，只读活跃面就会产出**假负**（资产绑错了面，按 MEM 规则改断言，不是放宽）。
    与 `verify_goal102_closeout.py:222-248` 的既有修法同形。
    """
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    haystacks = [charter]
    archive = root / ".cursor" / "plans" / "goals" / "archive"
    for path in sorted(archive.glob("*.md")):
        haystacks.append(path.read_text(encoding="utf-8"))
    rows = [
        line
        for haystack in haystacks
        for line in haystack.splitlines()
        if line.startswith(f"| 2026-11-01 | {PROGRAM_SEQ}（新增）")
    ]
    ok = bool(rows) and len(rows[0].strip("|").split("|")) == 5
    return [
        TOOLBOX.verdict(
            "revision-row-records-this-goal",
            ok,
            f"宪章「修订记录」必须有本 GOAL 的一行（{PROGRAM_SEQ}（新增）、5 格；活跃面或归档均可）",
        ),
    ]


def _ec_status_verdicts(goal: str) -> list[Any]:
    """EC 终态：八条全 PASS（收口复检跑时八件交付都已在树）。"""
    verdicts: list[Any] = []
    for index in range(1, 9):
        status = ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    return verdicts


def _scope_verdicts(goal: str) -> list[Any]:
    """残余 / 未覆盖 / 声称边界逐条明写（**不得留空**）。"""
    verdicts: list[Any] = []
    for name, markers in (
        ("uncovered-scope-enumerated", UNCOVERED_MARKERS),
        ("residuals-enumerated", RESIDUAL_MARKERS),
        ("claim-boundaries-enumerated", CLAIM_BOUNDARIES),
    ):
        missing = [item for item in markers if item not in goal]
        verdicts.append(TOOLBOX.verdict(name, not missing, ",".join(missing)))
    return verdicts


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、阶梯 / 进展 / 修订记账、残余逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict(
            "goal-declares-eight-ecs",
            all(f"id: EC-0{n}" in goal for n in range(1, 9)),
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
            "PLAN-20261101-103" in all_plan,
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
    parser = argparse.ArgumentParser(description="GOAL-20261101-103 closeout recheck")
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
