#!/usr/bin/env python3
"""GOAL-20260929-026 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023 / 024 / 025 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-026 特有的断言**：

- 逐 EC：判据文件在树 + **例数下界**（缺文件、例数掉下去，两向都判红）；
- **钉住的常量**：退避轨迹 `[30, 60, 100, 100]`、工具面与补偿面扫描下界 `400`、
  投递语义面的四个有界常量（豁免上限 / 扫描下界 / 分类下界 / CJK 正控制下界）；
- **EC-03 的产品修复**：`_consult_circuit` 对迁移异常必须 **fail-closed 抛**
  `CircuitOpenRelayError`（AST 断言，不是文本巧合）+ 豁免表在上限内且理由非空；
- **EC-05**：台账审计的**下界逻辑是行为判据**（空集 / 欠数集 / 有失败 job ⇒ 判红且点名，
  完整集 ⇒ 判绿）、台账 run id 有下界、两件新工具在树并进 `IN_SCOPE`（**纯收紧**）且与树根无关、
  记录面（前四 EC 终态 / 复检路径 / 子计划与记忆）、残余与未覆盖逐条、九项义务判定表、文件规模。

用法：`python tools/verify_goal026_closeout.py --root <树根> --verdict-only`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

STANDARD = "tools/closeout_recheck_assertions.py"
ENTRY = "tools/two_tree_recheck.py"
SELF = "tools/verify_goal026_closeout.py"
AUDIT = "tools/audit_goal026_ledger.py"
GOAL = ".cursor/plans/goals/GOAL-20260929-026-reliability-semantics-adversarial-self-check.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GATEWAY = "adapters/relay/gateway.py"
TRAJECTORY_FILE = "tests/adapters/sqlite/test_workflow_retry_trajectory.py"
TOOL_PLANE_JUDGE = "tests/application/test_tool_plane_breaker_boundary.py"
COMPENSATION_JUDGE = "tests/application/run_orchestration/test_compensation_boundary.py"
WORDING_JUDGE = "tests/architecture/python/test_delivery_semantics_wording.py"

#: 逐 EC：判据文件 + **例数下界**（下界是契约，不是「现在有多少」）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (
        (
            "tests/api/test_idempotency_sqlite_semantics.py",
            "tests/e2e/test_idempotency_canonical_dedup.py",
        ),
        (4, 2),
    ),
    "ec02": (
        (
            "tests/adapters/sqlite/test_workflow_lease_lifecycle.py",
            TRAJECTORY_FILE,
            "tests/worker/test_worker_renew_loop.py",
        ),
        (3, 2, 2),
    ),
    "ec03": (
        (
            "tests/adapters/relay/test_gateway_half_open_budget.py",
            "tests/adapters/sqlite/test_workflow_dead_letter_surface.py",
            "tests/adapters/sqlite/test_workflow_cancel_semantics.py",
            TOOL_PLANE_JUDGE,
        ),
        (5, 3, 3, 2),
    ),
    "ec04": (
        (
            "tests/adapters/sqlite/test_outbox_atomicity.py",
            COMPENSATION_JUDGE,
            WORDING_JUDGE,
        ),
        (5, 3, 6),
    ),
}

EXPECTED_TRAJECTORY = (30, 60, 100, 100)
EXPECTED_FLOOR = 400
EXPECTED_WORDING_BOUNDS = {
    "_MAX_EXEMPT": 8,
    "_MIN_SCANNED_FILES": 2500,
    "_MIN_CLASSIFIED": 16,
    "_MIN_CJK_CONTROL": 8,
}
EXPECTED_AUDIT_FLOORS = {"M0 Quality Gates": 8, "Push on main": 3}
EMPTY_SET_MARK = "未取证"
MAX_FUNCTION_LINES = 50
MIN_LEDGER_RUN_IDS = 8

SETTLED_EC = ("EC-01", "EC-02", "EC-03", "EC-04")
FINAL_EC = "EC-05"
REQUIRED_IN_SCOPE = (ENTRY, STANDARD, SELF, AUDIT)
INHERITED_RESIDUALS = "R-M1 R-D1 R-B1 R-N1 R-F1 R-F2 W-4 W-5 W-6 W-10 W-11 W-12".split()
INHERITED_G24 = "G24-1 G24-2 G24-3 G24-4 G24-5 G24-6".split()
ROUND_RESIDUALS = "R26-1 R26-2 R26-3 R26-4 R26-5 R26-6".split()
USER_DECISION_MARK = "需用户拍板"
UNCOVERED_SCOPE = ("读面未认证", "多租户", "BOLA", "部署面未验证", "R-M1 未收口")

#: 九项义务的判定表（EC-05 的交付物之一）：逐条出现在 GOAL 正文里。
NINE_OBLIGATIONS = (
    "idempotency key",
    "Task lease + heartbeat",
    "retry classification",
    "exponential backoff",
    "circuit breaker",
    "dead-letter",
    "cancellation semantics",
    "compensation for non-idempotent actions",
    "transactional outbox",
)

#: GitHub run 号形态（11 位数字）；盘符绝对路径（脚本不得硬编码某一棵树的根）。
_RUN_ID = re.compile(r"\b\d{11}\b")
_DRIVE = re.compile(r"[A-Za-z]:[\\/]")


def tree_path(root: Path, relative: str) -> Path:
    """把仓库相对路径挂到给定树根上（不硬编码任何仓库根）。"""
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


def literal(tree: ast.Module | None, name: str) -> object | None:
    """模块级常量的字面量取值（不可字面求值 ⇒ `None`）。"""
    for node in tree.body if tree is not None else ():
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if value is None or not any(isinstance(x, ast.Name) and x.id == name for x in targets):
            continue
        try:
            return cast("object", ast.literal_eval(value))
        except (ValueError, TypeError):
            return None
    return None


def test_case_count(root: Path, relative: str) -> int:
    tree = ast_module(root, relative)
    if tree is None:
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _name(node: ast.expr | None) -> str | None:
    """`Name` / `Attribute` 两种形态的名字；其它形态（含 `None`）⇒ `None`。"""
    if isinstance(node, ast.Name):
        return node.id
    return node.attr if isinstance(node, ast.Attribute) else None


def handler_denies(handler: ast.ExceptHandler) -> bool:
    """这条 except 分支是否「捕获迁移异常 ⇒ 抛 `CircuitOpenRelayError`」。"""
    target = handler.type
    parts = target.elts if isinstance(target, ast.Tuple) else [target]
    caught = {_name(part) for part in parts} & {"CircuitBreakerTransitionError"}
    raises = [node.exc for node in ast.walk(handler) if isinstance(node, ast.Raise)]
    raised = {_name(item.func) for item in raises if isinstance(item, ast.Call)}
    return bool(caught) and "CircuitOpenRelayError" in raised


def probe_budget_is_fail_closed(root: Path) -> bool:
    """`_consult_circuit` 里「迁移异常」那条 except 分支必须**抛** `CircuitOpenRelayError`。"""
    tree = ast_module(root, GATEWAY)
    for node in ast.walk(tree) if tree is not None else ():
        if isinstance(node, ast.Try) and any(handler_denies(item) for item in node.handlers):
            return True
    return False


def oversized_functions(root: Path, relative: str) -> list[str]:
    tree = ast_module(root, relative)
    if tree is None:
        return ["<不可解析>"]
    return sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.end_lineno
        and node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES
    )


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
    except Exception:  # 加载失败 ⇒ 相关判词判红，而不是整轮崩掉
        return None
    return module


def goal_metadata(root: Path) -> dict[str, object]:
    module = load_module(tree_path(root, GOVERNANCE), "goal026_governance_for_closeout")
    if module is None:
        return {}
    parser = cast(
        "Callable[[Path], tuple[dict[str, object], str]]", getattr(module, "parse_frontmatter")
    )
    metadata, _body = parser(tree_path(root, GOAL))
    return metadata


def ec_statuses(root: Path) -> dict[str, str]:
    criteria = goal_metadata(root).get("exit_criteria")
    if not isinstance(criteria, list):
        return {}
    found = ((str(item.get("id")), str(item.get("status"))) for item in criteria)
    return dict(item for item in found if isinstance(item, tuple))


def paths_exist(root: Path, raw: object) -> bool:
    if not isinstance(raw, list) or not raw:
        return False
    return all(isinstance(item, str) and tree_path(root, item).exists() for item in raw)


def criteria_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """逐 EC：判据文件在树 + 例数下界（缺文件、例数掉下去，两向都判红）。"""
    v = factory
    verdicts: list[object] = []
    for key, (files, floors) in EC_FILES.items():
        present = all(tree_path(root, item).is_file() for item in files)
        verdicts.append(v(f"{key}-files", present, f"缺文件：{files}"))
        counts = tuple(test_case_count(root, item) for item in files)
        above = all(count >= floor for count, floor in zip(counts, floors, strict=True))
        verdicts.append(v(f"{key}-cases-floor", above, f"例数 {counts} 低于下界 {floors}"))
    return verdicts


def pinned_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """钉住的常量与产品修复：退避轨迹 / fail-closed 探针 / 三处扫描下界 / 豁免表。"""
    v = factory
    wording = ast_module(root, WORDING_JUDGE)
    observed = {name: literal(wording, name) for name in EXPECTED_WORDING_BOUNDS}
    exempt = literal(wording, "_EXEMPT")
    limit = EXPECTED_WORDING_BOUNDS["_MAX_EXEMPT"]
    bounded = isinstance(exempt, dict) and 0 < len(exempt) <= limit
    reasons = exempt.values() if isinstance(exempt, dict) else ()
    reasoned = all(isinstance(item, str) and len(item) >= 20 for item in reasons)
    floors = {
        literal(ast_module(root, TOOL_PLANE_JUDGE), "_MIN_SCANNED"),
        literal(ast_module(root, COMPENSATION_JUDGE), "_MIN_SCANNED"),
    }
    trajectory = literal(ast_module(root, TRAJECTORY_FILE), "_EXPECTED_GAPS")
    # 常量写成 `list` 还是 `tuple` 不是语义；漂移指的是**值**。
    drift = list(trajectory) if isinstance(trajectory, (list, tuple)) else None
    return [
        v("ec02-trajectory-pinned", drift == list(EXPECTED_TRAJECTORY), f"漂移：{trajectory!r}"),
        v("ec03-probe-budget-fail-closed", probe_budget_is_fail_closed(root), "不再 fail-closed"),
        v("ec03-ec04-scan-floor-pinned", floors == {EXPECTED_FLOOR}, f"漂移：{floors}"),
        v("ec04-wording-bounds-pinned", observed == EXPECTED_WORDING_BOUNDS, f"漂移：{observed}"),
        v("ec04-exemptions-bounded", bounded and reasoned, f"豁免表越界 / 空 / 缺理由：{exempt!r}"),
    ]


def run_audit(script: Path, runs_dir: Path, prefix: str) -> tuple[int, str]:
    """在给定目录上跑一次台账审计（子进程：把「下界逻辑」当**行为**判，不当源码文本判）。"""
    completed = subprocess.run(
        [sys.executable, str(script), "--runs-dir", str(runs_dir), "--prefix", prefix],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout + completed.stderr


def probe_dir(base: Path, name: str, jobs: list[dict[str, object]]) -> Path:
    """合成一个输入目录（`base/name`）：一对 run / jobs 文件（run 名走 `MIN_JOBS` 的键）。"""
    directory = base / name
    directory.mkdir()
    run: dict[str, object] = {
        "name": "M0 Quality Gates",
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
        "head_sha": "0" * 40,
    }
    (directory / "probe-run-1.json").write_text(json.dumps(run), encoding="utf-8")
    (directory / "probe-run-1-jobs.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
    return directory


def audit_probe_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-05：台账审计的下界判定必须在**行为**上成立。

    这是对 `scratch/audit_goal025_ledger.sh`（把空 `jobs` 读成「没有失败」）的修复证据：
    只有行为判据算证据，源码里有 `if not jobs` 不算。
    """
    v = factory
    script = tree_path(root, AUDIT)
    if not script.is_file():
        return [v("ec05-audit-behaviour", False, f"缺 {AUDIT}")]
    ok: list[dict[str, object]] = [{"name": f"j{i}", "conclusion": "success"} for i in range(8)]
    failed: list[dict[str, object]] = [*ok[:7], {"name": "j7", "conclusion": "failure"}]
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        empty_rc, empty_out = run_audit(script, probe_dir(base, "empty", []), "probe-")
        short_rc, short_out = run_audit(script, probe_dir(base, "short", ok[:2]), "probe-")
        bad_rc, bad_out = run_audit(script, probe_dir(base, "bad", failed), "probe-")
        good_rc, good_out = run_audit(script, probe_dir(base, "good", ok), "probe-")
    return [
        v("ec05-audit-empty-jobs", empty_rc != 0 and EMPTY_SET_MARK in empty_out, f"rc={empty_rc}"),
        v("ec05-audit-short-jobs", short_rc != 0 and EMPTY_SET_MARK in short_out, f"rc={short_rc}"),
        v("ec05-audit-names-failed-job", bad_rc != 0 and "j7" in bad_out, f"rc={bad_rc}"),
        v("ec05-audit-good-set", good_rc == 0 and "failed=0" in good_out, f"rc={good_rc}"),
    ]


