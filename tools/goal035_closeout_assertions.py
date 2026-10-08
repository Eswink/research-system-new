#!/usr/bin/env python3
"""GOAL-20261008-035 收口复检的**本轮特有断言集**（EC-04）。

与 GOAL-023…034 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal035_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-035 特有的断言**。

三条主轴（逐条对 GOAL-035 的 EC）：

1. **EC-01 来源支持**：验收结论**落 canonical**（`ReviewFindingStore` 端口 + SQLite/PG 实现 +
   迁移 `016`），判词有**唯一渲染点**（`criterion_line`：读面与失败消息共用，不各说一套），
   且「读得到」经**只读路由** `GET /runs/{run_id}/reviews`（已登记进隐私读面清单）。
2. **EC-02 可复现**：研究循环的 run 路径在实验跑到科学终态时封存 `ReproducibilityAudit` 并
   **随实验落库**；读面**独立重算**校验（`audit_verified`）而不是复述落库时写下的那句话。
3. **EC-03 评审联动**：分数来源 = 合约**自己声明**的字段路径（`declared_review_score`），
   判定仍走既有域函数（**不建第二套**）；**fail-closed 语义未变**（`review score unknown`
   仍在域里 —— 「没有评审结论」不得被改成默认通过）。

另有两条**记录面**断言（EC-04 自己的交付面）：判词归档在树（两份、二进制写盘 CR=0）；
`IN_SCOPE` 纯收紧（本轮验证器与断言集都在清单里）。

**两条纪律**（承 GOAL-027…034 的实测教训）：

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
    ("tests/e2e/test_two_dimensional_coverage_and_claim_relation.py", 5),
    ("tests/e2e/test_reproducibility_conclusion_on_the_run_path.py", 3),
    ("tests/e2e/test_review_score_linkage_on_the_run_path.py", 3),
)

#: 三条轴**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/contracts/test_review_finding_store_contracts.py",
    "tests/observability/read_face_route_registry.py",
    "tests/domain/test_m5_domain_increments.py",
)

#: EC-01 落点（结论落 canonical + 唯一渲染点 + 只读路由）。
OBSERVATION = "packages/application/run_orchestration/acceptance_observation.py"
STORE_PORT = "packages/application/ports/review_finding_store.py"
STORE_SQLITE = "adapters/sqlite/review_finding_store.py"
STORE_POSTGRES = "adapters/postgres/review_finding_store.py"
MIGRATION = "adapters/postgres/migrations/016_review_findings.sql"
INSPECTION_ROUTER = "services/api/routers/inspection.py"
REGISTRY = "tests/observability/read_face_route_registry.py"
ROUTE_LITERAL = '"/runs/{run_id}/reviews"'

#: EC-02 落点（run 路径封存审计 + 落库 + 读面重算）。
EXECUTE = "packages/application/experiments/execute.py"
EXPERIMENT_TYPES = "packages/application/experiments/types.py"
EXPERIMENT_SUPPORT = "services/api/experiment_support.py"
EXPERIMENTS_ROUTER = "services/api/routers/experiments.py"

#: EC-03 落点（来源点名 + fail-closed 未变）。
GATE = "packages/application/run_orchestration/evaluation_gate.py"
CONTRACTS = "examples/contracts/task_contracts.yaml"
PROTOCOL = "examples/protocols/review_scored_research_v1.yaml"
ACCEPTANCE = "packages/domain/acceptance.py"
SCORE_PATH = "metric: review_decision.score"
FAIL_CLOSED = "review score unknown"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-035-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-035-verdict-clean.txt"

#: `IN_SCOPE` 清单所在判据（纯收紧：本轮两个新脚本必须在里面，只查在不在）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal035_closeout.py"
ASSERTIONS = "tools/goal035_closeout_assertions.py"


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


def _ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：结论落 canonical + 唯一渲染点 + 只读路由（且已登记隐私清单）。"""
    return [
        toolbox.verdict("ec01-store-port-present", (root / STORE_PORT).is_file()),
        toolbox.verdict("ec01-store-sqlite-present", (root / STORE_SQLITE).is_file()),
        toolbox.verdict("ec01-store-postgres-present", (root / STORE_POSTGRES).is_file()),
        toolbox.verdict("ec01-migration-present", (root / MIGRATION).is_file()),
        toolbox.verdict("ec01-single-render-point", _has_def(root, OBSERVATION, "criterion_line")),
        toolbox.verdict(
            "ec01-recorded-on-the-run-path",
            _has_def(root, OBSERVATION, "record_acceptance_evaluation"),
        ),
        toolbox.verdict("ec01-read-route-present", ROUTE_LITERAL in _text(root, INSPECTION_ROUTER)),
        toolbox.verdict("ec01-read-route-registered", ROUTE_LITERAL in _text(root, REGISTRY)),
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：run 路径封存审计 + 随实验落库 + 读面**重算**校验。"""
    return [
        toolbox.verdict("ec02-audit-on-the-run-path", _has_def(root, EXECUTE, "_audit_for")),
        toolbox.verdict(
            "ec02-audit-attached-to-the-outcome", "audit=_audit_for(" in _text(root, EXECUTE)
        ),
        toolbox.verdict("ec02-outcome-carries-audit", "audit:" in _text(root, EXPERIMENT_TYPES)),
        toolbox.verdict(
            "ec02-audit-persisted-with-the-experiment",
            "save_audit(outcome.audit)" in _text(root, EXPERIMENT_SUPPORT),
        ),
        toolbox.verdict(
            "ec02-read-face-recomputes", _has_def(root, EXPERIMENTS_ROUTER, "_apply_audit")
        ),
        toolbox.verdict(
            "ec02-read-face-reports-verification",
            "audit_verified" in _text(root, EXPERIMENTS_ROUTER),
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：分数来源由合约**自己声明** + 声明面新增 + fail-closed 语义未变。"""
    contracts = _text(root, CONTRACTS)
    return [
        toolbox.verdict(
            "ec03-declared-score-resolver", _has_def(root, GATE, "declared_review_score")
        ),
        toolbox.verdict(
            "ec03-resolver-used-on-the-path",
            "declared_review_score(contract, inputs.structured_output)" in _text(root, GATE),
        ),
        toolbox.verdict(
            "ec03-contract-declares-the-path",
            "review_scored_deliverable:" in contracts and SCORE_PATH in contracts,
        ),
        toolbox.verdict(
            "ec03-protocol-uses-the-contract",
            "task_contract: review_scored_deliverable" in _text(root, PROTOCOL),
        ),
        toolbox.verdict("ec03-fail-closed-unchanged", FAIL_CLOSED in _text(root, ACCEPTANCE)),
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/028 的实测教训）。"""
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
        *_ec01_verdicts(root, toolbox),
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
