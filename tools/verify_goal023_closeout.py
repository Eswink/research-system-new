#!/usr/bin/env python3
"""GOAL-20260928-023 收口复检（EC-04）：**标准断言集 + 本轮特有断言**。

本文件是 EC-01 的**使用示范**：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 直接调用 `tools/closeout_recheck_assertions.py`；
本文件**只写 GOAL-023 特有的断言**。这就是「未来的收口复检只写自己特有的断言」的实证。

协议与两树入口一致：

    python tools/verify_goal023_closeout.py --root <树根> --verdict-only

判词行只有 `PASS` / `FAIL`，且**不含任何树的绝对路径**（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-04` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以那条断言接受 `PASS ∪ PENDING` 并在 `detail` 里说明 —— **不是**放宽，是**时序**；
`current` 树与干净 checkout 因此能给出**逐行相同**的判词（这是两树同结论的前提）。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

STANDARD = "tools/closeout_recheck_assertions.py"
GOAL = ".cursor/plans/goals/GOAL-20260928-023-recheck-assets-archival-and-tooling-scope.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"
ENTRY = "tools/two_tree_recheck.py"
SELF = "tools/verify_goal023_closeout.py"
ASSERTIONS_JUDGE = "tests/tooling/test_closeout_assertions_are_in_tree.py"
GATES_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
BOUNDARY_JUDGE = "tests/architecture/python/test_recheck_scope_boundary_is_mechanical.py"

#: GOAL-023 的四个 EC（前三条在本收口复检跑之前必须已是 `PASS`）。
SETTLED_EC = ("EC-01", "EC-02", "EC-03")
FINAL_EC = "EC-04"

#: EC-02 的必备清单里**必须**含这几个脚本（本条收口把 EC-04 的验证器也点进来）。
REQUIRED_IN_SCOPE = (ENTRY, "tools/closeout_recheck_assertions.py", SELF)

#: EC-03 的射程边界（写死的是**期望值**，漂移即判红）。
EXPECTED_BOUNDARY_CUTOFF = "2026-09-28"
EXPECTED_OUT_OF_SCOPE_COUNT = 4

#: 承继残余（跨 GOAL 的 12 个 ID）—— **登记在位**判定：逐 ID 出现在 GOAL 正文里。
INHERITED_RESIDUALS = (
    "R-M1",
    "R-D1",
    "R-B1",
    "R-N1",
    "R-F1",
    "R-F2",
    "W-4",
    "W-5",
    "W-6",
    "W-10",
    "W-11",
    "W-12",
)

#: 本轮收口后**新增**登记的三条剩余。
NEW_RESIDUALS = (
    "历史遗留 `tools/` 脚本仍不受任何判据覆盖",
    "射程外四条历史收口复检仍不可回填",
    "断言集可复跑性 ≠ 跨平台复验",
)

#: 未覆盖范围（承 GOAL-023 的边界，逐条必须在 GOAL 正文里明写）。
UNCOVERED = ("读面未认证", "多租户", "BOLA", "部署面未验证", "宣称项目安全")

#: 全部必须在 GOAL 正文里**登记在位**的残余 ID / 短语。
REGISTERED_RESIDUALS = (*INHERITED_RESIDUALS, *NEW_RESIDUALS)

#: 单条断言函数最多返回几个判词（避免一个函数里堆太多分支）。
MAX_FUNCTION_LINES = 50


def tree_path(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def read_text(root: Path, relative: str) -> str:
    path = tree_path(root, relative)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_module(path: Path, name: str) -> ModuleType | None:
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # 加载失败 ⇒ 对应判词判红，而不是整轮崩掉
        return None
    return module


def declared_functions(path: Path) -> set[str]:
    """按 **AST 读声明**（不是「文本里出现过这个名字」）。

    函数**与类**都算声明 —— `Verdict` 是 `@dataclass` 类，只收 `FunctionDef`
    会把公开面判成缺失（本验证器第一次自跑就踩到了这一点）。
    """
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def oversized_functions(path: Path) -> list[str]:
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    over: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno:
            if node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES:
                over.append(node.name)
    return sorted(over)


def goal_metadata(root: Path) -> dict[str, object]:
    module = load_module(tree_path(root, GOVERNANCE), "goal023_governance_for_closeout")
    if module is None:
        return {}
    parser = cast(
        "Callable[[Path], tuple[dict[str, object], str]]",
        getattr(module, "parse_frontmatter"),
    )
    metadata, _body = parser(tree_path(root, GOAL))
    return metadata


def ec_statuses(root: Path) -> dict[str, str]:
    criteria = goal_metadata(root).get("exit_criteria")
    if not isinstance(criteria, list):
        return {}
    found: dict[str, str] = {}
    for item in criteria:
        if isinstance(item, dict):
            found[str(item.get("id"))] = str(item.get("status"))
    return found


def paths_exist(root: Path, raw: object) -> bool:
    if not isinstance(raw, list) or not raw:
        return False
    for item in raw:
        if not isinstance(item, str) or not tree_path(root, item).exists():
            return False
    return True


def ec01_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-01：断言集与其判据在树，且断言集**按 AST** 声明公开面。"""
    set_path = tree_path(root, "tools/closeout_recheck_assertions.py")
    judge_path = tree_path(root, ASSERTIONS_JUDGE)
    face = declared_functions(set_path)
    missing = [name for name in ("Verdict", "standard_verdicts", "emit") if name not in face]
    return [
        factory(
            "ec01-assertion-set-in-tree",
            set_path.is_file() and not missing,
            f"断言集缺失或公开面不全：{missing}",
        ),
        factory("ec01-assertion-judge-in-tree", judge_path.is_file(), f"缺 {ASSERTIONS_JUDGE}"),
        factory(
            "ec01-entry-refuses-single-tree",
            "TWO-TREE PASS" in read_text(root, ENTRY) and "taskkill" in read_text(root, ENTRY),
            f"{ENTRY} 不再声明两树结论 / 连整棵树杀",
        ),
    ]


