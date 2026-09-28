#!/usr/bin/env python3
"""GOAL-20260929-025 收口复检（EC-04）：**标准断言集 + 本轮特有断言**。

与 GOAL-023 / GOAL-024 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-025 特有的断言**：

- `EC-01` 响应头面：头部清单三档分区（受判 / 豁免 / 登记为不发射）+ 判据例数下界；
- `EC-02` 正控制矩阵：载体矩阵分区（正控制 / 机械理由）+ 源矩阵条数 + 例数下界；
- `EC-03` 白名单派生：**重算**「派生面 == 人工清单」（读树内快照 JSON 与两个清单的
  AST 字面量，**不执行**被检模块）+ 派生面下界 / 框架条数 / 例数下界；
- `EC-04` 记录自洽：前三 EC 终态、复检路径可解析、子计划 / 记忆在位、残余与未覆盖逐条、
  本验证器进 `IN_SCOPE`（纯收紧）。

协议与两树入口一致：`python tools/verify_goal025_closeout.py --root <树根> --verdict-only`。
判词行只有 `PASS` / `FAIL`，且**不含任何树的绝对路径**（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-04` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以那条断言接受 `PASS ∪ PENDING` 并在 `detail` 里说明 —— **不是**放宽，是**时序**。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

STANDARD = "tools/closeout_recheck_assertions.py"
ENTRY = "tools/two_tree_recheck.py"
SELF = "tools/verify_goal025_closeout.py"
GOAL = ".cursor/plans/goals/GOAL-20260929-025-privacy-residual-surfaces-and-positive-controls.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

SNAPSHOT = "docs/api/openapi.m13.json"
HEADER_INVENTORY = "tests/observability/read_face_header_inventory.py"
HEADER_JUDGE = "tests/observability/test_privacy_read_face_headers.py"
CONTROL_SUPPORT = "tests/observability/positive_control_support.py"
CONTROL_JUDGE = "tests/observability/test_privacy_positive_controls.py"
DERIVATION = "tests/observability/read_face_whitelist_derivation.py"
DERIVATION_JUDGE = "tests/observability/test_privacy_read_face_whitelist_derivation.py"
ROUTE_REGISTRY = "tests/observability/read_face_route_registry.py"

#: EC-01 头部清单契约：三档逐条计数（漂移即判红）+ 判据例数下界。
EXPECTED_HEADER_PARTITION = {"JUDGED": 2, "EXEMPT": 3, "ABSENT": 1}
MIN_HEADER_CASES = 13
#: EC-02 载体矩阵契约（正控制 / 机械理由 / 行数）+ 源矩阵条数 + 判据例数下界。
EXPECTED_CARRIER_PARTITION = {"POSITIVE": 6, "MECHANICAL": 2}
EXPECTED_CARRIER_ROWS = 8
EXPECTED_SOURCES = 4
MIN_CONTROL_CASES = 11
#: EC-03 派生面契约：下界 / 框架内建条数 / 判据例数下界。
MIN_DERIVED_FLOOR = 40
EXPECTED_FRAMEWORK_ROUTES = 4
MIN_DERIVATION_CASES = 10

MAX_FUNCTION_LINES = 50

#: 前三条 EC 在本收口复检跑之前必须已是 `PASS`。
SETTLED_EC = ("EC-01", "EC-02", "EC-03")
FINAL_EC = "EC-04"

#: EC-04 ①：本轮验证器（连同入口与标准断言集）必须显式进 `IN_SCOPE`（**纯收紧**）。
REQUIRED_IN_SCOPE = (ENTRY, STANDARD, SELF)

#: 承继残余（GOAL-019…024 的 12 个 ID）—— 逐 ID 出现在 GOAL 正文里。
INHERITED_RESIDUALS = "R-M1 R-D1 R-B1 R-N1 R-F1 R-F2 W-4 W-5 W-6 W-10 W-11 W-12".split()

#: 本轮的六条 `G24-*`（`G24-4` / `G24-5` 须同时注明「需用户拍板」）。
ROUND_RESIDUALS = ("G24-1", "G24-2", "G24-3", "G24-4", "G24-5", "G24-6")
USER_DECISION_RESIDUALS = ("G24-4", "G24-5")
USER_DECISION_MARK = "需用户拍板"

#: 未覆盖范围（逐条明写）。
UNCOVERED_SCOPE = ("读面未认证", "多租户", "BOLA", "部署面未验证", "R-M1 未收口")


def tree_path(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def read_text(root: Path, relative: str) -> str:
    path = tree_path(root, relative)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def ast_module(root: Path, relative: str) -> ast.Module | None:
    """按 **AST** 读树内文件（不执行模块，避开 import 副作用与跨树 sys.path 冲突）。"""
    text = read_text(root, relative)
    if not text:
        return None
    try:
        return ast.parse(text, filename=relative)
    except SyntaxError:
        return None


def bindings(tree: ast.Module | None) -> dict[str, ast.expr | None]:
    """模块级 `NAME = …` / `NAME: T = …` 的右值（仅注解无值者记 None）。"""
    found: dict[str, ast.expr | None] = {}
    for node in tree.body if tree is not None else ():
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node.value
    return found


def literal(tree: ast.Module | None, name: str) -> object | None:
    """模块级常量的字面量值（含变量引用的右值取不到 ⇒ None）。"""
    node = bindings(tree).get(name)
    if node is None:
        return None
    try:
        value: object = ast.literal_eval(node)
    except (ValueError, TypeError):
        return None
    return value


def tuple_length(tree: ast.Module | None, name: str) -> int:
    node = bindings(tree).get(name)
    return len(node.elts) if isinstance(node, ast.Tuple) else 0


def _calls(tree: ast.Module | None, callee: str) -> list[ast.Call]:
    found: list[ast.Call] = []
    for node in ast.walk(tree) if tree is not None else ():
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == callee:
                found.append(node)
    return found


def argument_texts(tree: ast.Module | None, callee: str, position: int) -> tuple[str, ...]:
    """`callee(…, 第 position 个参数, …)` 的**标识符 / 字符串字面量**（按 AST，不执行模块）。"""
    found: list[str] = []
    for call in _calls(tree, callee):
        if len(call.args) <= position:
            continue
        argument = call.args[position]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            found.append(argument.value)
        elif isinstance(argument, ast.Name):
            found.append(argument.id)
    return tuple(found)


def test_case_count(tree: ast.Module | None) -> int:
    if tree is None:
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def snapshot_get_paths(root: Path) -> tuple[str, ...]:
    """提交的 OpenAPI 快照里的 GET 路径（纯数据：读 JSON，不经被检模块）。"""
    text = read_text(root, SNAPSHOT)
    if not text:
        return ()
    try:
        schema: object = json.loads(text)
    except ValueError:
        return ()
    if not isinstance(schema, dict):
        return ()
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        return ()
    return tuple(
        sorted(
            str(item)
            for item, operations in paths.items()
            if isinstance(operations, dict) and "get" in operations
        )
    )


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
    module = load_module(tree_path(root, GOVERNANCE), "goal025_governance_for_closeout")
    if module is None:
        return {}
    parser = cast(
        "Callable[[Path], tuple[dict[str, object], str]]",
        getattr(module, "parse_frontmatter"),
    )
    metadata, _body = parser(tree_path(root, GOAL))
    return metadata


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
    """EC-01：响应头面判据在树，头部清单三档分区钉住，判据例数达下界。"""
    inventory = ast_module(root, HEADER_INVENTORY)
    judge = ast_module(root, HEADER_JUDGE)
    observed = argument_texts(inventory, "HeaderRule", 1)
    partition = {name: observed.count(name) for name in EXPECTED_HEADER_PARTITION}
    floor = literal(inventory, "MIN_JUDGED")
    cases = test_case_count(judge)
    return [
        factory(
            "ec01-header-face-files-in-tree",
            inventory is not None and judge is not None,
            f"缺 {HEADER_INVENTORY} 或 {HEADER_JUDGE}",
        ),
        factory(
            "ec01-header-partition-is-pinned",
            partition == EXPECTED_HEADER_PARTITION,
            f"头部清单分区漂移：{partition}",
        ),
        factory(
            "ec01-judged-floor-and-cases",
            floor == EXPECTED_HEADER_PARTITION["JUDGED"] and cases >= MIN_HEADER_CASES,
            f"受判头下界 {floor!r}；判据例数 {cases} < {MIN_HEADER_CASES}",
        ),
    ]


def ec02_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-02：正控制矩阵（载体分区 + 源矩阵）在树且形状钉住。"""
    support = ast_module(root, CONTROL_SUPPORT)
    judge = ast_module(root, CONTROL_JUDGE)
    observed = argument_texts(support, "CarrierControl", 2)
    partition = {name: observed.count(name) for name in EXPECTED_CARRIER_PARTITION}
    rows = tuple_length(support, "CARRIER_CONTROLS")
    sources = tuple_length(support, "SOURCE_ADJUDICATIONS")
    floor = literal(support, "MIN_POSITIVE_CARRIERS")
    cases = test_case_count(judge)
    return [
        factory(
            "ec02-positive-control-files-in-tree",
            support is not None and judge is not None,
            f"缺 {CONTROL_SUPPORT} 或 {CONTROL_JUDGE}",
        ),
        factory(
            "ec02-carrier-matrix-is-pinned",
            partition == EXPECTED_CARRIER_PARTITION
            and rows == EXPECTED_CARRIER_ROWS
            and floor == EXPECTED_CARRIER_PARTITION["POSITIVE"],
            f"载体矩阵漂移：{partition} / 行 {rows} / 下界 {floor!r}",
        ),
        factory(
            "ec02-source-matrix-is-pinned",
            sources == EXPECTED_SOURCES,
            f"源矩阵 {sources} 条，契约是 {EXPECTED_SOURCES} 条",
        ),
        factory(
            "ec02-control-cases-above-floor",
            cases >= MIN_CONTROL_CASES,
            f"判据例数 {cases} < {MIN_CONTROL_CASES}",
        ),
    ]


