#!/usr/bin/env python3
"""GOAL-20261012-065 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…064 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-065 特有的断言**。

三条主轴（逐条对 GOAL-065 的 EC）：

1. **EC-02 作者面落 canonical**：`MemoryRecord` 有 `proposed_by`（**可选**，缺省 `None`）；
   `commit` 把提案的它**带进**（不丢弃）；**三适配器同契约**（SQLite 加法式列 +
   PG 迁移只加列 + Fake）。
2. **EC-03 两读面同源披露**：编排面与 HTTP 面**都**披露；**既有键逐字不变**；
   `provenance`（**来源**）与作者**互不顶替**；DTO + 快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…064）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…32）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_memory_author_read_faces.py", 11),
    ("tests/postgres/test_memory_conflict_timeliness_pg.py", 2),
    ("tests/api/test_memory_api.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_dangling_reference_read_faces.py",
    "tests/adapters/canonical/test_memory_conflict_disposition.py",
    "tests/domain/test_conflict_timeliness.py",
)

#: EC-02 / EC-03 落点。
DOMAIN = "packages/domain/memory.py"
ORCH_FACE = "adapters/canonical/memory_read.py"
HTTP_ROUTER = "services/api/routers/memory.py"
HTTP_DTO = "services/api/dto/memory.py"
SQLITE = "adapters/sqlite/memory_store.py"
PG_STORE = "adapters/postgres/memory_store.py"
FAKE = "adapters/fakes/memory_store.py"
PG_MIGRATION = "adapters/postgres/migrations/027_memory_proposed_by.sql"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
FIELD = "proposed_by"
SOURCE = "provenance"

#: EC-04 判据 / 归档落点。
FACE_JUDGE = "tests/application/memory/test_memory_author_read_faces.py"
PG_JUDGE = "tests/postgres/test_memory_conflict_timeliness_pg.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-065-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal065_closeout.py"
ASSERTIONS = "tools/goal065_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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
    """EC-02：**记录有作者面** + `commit` **带进** + **三适配器同契约** + 迁移只加列。"""
    domain = _text(root, DOMAIN)
    sqlite = _text(root, SQLITE)
    pg = _text(root, PG_STORE)
    fake = _text(root, FAKE)
    migration = _text(root, PG_MIGRATION)
    return [
        toolbox.verdict(
            "ec02-the-record-carries-the-author",
            FIELD in _class_annotations(domain, "MemoryRecord"),
            f"记录必须有 `{FIELD}`（缺省 None ⇒ 既有行读出同值）",
        ),
        toolbox.verdict(
            "ec02-the-proposal-still-declares-it",
            FIELD in _class_annotations(domain, "MemoryWriteProposal"),
            "提案面的既有声明位必须仍在（本轮**不**新造第二个作者字段）",
        ),
        toolbox.verdict(
            "ec02-the-commit-carries-it-through",
            # **判关系**：写入侧从**提案**取值（而不是硬编码 `None` = 本 GOAL 的靶子）。
            f"{FIELD}=proposal.{FIELD}" in sqlite and f"proposal.{FIELD}" in pg,
            "提交必须把提案的它**带进**（硬编码 None 就是本 GOAL 的靶子形态）",
        ),
        toolbox.verdict(
            "ec02-the-three-adapters-share-the-contract",
            all(item.count(FIELD) >= 1 for item in (sqlite, pg, fake)),
            "三适配器同契约（少一个 ⇒ 该路径判据假绿 —— 承序 13/45/61 的实测教训）",
        ),
        toolbox.verdict(
            "ec02-the-migration-only-adds-the-column",
            "ADD COLUMN IF NOT EXISTS" in migration and FIELD in migration,
            "迁移必须**只加**该列",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两读面**都披露** + **来源与会者互不顶替** + DTO/快照同轮。"""
    orch = _text(root, ORCH_FACE)
    router = _text(root, HTTP_ROUTER)
    dto = _text(root, HTTP_DTO)
    return [
        toolbox.verdict(
            "ec03-the-orchestration-face-discloses-the-author",
            f'row["{FIELD}"] = record.{FIELD}' in orch,
            "编排读面必须**直接读** canonical 字段（不重写第二套判定）",
        ),
        toolbox.verdict(
            "ec03-the-http-face-discloses-the-author",
            f'"{FIELD}": record.{FIELD}' in router,
            "HTTP 读面必须披露（与编排面同源同值）",
        ),
        toolbox.verdict(
            "ec03-the-source-field-is-untouched",
            # **判关系**：`provenance`（来源）仍被**读**（本轮不删不改它的语义）。
            f"record.{SOURCE}" in orch or f"{SOURCE}" in _text(root, DOMAIN),
            "`provenance` 的既有语义必须逐字仍在（作者与来源是两件事）",
        ),
        toolbox.verdict(
            "ec03-the-dto-carries-the-author",
            FIELD in dto,
            "HTTP DTO 必须披露该键",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-author",
            FIELD in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该键（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    face = _text(root, FACE_JUDGE)
    pg = _text(root, PG_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-record-field-arm-is-asserted",
            "test_the_record_carries_the_author_now" in face,
            "`W-1` 的受判面必须在树（记录有作者面）",
        ),
        toolbox.verdict(
            "ec04-the-round-trip-arm-is-asserted",
            "test_the_author_survives_a_sqlite_round_trip" in face
            and "test_the_proposed_by_round_trips_on_pg" in pg,
            "`W-2` 的受判面必须在（两库往返）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_the_undeclared_author_stays_none" in face
            and "test_the_undeclared_author_reads_none_verbatim" in face,
            "`W-3` 的受判面必须在（两处缺省形态逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-disclosure-arm-is-asserted",
            "test_the_orchestration_face_discloses_the_author" in face,
            "`W-4` 的受判面必须在（读面披露在场）",
        ),
        toolbox.verdict(
            "ec04-the-separation-arm-is-asserted",
            "test_the_author_and_the_provenance_are_separate_facts" in face,
            "来源与作者**互不顶替**的受判面必须在树",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…064 的教训）。"""
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