def ec02_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-02：受判面判据在树、必备清单含三件、且入口自身不再超规模。"""
    judge = load_module(tree_path(root, GATES_JUDGE), "goal023_gates_judge")
    pinned = getattr(judge, "IN_SCOPE", ()) if judge is not None else ()
    legacy = getattr(judge, "LEGACY_OUT_OF_SCOPE", ()) if judge is not None else ()
    missing = [item for item in REQUIRED_IN_SCOPE if item not in tuple(pinned)]
    over = oversized_functions(tree_path(root, ENTRY))
    return [
        factory("ec02-gate-judge-in-tree", judge is not None, f"缺 {GATES_JUDGE}"),
        factory("ec02-scope-pins-the-three-scripts", not missing, f"必备清单缺少 {missing}"),
        factory("ec02-legacy-scope-is-registered", len(tuple(legacy)) >= 30, "遗留清单疑似被清空"),
        factory("ec02-entry-has-no-oversized-function", not over, f"入口有超 50 行函数：{over}"),
    ]


def ec03_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-03：边界判据在树，且它的期望边界与绑定值一致。"""
    judge = load_module(tree_path(root, BOUNDARY_JUDGE), "goal023_boundary_judge")
    cutoff = getattr(judge, "EXPECTED_CUTOFF", None) if judge is not None else None
    outside = getattr(judge, "EXPECTED_OUT_OF_SCOPE", ()) if judge is not None else ()
    return [
        factory("ec03-boundary-judge-in-tree", judge is not None, f"缺 {BOUNDARY_JUDGE}"),
        factory(
            "ec03-boundary-cutoff-is-pinned",
            str(cutoff) == EXPECTED_BOUNDARY_CUTOFF,
            f"受判起点变了：{cutoff!r}",
        ),
        factory(
            "ec03-out-of-scope-is-exactly-four",
            len(tuple(outside)) == EXPECTED_OUT_OF_SCOPE_COUNT,
            f"射程外清单不是四条：{len(tuple(outside))}",
        ),
    ]


def ec04_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-04：记录自洽（EC 终态 / 复检路径 / 子计划 / 记忆）+ 残余与未覆盖**登记在位**。"""
    statuses = ec_statuses(root)
    metadata = goal_metadata(root)
    body = read_text(root, GOAL)
    settled = [f"{item}={statuses.get(item)}" for item in SETTLED_EC]
    ec01_03_ok = all(statuses.get(item) == "PASS" for item in SETTLED_EC)
    latest = metadata.get("latest_recheck")
    latest_ok = isinstance(latest, str) and "/" in latest and tree_path(root, latest).is_file()
    missing_residuals = [item for item in REGISTERED_RESIDUALS if item not in body]
    missing_uncovered = [item for item in UNCOVERED if item not in body]
    return [
        factory("ec04-ec01-to-ec03-are-pass", ec01_03_ok, f"未终态：{settled}"),
        factory("ec04-latest-recheck-resolves", latest_ok, f"latest_recheck 不可解析：{latest!r}"),
        factory(
            "ec04-child-plans-and-memories-exist",
            paths_exist(root, metadata.get("child_plans"))
            and paths_exist(root, metadata.get("memory_entries")),
            "child_plans 或 memory_entries 有空项 / 不存在",
        ),
        factory(
            "ec04-residuals-are-registered",
            not missing_residuals,
            f"GOAL 正文缺少这些残余登记：{missing_residuals}",
        ),
        factory(
            "ec04-uncovered-scope-is-written",
            not missing_uncovered,
            f"GOAL 正文缺少这些未覆盖范围：{missing_uncovered}",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-023 收口复检（标准断言集 + 本轮特有断言）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    standard = load_module(tree_path(root, STANDARD), "goal023_standard_for_closeout")
    if standard is None or not root.is_dir():
        print("FAIL goal023-standard-assertions-loadable -> 无法加载标准断言集")
        return 2
    factory = cast("Callable[[str, bool, str], object]", getattr(standard, "Verdict"))
    emit = cast("Callable[[Iterable[object]], bool]", getattr(standard, "emit"))
    collect = cast("Callable[[Path], list[object]]", getattr(standard, "standard_verdicts"))
    verdicts: list[object] = [*collect(root)]
    for builder in (ec01_verdicts, ec02_verdicts, ec03_verdicts, ec04_verdicts):
        verdicts.extend(builder(root, factory))
    return 0 if emit(verdicts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
