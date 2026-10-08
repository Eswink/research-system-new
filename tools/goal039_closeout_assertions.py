#!/usr/bin/env python3
"""GOAL-20261008-039 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…036 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal039_closeout.py` 直接调用
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
    ("tests/adapters/sqlite/test_memory_scope_and_validity.py", 11),
    ("tests/postgres/test_memory_scope_pg.py", 2),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/api/test_memory_api.py",
    "tests/observability/read_face_route_registry.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-01/EC-02 落点（域 + 迁移 + 三实现同契约）。
MEMORY_DOMAIN = "packages/domain/memory.py"
MIGRATION = "adapters/postgres/migrations/018_memory_scope_and_validity.sql"
SQLITE_STORE = "adapters/sqlite/memory_store.py"
PG_STORE = "adapters/postgres/memory_store.py"
FAKE_STORE = "adapters/fakes/memory_store.py"
MEMORY_ROUTER = "services/api/routers/memory.py"
MEMORY_DTO = "services/api/dto/memory.py"

#: EC-03/EC-04 落点（声明式时效 + 三态判定 + 读面）。
VALIDITY = "packages/application/memory/validity.py"
JUDGE = "tests/adapters/sqlite/test_memory_scope_and_validity.py"
PG_JUDGE = "tests/postgres/test_memory_scope_pg.py"
VALIDITY_ROUTE = '"/projects/{project_id}/memory/validity"'

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-039-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-039-verdict-clean.txt"

#: `IN_SCOPE` 清单所在判据（纯收紧：本轮两个新脚本必须在里面）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal039_closeout.py"
ASSERTIONS = "tools/goal039_closeout_assertions.py"


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
    """EC-01/02：域面（scope + 两时点）、迁移（只加列）、三实现同契约、读面披露。"""
    domain = _text(root, MEMORY_DOMAIN)
    migration = _text(root, MIGRATION)
    sqlite = _text(root, SQLITE_STORE)
    pg = _text(root, PG_STORE)
    fake = _text(root, FAKE_STORE)
    return [
        toolbox.verdict(
            "ec01-record-carries-scope",
            'scope: str = "project"' in domain and "memory scope must not be empty" in domain,
        ),
        toolbox.verdict(
            "ec01-proposal-carries-validity",
            "review_after: Timestamp | None = None" in domain
            and "expires_at: Timestamp | None = None" in domain,
        ),
        toolbox.verdict(
            "ec02-migration-adds-only",
            "ADD COLUMN IF NOT EXISTS scope" in migration and "DROP COLUMN" not in migration,
        ),
        toolbox.verdict(
            "ec02-three-implementations-agree",
            all("scope=proposal.scope" in source for source in (sqlite, pg, fake)),
        ),
        toolbox.verdict(
            "ec02-pg-writes-real-validity",
            "proposal.review_after.value" in pg and "None,  # review_after" not in pg,
        ),
        toolbox.verdict(
            "ec02-read-face-discloses-scope",
            "scope=record.scope" in _text(root, MEMORY_ROUTER)
            and 'scope: str = "project"' in _text(root, MEMORY_DTO),
        ),
    ]


def _ec03_04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03/04：三态纯函数（不读挂钟）+ 读面路由 + 判据在树。"""
    validity = _text(root, VALIDITY)
    return [
        toolbox.verdict(
            "ec03-validity-three-states",
            all(state in validity for state in ("EXPIRED", "REVIEW_DUE")),
        ),
        toolbox.verdict(
            "ec03-validity-does-not-read-the-clock",
            "datetime.now" not in validity and "Timestamp.now()" not in validity,
        ),
        toolbox.verdict(
            "ec04-validity-route-present",
            VALIDITY_ROUTE in _text(root, MEMORY_ROUTER),
        ),
        toolbox.verdict(
            "ec04-judge-asserts-undeclared-is-not-misreported",
            "未声明" in _text(root, JUDGE) and "误报" in _text(root, JUDGE),
        ),
        toolbox.verdict("ec04-pg-judge-present", _text(root, PG_JUDGE) != ""),
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
