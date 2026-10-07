#!/usr/bin/env python3
"""GOAL-20261008-033 收口复检的**本轮特有断言集**（EC-04）。

与 GOAL-023…032 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal033_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-033 特有的断言**。

四条主轴（逐条对 GOAL-033 的 EC）：

1. **EC-01 死信恢复产品入口**：`services/api/routers/tasks.py` 在树且**真的**调用了
   `.requeue(`（AST，不是文本巧合）；它**不**出现 `ResearchTaskState.transition`
   （不建第二套）；`app.py` 注册了 `tasks.router`；判据文件在树且例数达下界；
   `docs/api/openapi.m13.json` 里 `/tasks/{task_id}/retry` 在位（生成物同轮更新）。
2. **EC-02 死信 ↔ run 续跑协同**：`tests/e2e/test_dead_letter_run_coordination_matrix.py`
   在树且例数达下界；它断言的三面（run 状态两条组合 / 派发方 spy / 任务面两路）由
   `CASE_FLOORS` 的下界承载；`RetryDispatchScheduler` 的状态过滤**仍在**
   （`run.state != ResearchRunState.State.PAUSED` 那一句在位 —— 它是 ③ 判据的被判机制）。
3. **EC-03 续跑覆盖度声明集**：声明集模块与对账判据在树；声明集规模与三面下界由模块自身
   的常量承载（`MIN_DECLARED_CASES` / `MIN_HANDLED` / `MIN_REFUSED` / `MIN_NOT_THIS_ENTRY`
   逐条在位且**下界值未被调低**）；既有覆盖度矩阵判据文件**仍在树**（引用而非重复）。
4. **MAINLINE 宪章与程序表**：`MAINLINE.md` 在树；序 1 的 id 已换成真实 GOAL id；
   宪章判据在树且例数达下界。

另有两条**记录面**断言（EC-04 自己的交付面）：判词归档在树（两份，二进制写盘 CR=0）；
`IN_SCOPE` 纯收紧（本轮验证器与断言集都在清单里）。

**两条纪律**（承 GOAL-027…032 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_task_retry_api.py", 9),
    ("tests/e2e/test_dead_letter_run_coordination_matrix.py", 6),
    ("tests/tooling/test_resume_coverage_declaration_matches_source.py", 6),
    ("tests/tooling/test_mainline_program_is_intact.py", 8),
)

#: EC-03 声明集的**下界常量**必须逐条在位且不低于这些值（调低即判红）。
DECLARATION_FLOORS: tuple[tuple[str, int], ...] = (
    ("MIN_DECLARED_CASES = 14", 14),
    ("MIN_HANDLED = 2", 2),
    ("MIN_REFUSED = 6", 6),
    ("MIN_NOT_THIS_ENTRY = 5", 5),
)

#: EC-03 引用（而非重复）的既有连续性套件 —— 必须仍在树。
PRIOR_CONTINUITY_SUITES: tuple[str, ...] = (
    "tests/e2e/test_research_continuity_coverage_matrix.py",
    "tests/e2e/test_restart_rebuild_resume.py",
    "tests/e2e/test_retry_park_and_resume.py",
    "tests/e2e/test_workflow_restart_recovery.py",
)

#: EC-01 的产品面（路由 / DTO / 组合根注册）。
ROUTER = "services/api/routers/tasks.py"
DTO = "services/api/dto/tasks.py"
APP = "services/api/app.py"
OPENAPI = "docs/api/openapi.m13.json"
RETRY_PATH = "/tasks/{task_id}/retry"

#: EC-02 的被判机制（派发方只扫 `PAUSED` 的那一句）。
SCHEDULER = "services/api/scheduler.py"
_PAUSED_FILTER = "run.state != ResearchRunState.State.PAUSED"

#: EC-03 的声明集与对账判据。
DECLARATION = "tests/tooling/resume_coverage_declaration.py"

#: MAINLINE 宪章与其判据。
CHARTER = ".cursor/plans/goals/MAINLINE.md"
CHARTER_JUDGE = "tests/tooling/test_mainline_program_is_intact.py"

#: 本轮归档的判词落点（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-033-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-033-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _calls_the_port(root: Path) -> bool:
    """`tasks.py` 里是否有 `.requeue(` 的**调用**（AST，不是文本巧合）。"""
    source = _text(root, ROUTER)
    if not source:
        return False
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "requeue":
                return True
    return False


def _does_not_reimplement(root: Path) -> bool:
    """`tasks.py` 不得自行迁移任务状态（那等于第二套恢复逻辑）。"""
    source = _text(root, ROUTER)
    if not source:
        return False
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "transition":
            return False
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "UPDATE tasks" in node.value.upper():
                return False
    return True


def _count_test_cases(root: Path, relative: str) -> int:
    """该文件里 `test_*` 的**定义**数（AST；参数化只算一条定义）。"""
    source = _text(root, relative)
    if not source:
        return 0
    tree = ast.parse(source)
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _declaration_floors_hold(root: Path) -> tuple[bool, str]:
    """声明集的下界常量在位且**不低于**名录值（调低即判红）。"""
    source = _text(root, DECLARATION)
    if not source:
        return False, "declaration module missing"
    problems: list[str] = []
    for literal, floor in DECLARATION_FLOORS:
        match = re.search(re.escape(literal.split(" = ")[0]) + r"\s*=\s*(\d+)", source)
        if match is None:
            problems.append(f"missing {literal}")
            continue
        if int(match.group(1)) < floor:
            problems.append(f"{literal} lowered to {match.group(1)}")
    return not problems, ",".join(problems)


def _charter_binds_a_real_goal(root: Path) -> bool:
    """宪章程序表序 1 的 id 已换成真实 GOAL id（不留占位符）。"""
    source = _text(root, CHARTER)
    if not source:
        return False
    if "GOAL-PLACEHOLDER" in source:
        return False
    return re.search(r"\|\s*1\s*\|\s*GOAL-\d{8}-\d{3}\s*\|", source) is not None


def _product_entry_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01 产品入口面（路由在树 / 真的调 Port / 不建第二套 / 已注册 / 快照在位）。"""
    return [
        toolbox.verdict("ec01-router-present", (root / ROUTER).is_file()),
        toolbox.verdict("ec01-dto-present", (root / DTO).is_file()),
        toolbox.verdict("ec01-router-calls-the-port", _calls_the_port(root)),
        toolbox.verdict("ec01-router-does-not-reimplement", _does_not_reimplement(root)),
        toolbox.verdict(
            "ec01-router-registered", "app.include_router(tasks.router)" in _text(root, APP)
        ),
        toolbox.verdict("ec01-openapi-carries-the-route", RETRY_PATH in _text(root, OPENAPI)),
    ]


