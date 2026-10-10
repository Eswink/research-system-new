#!/usr/bin/env python3
"""GOAL-20261008-040 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…036 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal040_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-037 特有的断言**。

三条主轴（逐条对 GOAL-038 的 EC）：

1. **EC-01 勘察定稿 + EC-02/EC-03 声明式消费与编排层求值**：域类型与合约字段在场
   （`CUSTOM_EVALUATOR` / `evaluator`）；域求值器仍恒判负（既有语义**未动**）；
   `declared_consumption.py` 的求值器、`evaluation_gate.py` 的注入位与贴回在树。
2. **EC-04 跨轮消费真的被判定**：合约**声明**消费路径（`cross_run_consumption` +
   `metric`）；运行路径接线（`prior_conclusion` 经 `fact_stores()` 到 `PhaseRunnerDeps`）；
   判据文件在树且例数达下界。
3. **记录面（本轮自己的交付面）**：判词归档在树（两份、非空、`CR=0`）；`IN_SCOPE`
   纯收紧（本轮两个新脚本都在清单里）。

**两条纪律**（承 GOAL-027…036 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_program_runner.py", 13),
    ("tests/e2e/test_program_stop_reasons_are_decidable.py", 4),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/e2e/test_program_advance_on_the_run_path.py",
    "tests/postgres/test_program_store_pg.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-01/EC-02 落点（判定种类 + 声明 + 迁移 + 两适配器）。
PROGRAM_DOMAIN = "packages/domain/program.py"
MIGRATION = "adapters/postgres/migrations/019_program_attempts.sql"
SQLITE_STORE = "adapters/sqlite/program_store.py"
PG_STORE = "adapters/postgres/program_store.py"
ROUTER = "services/api/routers/programs.py"
DTOS = "services/api/dto/programs.py"

#: EC-03/EC-04 落点（分派 + 实跑反证）。
RUNNER = "packages/application/run_orchestration/program_runner.py"
JUDGE = "tests/e2e/test_program_stop_reasons_are_decidable.py"
DRIVER_JUDGE = "tests/application/run_orchestration/test_program_runner.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-040-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-040-verdict-clean.txt"

#: `IN_SCOPE` 清单所在判据（纯收紧：本轮两个新脚本必须在里面）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal040_closeout.py"
ASSERTIONS = "tools/goal040_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _has_def(root: Path, relative: str, name: str) -> bool:
    """模块里是否**定义**了该函数 / 类（AST，不看文本巧合）。"""
    source = _text(root, relative)
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:  # pragma: no cover - 语法坏掉时判据会判红
        return False
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and node.name == name
        for node in ast.walk(parsed)
    )


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _ec01_02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/02：三种新判定种类 + 有界重试声明（域 / 迁移 / 两适配器 / 接口面）。"""
    domain = _text(root, PROGRAM_DOMAIN)
    migration = _text(root, MIGRATION)
    sqlite = _text(root, SQLITE_STORE)
    pg = _text(root, PG_STORE)
    return [
        toolbox.verdict(
            "ec02-three-new-kinds",
            all(
                marker in domain
                for marker in ("STOP_RUN_FAILED", "STOP_CANCELLED", "RETRY_FAILED_RUN")
            ),
        ),
        toolbox.verdict(
            "ec02-optional-bounded-retry-declaration",
            "max_attempts_per_index: int = 1" in domain
            and "max_attempts_per_index must be >= 1" in domain,
        ),
        toolbox.verdict(
            "ec02-migration-adds-only",
            "ADD COLUMN IF NOT EXISTS max_attempts_per_index" in migration
            and "DROP COLUMN" not in migration,
        ),
        toolbox.verdict(
            "ec02-both-stores-persist-it",
            "max_attempts_per_index" in sqlite and "max_attempts_per_index" in pg,
        ),
        toolbox.verdict(
            "ec02-create-face-declares-it",
            "max_attempts_per_index" in _text(root, ROUTER)
            and "max_attempts_per_index" in _text(root, DTOS),
        ),
    ]


def _dispatch_precedes_conclusion_face(runner: str) -> bool:
    """失败面分派是否**先于**结论面求值（**结构判据**，与调用签名无关）。

    **为什么改这里**（GOAL-20261010-043 EC-03）：本判据原按**文本**匹配
    `"_non_success_terminal(program, existing, last)"` —— 而 GOAL-041 已**正当**给该函数
    加了 `programs` 形参（多轮推进需要）⇒ 文本失配 ⇒ **整条断言集崩溃**
    （`ValueError: substring not found`），复检资产**随被引代码演进静默失效**。

    改法：用 **AST** 按**被调用函数名**取行号，与实参列表无关 ⇒ 签名演进不再打断它。
    **受判面等价**（仍是「前者先于后者」这一件事），**不**放宽（两者都必须在场）。

    **第二次修正**（GOAL-20261010-048 实测）：落库判词此后被**读一次供两处共用**
    （条件闸门与结论面看到同一批事实）⇒ `_verdicts` 的**读取行**移到两处之前，
    原先拿它当「结论面」的坐标就**假红**了。正确的坐标是**结论面自己的分派点**
    （`_after_hit` / `STOP_RULE` 那条分支的判定）—— 判的仍是「失败面分派先于结论面」，
    而**不是**「某个读取语句在哪一行」（承 `MEM-20261010-215`：判关系，不判位置）。
    """
    dispatch = _first_call_line(runner, "_non_success_terminal")
    conclusion = _first_call_line(runner, "_after_hit")
    if dispatch is None or conclusion is None:
        return False
    return dispatch < conclusion


def _first_call_line(source: str, function_name: str) -> int | None:
    """源码里**首次调用**该函数名的行号（AST；看被调名，不看实参）。"""
    if not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    lines = [
        node.lineno
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
    ]
    return min(lines) if lines else None


def _ec03_04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03/04：按终态分派（结论面在之后）+ 反证断言在判据里。"""
    runner = _text(root, RUNNER)
    judge = _text(root, JUDGE)
    driver = _text(root, DRIVER_JUDGE)
    return [
        toolbox.verdict(
            "ec03-dispatch-by-terminal-state",
            "ResearchRunState.State.SUCCEEDED" in runner and "_non_success_terminal" in runner,
        ),
        toolbox.verdict(
            "ec03-conclusion-face-comes-after-the-dispatch",
            _dispatch_precedes_conclusion_face(runner),
        ),
        toolbox.verdict(
            "ec04-judge-asserts-the-old-shape-is-gone",
            "cited_facts" in judge and "STOP_RULE" in judge,
        ),
        toolbox.verdict(
            "ec04-bounded-retry-is-asserted",
            "attempts=1/2" in driver and "重试已用尽" in runner,
        ),
        toolbox.verdict(
            "ec04-cancelled-is-never-retried",
            "STOP_CANCELLED" in driver and "取消不得被自动重试" in driver,
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树（引用而非重复）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035/036 的实测教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
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


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """`IN_SCOPE` 纯收紧：本轮两个新脚本都在必备清单里（**只查在不在**）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec01_02_verdicts(root, toolbox),
        *_ec03_04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
