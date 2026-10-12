#!/usr/bin/env python3
"""GOAL-20261012-061 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…060 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-061 特有的断言**。

三条主轴（逐条对 GOAL-061 的 EC）：

1. **EC-02 冲突时效可判定**：域上有两个声明位；纯函数三态（`STALE` / `REVIEW_DUE` /
   `None`）；两条坏形态**点名**；**不猜**（未声明 ⇒ `None`）。
2. **EC-03 两读面同源 + 三适配器同契约**：两读面**都引用**同一个纯函数（不各写一套）；
   SQLite / PG 两列 + Fake 同契约；DTO + 快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…060）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…28）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/domain/test_conflict_timeliness.py", 11),
    ("tests/application/memory/test_conflict_timeliness_read_faces.py", 7),
    ("tests/postgres/test_memory_conflict_timeliness_pg.py", 1),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_conflict_resolution_lifecycle.py",
    "tests/application/memory/test_conflict_resolution_read_faces.py",
    "tests/api/test_memory_api.py",
)

#: EC-02 / EC-03 落点。
DOMAIN = "packages/domain/memory.py"
VALIDITY = "packages/application/memory/validity.py"
ORCH_FACE = "adapters/canonical/memory_read.py"
HTTP_ROUTER = "services/api/routers/memory.py"
HTTP_DTO = "services/api/dto/memory.py"
SQLITE = "adapters/sqlite/memory_store.py"
PG_STORE = "adapters/postgres/memory_store.py"
FAKE = "adapters/fakes/memory_store.py"
PG_MIGRATION = "adapters/postgres/migrations/026_memory_conflict_timeliness.sql"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
STATE_ENUM = "ConflictTimelinessState"
JUDGE = "conflict_timeliness_at"
FIELDS: tuple[str, ...] = ("conflict_review_after", "conflict_expires_at")
STATES: tuple[str, ...] = ("STALE", "REVIEW_DUE")
KEY = "conflict_timeliness"

#: EC-02：坏形态判词片段（f-string ⇒ 按**子串**核对）。
REJECT_FRAGMENTS: tuple[str, ...] = (
    "declares no contradictions",
    "must not precede",
)

#: EC-04 判据 / 归档落点。
DOMAIN_JUDGE = "tests/domain/test_conflict_timeliness.py"
FACES_JUDGE = "tests/application/memory/test_conflict_timeliness_read_faces.py"
PG_JUDGE = "tests/postgres/test_memory_conflict_timeliness_pg.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-061-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal061_closeout.py"
ASSERTIONS = "tools/goal061_closeout_assertions.py"


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


def _never_maps_undeclared_to_a_state(source: str) -> bool:
    """该判定**不把「未声明」映射成具名状态**（AST 读 —— 不靠文本巧合）。

    判的是**关系**：函数体里每一条 `if <含 `is None` 的条件>:` 的分支**都不返回**
    具名状态常量（`ConflictTimelinessState.*`）—— 少一个「未声明 ⇒ 某状态」的写法即通过。

    **为什么不用文件末尾形态判**（首版写法，已按纪律改）：判「末尾是 `return None`」
    会被**任何**末尾重排假红（与序 22/27 的「判关系不判位置」同一纪律）。
    """
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(parsed):
        if not isinstance(node, ast.FunctionDef) or node.name != JUDGE:
            continue
        return all(_branch_keeps_undeclared_unsigned(branch) for branch in node.body)
    return True


def _branch_keeps_undeclared_unsigned(branch: ast.stmt) -> bool:
    """该分支**不把「未声明」映射成具名状态**（`True` = 合规）。

    两条（缺一即不合规 —— 都不看**写法**，看的是**关系**）：

    1. 分支**返回具名状态**（`ConflictTimelinessState.*`）时，它的条件里**不得**出现
       「未声明」那一类形态（`is None` / `not <expr>` / `A is None or B`）；
    2. 条件不含具名状态返回的分支**一律合规**（未声明的支返回 `None` 是本轮的要件，
       由 `test_an_undeclared_timeliness_stays_none_not_stale` 在**行为面**正证）。
    """
    if not isinstance(branch, ast.If):
        return True
    body = ast.dump(ast.Module(body=branch.body, type_ignores=[]))
    if STATE_ENUM not in body:
        return True
    test_text = ast.dump(branch.test)
    if "'None'" in test_text or '"None"' in test_text:
        return False
    if isinstance(branch.test, ast.UnaryOp) and isinstance(branch.test.op, ast.Not):
        return False
    # `Is()` 是「是 None」那一支；合法支用 `IsNot()`（**不**含 `Is(`）。
    return not ("Is(" in test_text or "Or(" in test_text)


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
    """EC-02：**两个声明位** + 三态枚举 + **两条坏形态点名** + **不猜**（缺省 `None`）。"""
    domain = _text(root, DOMAIN)
    validity = _text(root, VALIDITY)
    domain_literals = _module_string_literals(domain)
    missing_fields = [
        item
        for item in FIELDS
        if item not in _class_annotations(domain, "MemoryRecord")
        or item not in _class_annotations(domain, "MemoryWriteProposal")
    ]
    missing_states = [item for item in STATES if f"{STATE_ENUM}.{item}" not in validity]
    missing_reject = [item for item in REJECT_FRAGMENTS if not _contains(domain_literals, item)]
    return [
        toolbox.verdict(
            "ec02-both-declaration-points-carry-the-two-fields",
            not missing_fields,
            ",".join(missing_fields) or "记录与提案都必须有这两个声明位",
        ),
        toolbox.verdict(
            "ec02-the-three-state-judge-exists",
            f"class {STATE_ENUM}" in validity and f"def {JUDGE}" in validity,
            "三态判定必须是**具名**枚举 + 纯函数（读面不重写第二套）",
        ),
        toolbox.verdict(
            "ec02-both-states-are-declared",
            not missing_states,
            ",".join(missing_states),
        ),
        toolbox.verdict(
            "ec02-every-bad-shape-is-named",
            not missing_reject,
            ",".join(missing_reject),
        ),
        toolbox.verdict(
            "ec02-the-undeclared-form-is-not-guessed",
            # **判关系**（不判写法 / 不判文件末尾形态 —— 承「判据不得按位置写死」）：
            # 该纯函数里**没有任何一处**把「未声明」映射成某个**具体状态**
            # （即：不出现 `is None` 与状态返回同处一支的写法）。
            _never_maps_undeclared_to_a_state(validity),
            "未声明**不得**被当成已到期（缺省支**不返回任何**具名状态）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两读面**同源**（都引用同一纯函数）+ 三适配器同契约 + DTO/快照同轮。"""
    orch = _text(root, ORCH_FACE)
    router = _text(root, HTTP_ROUTER)
    sqlite = _text(root, SQLITE)
    pg = _text(root, PG_STORE)
    fake = _text(root, FAKE)
    migration = _text(root, PG_MIGRATION)
    return [
        toolbox.verdict(
            "ec03-the-orchestration-face-uses-the-shared-judge",
            JUDGE in orch,
            "编排读面必须**直接调**共用纯函数（不重写第二套判定）",
        ),
        toolbox.verdict(
            "ec03-the-http-face-uses-the-same-judge",
            JUDGE in router,
            "HTTP 读面必须调**同一个**函数（两处各写一套 = 漂移无从发现）",
        ),
        toolbox.verdict(
            "ec03-all-three-adapters-carry-the-two-fields",
            all(
                item.count(FIELDS[0]) >= 1 and item.count(FIELDS[1]) >= 1
                for item in (sqlite, pg, fake)
            ),
            "三个适配器**同契约**（少一个 ⇒ 该路径判据假绿 —— 承序 13 的实测教训）",
        ),
        toolbox.verdict(
            "ec03-the-migration-adds-both-columns",
            migration.count("ADD COLUMN IF NOT EXISTS") >= 2
            and FIELDS[0] in migration
            and FIELDS[1] in migration,
            "迁移必须**只加**两列",
        ),
        toolbox.verdict(
            "ec03-the-dtos-carry-the-key",
            KEY in _text(root, HTTP_DTO),
            "HTTP DTO 必须披露该键（与编排面同源同值）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-key",
            KEY in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该键（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    domain_judge = _text(root, DOMAIN_JUDGE)
    faces = _text(root, FACES_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-stale-arm-is-asserted",
            "test_an_expired_conflict_declaration_reads_stale" in domain_judge,
            "`X-1` 的受判面必须在树（失效判成有效）",
        ),
        toolbox.verdict(
            "ec04-the-future-bound-arm-is-asserted",
            "test_a_future_bound_has_not_arrived_yet" in domain_judge,
            "`X-2` 的受判面必须在树（未到期判成失效）",
        ),
        toolbox.verdict(
            "ec04-the-undeclared-arm-is-asserted",
            "test_an_undeclared_timeliness_stays_none_not_stale" in domain_judge,
            "`X-3` 的受判面必须在树（未声明被当成已到期）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted-on-the-face",
            "test_an_undeclared_timeliness_discloses_none_verbatim" in faces,
            "`X-4` 的受判面必须在**披露面**（缺省形态逐字不变）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…060 的教训）。"""
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
