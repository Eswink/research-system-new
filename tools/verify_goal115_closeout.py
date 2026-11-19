#!/usr/bin/env python3
"""GOAL-20261119-115 收口复检（EC-08）：**标准断言集 + 本轮产品面 + 记录面**。

与 GOAL-023…114 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`。本文件只写本 GOAL 特有的
**记录面**（八条 EC 终态、程序表 / 阶梯 / 进展 / 修订记账、残余与未覆盖逐条明写）；
产品面（换站 / 零价 / 旧 pin / 四类失败模式 / 三次读数 / advisory / 可重试 / PRD）
收在 `tools/goal115_closeout_assertions.py`。

**自指**：本验证器**必须加载自己那份**断言集（按**本文件名**推应载文件名）。

**EC 状态按 GOAL 的 `status` 分叉**（与 106…114 同一条纪律）：未收口时只判
「EC 取值合法」，收口后才要求八条全 PASS。

用法：`uv run --frozen --no-sync python -B tools/verify_goal115_closeout.py --root .
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
SELF = "tools/verify_goal115_closeout.py"
ASSERTIONS = "tools/goal115_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261119-115-review-reliability-and-product-gap.md"
RECHECK = ".cursor/plans/rechecks/RECHECK-20261119-115-goal-closeout.md"
ALL_PLAN = ".cursor/plans/ALL_PLAN.md"

EC_COUNT = 8
PROGRAM_SEQ = 83
LADDER_GOAL = "GOAL-20261119-115"
LADDER_ROW = "| 复检 |"

#: 本轮残余 / 未覆盖 / 声称边界（逐条明写；不得留空）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-2`", "`W-3`")
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`")
CLAIM_BOUNDARIES: tuple[str, ...] = ("`R-1`", "`R-2`", "`R-3`")


def _load_toolbox() -> Any:
    """按路径加载同目录的工具集（`tools/` 不是包 ⇒ 静态 import 不可用）。"""
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal115_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal115_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（按**本文件名**推应载文件名）。"""
    path = Path(__file__).resolve().parent / "goal115_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal115_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal115_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> Any | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal115_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal115_standard"] = module
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


def _frontmatter_status(goal: str) -> str:
    """GOAL frontmatter 的 `status:`（`---` 之间的那一份，不扫正文）。"""
    if not goal.startswith("---"):
        return "MISSING"
    body = goal.split("---", 2)
    if len(body) < 3:
        return "MISSING"
    for line in body[1].splitlines():
        if line.startswith("status:"):
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


def _program_verdicts(root: Path) -> list[Any]:
    """程序表的序 83 那一行（本轮必须真的登记过）。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [
        line
        for line in charter.splitlines()
        if line.startswith(f"| {PROGRAM_SEQ} | {LADDER_GOAL} |")
    ]
    return [
        TOOLBOX.verdict(
            "program-table-has-this-round",
            bool(rows),
            f"宪章程序表必须有 `| {PROGRAM_SEQ} | {LADDER_GOAL} |` 那一行",
        ),
        TOOLBOX.verdict(
            "program-row-has-six-cells",
            bool(rows) and len(rows[0].strip("|").split("|")) == 6,
            "程序表每行六格（序 / GOAL id / 轴 / 目标 / 依赖 / 能力域）",
        ),
    ]


def _ladder_verdicts(root: Path) -> list[Any]:
    """阶梯「复检」行：本轮必须真的写了读数（依据列收录本 GOAL）。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    row = next((line for line in charter.splitlines() if line.startswith(LADDER_ROW)), "")
    cells = row.split("|")
    return [
        TOOLBOX.verdict(
            "ladder-review-row-records-this-goal",
            len(cells) > 3 and LADDER_GOAL in cells[3],
            "「复检」行的依据列必须收录本 GOAL（新读数的出处可追溯）",
        ),
    ]


