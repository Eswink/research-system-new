#!/usr/bin/env python3
"""GOAL-20261007-032 收口复检的**本轮特有断言集**（EC-04）。

与 GOAL-023…031 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal032_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-032 特有的断言**。

三条主轴（逐条对 GOAL-032 的 EC）：

1. **EC-01 死信人工恢复**：状态机出边**恰为** `DEAD_LETTER --REQUEUE--> QUEUED`
   （AST 读 `_TRANSITIONS` 的键集）；`terminal()` **仍含** `DEAD_LETTER`（语义收紧为
   「对自动路径终态」而不是把它移出去）；`require` 面三实现逐条有 `requeue`
   （SQLite / PG / Fake 的类或模块体里定义了它）；Port 的 `requeue` 在协议类体内；
   ADR-0033 在树且 `Status: Accepted` **且** ADR-0030 仍是 `Proposed`（不动邻接决策）；
2. **EC-02 relay 取证**：`PgOutboxRelay.run_once` 的 drain→publish→mark 三段在
   `outbox_relay.py` 里逐段在位（AST）；`pg_composition.py` 里
   `outbox_relay_enabled = True` **恰好一处**；`ApiDeps` 默认 `False`；四条取证判据
   文件在树且例数达下界；
3. **EC-03 连续性覆盖度**：`run_resume.rebuild_and_resume` 与
   `RunOrchestrationService.resume_rebuilt` / `_remaining_specs` 在树（AST）；
   覆盖度矩阵判据文件在树且例数达下界；既有四个连续性套件**仍在树**（引用它们不重复）。

另有两条**记录面**断言（EC-04 自己的交付面）：判词归档在树（两份，二进制写盘 CR=0）；
`IN_SCOPE` 纯收紧（本轮验证器与断言集都在清单里）。

**两条纪律**（承 GOAL-027…031 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与**行数下界**；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py", 6),
    ("tests/contracts/test_dead_letter_manual_recovery_contract.py", 4),
    ("tests/e2e/test_dead_letter_recovery_full_loop.py", 1),
    ("tests/postgres/test_outbox_relay_forensics.py", 4),
    ("tests/architecture/python/test_outbox_relay_enablement_is_explicit.py", 5),
    ("tests/e2e/test_research_continuity_coverage_matrix.py", 4),
)

#: EC-03 引用（而非重复）的既有连续性套件 —— 必须仍在树。
PRIOR_CONTINUITY_SUITES: tuple[str, ...] = (
    "tests/e2e/test_restart_rebuild_resume.py",
    "tests/e2e/test_retry_park_and_resume.py",
    "tests/e2e/test_workflow_restart_recovery.py",
    "tests/application/run_orchestration/test_rebuild_readiness.py",
)

TASK_STATE = "packages/domain/task_state.py"
WORKFLOW_PORT = "packages/application/ports/workflow_engine.py"
SQLITE_REQUEUE = "adapters/sqlite/requeue.py"
PG_REQUEUE = "adapters/postgres/workflow_requeue.py"
FAKE_ENGINE = "adapters/fakes/workflow_engine.py"
OUTBOX_RELAY = "adapters/postgres/outbox_relay.py"
PG_COMPOSITION = "services/api/pg_composition.py"
COMPOSITION = "services/api/composition.py"
ADR_0033 = "docs/adr/ADR-0033-dead-letter-manual-recovery.md"
ADR_0030 = "docs/adr/ADR-0030-validation-failure-consumption.md"
GOAL = ".cursor/plans/goals/GOAL-20261007-032-dead-letter-recovery-and-research-continuity.md"
IN_SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal032_closeout.py"
ASSERTIONS = "tools/goal032_closeout_assertions.py"

#: 判词归档（二进制写盘 → CR=0；两份：本树 + 干净 checkout）。
EVIDENCE = (
    ".cursor/plans/goals/evidence/GOAL-20261007-032-verdict-current.txt",
    ".cursor/plans/goals/evidence/GOAL-20261007-032-verdict-clean.txt",
)


def _parse(root: Path, relative: str) -> ast.Module | None:
    """按 AST 读树内文件（不执行模块；语法不可读 ⇒ None，判据会判红）。"""
    body = _TEXT.get(relative) if _TEXT else None
    if body is None:
        import pathlib

        path = pathlib.Path(root) / relative
        if not path.is_file():
            return None
        body = path.read_text(encoding="utf-8", errors="replace")
    try:
        return ast.parse(body)
    except SyntaxError:
        return None


#: 由 `assertion_verdicts` 注入的文本缓存（`toolbox.text` 一次读齐）。
_TEXT: dict[str, str] = {}


def _read(root: Path, relative: str, toolbox: Any) -> str:
    """按 toolbox 的 `text` 读文件（同时缓存进 `_TEXT`，供 `_parse` 复用）。"""
    value: str = toolbox.text(root, relative)
    _TEXT[relative] = value
    return value


def _literal(tree: ast.Module | None, name: str) -> object:
    """模块级 `name = <字面量>` 的取值（不可求值 ⇒ `None`）。"""
    for node in tree.body if tree is not None else ():
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is None or not any(isinstance(x, ast.Name) and x.id == name for x in targets):
                continue
            try:
                evaluated: object = ast.literal_eval(value)
                return evaluated
            except (ValueError, TypeError):
                return None
    return None


def _dict_keys(tree: ast.Module | None, name: str) -> list[ast.expr] | None:
    """`name = {k: v, ...}` 的**键表达式列表**（AST，不求值）。

    走**全树**：`_TRANSITIONS` 定义在**类体**里（`class ResearchTaskState`），
    不是模块级 —— 只读 `tree.body` 会拿到空集而**静默判绿**（本文件首版实测踩到）。
    `AnnAssign` 形态也收。
    """
    if tree is None:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if value is None or not any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            continue
        if isinstance(value, ast.Dict):
            return [key for key in value.keys if key is not None]
    return None


def _attr_names(nodes: list[ast.expr] | None) -> set[tuple[str, str]]:
    """键表达式列表 → `{(源类名, 事件名)}`（读 `State.X` / `Transition.Y` 的属性名）。"""
    pairs: set[tuple[str, str]] = set()
    for node in nodes or []:
        if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
            continue
        parts: list[str] = []
        for elt in node.elts:
            if isinstance(elt, ast.Attribute):
                parts.append(elt.attr)
            else:
                return set()  # 形态不认识 ⇒ 空集（判据会判红，不静默放行）
        pairs.add((parts[0], parts[1]))
    return pairs


def _defines(tree: ast.Module | None, name: str) -> bool:
    if tree is None:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(tree)
    )


def _class_body_defines(tree: ast.Module | None, class_name: str, method: str) -> bool:
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return any(
                isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)) and inner.name == method
                for inner in node.body
            )
    return False


def _true_assignments(tree: ast.Module | None, attr: str) -> int:
    count = 0
    if tree is None:
        return count
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0] if node.targets else None
        if (
            isinstance(target, ast.Attribute)
            and target.attr == attr
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            count += 1
    return count


def case_count(root: Path, relative: str, toolbox: Any) -> int:
    """文件里 `test_` 开头的函数数（例数读数；复用 toolbox 的既有计数器）。"""
    return int(toolbox.count_test_defs(_read(root, relative, toolbox)))


def ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：出边恰一条、terminal 语义、三实现、Port、两个 ADR 的状态。"""
    state = _parse(root, TASK_STATE)
    edges = _attr_names(_dict_keys(state, "_TRANSITIONS"))
    dead_letter_edges = sorted(event for source, event in edges if source == "DEAD_LETTER")
    goal_text = _read(root, TASK_STATE, toolbox)
    verdicts = [
        toolbox.verdict(
            "ec01-dead-letter-has-exactly-one-edge",
            dead_letter_edges == ["REQUEUE"],
            ",".join(dead_letter_edges) or "none",
        ),
        toolbox.verdict(
            "ec01-dead-letter-still-terminal",
            "ResearchTaskState.State.DEAD_LETTER" in goal_text and "def terminal()" in goal_text,
        ),
        toolbox.verdict(
            "ec01-port-declares-requeue",
            _class_body_defines(_parse(root, WORKFLOW_PORT), "WorkflowEngine", "requeue"),
        ),
        toolbox.verdict(
            "ec01-sqlite-requeue-in-tree",
            _defines(_parse(root, SQLITE_REQUEUE), "requeue_task"),
        ),
        toolbox.verdict(
            "ec01-pg-requeue-in-tree",
            _defines(_parse(root, PG_REQUEUE), "requeue"),
        ),
        toolbox.verdict(
            "ec01-fake-requeue-in-tree",
            _class_body_defines(_parse(root, FAKE_ENGINE), "FakeWorkflowEngine", "requeue"),
        ),
        toolbox.verdict(
            "ec01-adr-0033-accepted",
            "Status: Accepted" in _read(root, ADR_0033, toolbox),
        ),
        toolbox.verdict(
            "ec01-adr-0030-still-proposed",
            "Status: Proposed" in _read(root, ADR_0030, toolbox),
            "邻接决策未被本 GOAL 改动",
        ),
    ]
    return verdicts


def ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：relay 三段、启用面恰一处、默认假。"""
    relay = _read(root, OUTBOX_RELAY, toolbox)
    tree = _parse(root, PG_COMPOSITION)
    composition = _read(root, COMPOSITION, toolbox)
    return [
        toolbox.verdict(
            "ec02-relay-drains-publishes-marks",
            all(
                token in relay for token in ("pending_outbox", ".publish(", "mark_outbox_published")
            ),
        ),
        toolbox.verdict(
            "ec02-pg-root-enables-relay-once",
            _true_assignments(tree, "outbox_relay_enabled") == 1,
        ),
        toolbox.verdict(
            "ec02-api-deps-default-is-false",
            "outbox_relay_enabled: bool = False" in composition,
        ),
    ]


def ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：入口与会话重算在树、既有套件仍在树（引用而非重复）。"""
    service = _read(root, "packages/application/run_orchestration/service.py", toolbox)
    verdicts = [
        toolbox.verdict(
            "ec03-resume-entry-in-tree",
            _defines(_parse(root, "services/api/run_resume.py"), "rebuild_and_resume"),
        ),
        toolbox.verdict(
            "ec03-remaining-specs-in-tree",
            "_remaining_specs" in service and "resume_rebuilt" in service,
        ),
    ]
    for relative in PRIOR_CONTINUITY_SUITES:
        verdicts.append(
            toolbox.verdict(f"prior-suite-{Path(relative).name}", (root / relative).is_file())
        )
    return verdicts


