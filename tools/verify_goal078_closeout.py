#!/usr/bin/env python3
"""GOAL-20261014-078 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…077 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-077 特有的断言**
（收在 `tools/goal077_closeout_assertions.py`），并补记录面（EC 终态、子计划 / 复检在位、
MAINLINE 程序表与阶梯、残余与未覆盖逐条明写）。

**为什么本验证器不检查两树判词归档的「一致性」**（承 GOAL-029…075 实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做一致性断言，
就会出现「输入即输出」⇒ **永不收敛**。⇒ 本验证器只判归档的**存在性**与**形态**（非空、
`CR=0`），一致性由两树入口自己（`COMPARE`）回答。

用法：`uv run --frozen --no-sync python -B tools/verify_goal078_closeout.py
--root . --verdict-only`；
判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027…075 同款）。
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
    spec = importlib.util.spec_from_file_location("goal078_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal078_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal078_closeout.py"
#: 本 GOAL **自己的**断言集。**实测缺陷修复**（GOAL-20261015-079 cycle 5）：
#: 本行与下方 `_load_assertions()` 曾双双写着 `goal077_closeout_assertions.py`
#: ⇒ `goal078_closeout_assertions.py` 的 29 条自有断言**从未**在本验证器里运行过
#: （与 GOAL-038/039/040 被 `test_closeout_verifiers_run_their_own_assertions.py`
#: 记录的历史缺陷同形；那一轮把「声明 == 实载」钉住了，但**自洽地加载上一轮**
#: 这个形态当时抓不到 —— 该判据在本 cycle 一并收紧为「实载必须是自己那份」）。
ASSERTIONS = "tools/goal078_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261014-078-retrieved-content-reaches-the-model-context.md"
#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261014-469-goal-078-ec01-retrieval-content-reaches-the-session-context.md",
    ".cursor/plans/tasks/PLAN-20261014-471-goal-078-ec02-retrieval-context-reaches-a-downstream-session.md",
    ".cursor/plans/tasks/PLAN-20261015-473-goal-078-ec03-what-entered-the-context-is-readable.md",
    ".cursor/plans/tasks/PLAN-20261015-475-goal-078-ec04-live-run-on-the-new-relay.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261014-470-goal-078-ec01-retrieval-content-reaches-the-session-context.md",
    ".cursor/plans/rechecks/RECHECK-20261015-472-goal-078-ec02-retrieval-context-reaches-a-downstream-session.md",
    ".cursor/plans/rechecks/RECHECK-20261015-474-goal-078-ec03-what-entered-the-context-is-readable.md",
    ".cursor/plans/rechecks/RECHECK-20261015-476-goal-078-ec04-live-run-on-the-new-relay.md",
)

#: 记录面：GOAL 目录 README（格式契约）+ MAINLINE 宪章（本轮的战役程序：程序表 + 阶梯）。
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
)

#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**）。
#: **逐字取自本 GOAL 自己的措辞**（不是从模板抄的）：模板串在本 GOAL 里对不上，
#: 而把 GOAL 改成模板的措辞是「让记录迁就判据」—— 判据要认的是**本记录实际写了什么**。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面认证",
    "多租户·RBAC·BOLA·BFLA",
    "部署面验证",
    "D 组审批通道",
    "`R-M1` 未收口",
)

#: 本轮残余（逐条明写）。**回引号是判据的一部分**（不是装饰）。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "`W-1`",
    "`W-2`",
    "`W-3`",
    "无损注入检索正文",
)

#: 阶梯记账（本 GOAL 的宪章面）：报告域那一行必须收录本 GOAL。
LADDER_GOAL = "GOAL-20261014-078"
LADDER_DOMAIN = "| 检索 |"


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（`tools/` 不是包 ⇒ 静态 import 不行）。

    **两处同族缺陷**（`goal038/039/040` 是「声明自己的、加载上一轮的」；本文件 cycle 5
    实测是同一个形态的第二例）⇒ 只把常量改对不够，**加载行也必须是自己那份**。
    上游守卫是 `test_closeout_verifiers_run_their_own_assertions.py`（cycle 5 已收紧为
    「实载必须是**自己**那份」），下方 `self-loads-its-own-assertions` 判词是第二道。
    """
    path = Path(__file__).resolve().parent / "goal078_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal078_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal078_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal078_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal078_standard"] = module
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
    """自指：本验证器**加载的是它自己那份**断言集（不是上一轮的）。

    **这里曾写死 `'goal077_closeout_assertions.py"'`**（GOAL-20261015-079 cycle 5 实测）：
    判词问的是「字符串在不在」，而它写的那个名字**恰好就是当时实载的那个**（上一轮那份）
    ⇒ 判词**恒绿**，缺陷从它眼皮底下过去。改为**按本文件名推**自己那份
    （`verify_goal078_closeout.py` ⇒ `goal078_closeout_assertions.py`）⇒
    判词与实载同源可比，写死的那一版在构造上不可能再通过。
    """
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
    """宪章阶梯：报告域那一行必须**收录本 GOAL**（战役的每轮记账面）。

    这正是 `test_mainline_research_ladder_advances.py` 的核心不变式在**收口面**的对应读数；
    本验证器把它复述一遍，使「GOAL 收口了却没进阶梯」在收口复检时也可见。
    """
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith(LADDER_DOMAIN)]
    recorded = [line for line in rows if LADDER_GOAL in line]
    return [
        TOOLBOX.verdict(
            "ladder-report-row-exists",
            bool(rows),
            "宪章阶梯里必须有「检索」域那一行",
        ),
        TOOLBOX.verdict(
            "ladder-records-this-goal",
            bool(recorded),
            "检索域那一行的「依据 GOAL」必须收录本 GOAL（每轮必须更近科研）",
        ),
    ]


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、阶梯记账、残余与未覆盖逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict("goal-declares-five-ecs", all(f"id: EC-0{n}" in goal for n in range(1, 6))),
        _self_loading_verdict(),
        *_ladder_verdicts(root),
    ]
    for index in range(1, 5):
        status = ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    # EC-05 允许 PASS ∪ PENDING（时间口径见模块 docstring）。
    ec05 = ec_status(goal, "EC-05")
    verdicts.append(TOOLBOX.verdict("goal-ec05-status", ec05 in {"PASS", "PENDING"}, ec05))
    for relative in (*CHILD_PLANS, *RECHECKS, *README_AND_PRIOR):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
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
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261014-078 closeout recheck")
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
