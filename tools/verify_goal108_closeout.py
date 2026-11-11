#!/usr/bin/env python3
"""GOAL-20261111-108 收口复检（EC-11）：**标准断言集 + 本轮产品面 + 记录面**。

与 GOAL-023…107 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`。本文件只写本 GOAL 特有的
**记录面**（十一条 EC 终态、子计划 / 复检在位、程序表 / 阶梯 / 进展 / 修订记账、
残余与未覆盖逐条明写）；产品面（换站 / 分工 / 四件可靠性 / 文档）收在
`tools/goal108_closeout_assertions.py`。

**自指**：本验证器**必须加载自己那份**断言集，由 `self-loads-its-own-assertions`
（按**本文件名**推应载文件名）钉住。

**EC 状态按 GOAL 的 `status` 分叉**（与 106/107 同一条纪律）：未收口时只判「EC 取值合法」，
收口后才要求十一条全 PASS。理由：对未完成的目标要求全 PASS，会把一条**防伪造**的判据
变成一条**逼人提前把 EC 改成 PASS** 的判据。

**本轮特有的两条**：

1. `live-run-readings-are-honest`：EC-08 的判词是「**能跑起来并如实记录**」，不是
   「一定成功」。判据因此判**读数文件在树且带 run id / 终态 / 相级时间线**，
   并判 GOAL 的 `## 真跑读数` 一节**没有留空**。它**不**要求 `SUCCEEDED`。
2. `ec08-states-its-root-cause`：真跑失败时，台账必须写明**归类到具体根因**
   （本轮 = 上游 Europe PMC 检索超时），不许用「重跑就绿」掩盖。

用法：`uv run --frozen --no-sync python -B tools/verify_goal108_closeout.py --root .
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
SELF = "tools/verify_goal108_closeout.py"
ASSERTIONS = "tools/goal108_closeout_assertions.py"

GOAL = (
    ".cursor/plans/goals/GOAL-20261111-108-relay-swap-single-model-test-and-silent-stall-closure.md"
)
RECHECK = ".cursor/plans/rechecks/RECHECK-20261111-108-relay-swap-and-reliability.md"
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261111-108-relay-swap-and-reliability.md",
)
RECHECKS: tuple[str, ...] = (RECHECK,)
ALL_PLAN = ".cursor/plans/ALL_PLAN.md"

RECHECK_ID = "RECHECK-20261111-108"
PROGRAM_SEQ = 76
LADDER_GOAL = "GOAL-20261111-108"
CHILD_PLAN_ID = "PLAN-20261111-108"

EC_COUNT = 11

#: 本轮残余（**没做到**的那部分，逐条明写；不得留空）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-2`", "`W-3`")
#: 未覆盖范围（逐条明写）。
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`")
#: 声称边界（不得宣称的事）。
CLAIM_BOUNDARIES: tuple[str, ...] = ("`R-1`", "`R-2`", "`R-3`")

#: EC-08 的读数必须包含的三件事实（run id / 终态 / 相级时间线在读数文件里）。
LIVE_READING_KEYS: tuple[str, ...] = ("run_id", "state", "phase_states")

#: 真跑读数一节的标题（**只认行首**：frontmatter 里也引用了这个名字）。
LIVE_SECTION = "## 真跑读数"

#: 失败归类的证据词（本轮根因 = 上游检索超时；台账必须点名它，而不是「重跑就绿」）。
ROOT_CAUSE_MARKERS: tuple[str, ...] = ("europe pmc", "timed out")


def _load_toolbox() -> Any:
    """按路径加载同目录的工具集（`tools/` 不是包 ⇒ 静态 import 不可用）。"""
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal108_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal108_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())


def _load_assertions() -> Any:
    """按路径加载**本 GOAL 自己**的断言集（按**本文件名**推应载文件名）。"""
    path = Path(__file__).resolve().parent / "goal108_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal108_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal108_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> Any | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal108_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal108_standard"] = module
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


def _section(text: str, heading: str) -> str:
    """按**行首**取一节（frontmatter 里也引用了同名标题，按子串切会切到 YAML 里）。"""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(heading)), None)
    if start is None:
        return ""
    end = next(
        (i for i, line in enumerate(lines[start + 1 :], start=start + 1) if line.startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


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
    """程序表的序 76 那一行（本轮必须真的登记过）。"""
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
    """阶梯「复检」行收录本 GOAL（本轮不动任何一格的 `下一级`）。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    rows = [line for line in charter.splitlines() if line.startswith("| 复检 |")]
    joined = " ".join(rows)
    return [
        TOOLBOX.verdict("ladder-recheck-row-exists", bool(rows), "阶梯必须有 `| 复检 |` 那一行"),
        TOOLBOX.verdict(
            "ladder-records-this-goal",
            LADDER_GOAL in joined,
            "「复检」行的「依据 GOAL」必须收录本 GOAL",
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
            any(RECHECK_ID in line for line in progress_rows),
            "进展记录那一行的 RECHECK 列必须指向本轮复检文件",
        ),
    ]


