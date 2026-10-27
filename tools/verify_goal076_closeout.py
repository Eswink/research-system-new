#!/usr/bin/env python3
"""GOAL-20261014-076 的**记录面复检**（EC-05 的悬空引用，2026-10-27 回填）。

**它不是收口证明** —— 见 `tools/goal076_closeout_assertions.py` 的模块 docstring：GOAL-076
的 status 是 `PAUSED`，那 10 条长度界从未加进去。本验证器判的是「**记录与树一致**」：
状态没被改成终态、EC 没被改成 PASS、那批界**确实**还缺席、五面判据**确实**在树。

与 GOAL-023…097 的验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件只加**记录面**几条。

**自指**：本验证器必须加载**自己那份**断言集（`goal076_closeout_assertions.py`）—— GOAL-078
曾自洽地加载上一轮那份，自有断言从未运行。

用法：
    uv run --frozen --no-sync python -B tools/verify_goal076_closeout.py --root . --verdict-only
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
    spec = importlib.util.spec_from_file_location("goal076_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal076_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal076_closeout.py"
ASSERTIONS = "tools/goal076_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261014-076-declared-query-params-have-explicit-length-bounds.md"
CHILD_PLAN = (
    ".cursor/plans/tasks/"
    "PLAN-20261014-461-goal-076-ec01-05-declared-query-params-have-explicit-length-bounds.md"
)
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
    ".cursor/plans/ALL_PLAN.md",
)

PROGRAM_SEQ = 44
GOAL_ID = "GOAL-20261014-076"


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（`tools/` 不是包 ⇒ 静态 import 不行）。"""
    path = Path(__file__).resolve().parent / "goal076_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal076_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal076_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal076_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal076_standard"] = module
    spec.loader.exec_module(module)
    return module


def _self_loading_verdict() -> Any:
    """自指：本验证器加载的是**它自己那份**断言集（按**本文件名**推，不写死）。"""
    digits = "".join(ch for ch in Path(__file__).name.split("_")[1] if ch.isdigit())
    expected = f"goal{digits}_closeout_assertions.py"
    source = Path(__file__).read_text(encoding="utf-8")
    loaded_own = f'"{expected}"' in source.split("def _load_assertions")[1]
    return TOOLBOX.verdict(
        "self-loads-its-own-assertions",
        loaded_own,
        "" if loaded_own else f"加载的不是本轮断言集（应为 {expected}）",
    )


def record_verdicts(root: Path) -> list[Any]:
    """记录面：文件在位 + 程序表那一行在 + 状态如实。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    verdicts: list[Any] = [
        _self_loading_verdict(),
        TOOLBOX.verdict(
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {GOAL_ID} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
        TOOLBOX.verdict(
            "charter-names-this-goal-in-the-ladder",
            GOAL_ID in charter,
            "宪章必须至少在一处收录本 GOAL（阶梯 / 进展 / 程序表任一处）",
        ),
    ]
    for relative in (GOAL, CHILD_PLAN, *README_AND_PRIOR):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261014-076 record-face recheck")
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
