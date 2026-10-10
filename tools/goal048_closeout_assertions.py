#!/usr/bin/env python3
"""GOAL-20261010-048 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…047 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal048_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-048 特有的断言**。

三条主轴（逐条对 GOAL-048 的 EC）：

1. **EC-02 声明面**：域有**可选** `human_gate_on_verdicts`（与 `verdict_in` **同族**的取值集合）
   + 三种坏声明**点名** + 与序号声明**互斥** + **两库同契约**（SQLite / PG 列 + 迁移 021 只加列）
   + DTO / 路由透传 + **OpenAPI 快照含新字段**（承 `MEM-20261010-216`）。
2. **EC-03 求值面**：`declared_gate_trigger`（**只读**）按落库判词判定；**触发判定单一来源**
   （判定面与注册面都调它）；命中 ⇒ **点名条件与命中依据**；不命中 ⇒ 逐字走结论面。
3. **EC-04 两向**：判据在树，四条按压（成立仍放行 / 不成立也拦 / 非法被静默 / 未声明也产生
   副作用）逐条对得上用例；归档进树。

**两条纪律**（承 GOAL-027…047 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/domain/test_research_program.py", 11),
    ("tests/application/run_orchestration/test_program_conditional_gate_on_the_run_path.py", 5),
    ("tests/e2e/test_program_advance_on_the_run_path.py", 13),
    # 既有的两处（序号声明的判定面 / 接回面）**本轮未删用例** ⇒ 下界保持不变。
    ("tests/application/run_orchestration/test_program_waiting_on_the_run_path.py", 20),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（域 / 两库 / 迁移 / 接口面 / 快照）。
DOMAIN = "packages/domain/program.py"
SQLITE_STORE = "adapters/sqlite/program_store.py"
PG_STORE = "adapters/postgres/program_store.py"
MIGRATION = "adapters/postgres/migrations/021_program_conditional_gate.sql"
DTOS = "services/api/dto/programs.py"
ROUTER = "services/api/routers/programs.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-03 落点（求值面 / 注册面 / 驱动）。
TRIGGER_SOURCES: tuple[str, ...] = ("packages/application/run_orchestration/program_waiting.py",)
REGISTRATION = "packages/application/run_orchestration/program_gate_registration.py"
RUNNER = "packages/application/run_orchestration/program_runner.py"

#: EC-03 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "human_gate_on_verdicts=",
    "命中",
    "at least one verdict",
    "mutually exclusive",
)

#: EC-04 判据文件（逐条点名按压各自的用例）。
CONDITIONAL_JUDGE = (
    "tests/application/run_orchestration/test_program_conditional_gate_on_the_run_path.py"
)
E2E_JUDGE = "tests/e2e/test_program_advance_on_the_run_path.py"
DOMAIN_JUDGE = "tests/domain/test_research_program.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal048_closeout.py"
ASSERTIONS = "tools/goal048_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-048-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-048-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261010-048-press-two-way.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _joined(root: Path, relatives: tuple[str, ...]) -> str:
    """多落点的合并文本（判关系不判位置）。"""
    return "\n".join(_text(root, relative) for relative in relatives)


def _function_names(source: str) -> set[str]:
    """模块里定义的函数名（AST 读，不靠文本巧合）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


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


def _count_calls(source: str, name: str) -> int:
    """源码里**调用**该名字的次数（AST 计数 —— **不**把它的**定义行**算进去）。

    **为什么不用文本计数**（本判据当场兑现）：`source.count("_verdicts(")` 会把
    `def _verdicts(` 那行**也**算成一次 ⇒ 「只读一次」判成「读了两次」而**假红**。
    与 `MEM-20261010-215` 同族：判关系要用 AST 读，不用文本巧合。
    """
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == name)
            or getattr(node.func, "attr", None) == name
        )
    )