def _coordination_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 协同面（矩阵在树 + 被判机制仍在）。"""
    return [
        toolbox.verdict(
            "ec02-coordination-matrix-present",
            (root / "tests/e2e/test_dead_letter_run_coordination_matrix.py").is_file(),
        ),
        toolbox.verdict(
            "ec02-dispatcher-paused-filter-intact", _PAUSED_FILTER in _text(root, SCHEDULER)
        ),
    ]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03 声明集面（模块在树 + 下界常量未被调低）。"""
    return [
        toolbox.verdict("ec03-declaration-present", (root / DECLARATION).is_file()),
        _declaration_floor_verdict(root, toolbox),
    ]


def _charter_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """MAINLINE 宪章面（宪章 + 判据在树 + 程序表已绑真实 id）。"""
    return [
        toolbox.verdict("mainline-charter-present", (root / CHARTER).is_file()),
        toolbox.verdict("mainline-charter-judge-present", (root / CHARTER_JUDGE).is_file()),
        toolbox.verdict("mainline-program-binds-a-real-goal", _charter_binds_a_real_goal(root)),
    ]


def _floor_and_suite_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据例数下界 + 既有连续性套件仍在树。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_CONTINUITY_SUITES:
        verdicts.append(
            toolbox.verdict(f"prior-suite-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 MEM-20260928-152）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出 ⇒ 不收敛）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", ARCHIVE_CURRENT), ("clean", ARCHIVE_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    goal = _text(
        root,
        ".cursor/plans/goals/"
        "GOAL-20261008-033-dead-letter-product-entry-and-resume-coordination.md",
    )
    return [
        *_product_entry_verdicts(root, toolbox),
        *_coordination_verdicts(root, toolbox),
        *_declaration_verdicts(root, toolbox),
        *_charter_verdicts(root, toolbox),
        *_floor_and_suite_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        toolbox.verdict("goal-text-readable", bool(goal)),
    ]


def _declaration_floor_verdict(root: Path, toolbox: Any) -> Any:
    ok, detail = _declaration_floors_hold(root)
    return toolbox.verdict("ec03-declaration-floors-hold", ok, detail)
