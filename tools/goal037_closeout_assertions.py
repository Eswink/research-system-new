#!/usr/bin/env python3
"""GOAL-20261008-037 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…036 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal037_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-037 特有的断言**。

四条主轴（逐条对 GOAL-037 的 EC）：

1. **EC-01/EC-02 canonical 骨架 + 程序编排**：域字段（`program_id` / `program_index`）
   与 `RunStore.for_program` / 迁移 `017`；程序域类型 + 端口 + 两适配器；三个路由
   （建程序 / 推进 / 读面）；启动面接线（`ExecutionRequest` 带程序归属）。
2. **EC-03 跨 run 知识**：`research_state_read` 实现 + 能力映射 + 会话绑定行 +
   两组合根接线 + 声明 + 一条只读 allow + 镜像表；协议与合约在树；判据文件达例数下界。
3. **EC-04 幂等与中断**：判据文件在树（例数下界）+ 口径标记（at-least-once / 幂等 /
   「恰好一次」的**否认**形态）。
4. **记录面（本轮自己的交付面）**：判词归档在树（两份、非空、`CR=0`）；`IN_SCOPE`
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
    ("tests/e2e/test_program_advance_on_the_run_path.py", 6),
    ("tests/e2e/test_cross_run_knowledge_on_the_run_path.py", 6),
    ("tests/e2e/test_program_idempotency_on_the_run_path.py", 5),
    ("tests/application/run_orchestration/test_program_runner.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/architecture/python/test_capability_coverage_is_implemented.py",
    "tests/application/preflight/test_release_expansion_is_read_only.py",
    "tests/application/preflight/test_read_grant_is_per_item.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-01/EC-02 落点（canonical 骨架 + 程序编排）。
DOMAIN_RUN = "packages/domain/run.py"
DOMAIN_PROGRAM = "packages/domain/program.py"
PROGRAM_PORT = "packages/application/ports/program_store.py"
MIGRATION = "adapters/postgres/migrations/017_research_programs.sql"
RUNNER = "packages/application/run_orchestration/program_runner.py"
ROUTER = "services/api/routers/programs.py"
DTOS = "services/api/dto/programs.py"
EXECUTION = "services/api/run_execution.py"
RUN_STORE_SQLITE = "adapters/sqlite/run_store.py"

#: EC-03 落点（跨 run 知识）。
STATE_READ = "adapters/canonical/research_state_read.py"
SURFACE = "adapters/canonical/read_surface.py"
PROVIDER = "adapters/canonical/read_provider.py"
BINDINGS = "services/api/session_tool_support.py"
PG_ROOT = "services/api/pg_composition.py"
CATALOG = "examples/config/tool_providers.yaml"
POLICY = "examples/config/policy.yaml"
SCOPE_MIRROR = "packages/application/preflight/policy_check.py"
PROTOCOL = "examples/protocols/cross_run_knowledge_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
CONSUME_CONTRACT = "cross_run_consumption_deliverable"

#: EC-04 落点（幂等与中断）。
IDEMPOTENCY_JUDGE = "tests/e2e/test_program_idempotency_on_the_run_path.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-037-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-037-verdict-clean.txt"

#: `IN_SCOPE` 清单所在判据（纯收紧：本轮两个新脚本必须在里面）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal037_closeout.py"
ASSERTIONS = "tools/goal037_closeout_assertions.py"

#: 会话绑定表里的那一条（逐字）。
BINDING_ROW = '("research_state.read", "m12_artifact", "research_state_read")'


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
    """EC-01/EC-02：canonical 骨架（域 / 端口 / 迁移 / 存储）与程序编排（驱动 / 路由 / 接线）。"""
    domain = _text(root, DOMAIN_RUN)
    runner = _text(root, RUNNER)
    router = _text(root, ROUTER)
    return [
        toolbox.verdict(
            "ec01-run-carries-program-fields",
            "program_id: str | None = None" in domain
            and "program_index: int | None = None" in domain,
        ),
        toolbox.verdict(
            "ec01-for-program-query",
            "def for_program" in _text(root, RUN_STORE_SQLITE)
            and "for_program" in _text(root, "packages/application/ports/run_store.py"),
        ),
        toolbox.verdict(
            "ec01-program-domain-and-port",
            _has_def(root, DOMAIN_PROGRAM, "ResearchProgram")
            and _has_def(root, PROGRAM_PORT, "ProgramStore"),
        ),
        toolbox.verdict(
            "ec01-migration-017",
            "research_programs" in _text(root, MIGRATION)
            and "program_decisions" in _text(root, MIGRATION),
        ),
        toolbox.verdict("ec02-driver-present", _has_def(root, RUNNER, "advance_program")),
        toolbox.verdict(
            "ec02-driver-decisions-are-distinguishable",
            all(marker in runner for marker in ("STOP_RULE", "STOP_GUARDRAIL", "DEDUP", "WAIT")),
        ),
        toolbox.verdict(
            "ec02-router-three-faces",
            '"/projects/{project_id}/programs"' in router
            and '"/programs/{program_id}"' in router
            and '"/programs/{program_id}/advance"' in router,
        ),
        toolbox.verdict(
            "ec02-start-face-carries-program-binding",
            "program_id=inputs.program_id" in _text(root, EXECUTION)
            or "program_id=req.program_id" in _text(root, EXECUTION),
        ),
        toolbox.verdict("ec02-dtos-present", _text(root, DTOS) != ""),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：跨 run 知识的五件事 + 协议与合约。"""
    return [
        toolbox.verdict(
            "ec03-implementation-module",
            _has_def(root, STATE_READ, "research_state_read"),
        ),
        toolbox.verdict(
            "ec03-tool-capability-mapping",
            '"research_state_read": "research_state.read"' in _text(root, SURFACE),
        ),
        toolbox.verdict(
            "ec03-provider-handler",
            '"research_state_read": self._research_state_read' in _text(root, PROVIDER),
        ),
        toolbox.verdict("ec03-session-binding", BINDING_ROW in _text(root, BINDINGS)),
        toolbox.verdict(
            "ec03-both-roots-wired",
            "program_store=ports.program_store" in _text(root, BINDINGS)
            and 'c["program_store"]' in _text(root, PG_ROOT),
        ),
        toolbox.verdict(
            "ec03-catalog-declares-it", "- research_state.read" in _text(root, CATALOG)
        ),
        toolbox.verdict(
            "ec03-policy-grants-it-once",
            _text(root, POLICY).count("- capability: research_state.read") == 1,
        ),
        toolbox.verdict(
            "ec03-scope-mirror-synced",
            '"research_state.read": "project"' in _text(root, SCOPE_MIRROR),
        ),
        toolbox.verdict(
            "ec03-protocol-and-contract",
            _text(root, PROTOCOL) != "" and f"  {CONSUME_CONTRACT}:" in _text(root, CONTRACTS),
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：幂等与中断（判据在树 + 口径标记逐条）。"""
    judge = _text(root, IDEMPOTENCY_JUDGE)
    return [
        toolbox.verdict("ec04-judge-present", judge != ""),
        toolbox.verdict("ec04-names-at-least-once", "at-least-once" in judge),
        toolbox.verdict("ec04-names-dedup-window", "DEDUP" in judge and "崩溃窗口" in judge),
        toolbox.verdict("ec04-denies-exactly-once", "恰好一次" in judge and "明确否认" in judge),
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
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