def _first_call_line_any(source: str, names: set[str]) -> int | None:
    """源码里**首次调用**这些名字之一的行号（AST；`Name` 与 `Attribute` 两种形态都认）。"""
    if not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    lines: list[int] = []
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if called in names:
            lines.append(node.lineno)
    return min(lines) if lines else None


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：声明面（域可选 + 坏声明点名 + 互斥 + 两库同契约 + 迁移只加列 + 快照同步）。"""
    domain = _text(root, DOMAIN)
    migration = _text(root, MIGRATION)
    return [
        toolbox.verdict(
            "ec02-the-domain-declares-an-optional-condition",
            "human_gate_on_verdicts: tuple[str, ...] | None = None" in domain,
            "域必须**可选**声明（缺省 None ⇒ 逐字不变）",
        ),
        toolbox.verdict(
            "ec02-the-empty-declaration-is-named",
            "must name at least one verdict when declared" in domain,
        ),
        toolbox.verdict(
            "ec02-the-empty-string-is-named",
            "must not be empty strings" in domain,
        ),
        toolbox.verdict(
            "ec02-the-two-declarations-are-mutually-exclusive",
            "mutually exclusive" in domain,
            "两条闸门声明并存会让「为什么停」读不出是哪一条要求的",
        ),
        toolbox.verdict(
            "ec02-the-sqlite-store-carries-the-column",
            "human_gate_on_verdicts" in _text(root, SQLITE_STORE),
        ),
        toolbox.verdict(
            "ec02-the-pg-store-carries-the-column",
            "human_gate_on_verdicts" in _text(root, PG_STORE),
        ),
        toolbox.verdict(
            "ec02-the-migration-only-adds-a-column",
            "ADD COLUMN IF NOT EXISTS human_gate_on_verdicts" in migration
            and "DROP COLUMN" not in migration,
            "迁移必须**只加列**（NULL = 未声明，**与 `[]` 语义不同**）",
        ),
        toolbox.verdict(
            "ec02-the-create-face-declares-it",
            "human_gate_on_verdicts" in _text(root, DTOS)
            and "human_gate_on_verdicts" in _text(root, ROUTER),
        ),
        toolbox.verdict(
            "ec02-the-snapshot-carries-the-field",
            "human_gate_on_verdicts" in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含新字段（承 MEM-20261010-216 的下游同步纪律）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：求值面（只读 + 单一来源 + 点名条件与依据）。"""
    waiting = _joined(root, TRIGGER_SOURCES)
    registration = _text(root, REGISTRATION)
    runner = _text(root, RUNNER)
    names = _function_names(waiting)
    return [
        toolbox.verdict(
            "ec03-the-trigger-helper-exists",
            "declared_gate_trigger" in names,
            ",".join(sorted(names & {"declared_gate_trigger"})),
        ),
        toolbox.verdict(
            "ec03-the-trigger-judges-landed-verdicts",
            "on_verdicts" in waiting and "hit = [item for item in verdicts" in waiting,
            "条件必须按**落库判词取值**判定（与 verdict_in 同族）",
        ),
        toolbox.verdict(
            "ec03-the-trigger-is-read-only",
            "register(" not in waiting and "replace(" not in waiting,
            "求值面必须**只读**（有副作用的注册在单列模块里）",
        ),
        toolbox.verdict(
            "ec03-the-trigger-is-the-single-source",
            "declared_gate_trigger(" in registration,
            "注册面必须**调**同一份触发判定（两处不可能对「是否触发」有分歧）",
        ),
        toolbox.verdict(
            "ec03-the-evidence-is-named",
            all(marker in waiting for marker in NAMED_FORMS[:2]),
            ",".join(item for item in NAMED_FORMS[:2] if item not in waiting),
        ),
        toolbox.verdict(
            "ec03-the-verdicts-are-read-once-for-both-faces",
            _count_calls(runner, "_verdicts") == 1
            and "gated = _declared_gate_evaluation(" in runner
            and "verdicts," in runner,
            "落库判词只读**一次**供两处共用（条件闸门与结论面看到同一批事实）",
        ),
        toolbox.verdict(
            "ec03-the-gate-is-evaluated-before-the-conclusion-face",
            _gate_precedes_conclusion_face(runner),
        ),
    ]


def _gate_precedes_conclusion_face(runner: str) -> bool:
    """闸门求值是否**先于**结论面（AST 取行号；**按关系**，不按某条读取语句的位置）。"""
    gate = _first_call_line_any(runner, {"declared_gate_verdict", "_declared_gate_evaluation"})
    conclusion = _first_call_line_any(runner, {"_after_hit"})
    if gate is None or conclusion is None:
        return False
    return gate < conclusion


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的用例逐条点名 + 归档形态。"""
    judge = _text(root, CONDITIONAL_JUDGE)
    e2e = _text(root, E2E_JUDGE)
    domain = _text(root, DOMAIN_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-hit-case-is-asserted",
            "test_a_conditional_gate_fires_when_the_landed_verdicts_hit" in judge,
        ),
        toolbox.verdict(
            "ec04-the-not-hit-case-is-asserted",
            "test_a_conditional_gate_stays_out_of_the_way_when_not_hit" in judge,
        ),
        toolbox.verdict(
            "ec04-the-evidence-is-named-in-the-facts",
            "test_a_conditional_gate_names_the_evidence_it_judged_on" in judge,
        ),
        toolbox.verdict(
            "ec04-the-condition-registers-through-the-same-face",
            "test_a_conditional_gate_registers_a_decidable_approval" in judge,
        ),
        toolbox.verdict(
            "ec04-the-undeclared-case-is-asserted",
            "test_an_undeclared_condition_changes_nothing" in judge,
        ),
        toolbox.verdict(
            "ec04-the-http-face-pair-is-asserted",
            "test_a_conditional_gate_fires_on_the_landed_verdicts_over_the_http_face" in e2e
            and "test_a_conditional_gate_that_is_not_hit_leaves_the_advance_unchanged" in e2e,
            "两条实跑臂必须**成对**（命中 / 不命中）",
        ),
        toolbox.verdict(
            "ec04-the-bad-declarations-are-asserted",
            "test_conditional_gate_is_optional_and_bad_declarations_are_named" in domain,
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…047 的教训）。"""
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
    press_path = root / PRESS_ARCHIVE
    press_raw = press_path.read_bytes() if press_path.is_file() else b""
    verdicts.append(
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(press_raw) and not _has_carriage_return(press_raw),
            "missing/empty" if not press_raw else "contains CR",
        )
    )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**射程分区清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifier_text = _text(root, VERIFIER_JUDGE)
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
        toolbox.verdict(
            "verifier-scope-declares-this-rounds-scripts",
            SELF in verifier_text,
            "GOAL-043 立的射程分区清单也必须登记本轮验证器",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
