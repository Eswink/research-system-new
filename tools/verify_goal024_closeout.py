#!/usr/bin/env python3
"""GOAL-20260928-024 收口复检（EC-04）：**标准断言集 + 本轮特有断言**。

与 GOAL-023 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 直接调用 `tools/closeout_recheck_assertions.py`；
本文件**只写 GOAL-024 特有的断言**（观测隐私受判面 / 读面白名单 / 文档条款 / 残余登记）。

协议与两树入口一致：

    python tools/verify_goal024_closeout.py --root <树根> --verdict-only

判词行只有 `PASS` / `FAIL`，且**不含任何树的绝对路径**（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-04` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以那条断言接受 `PASS ∪ PENDING` 并在 `detail` 里说明 —— **不是**放宽，是**时序**。
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
GOAL = ".cursor/plans/goals/GOAL-20260928-024-observability-privacy-adversarial-self-check.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"
ENTRY = "tools/two_tree_recheck.py"
SELF = "tools/verify_goal024_closeout.py"
ASSERTIONS_JUDGE = "tests/tooling/test_closeout_assertions_are_in_tree.py"
GATES_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

CENSUS_SUPPORT = "tests/observability/privacy_exit_census.py"
CENSUS_JUDGE = "tests/observability/test_privacy_exit_census.py"
CANARY_SUPPORT = "tests/observability/content_canary_support.py"
E2E_JUDGE = "tests/observability/test_privacy_content_canary_end_to_end.py"
READ_FACE_SUPPORT = "tests/observability/read_face_canary_support.py"
READ_FACE_REGISTRY = "tests/observability/read_face_route_registry.py"
READ_FACE_JUDGE = "tests/observability/test_privacy_read_face_canary.py"
CLAUSE_JUDGE = "tests/observability/test_privacy_boundary_clauses_are_pinned.py"

OBSERVABILITY = "docs/architecture/OBSERVABILITY.md"
THREAT_MODEL = "docs/security/THREAT_MODEL.md"
DOCS_INDEX = "docs/INDEX.md"

#: 前三条 EC 在本收口复检跑之前必须已是 `PASS`。
SETTLED_EC = ("EC-01", "EC-02", "EC-03")
FINAL_EC = "EC-04"

#: EC-04 把本轮验证器也点进必备清单（**纯收紧**：清单下界断言是单调的）。
REQUIRED_IN_SCOPE = (ENTRY, STANDARD, SELF)

#: EC-01：受判出口必须是**恰好这六条**（漂移即判红）。
EXPECTED_JUDGED_EXITS = (
    "otlp-traces-wire",
    "otlp-metrics-wire",
    "application-log",
    "read-face-http",
    "failure-payload",
    "disk-run-artifacts",
)
MIN_JUDGED_EXITS = 5
MIN_UNCOVERED_SHAPES = 4

#: EC-02：读面清单的上下界必须仍在判据源码里（防白名单膨胀/收缩）。
EXPECTED_MAX_DECLARED = 15
MIN_ZERO_HIT = 45
MIN_EXERCISED = 40
MIN_CANARY_SOURCES = 7
MIN_INJECTED_SOURCES = 3

#: EC-03：两条条款锚点 + 四条未覆盖面 + 五条未覆盖范围。
CLAUSE_ANCHORS = ("条款 ①（canonical 允许持有用户输入）", "条款 ②（非 canonical 出口不得含内容）")
UNCOVERED_ITEMS = ("未覆盖面 1", "未覆盖面 2", "未覆盖面 3", "未覆盖面 4")
UNCOVERED_SCOPE = ("读面未认证", "多租户", "BOLA", "部署面未验证", "宣称项目安全")

#: EC-03：被点名的五条判据（存在性 + 判据自己必须点名它们；写死防漂移）。
EXPECTED_NAMED_JUDGES = (
    "tests/observability/test_privacy_canary.py",
    "tests/observability/test_privacy_exit_census.py",
    "tests/observability/test_privacy_content_canary_end_to_end.py",
    "tests/observability/test_privacy_read_face_canary.py",
    CLAUSE_JUDGE,
)

#: 承继残余（跨 GOAL 的 12 个 ID）—— 逐 ID 出现在 GOAL 正文里。
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

#: 本轮收口后**新增**登记的四条剩余（逐条必须在 GOAL 正文里明写）。
NEW_RESIDUALS = (
    "四个金丝雀源在默认离线链上没有注入面",
    "只扫响应体、响应头不在面",
    "白名单是人工判定 + 机械自审",
    "条款是文档 + 判据形态",
)

REGISTERED_RESIDUALS = (*INHERITED_RESIDUALS, *NEW_RESIDUALS)

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


def _assigned_value(node: ast.stmt, name: str) -> ast.expr | None:
    """取出 `name = ...` / `name: T = ...` 的右值（其它语句返回 None）。"""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return node.value
        return None
    if isinstance(node, ast.AnnAssign):
        target = node.target
        if isinstance(target, ast.Name) and target.id == name:
            return node.value
    return None


def module_constant(path: Path, name: str, kind: type) -> object | None:
    """按 **AST** 读模块级常量（不执行模块，避开 import 副作用）。

    带注解的写法（`NAME: tuple[str, ...] = (...)`）是 `AnnAssign`，不带注解是 `Assign`
    —— 两种都要认，否则判词会以「清单为空」的形态假红。含变量引用的右值取不到常量
    （`literal_eval` 会抛）⇒ 返回 None，调用方据此改用长度口径。
    """
    if not path.is_file():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return None
    for node in tree.body:
        value_node = _assigned_value(node, name)
        if value_node is None:
            continue
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, TypeError):
            return None
        return value if isinstance(value, kind) else None
    return None


def count_tuple_entries(path: Path, name: str) -> int:
    """`(a, b, c)` 形态的元组长度（元素可以是元组/表达式，不做字面量求值）。"""
    if not path.is_file():
        return 0
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return 0
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and isinstance(node.value, ast.Tuple):
                return len(node.value.elts)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            if isinstance(node.value, ast.Tuple):
                return len(node.value.elts)
    return 0


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
    module = load_module(tree_path(root, GOVERNANCE), "goal024_governance_for_closeout")
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
    """EC-01：出口清单判据在树，受判出口**恰好六条**，未覆盖形态 ≥ 4 条。"""
    judge = tree_path(root, CENSUS_JUDGE)
    exits = module_constant(judge, "REQUIRED_JUDGED_EXITS", tuple)
    required: tuple[str, ...] = (
        tuple(str(item) for item in exits) if isinstance(exits, tuple) else ()
    )
    shapes = count_tuple_entries(judge, "UNCOVERED_SHAPES")
    return [
        factory(
            "ec01-census-support-and-judge-in-tree",
            tree_path(root, CENSUS_SUPPORT).is_file() and judge.is_file(),
            f"缺 {CENSUS_SUPPORT} 或 {CENSUS_JUDGE}",
        ),
        factory(
            "ec01-judged-exits-are-exactly-six",
            required == EXPECTED_JUDGED_EXITS,
            f"受判出口清单漂移：{required!r}",
        ),
        factory(
            "ec01-judged-exits-above-floor",
            len(required) >= MIN_JUDGED_EXITS,
            f"受判出口低于下界：{len(required)}",
        ),
        factory(
            "ec01-uncovered-shapes-are-registered",
            shapes >= MIN_UNCOVERED_SHAPES,
            f"未覆盖形态少于 {MIN_UNCOVERED_SHAPES} 条：{shapes}",
        ),
    ]


def ec02_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-02：端到端 + 读面判据在树，读面上下界在位，七源矩阵逐条登记。"""
    registry = tree_path(root, READ_FACE_REGISTRY)
    declared = count_tuple_entries(registry, "DECLARED_CONTENT")
    zero_hit = count_tuple_entries(registry, "ZERO_HIT_ROUTES")
    max_declared = module_constant(registry, "MAX_DECLARED", int)
    min_zero = module_constant(registry, "MIN_ZERO_HIT", int)
    min_exercised = module_constant(registry, "MIN_EXERCISED", int)
    sources = count_tuple_entries(tree_path(root, READ_FACE_JUDGE), "CANARY_SOURCE_INJECTION")
    injected = read_text(root, READ_FACE_JUDGE).count("        True,\n")
    files_ok = all(
        tree_path(root, item).is_file()
        for item in (CANARY_SUPPORT, E2E_JUDGE, READ_FACE_SUPPORT, READ_FACE_JUDGE)
    )
    bounds_ok = (
        max_declared == EXPECTED_MAX_DECLARED
        and min_zero == MIN_ZERO_HIT
        and min_exercised == MIN_EXERCISED
    )
    declared_ceiling = max_declared if isinstance(max_declared, int) else 0
    zero_floor = min_zero if isinstance(min_zero, int) else 0
    return [
        factory(
            "ec02-canary-and-read-face-judges-in-tree",
            files_ok,
            "端到端 / 读面判据或其支撑面不在树",
        ),
        factory(
            "ec02-read-face-bounds-are-pinned",
            bounds_ok,
            f"读面上下界漂移：{max_declared}/{min_zero}/{min_exercised}",
        ),
        factory(
            "ec02-read-face-partition-holds-bounds",
            declared <= declared_ceiling and zero_hit >= zero_floor,
            f"读面清单越界：声明 {declared} / 零命中 {zero_hit}",
        ),
        factory(
            "ec02-canary-sources-are-registered",
            sources >= MIN_CANARY_SOURCES and injected >= MIN_INJECTED_SOURCES,
            f"七源矩阵不完整：{sources} 条 / 注入 {injected} 条",
        ),
    ]


