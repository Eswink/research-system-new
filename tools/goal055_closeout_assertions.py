#!/usr/bin/env python3
"""GOAL-20261011-055 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…054 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal055_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-055 特有的断言**。

三条主轴（逐条对 GOAL-055 的 EC）：

1. **EC-02 多点可声明**：域上有 `human_gate_at_indexes` 字段；三处校验（非空 / 范围 / 重复）
   的判词**逐条在位**；**两根都落库**（SQLite 列 + PG 迁移文件）；DTO 有该字段。
2. **EC-03 推进面逐点生效**：判定面有第三个分支（一组序号）+ **点名触发者**。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**四条纪律**（承 GOAL-027…054 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责；
- **判词行不含本树绝对路径**（两树入口会拒绝），且用 **AST** 读而不是文本巧合；
- **f-string 的 AST 分片**：判词若含插值 ⇒ `Constant` 分片 ⇒ 按**整句**核对**永不命中**
  （承序 22 的五条假红）⇒ 本文件核对**片段**；
- **本文件自身也不得恒假**；**红的那一向由 `scratch/goal055_press.py` 的四条按压证**。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/domain/test_program_multi_point_gate.py", 8),
    ("tests/application/run_orchestration/test_multi_point_gate_on_the_run_path.py", 5),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/domain/test_research_program.py",
    "tests/adapters/sqlite/test_program_store_sqlite.py",
    "tests/postgres/test_program_store_pg.py",
    "tests/adapters/sqlite/test_shared_connection_transaction_scope.py",
)

#: EC-02/EC-03 落点。
DOMAIN = "packages/domain/program.py"
WAITING = "packages/application/run_orchestration/program_waiting.py"
SQLITE = "adapters/sqlite/program_store.py"
PG_MIGRATION = "adapters/postgres/migrations/022_program_multi_point_gate.sql"
DTO = "services/api/dto/programs.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-02：新字段名（逐条点名；缺一即判红）。
FIELD = "human_gate_at_indexes"

#: EC-02：三处校验的判词**片段**（f-string ⇒ 见模块 docstring）。
VALIDATION_FRAGMENTS: tuple[str, ...] = (
    "must name at least one index",
    "entries must be within 1..max_runs",
    "must not repeat an index",
    "are mutually exclusive",
)

#: EC-03：判定面的第三支 + 点名形态。
TRIGGER_HELPER = "_multi_point_trigger"
TRIGGER_FRAGMENT = "本轮命中"

#: EC-04 判据 / 归档落点。
NEW_JUDGE = "tests/application/run_orchestration/test_multi_point_gate_on_the_run_path.py"
DOMAIN_JUDGE = "tests/domain/test_program_multi_point_gate.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-055-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-055-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-055-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal055_closeout.py"
ASSERTIONS = "tools/goal055_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _module_string_literals(source: str) -> set[str]:
    """模块里的**字符串字面量**（AST 读 —— 不按文本包含判，避免注释/散文偶然命中）。

    f-string 会被 AST 拆成 `Constant` 分片 ⇒ 返回的是**片段集合**（调用方按片段核对）。
    """
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.value
        for node in ast.walk(parsed)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _contains(literals: set[str], fragment: str) -> bool:
    """某个**片段**是否出现在那些字符串字面量里（**子串**匹配 —— 不是集合成员）。

    **为什么**：判词多是 f-string ⇒ AST 里被拆成 `Constant` 分片，且**片段本身可能只是
    某个分片的一部分**（比如 `"...，本轮命中 "` 里的 `本轮命中`）⇒ 按「集合成员」核对会
    **永远失配**（承序 22 的五条假红；本轮实测又踩到一次）。
    """
    return any(fragment in literal for literal in literals)


def _class_annotations(source: str, class_name: str) -> set[str]:
    """类体的**注解名**（AST 读 —— **不 import 那个包**）。

    为什么不用 `dataclasses.fields`：本文件被两树入口按**路径**加载（`tools/` 不是包），
    `from packages.domain.program import ...` 在那种加载方式下**不可用**（实测
    `ModuleNotFoundError: No module named 'packages'`）⇒ 读**文本**的那一类里判注解名。
    """
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance((target := item.target), ast.Name)
            }
    return set()


def _field_names(source: str, class_name: str) -> set[str]:
    """类体里的**注解名**（AST 读 —— 不靠行首正则）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance((target := item.target), ast.Name)
            }
    return set()


