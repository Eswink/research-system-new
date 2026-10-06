#!/usr/bin/env python3
"""GOAL-20261006-031 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023…030 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-031 特有的断言**：

- **逐 EC：判据文件在树 + 例数下界**（缺文件、例数掉下去，两向都判红）；
- **本轮主干交付物逐条在位**（AST 断言，不是文本巧合）：
  ① EC-01：`policy.yaml` 的 `allow` 含 6 条新放行（逐条）+ `_CAPABILITY_SCOPE` 镜像同轮同步；
  ② EC-02：`parsing.validate_citation_support` + 三态常量 + `ncbi.py` 取数点**唯一**；
  ③ EC-03：`RunChainCall` 的三个声明字段 + `phase_capability_triggers` 的判定函数 +
     跳过贯通到 `run.completed`（`TaskOutcome.skipped`）；
  ④ EC-04：两个 DTO 的字段是 `text`（AST 读注解名）+ 旧名在血缘上下文零命中 + 快照同步；
- **两条新协议在树**：phase 数 + 必须声明 `capability_execution: run_chain` 的 phase；
- **`IN_SCOPE` 纯收紧**（本轮新增 `tools/verify_goal031_closeout.py`）；
- **记录面**：五个 EC 的终态、子计划 / 复检逐条在位、残余与未覆盖逐条明写；
- **判词归档在树**（两份：EC-03 两臂 / EC-04 改名），二进制写盘（CR=0）逐文件核。

**为什么本验证器不检查两树判词归档的「一致性」**（承 GOAL-029/030 实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做断言，
就会出现「输入即输出」⇒ **永不收敛**。⇒ 归档的**形态**由**专属判据**负责
（`tests/tooling/test_two_tree_verdicts_are_archived.py`，跑在门禁里、在两树写入**之后**），
本验证器只判 GOAL 自己的交付物与前一轮归档的**存在性**（它们已冻结，不再被本 GOAL 改写）。

用法：`python tools/verify_goal031_closeout.py --root <树根> [--verdict-only]`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027…030 同款）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, cast


def _load_toolbox() -> object:
    """按**路径**加载同目录的工具集。

    `tools/` **不是包**（没有 `__init__.py`）⇒ 静态 `import tools.x` 会失败
    （承 `MEM-20261001-181`：按路径加载，且必须先写 `sys.modules` 再 `exec_module`，
    否则 dataclasses / typing 在模块自省时会崩）。
    """
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal031_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal031_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

STANDARD = "tools/closeout_recheck_assertions.py"

GOAL = ".cursor/plans/goals/GOAL-20261006-031-capability-release-and-the-research-loop.md"
#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261006-293-goal-031-ec01-read-capability-release.md",
    ".cursor/plans/tasks/PLAN-20261006-295-goal-031-ec02-citation-validate-full-chain.md",
    ".cursor/plans/tasks/PLAN-20261006-297-goal-031-ec03-two-round-derived-research-loop.md",
    ".cursor/plans/tasks/PLAN-20261006-299-goal-031-ec04-lineage-label-rename.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261006-293-goal-031-ec01-read-capability-release.md",
    ".cursor/plans/rechecks/RECHECK-20261006-295-goal-031-ec02-citation-validate-full-chain.md",
    ".cursor/plans/rechecks/RECHECK-20261006-297-goal-031-ec03-two-round-derived-research-loop.md",
    ".cursor/plans/rechecks/RECHECK-20261006-299-goal-031-ec04-lineage-label-rename.md",
)


#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**，不判定它们足不足够）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "RBAC 未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "`R-M1` 未收口",
)

#: 承继残余 + 本轮新增残余（逐条明写）。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "W31-1",
    "W31-2",
    "W31-3",
    "W31-4",
    "W-EC02-1",
    "W-EC03-1",
)


def _load_assertions() -> Any:
    """按路径加载本轮特有断言集（`tools/` 不是包 ⇒ 静态 import 不行）。"""
    path = Path(__file__).resolve().parent / "goal031_closeout_assertions.py"
    spec = importlib.util.spec_from_file_location("goal031_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal031_assertions"] = module
    spec.loader.exec_module(module)
    return module


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal031_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal031_standard"] = module
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


def record_verdicts(root: Path) -> list[Any]:
    """记录面：EC 终态、子计划 / 复检在位、残余与未覆盖逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[Any] = [
        TOOLBOX.verdict("goal-declares-five-ecs", all(f"id: EC-0{n}" in goal for n in range(1, 6)))
    ]
    for index in range(1, 5):
        status = ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    # EC-05 允许 PASS ∪ PENDING（时间口径见模块 docstring）。
    ec05 = ec_status(goal, "EC-05")
    verdicts.append(TOOLBOX.verdict("goal-ec05-status", ec05 in {"PASS", "PENDING"}, ec05))
    for relative in CHILD_PLANS:
        verdicts.append(
            TOOLBOX.verdict(
                f"child-plan-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file()
            )
        )
    for relative in RECHECKS:
        verdicts.append(
            TOOLBOX.verdict(
                f"recheck-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file()
            )
        )
    for relative in README_AND_PRIOR_GOAL:
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


#: 记录面：GOAL 目录 README（格式契约）。
README_AND_PRIOR_GOAL: tuple[str, ...] = (".cursor/plans/goals/README.md",)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-031 closeout recheck")
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
