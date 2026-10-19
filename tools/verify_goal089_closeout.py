#!/usr/bin/env python3
"""GOAL-20261019-089 收口复检（EC-05）：**标准断言集 + 本轮特有断言 + 记录面**。

与 GOAL-023…088 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写本 GOAL 特有的记录面**
（EC 终态、子计划 / 复检在位、MAINLINE 阶梯与进展记账、残余与未覆盖逐条明写），产品面的
特有断言收在 `tools/goal089_closeout_assertions.py`。

**为什么本验证器不检查两树判词归档的「一致性」**（承 GOAL-029…088 的循环依赖教训）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做一致性断言，
就会出现「输入即输出」⇒ 永不收敛。⇒ 只判归档的**存在性**与**形态**。

**自指**：本验证器**必须加载自己那份**断言集（`goal089_closeout_assertions.py`），
由 `self-loads-its-own-assertions`（按**本文件名**推应载文件名）钉住 ——
GOAL-078 曾自洽地加载上一轮那份，自有断言从未运行。

用法：`uv run --frozen --no-sync python -B tools/verify_goal089_closeout.py
--root . --verdict-only`；
判词行只有 `PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是待办（它的判词就是本文件产出的），
所以 EC-05 那条断言接受「达成 ∪ 待办」两种取值 —— **不是**放宽，是**时序**。
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
    spec = importlib.util.spec_from_file_location("goal089_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal089_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal089_closeout.py"
ASSERTIONS = "tools/goal089_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261019-089-direction-drives-question-drives-retrieval.md"
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261019-089-live-run.txt"
#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261019-089-goal-089-ec01-05-direction-drives-question.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261019-089-goal-089-direction-drives-question-drives-retrieval.md",
)

#: 记录面：GOAL 目录 README（格式契约）+ MAINLINE 宪章（程序表 + 阶梯）。
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
)

#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面认证",
    "多租户·RBAC·BOLA·BFLA",
    "部署面验证",
    "D 组审批通道",
    "`R-M1` 未收口",
)

#: 本轮残余（逐条明写；**回引号是判据的一部分**）。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "`W-1`",
    "`W-2`",
    "`W-3`",
    "`W-4`",
    "`W-5`",
    "`W-6`",
)

#: 阶梯记账（本 GOAL 的宪章面）：**检索**与**迭代**两行都必须收录本 GOAL。
LADDER_GOAL = "GOAL-20261019-089"
LADDER_DOMAINS: tuple[str, ...] = ("| 检索 |", "| 迭代 |")
#: 本轮复检文件（进展记录那一行的 RECHECK 列必须指向它）。
RECHECK_ID = "RECHECK-20261019-089"


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（`tools/` 不是包 ⇒ 静态 import 不行）。"""
    path = Path(__file__).resolve().parent / "goal089_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal089_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal089_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal089_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal089_standard"] = module
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


def _progress_section(charter: str) -> str:
    """宪章「进展记录」小节正文（到下一个 `## ` 为止）。"""
    marker = "## 进展记录"
    start = charter.find(marker)
    if start == -1:
        return ""
    tail = charter[start + len(marker) :]
    stop = tail.find("\n## ")
    return tail[: stop if stop != -1 else len(tail)]


def _ladder_verdicts(root: Path) -> list[Any]:
    """宪章记账的**两个面**都必须收录本 GOAL：阶梯行 + 进展记录行。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    lines = charter.splitlines()
    verdicts: list[Any] = []
    for domain in LADDER_DOMAINS:
        rows = [line for line in lines if line.startswith(domain)]
        recorded = [line for line in rows if LADDER_GOAL in line]
        label = domain.strip("| ").strip()
        verdicts.append(
            TOOLBOX.verdict(
                f"ladder-{label}-row-exists", bool(rows), f"宪章阶梯里必须有「{label}」域那一行"
            )
        )
        verdicts.append(
            TOOLBOX.verdict(
                f"ladder-{label}-records-this-goal",
                bool(recorded),
                f"{label}域那一行的「依据 GOAL」必须收录本 GOAL（每轮必须更近科研）",
            )
        )
    progress = _progress_section(charter)
    progress_rows = [
        line for line in progress.splitlines() if line.startswith("| ") and LADDER_GOAL in line
    ]
    verdicts.extend([
        TOOLBOX.verdict(
            "progress-records-this-goal",
            bool(progress_rows),
            "宪章「进展记录」必须有本 GOAL 的一行（EC-05 契约逐字要求）",
        ),
        TOOLBOX.verdict(
            "progress-row-names-the-recheck",
            any(RECHECK_ID in line for line in progress_rows),
            "进展记录那一行的 RECHECK 列必须指向本轮的复检文件",
        ),
    ])
    return verdicts


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
    # EC-05 允许 达成 ∪ 待办（时间口径见模块 docstring）。
    ec05 = ec_status(goal, "EC-05")
    verdicts.append(TOOLBOX.verdict("goal-ec05-status", ec05 in {"PASS", "PENDING"}, ec05))
    for relative in (*CHILD_PLANS, *RECHECKS, *README_AND_PRIOR, EVIDENCE):
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
    parser = argparse.ArgumentParser(description="GOAL-20261019-089 closeout recheck")
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