def _defines(source: str, name: str) -> bool:
    """该模块**自己定义**了该名字（AST —— 判关系不判写法）。"""
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
        and node.col_offset == 0
        for node in ast.walk(parsed)
    )


def _defines_method(source: str, name: str) -> bool:
    """该模块里有**任何**同名函数（**含类方法** —— 缩进不判）。

    「构造期的列补齐」是**方法**（挂在 store 类上）⇒ 要求模块级会永远失配
    （实测：那样写时这条判据恒假）。
    """
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：域字段 + 三处校验判词 + **两根都落库** + DTO 字段 + 快照同轮。"""
    domain_literals = _module_string_literals(_text(root, DOMAIN))
    missing = [item for item in VALIDATION_FRAGMENTS if not _contains(domain_literals, item)]
    dto_fields = _field_names(_text(root, DTO), "ProgramDetailDto")
    return [
        toolbox.verdict(
            "ec02-the-domain-declares-the-multi-point-field",
            FIELD in _class_annotations(_text(root, DOMAIN), "ResearchProgram"),
            "域上必须有 `human_gate_at_indexes`（一组序号）",
        ),
        toolbox.verdict(
            "ec02-every-validation-verdict-is-present",
            not missing,
            ",".join(missing),
        ),
        toolbox.verdict(
            "ec02-the-sqlite-column-and-additive-migration-are-present",
            # **判关系**：列名在树（`_SCHEMA`）**且**构造期有加法式补齐（旧库也能用）。
            "human_gate_at_indexes_json" in _text(root, SQLITE)
            and _defines_method(_text(root, SQLITE), "_ensure_compatible_schema"),
            "SQLite 既要有列，也要有**加法式补齐**（旧库文件不然插不进去）",
        ),
        toolbox.verdict(
            "ec02-the-pg-migration-adds-the-column",
            "human_gate_at_indexes_json" in _text(root, PG_MIGRATION)
            and "ADD COLUMN IF NOT EXISTS" in _text(root, PG_MIGRATION),
            "PG 要有一条**只加列**的迁移（`ADD COLUMN IF NOT EXISTS`）",
        ),
        toolbox.verdict(
            "ec02-the-dto-and-snapshot-carry-the-field",
            FIELD in dto_fields and FIELD in _text(root, SNAPSHOT),
            "DTO 与 OpenAPI 快照都要有该字段（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：判定面有第三支 + **点名触发者**（判词要回答「为什么**这**一轮停了」）。"""
    waiting = _text(root, WAITING)
    literals = _module_string_literals(waiting)
    return [
        toolbox.verdict(
            "ec03-the-trigger-reads-the-multi-point-form",
            FIELD in waiting and _defines(waiting, TRIGGER_HELPER),
            "判定面必须有第三支（一组序号）",
        ),
        toolbox.verdict(
            "ec03-the-trigger-names-the-point-that-fired",
            _contains(literals, TRIGGER_FRAGMENT),
            f"判词必须点名命中的点（缺片段 {TRIGGER_FRAGMENT!r}）",
        ),
        toolbox.verdict(
            "ec03-the-cited-facts-name-the-form",
            f"{FIELD}=[" in waiting.replace(" ", "").replace(f'"{FIELD}=[",', f"{FIELD}=[")
            or FIELD in waiting,
            "被引事实要点名**是哪条声明**（一组序号）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    domain_judge = _text(root, DOMAIN_JUDGE)
    run_judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-first-point-case-is-asserted",
            "test_the_first_declared_point_stops_the_advance_and_names_it" in run_judge,
            "`R-1` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-out-of-range-case-is-asserted",
            "test_an_out_of_range_index_is_rejected_by_name" in domain_judge,
            "`R-2` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-repeated-index-case-is-asserted",
            "test_a_repeated_index_is_rejected_by_name" in domain_judge,
            "`R-3` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-undeclared-form-case-is-asserted",
            "test_an_undeclared_multi_point_gate_leaves_the_advance_unchanged" in run_judge,
            "`R-4` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-baseline-gate-is-in-the-archive",
            "BASELINE" in press and "GREEN" in press,
            "归档必须含**基线行**（未按压不得红 —— 承 §8 的一级纪律）",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…054 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", VERDICT_CURRENT), ("clean", VERDICT_CLEAN)):
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
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    registered = isinstance(verifiers, tuple) and SELF in verifiers
    return [
        toolbox.verdict("scope-in-scope-covers-this-round", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-verifier-registry-covers-this-round",
            registered,
            "收口验证器必须已登记进射程清单",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言全集（顺序稳定；判词名不带路径）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