def record_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-05：记录面（前四 EC 终态 / 时序 / 复检路径可解析 / 子计划与记忆在位）。"""
    v = factory
    statuses = ec_statuses(root)
    metadata = goal_metadata(root)
    latest = metadata.get("latest_recheck")
    latest_ok = isinstance(latest, str) and "/" in latest and tree_path(root, latest).is_file()
    settled = [f"{item}={statuses.get(item)}" for item in SETTLED_EC]
    return [
        v(
            "ec05-ec01-to-ec04-pass",
            all(statuses.get(i) == "PASS" for i in SETTLED_EC),
            f"{settled}",
        ),
        v("ec05-final-ec-timing", statuses.get(FINAL_EC) in ("PASS", "PENDING"), "状态异常"),
        v("ec05-latest-recheck", latest_ok, f"latest_recheck 不可解析：{latest!r}"),
        v(
            "ec05-child-plans-and-memories",
            paths_exist(root, metadata.get("child_plans"))
            and paths_exist(root, metadata.get("memory_entries")),
            "child_plans 或 memory_entries 有空项 / 不存在",
        ),
    ]


def scope_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-05：射程（两件新工具进 `IN_SCOPE`）、残余、未覆盖、九项义务表、文件规模。"""
    v = factory
    scope = literal(ast_module(root, TOOLING_JUDGE), "IN_SCOPE")
    declared = tuple(str(item) for item in scope) if isinstance(scope, tuple) else ()
    missing_scope = [item for item in REQUIRED_IN_SCOPE if item not in declared]
    body = read_text(root, GOAL)
    residuals = (*INHERITED_RESIDUALS, *INHERITED_G24, *ROUND_RESIDUALS)
    missing_residuals = [item for item in residuals if item not in body]
    missing_obligations = [item for item in NINE_OBLIGATIONS if item not in body]
    missing_uncovered = [item for item in UNCOVERED_SCOPE if item not in body]
    over = oversized_functions(root, SELF)
    return [
        v("ec05-tooling-scope", not missing_scope, f"IN_SCOPE 缺少：{missing_scope}"),
        v(
            "ec05-residuals",
            not missing_residuals and USER_DECISION_MARK in body,
            f"GOAL 正文缺少残余：{missing_residuals}",
        ),
        v("ec05-nine-obligations-table", not missing_obligations, f"缺条目：{missing_obligations}"),
        v("ec05-uncovered-scope", not missing_uncovered, f"缺：{missing_uncovered}"),
        v("ec05-self-size", not over, f"超 {MAX_FUNCTION_LINES} 行函数：{over}"),
    ]


