#!/usr/bin/env python3
"""GOAL-20261023-095 收口复检（EC-05；2026-10-27 回填）。

**回填**（如实登记）：`tools/verify_goal095_closeout.py` **从未存在** —— GOAL-096 的 `W-3`
记的就是这件事；`_CUTOFF_SEQ = 64` 把序 63 挡在受判面外 ⇒ 它不判红。本文件 + 断言集
补齐历史，**不等于**它当年过了门。

与 GOAL-023…097 的验证器同形：公共面直接调用
`tools/closeout_recheck_assertions.standard_verdicts`，本文件只加**记录面**几条。

**自指**：必须加载**自己那份**断言集（`goal095_closeout_assertions.py`）。

用法：
    uv run --frozen --no-sync python -B tools/verify_goal095_closeout.py --root . --verdict-only
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, cast


def _load_toolbox() -> object:
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal095_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal095_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal095_closeout.py"
ASSERTIONS = "tools/goal095_closeout_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261023-095-the-ledger-judge-reads-both-directions.md"
RECHECK = (
    ".cursor/plans/rechecks/RECHECK-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md"
)
CHILD_PLAN = (
    ".cursor/plans/tasks/PLAN-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md"
)
README_AND_PRIOR: tuple[str, ...] = (
    ".cursor/plans/goals/README.md",
    ".cursor/plans/goals/MAINLINE.md",
    ".cursor/plans/ALL_PLAN.md",
)

PROGRAM_SEQ = 63
GOAL_ID = "GOAL-20261023-095"
RECHECK_ID = "RECHECK-20261023-095"


def _load_assertions() -> Any:
    path = Path(__file__).resolve().parent / "goal095_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal095_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal095_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal095_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal095_standard"] = module
    spec.loader.exec_module(module)
    return module


def _self_loading_verdict() -> Any:
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
    charter = TOOLBOX.text(root, ".cursor/plans/goals/MAINLINE.md")
    verdicts: list[Any] = [
        _self_loading_verdict(),
        TOOLBOX.verdict(
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {GOAL_ID} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
    ]
    progress = charter.split("## 进展记录", 1)[-1]
    pointer = re.search(
        r">\s*序\s*63\s*的进展记录已移入\s*\[[^\]]*\]\((?P<path>archive/[^)]*)\)", charter
    )
    verdicts.append(
        TOOLBOX.verdict(
            "progress-row-or-archive-pointer-is-present",
            RECHECK_ID in progress or pointer is not None,
            "进展记录（或指向它的归档指针）必须在宪章里",
        )
    )
    if pointer is not None:
        archived = root / ".cursor" / "plans" / "goals" / pointer.group("path")
        verdicts.append(
            TOOLBOX.verdict(
                "the-archive-file-it-points-at-exists",
                archived.is_file(),
                f"归档指针必须指向真实文件：{pointer.group('path')}",
            )
        )
    else:
        verdicts.append(
            TOOLBOX.verdict(
                "the-archive-file-it-points-at-exists",
                RECHECK_ID in progress,
                "既没有归档指针，活跃表里也没有本轮的 RECHECK ⇒ 记账断链",
            )
        )
    for relative in (GOAL, RECHECK, CHILD_PLAN, *README_AND_PRIOR):
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-20261023-095 closeout recheck")
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