def ec03_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-03：**重算**派生面 == 人工清单（两向），并钉住下界 / 框架条数 / 例数。"""
    derivation = ast_module(root, DERIVATION)
    registry = ast_module(root, ROUTE_REGISTRY)
    judge = ast_module(root, DERIVATION_JUDGE)
    snapshot = snapshot_get_paths(root)
    framework = argument_texts(derivation, "FrameworkRoute", 0)
    registered = argument_texts(registry, "ReadRouteRule", 0)
    derived = set(snapshot) | set(framework)
    missing = sorted(derived - set(registered))
    stale = sorted(set(registered) - derived)
    floor = literal(derivation, "MIN_DERIVED")
    cases = test_case_count(judge)
    return [
        factory(
            "ec03-derivation-files-in-tree",
            derivation is not None and registry is not None and judge is not None,
            f"缺 {DERIVATION} / {ROUTE_REGISTRY} / {DERIVATION_JUDGE}",
        ),
        factory(
            "ec03-derived-face-equals-the-registry",
            bool(registered) and not missing and not stale,
            f"派生面有而清单没有：{missing[:3]}；清单有而派生面没有：{stale[:3]}",
        ),
        factory(
            "ec03-derivation-floors-are-pinned",
            floor == MIN_DERIVED_FLOOR
            and len(snapshot) >= MIN_DERIVED_FLOOR
            and len(framework) == EXPECTED_FRAMEWORK_ROUTES,
            f"下界 {floor!r} / 快照 GET {len(snapshot)} / 框架 {len(framework)}",
        ),
        factory(
            "ec03-derivation-cases-above-floor",
            cases >= MIN_DERIVATION_CASES,
            f"判据例数 {cases} < {MIN_DERIVATION_CASES}",
        ),
    ]


def ec04_record_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-04 的记录面：前三 EC 终态 / 本 EC 时序 / 复检路径 / 子计划与记忆。"""
    statuses = ec_statuses(root)
    metadata = goal_metadata(root)
    settled = [f"{item}={statuses.get(item)}" for item in SETTLED_EC]
    latest = metadata.get("latest_recheck")
    latest_ok = isinstance(latest, str) and "/" in latest and tree_path(root, latest).is_file()
    return [
        factory(
            "ec04-ec01-to-ec03-are-pass",
            all(statuses.get(item) == "PASS" for item in SETTLED_EC),
            f"未终态：{settled}",
        ),
        # 时序：本文件就是 EC-04 的判词产出者 ⇒ 接受 PASS ∪ PENDING（不是放宽）。
        factory(
            "ec04-final-ec-is-pending-or-pass",
            statuses.get(FINAL_EC) in ("PASS", "PENDING"),
            f"EC-04 状态异常：{statuses.get(FINAL_EC)}",
        ),
        factory("ec04-latest-recheck-resolves", latest_ok, f"latest_recheck 不可解析：{latest!r}"),
        factory(
            "ec04-child-plans-and-memories-exist",
            paths_exist(root, metadata.get("child_plans"))
            and paths_exist(root, metadata.get("memory_entries")),
            "child_plans 或 memory_entries 有空项 / 不存在",
        ),
    ]