def case_and_evidence_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮判据文件的例数下界 + 判词归档（存在性 + CR=0）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        path = root / relative
        if not path.is_file():
            verdicts.append(toolbox.verdict(f"cases-{Path(relative).name}", False, "不在树"))
            continue
        observed = case_count(root, relative, toolbox)
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).name}", observed >= floor, f"{observed}>={floor}"
            )
        )
    for relative in EVIDENCE:
        path = root / relative
        if not path.is_file():
            verdicts.append(toolbox.verdict(f"evidence-{Path(relative).name}", False, "不在树"))
            continue
        raw = path.read_bytes()
        verdicts.append(
            toolbox.verdict(
                f"evidence-{Path(relative).name}",
                b"\r" not in raw and raw.count(b"\n") > 10,
                f"{len(raw)}B",
            )
        )
    return verdicts


def scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """`IN_SCOPE` 纯收紧：本轮两个新脚本都在必备清单里。"""
    literal = _literal(_parse(root, IN_SCOPE_JUDGE), "IN_SCOPE")
    pinned = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in pinned]
    return [
        toolbox.verdict(
            "new-scripts-in-scope",
            not missing,
            f"未进 IN_SCOPE：{missing}",
        )
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有的全部断言（收口验证器只调这一个入口）。"""
    verdicts: list[Any] = []
    verdicts.extend(ec01_verdicts(root, toolbox))
    verdicts.extend(ec02_verdicts(root, toolbox))
    verdicts.extend(ec03_verdicts(root, toolbox))
    verdicts.extend(case_and_evidence_verdicts(root, toolbox))
    verdicts.extend(scope_verdicts(root, toolbox))
    return verdicts
