#!/usr/bin/env python3
"""GOAL-20261015-080 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…078 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-079 特有的断言**
（收在 `tools/goal080_closeout_assertions.py`），并补记录面（EC 终态、子计划 / 复检在位、
MAINLINE 程序表与阶梯、残余与未覆盖逐条明写）。

**为什么本验证器不检查两树判词归档的「一致性」**（承 GOAL-029…078 实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做一致性断言，
就会出现「输入即输出」⇒ **永不收敛**。⇒ 本验证器只判归档的**存在性**与**形态**（非空、
`CR=0`），一致性由两树入口自己（`COMPARE`）回答。

**本 cycle 的两处自指**（都被判据钉住，不是散文）：

- 本验证器**必须加载自己那份**断言集（`goal080_closeout_assertions.py`）——
  GOAL-078 的验证器实测就在这一点上错了（自洽地加载 `goal077` 那份 ⇒ 29 条自有断言
  从未运行）⇒ 现在由 `self-loads-its-own-assertions`（按**本文件名**推应载文件名）
  与 `test_closeout_verifiers_run_their_own_assertions.py` 双面钉住。
- **阶梯记账**由 `ladder-records-this-goal` 在收口面复述一遍（宪章判据已在 m0 里，
  这里使「GOAL 收口了却没人记账」在收口复检时也可见）。

用法：`uv run --frozen --no-sync python -B tools/verify_goal080_closeout.py
--root . --verdict-only`；
判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件
产出的），所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**。
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
    spec = importlib.util.spec_from_file_location("goal080_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal080_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal080_closeout.py"
ASSERTIONS = "tools/goal080_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261015-080-experiment-design-derived-from-the-plan.md"
#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261015-487-goal-080-ec01-the-design-source-is-declared-and-run-scoped.md",
    ".cursor/plans/tasks/PLAN-20261015-489-goal-080-ec02-the-design-content-decides-the-experiment.md",
    ".cursor/plans/tasks/PLAN-20261015-491-goal-080-ec03-plan-change-means-experiment-change.md",
    ".cursor/plans/tasks/PLAN-20261015-493-goal-080-ec04-live-design-from-the-plan.md",
    ".cursor/plans/tasks/PLAN-20261016-495-goal-080-ec05-self-bootstrap-closeout.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261015-488-goal-080-ec01-the-design-source-is-declared-and-run-scoped.md",
    ".cursor/plans/rechecks/RECHECK-20261015-490-goal-080-ec02-the-design-content-decides-the-experiment.md",
    ".cursor/plans/rechecks/RECHECK-20261015-492-goal-080-ec03-plan-change-means-experiment-change.md",
    ".cursor/plans/rechecks/RECHECK-20261015-494-goal-080-ec04-live-design-from-the-plan.md",
    ".cursor/plans/rechecks/RECHECK-20261016-496-goal-080-ec05-self-bootstrap-closeout.md",
)

#: 记录面：GOAL 目录 README（格式契约）+ MAINLINE 宪章（本轮的战役程序：程序表 + 阶梯）。
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
)

#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**）。
#: **逐字取自本 GOAL 自己的措辞**（不是从模板抄的）：把 GOAL 改成模板的措辞是
#: 「让记录迁就判据」—— 判据要认的是**本记录实际写了什么**。
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
    "`W-4`",
    "实验设计本身",
)

#: 阶梯记账（本 GOAL 的宪章面）：实验域那一行必须收录本 GOAL。
LADDER_GOAL = "GOAL-20261015-080"
LADDER_DOMAIN = "| 计划 |"


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（`tools/` 不是包 ⇒ 静态 import 不行）。

    **这一行是本 cycle 实测缺陷的修复点**：GOAL-078 的验证器在这里加载了**上一轮**的
    断言集（自洽地声明+加载 `goal077` 那份）⇒ 自有断言从未运行。上方 `ASSERTIONS`
    常量与下方文件名**必须同指本人**，由 `self-loads-its-own-assertions` 判词
    （按本文件名推）与家族判据 `test_closeout_verifiers_run_their_own_assertions.py`
    （第三项对拍：实载 == 自己那份）双面钉住。
    """
    path = Path(__file__).resolve().parent / "goal080_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal080_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal080_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal080_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal080_standard"] = module
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
    """自指：本验证器**加载的是它自己那份**断言集（按**本文件名**推，不写死）。

    写死一个名字问「串在不在」的形态**在构造上不可信** —— GOAL-078 的验证器正是
    这样通过的（它写死的那个名字**就是**当时实载的上一轮那份）。本判词改为推导：
    `verify_goal080_closeout.py` ⇒ `goal080_closeout_assertions.py`。
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
    """宪章阶梯：实验域那一行必须**收录本 GOAL**（战役的每轮记账面）。

    这正是 `test_mainline_research_ladder_advances.py` 的核心不变式在**收口面**的对应读数；
    本验证器把它复述一遍，使「GOAL 收口了却没进阶梯」在收口复检时也可见。
    """
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith(LADDER_DOMAIN)]
    recorded = [line for line in rows if LADDER_GOAL in line]
    return [
        TOOLBOX.verdict(
            "ladder-experiment-row-exists",
            bool(rows),
            "宪章阶梯里必须有「实验」域那一行",
        ),
        TOOLBOX.verdict(
            "ladder-records-this-goal",
            bool(recorded),
            "实验域那一行的「依据 GOAL」必须收录本 GOAL（每轮必须更近科研）",
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
    parser = argparse.ArgumentParser(description="GOAL-20261015-080 closeout recheck")
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