def ec03_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-03：条款锚点 / 未覆盖面 / INDEX 登记 / 被点名判据文件存在性。

    被点名的五条**写死在本文件**（而不是从判据模块读）—— 判据模块里的元组含变量引用，
    读出来是空集会让这条判词以「没有点名」的形态假红；而且「哪些判据被点名」本身
    就是收口断言的一部分，写死才防漂移。
    """
    judge = tree_path(root, CLAUSE_JUDGE)
    observability = read_text(root, OBSERVABILITY)
    threat_model = read_text(root, THREAT_MODEL)
    judge_text = read_text(root, CLAUSE_JUDGE)
    missing_named = [item for item in EXPECTED_NAMED_JUDGES if not tree_path(root, item).is_file()]
    not_named = [item for item in EXPECTED_NAMED_JUDGES if item not in judge_text]
    return [
        factory("ec03-pinning-judge-in-tree", judge.is_file(), f"缺 {CLAUSE_JUDGE}"),
        factory(
            "ec03-clauses-are-pinned-in-both-docs",
            all(item in observability and item in threat_model for item in CLAUSE_ANCHORS),
            "两份文档缺条款锚点",
        ),
        factory(
            "ec03-uncovered-scope-is-registered",
            all(item in observability for item in UNCOVERED_ITEMS) and "未覆盖面" in threat_model,
            "未覆盖面四条未逐条登记",
        ),
        factory(
            "ec03-named-judges-exist",
            not missing_named and not not_named,
            f"被点名但缺失：{missing_named}；判据未点名：{not_named}",
        ),
        factory(
            "ec03-index-registers-the-docs",
            "观测隐私" in read_text(root, DOCS_INDEX),
            f"{DOCS_INDEX} 未登记观测隐私节",
        ),
    ]


def ec04_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-04：记录自洽（EC 终态 / 复检路径 / 子计划 / 记忆）+ 残余与未覆盖**登记在位**。"""
    statuses = ec_statuses(root)
    metadata = goal_metadata(root)
    body = read_text(root, GOAL)
    settled = [f"{item}={statuses.get(item)}" for item in SETTLED_EC]
    settled_ok = all(statuses.get(item) == "PASS" for item in SETTLED_EC)
    # 时序：本文件就是 EC-04 的判词产出者 ⇒ 接受 PASS ∪ PENDING（不是放宽）。
    final_ok = statuses.get(FINAL_EC) in ("PASS", "PENDING")
    latest = metadata.get("latest_recheck")
    latest_ok = isinstance(latest, str) and "/" in latest and tree_path(root, latest).is_file()
    missing_residuals = [item for item in REGISTERED_RESIDUALS if item not in body]
    missing_uncovered = [item for item in UNCOVERED_SCOPE if item not in body]
    over = oversized_functions(tree_path(root, SELF))
    return [
        factory("ec04-ec01-to-ec03-are-pass", settled_ok, f"未终态：{settled}"),
        factory(
            "ec04-final-ec-is-pending-or-pass",
            final_ok,
            f"EC-04 状态异常：{statuses.get(FINAL_EC)}",
        ),
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
        factory(
            "ec04-self-has-no-oversized-function",
            not over,
            f"本验证器有超 {MAX_FUNCTION_LINES} 行函数：{over}",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-024 收口复检（标准断言集 + 本轮特有断言）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    standard = load_module(tree_path(root, STANDARD), "goal024_standard_for_closeout")
    if standard is None or not root.is_dir():
        print("FAIL goal024-standard-assertions-loadable -> 无法加载标准断言集")
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
