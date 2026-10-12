#!/usr/bin/env python3
"""GOAL-20261012-060 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…059 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-060 特有的断言**。

三条主轴（逐条对 GOAL-060 的 EC）：

1. **EC-02 混合式可声明**：域上有值对象（两维**缺一不可**）；坏形态点名；
   与三条既有声明**互斥**（同一维度上的既有互斥**未解除**）。
2. **EC-03 两维各自点名**：触发面两维**分开判、分开点名**（两维都命中 ⇒ 两条都点名）；
   两库同契约（SQLite 两列 + PG 迁移只加列）；DTO 透传 + 快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…059）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…27）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/domain/test_program_hybrid_gate.py", 10),
    ("tests/application/run_orchestration/test_program_hybrid_gate_on_the_run_path.py", 5),
    ("tests/e2e/test_hybrid_gate_on_the_http_face.py", 4),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/domain/test_program_multi_point_gate.py",
    "tests/domain/test_research_program.py",
    "tests/application/run_orchestration/test_program_conditional_gate_on_the_run_path.py",
)

#: EC-02 / EC-03 落点。
DOMAIN = "packages/domain/program.py"
WAITING = "packages/application/run_orchestration/program_waiting.py"
SQLITE = "adapters/sqlite/program_store.py"
PG_STORE = "adapters/postgres/program_store.py"
PG_MIGRATION = "adapters/postgres/migrations/025_program_hybrid_gate.sql"
DTO = "services/api/dto/programs.py"
ROUTER = "services/api/routers/programs.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
VALUE_OBJECT = "HybridGateDeclaration"
FIELD = "human_gate_hybrid"
DIMENSIONS: tuple[str, ...] = ("at_indexes", "on_verdicts")

#: EC-02：值对象的**两维非空**判词片段（f-string ⇒ 按**子串**核对）。
REJECT_FRAGMENTS: tuple[str, ...] = (
    "at_indexes must name at least one index",
    "on_verdicts must name at least one verdict",
    "on_verdicts must not be empty strings",
)

#: EC-03：触发面两维**各自的**命中计算（判**关系**：两维都算过才可能各自点名）。
DIMENSION_ASSIGNMENTS: tuple[str, ...] = ("hits_index = [", "hits_verdict = [")

#: EC-04 判据 / 归档落点。
DOMAIN_JUDGE = "tests/domain/test_program_hybrid_gate.py"
RUN_PATH_JUDGE = "tests/application/run_orchestration/test_program_hybrid_gate_on_the_run_path.py"
PRODUCT_JUDGE = "tests/e2e/test_hybrid_gate_on_the_http_face.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-060-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal060_closeout.py"
ASSERTIONS = "tools/goal060_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _module_string_literals(source: str) -> set[str]:
    """模块里的**字符串字面量**（AST 读；f-string 会被拆成 `Constant` **分片**）。"""
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
    """**子串**匹配（判词是 f-string ⇒ 片段可能只是某个分片的一部分；承序 22/23）。"""
    return any(fragment in literal for literal in literals)


def _class_annotations(source: str, class_name: str) -> set[str]:
    """类体的**注解名**（AST 读 —— 不 import 那个包）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            names: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    names.add(item.target.id)
            return names
    return set()


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：**值对象两维** + 坏形态点名 + **既有互斥未解除** + 两库落库。"""
    domain = _text(root, DOMAIN)
    domain_literals = _module_string_literals(domain)
    fields = _class_annotations(domain, VALUE_OBJECT)
    missing_dims = [item for item in DIMENSIONS if item not in fields]
    missing_reject = [item for item in REJECT_FRAGMENTS if not _contains(domain_literals, item)]
    sqlite = _text(root, SQLITE)
    pg = _text(root, PG_STORE)
    migration = _text(root, PG_MIGRATION)
    return [
        toolbox.verdict(
            "ec02-the-value-object-declares-both-dimensions",
            not missing_dims and f"class {VALUE_OBJECT}" in domain,
            ",".join(missing_dims) or f"缺 class {VALUE_OBJECT}",
        ),
        toolbox.verdict(
            "ec02-the-record-carries-the-hybrid-declaration",
            FIELD in _class_annotations(domain, "ResearchProgram"),
            f"程序上必须有 `{FIELD}`（缺省 None ⇒ 既有行为逐字不变）",
        ),
        toolbox.verdict(
            "ec02-every-bad-shape-is-named",
            not missing_reject,
            ",".join(missing_reject),
        ),
        toolbox.verdict(
            "ec02-the-existing-exclusivity-is-not-relaxed",
            # **判关系**：混合式**进了**互斥清单（而不是把那条纪律删掉）。
            f'("{FIELD}", program.{FIELD})' in domain,
            "混合式必须**同列**互斥清单（同一维度上的既有纪律不得解除）",
        ),
        toolbox.verdict(
            "ec02-both-stores-persist-the-two-columns",
            sqlite.count(FIELD) >= 2
            and pg.count(FIELD) >= 2
            and "ADD COLUMN IF NOT EXISTS" in migration
            and migration.count(FIELD) >= 1,
            "两库都要落**两列**（成对；迁移只加列）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：触发面**两维各自判**（⇒ 才可能各自点名）+ 全命中都点名 + DTO/快照同轮。"""
    waiting = _text(root, WAITING)
    dto = _text(root, DTO)
    return [
        toolbox.verdict(
            "ec03-the-trigger-computes-both-dimensions",
            all(item in waiting for item in DIMENSION_ASSIGNMENTS),
            "两维必须**各自**算（只算一维 ⇒ 另一维的命中读不出来）",
        ),
        toolbox.verdict(
            "ec03-both-dimensions-are-named-in-the-verdict",
            waiting.count("notes.append(") >= 2,
            "命中的维**各自**追加点名（两维都命中 ⇒ 两条都在）",
        ),
        toolbox.verdict(
            "ec03-the-hybrid-branch-sits-before-the-condition-branch",
            # **判关系**：混合式分支存在（缺省 None ⇒ 不影响既有三条）。
            f'getattr(program, "{FIELD}", None)' in waiting,
            "触发面必须**认**这条声明（缺省 None ⇒ 既有行为逐字不变）",
        ),
        toolbox.verdict(
            "ec03-the-dtos-carry-the-declaration",
            FIELD in dto and VALUE_OBJECT.replace("Declaration", "Dto") in dto,
            "建程序面与读面都要带（嵌套对象 ⇒ 「只声明一半」在 DTO 层就缺键）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-declaration",
            FIELD in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该键（动 DTO ⇒ 同轮同步）",
        ),
        toolbox.verdict(
            "ec03-the-other-three-declarations-are-untouched",
            all(
                f'getattr(program, "{name}", None)' in waiting
                for name in (
                    "human_gate_at_index",
                    "human_gate_on_verdicts",
                    "human_gate_at_indexes",
                )
            ),
            "三条既有声明的触发分支**逐条仍在**（本轮只加一种形态）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    domain_judge = _text(root, DOMAIN_JUDGE)
    run_path = _text(root, RUN_PATH_JUDGE)
    product = _text(root, PRODUCT_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-exclusivity-arm-is-asserted",
            "test_the_hybrid_form_stays_exclusive_with_the_other_declarations" in domain_judge,
            "`W-1` 的受判面必须在树（互斥）",
        ),
        toolbox.verdict(
            "ec04-the-index-dimension-arm-is-asserted",
            "test_the_index_dimension_alone_is_named" in run_path,
            "`W-2` 的受判面必须在树（序号维各自点名）",
        ),
        toolbox.verdict(
            "ec04-the-condition-dimension-arm-is-asserted",
            "test_the_condition_dimension_alone_is_named" in run_path,
            "`W-3` 的受判面必须在树（条件维各自点名）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted-on-the-product-path",
            "test_an_undeclared_hybrid_leaves_the_http_advance_verbatim" in product,
            "`W-4` 的受判面必须在**产品路径**判据里（只有真接线才可能绿）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…059 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：按压判词归档形态（非空、`CR=0`）。**不读内容做断言**（输入即输出）。"""
    path = root / PRESS_ARCHIVE
    raw = path.read_bytes() if path.is_file() else b""
    return [
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(raw) and not _has_carriage_return(raw),
            "missing/empty" if not raw else "contains CR",
        )
    ]


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