def ledger_verdicts(root: Path, factory: Callable[[str, bool, str], object]) -> list[object]:
    """EC-05：台账证据（审计脚本形状 / run id 下界 / 两件新工具在树且与树根无关）。"""
    v = factory
    floors = literal(ast_module(root, AUDIT), "MIN_JOBS")
    mark = literal(ast_module(root, AUDIT), "EMPTY_SET_MARK")
    ids = tuple(sorted(set(_RUN_ID.findall(read_text(root, GOAL)))))
    offenders = [item for item in (SELF, AUDIT) if _DRIVE.search(read_text(root, item))]
    in_tree = all(tree_path(root, item).is_file() for item in (SELF, AUDIT))
    return [
        v("ec05-audit-job-floors", floors == EXPECTED_AUDIT_FLOORS, f"漂移：{floors!r}"),
        v(
            "ec05-audit-empty-mark",
            mark == EMPTY_SET_MARK and read_text(root, AUDIT).count(EMPTY_SET_MARK) >= 2,
            f"空集标记漂移或未在空集分支使用：{mark!r}",
        ),
        v("ec05-ledger-run-ids", len(ids) >= MIN_LEDGER_RUN_IDS, f"现有 {len(ids)} 个 run id"),
        v("ec05-new-tools-in-tree", in_tree and not offenders, f"缺文件或盘符路径：{offenders}"),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-026 收口复检（标准断言集 + 本轮特有断言）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    standard = load_module(tree_path(root, STANDARD), "goal026_standard_for_closeout")
    if standard is None or not root.is_dir():
        print("FAIL goal026-standard-assertions-loadable -> 无法加载标准断言集")
        return 2
    factory = cast("Callable[[str, bool, str], object]", getattr(standard, "Verdict"))
    emit = cast("Callable[[Iterable[object]], bool]", getattr(standard, "emit"))
    collect = cast("Callable[[Path], list[object]]", getattr(standard, "standard_verdicts"))
    verdicts: list[object] = [*collect(root)]
    builders = (
        criteria_verdicts,
        pinned_verdicts,
        audit_probe_verdicts,
        record_verdicts,
        scope_verdicts,
        ledger_verdicts,
    )
    for builder in builders:
        verdicts.extend(builder(root, factory))
    return 0 if emit(verdicts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