def ec04_scope_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-04 的射程与残余面：验证器进 `IN_SCOPE`、残余与未覆盖逐条、本文件无超长函数。"""
    scope = literal(ast_module(root, TOOLING_JUDGE), "IN_SCOPE")
    scope_tuple = tuple(str(item) for item in scope) if isinstance(scope, tuple) else ()
    missing_scope = [item for item in REQUIRED_IN_SCOPE if item not in scope_tuple]
    body = read_text(root, GOAL)
    missing_residuals = [
        item for item in (*INHERITED_RESIDUALS, *ROUND_RESIDUALS) if item not in body
    ]
    decisions = [item for item in USER_DECISION_RESIDUALS if item not in body]
    missing_uncovered = [item for item in UNCOVERED_SCOPE if item not in body]
    over = oversized_functions(tree_path(root, SELF))
    return [
        factory(
            "ec04-self-is-in-the-tooling-scope",
            not missing_scope,
            f"{TOOLING_JUDGE} 的 IN_SCOPE 缺少：{missing_scope}",
        ),
        factory(
            "ec04-residuals-are-registered",
            not missing_residuals and not decisions and USER_DECISION_MARK in body,
            f"GOAL 正文缺少残余：{missing_residuals}；缺「{USER_DECISION_MARK}」的：{decisions}",
        ),
        factory(
            "ec04-uncovered-scope-is-written",
            not missing_uncovered,
            f"GOAL 正文缺少未覆盖范围：{missing_uncovered}",
        ),
        factory(
            "ec04-self-has-no-oversized-function",
            not over,
            f"本验证器有超 {MAX_FUNCTION_LINES} 行函数：{over}",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-025 收口复检（标准断言集 + 本轮特有断言）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    standard = load_module(tree_path(root, STANDARD), "goal025_standard_for_closeout")
    if standard is None or not root.is_dir():
        print("FAIL goal025-standard-assertions-loadable -> 无法加载标准断言集")
        return 2
    factory = cast("Callable[[str, bool, str], object]", getattr(standard, "Verdict"))
    emit = cast("Callable[[Iterable[object]], bool]", getattr(standard, "emit"))
    collect = cast("Callable[[Path], list[object]]", getattr(standard, "standard_verdicts"))
    verdicts: list[object] = [*collect(root)]
    for builder in (
        ec01_verdicts,
        ec02_verdicts,
        ec03_verdicts,
        ec04_record_verdicts,
        ec04_scope_verdicts,
    ):
        verdicts.extend(builder(root, factory))
    return 0 if emit(verdicts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