def _revision_rows(text: str) -> list[str]:
    """某份宪章正文里序 76 的修订行（活跃面与归档共用同一个取法）。"""
    return [
        line
        for line in text.splitlines()
        if line.startswith(f"| 2026-11-11 | {PROGRAM_SEQ}（新增）")
    ]


def _revision_row_verdicts(root: Path) -> list[Any]:
    """修订记录：本 GOAL 那一行在场且 5 格（**活跃面或归档均可**）。"""
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    haystacks = [charter]
    archive = root / ".cursor" / "plans" / "goals" / "archive"
    for path in sorted(archive.glob("*.md")):
        haystacks.append(path.read_text(encoding="utf-8"))
    rows = [line for haystack in haystacks for line in _revision_rows(haystack)]
    ok = bool(rows) and len(rows[0].strip("|").split("|")) == 5
    return [
        TOOLBOX.verdict(
            "revision-row-records-this-goal",
            ok,
            f"宪章「修订记录」必须有本 GOAL 的一行（序 {PROGRAM_SEQ}、5 格；活跃面或归档均可）",
        ),
    ]


def _ec_status_verdicts(goal: str) -> list[Any]:
    """EC 终态：按 GOAL 的 `status` 分叉（见模块 docstring）。"""
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


def _live_run_verdicts(root: Path, goal: str) -> list[Any]:
    """EC-08：**读数在树、台账没留空、失败有根因归类**（不要求 SUCCEEDED）。"""
    section = _section(goal, LIVE_SECTION)
    filled = bool(section) and "（收口时填写" not in section and len(section) > 400
    readings: list[str] = []
    for relative in (".cursor/plans/goals/evidence/GOAL-20261111-108-live-run2.json",):
        path = TOOLBOX.tree(root, relative)
        if path.is_file():
            readings.append(path.read_text(encoding="utf-8"))
    joined = "\n".join(readings)
    return [
        TOOLBOX.verdict(
            "live-run-readings-are-in-tree",
            bool(readings),
            "EC-08 的读数文件必须在树（成功或失败都要有读数）",
        ),
        TOOLBOX.verdict(
            "live-run-readings-carry-the-three-facts",
            bool(joined) and all(f'"{key}"' in joined for key in LIVE_READING_KEYS),
            f"读数必须带 {LIVE_READING_KEYS}",
        ),
        TOOLBOX.verdict(
            "live-run-section-is-filled",
            filled,
            "GOAL 的 `## 真跑读数` 一节必须填实（不得留占位符）",
        ),
        TOOLBOX.verdict(
            "live-run-root-cause-is-named",
            all(marker in section.lower() for marker in ROOT_CAUSE_MARKERS),
            "真跑失败必须归类到具体根因（本轮 = 上游检索超时），不许用「重跑就绿」掩盖",
        ),
    ]


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、宪章记账、残余逐条明写、真跑读数。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict(
            "goal-declares-eleven-ecs",
            all(f"id: EC-{n:02d}" in goal for n in range(1, EC_COUNT + 1)),
        ),
        _self_loading_verdict(),
        *_program_verdicts(root),
        *_ladder_verdicts(root),
        *_progress_verdicts(root),
        *_revision_row_verdicts(root),
        *_ec_status_verdicts(goal),
        *_live_run_verdicts(root, goal),
    ]
    for relative in (*CHILD_PLANS, *RECHECKS, ALL_PLAN):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    all_plan = TOOLBOX.text(root, ALL_PLAN)
    verdicts.append(
        TOOLBOX.verdict(
            "child-plan-registered-in-all-plan",
            CHILD_PLAN_ID in all_plan,
            f"子计划必须登记进 ALL_PLAN.md 的 Active 表（{CHILD_PLAN_ID}）",
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
    parser = argparse.ArgumentParser(description="GOAL-20261111-108 closeout recheck")
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