def _progress_verdicts(root: Path) -> list[Any]:
    """进展记录：收录本 GOAL + 指向本轮复检。"""
    progress_rows = TOOLBOX.progress_rows(root, LADDER_GOAL)
    return [
        TOOLBOX.verdict(
            "progress-records-this-goal",
            bool(progress_rows),
            "宪章「进展记录」必须有本 GOAL 的一行",
        ),
        TOOLBOX.verdict(
            "progress-row-names-the-recheck",
            any(Path(RECHECK).stem in line for line in progress_rows),
            "进展记录那一行的 RECHECK 列必须指向本轮复检文件",
        ),
    ]


def _ec_status_verdicts(goal: str) -> list[Any]:
    """EC 终态：按 GOAL 的 `status` 分叉。"""
    status = _frontmatter_status(goal)
    statuses = {
        f"EC-{index:02d}": ec_status(goal, f"EC-{index:02d}") for index in range(1, EC_COUNT + 1)
    }
    if status == "ACHIEVED":
        return [
            TOOLBOX.verdict(
                f"goal-{ec.lower()}-status",
                value == "PASS",
                f"{ec}={value!r}（ACHIEVED 要求全 PASS）",
            )
            for ec, value in statuses.items()
        ]
    allowed = {"PASS", "PENDING", "BLOCKED"}
    return [
        TOOLBOX.verdict(
            "goal-ec-statuses-are-legal-values",
            all(value in allowed for value in statuses.values()),
            f"非 ACHIEVED 时 EC 取值必须属于 {sorted(allowed)}",
        ),
        TOOLBOX.verdict(
            "goal-does-not-claim-completion",
            status != "ACHIEVED" or all(v == "PASS" for v in statuses.values()),
            f"status={status!r} 且 EC={statuses} —— 声称完成就必须逐条 PASS",
        ),
    ]


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
    """记录面：EC 终态、复检在位、宪章记账、残余逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict(
            "goal-declares-eight-ecs",
            all(f"id: EC-{n:02d}" in goal for n in range(1, EC_COUNT + 1)),
            "GOAL 必须声明 EC-01…EC-08",
        ),
        _self_loading_verdict(),
        *_program_verdicts(root),
        *_ladder_verdicts(root),
        *_progress_verdicts(root),
        *_ec_status_verdicts(goal),
    ]
    for relative in (RECHECK, ALL_PLAN, ASSERTIONS, SELF):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
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
    parser = argparse.ArgumentParser(description="GOAL-20261119-115 closeout verifier")
    parser.add_argument("--root", default=".")
    parser.add_argument("--verdict-only", action="store_true")
    return parser


def verdicts_for(root: Path) -> list[Any]:
    """全部判词：本轮断言集 + 标准断言集 + 记录面。"""
    module = _load_assertions()
    verdicts: list[Any] = list(module.assertion_verdicts(root, TOOLBOX))
    standard = load_standard(root)
    if standard is not None:
        verdicts.extend(standard.standard_verdicts(root))
    verdicts.extend(record_verdicts(root))
    return verdicts


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    root = Path(args.root).resolve()
    verdicts = verdicts_for(root)
    # `verdict_line` 属**标准断言集**（判词行格式的唯一来源），不在 toolbox 里。
    standard = load_standard(root)
    if standard is not None:
        format_line = standard.verdict_line
    else:  # 标准集缺席时的退化格式（两树复检仍可比）

        def format_line(item: Any) -> str:
            return f"{'PASS' if item.ok else 'FAIL'} {item.name}"

    lines: list[str] = [format_line(verdict) for verdict in verdicts]
    failed = [item for item in verdicts if not item.ok]
    if not args.verdict_only:
        lines.append(f"SUMMARY total={len(verdicts)} failed={len(failed)}")
    print("\n".join(lines))
    return 1 if failed else 0


assert_callable: Callable[..., Any] = verdicts_for

if __name__ == "__main__":
    raise SystemExit(main())
