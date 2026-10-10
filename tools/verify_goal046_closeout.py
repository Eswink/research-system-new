#!/usr/bin/env python3
"""GOAL-20261010-046 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…040 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-041 特有的断言**
（收在 `tools/goal046_closeout_assertions.py`），并补记录面（EC 终态、子计划 / 复检在位、
MAINLINE 程序表、残余与未覆盖逐条明写）。

**为什么本验证器不检查两树判词归档的「一致性」**（承 GOAL-029…040 实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做一致性断言，
就会出现「输入即输出」⇒ **永不收敛**。⇒ 本验证器只判归档的**存在性**与**形态**（非空、
`CR=0`），一致性由两树入口自己（`COMPARE`）回答。

用法：`uv run --frozen --no-sync python -B tools/verify_goal046_closeout.py
--root . --verdict-only`；
判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027…040 同款）。
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
    spec = importlib.util.spec_from_file_location("goal046_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal046_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal046_closeout.py"
ASSERTIONS = "tools/goal046_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261010-046-program-level-human-gate-becomes-declarable.md"
#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261010-383-goal-046-ec01-04-program-human-gate.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261010-386-goal-046-ec05-self-bootstrap-closeout.md",
)

#: 记录面：GOAL 目录 README（格式契约）+ MAINLINE 宪章（本轮的战役程序）。
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
)

#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "RBAC 未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "`R-M1` 未收口",
)

#: 本轮残余（逐条明写；GOAL 的「本轮新增残余」一节里以**回引号区间**形态写出：`X-1`…`X-3`）。
#: **回引号是判据的一部分**（不是装饰）：裸子串会被无关登记串偶然命中（GOAL-036 实测：
#: 裸 `M-1` 被 `MEM-160` 命中 ⇒ 假绿）。
#: **判据取首尾两个锚点**而不是逐条 `U-N`：GOAL 原文用区间写法（`U-1`…`U-3`）逐条列出
#: 三小节的标题另有编号（`U-1` / `U-2` / `U-3` 各自成节）—— 逐条匹配会与区间写法打架，
#: 而「首尾都在」已足够证明**该区间被明写**（区间非空是原文的写法事实）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`X-1`", "`X-3`")

#: `R26-*` 终态表（承继：逐条保持）。
R26_MARKERS: tuple[str, ...] = ("R26-1", "R26-2", "R26-3", "R26-4", "R26-5", "R26-6")

#: 承继残余的登记（GOAL-045 的 `W-*`：逐条保持，本轮**只追加**）；同取首尾锚点（理由同上）。
PRIOR_RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-3`")


def _load_assertions() -> Any:
    """按路径加载本轮特有断言集（`tools/` 不是包 ⇒ 静态 import 不行）。

    **必须加载本 GOAL 声明的那一份**（GOAL-038/039/040 实测到一处同族缺陷：
    它们声明了自己的断言集却加载了 `goal037_closeout_assertions.py` ⇒ 自有断言**从未运行**）。
    本验证器由 `test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` 钉住，
    且下方 `self-loads-its-own-assertions` 判词会在**加载错文件**时判红。
    """
    path = Path(__file__).resolve().parent / "goal046_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal046_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal046_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal046_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal046_standard"] = module
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
    """自指：本验证器**加载的是本 GOAL 的断言集**（不是上一轮的）。"""
    source = Path(__file__).read_text(encoding="utf-8")
    loaded_own = 'goal046_closeout_assertions.py"' in source.split("def _load_assertions")[1]
    return TOOLBOX.verdict(
        "self-loads-its-own-assertions",
        loaded_own,
        "" if loaded_own else "加载的不是本轮断言集（GOAL-038/039/040 的同族缺陷形态）",
    )


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、`R26-*` 终态、残余与未覆盖逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict("goal-declares-five-ecs", all(f"id: EC-0{n}" in goal for n in range(1, 6))),
        _self_loading_verdict(),
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
    for marker in R26_MARKERS:
        verdicts.append(TOOLBOX.verdict(f"r26-{marker}-registered", marker in goal))
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
    missing_prior = [item for item in PRIOR_RESIDUAL_MARKERS if item not in goal]
    verdicts.append(
        TOOLBOX.verdict("prior-residuals-kept", not missing_prior, ",".join(missing_prior))
    )
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261010-046 closeout recheck")
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
