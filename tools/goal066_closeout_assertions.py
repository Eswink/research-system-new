#!/usr/bin/env python3
"""GOAL-20261013-066 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…065 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-066 特有的断言**。

三条主轴（逐条对 GOAL-066 的 EC）：

1. **EC-02 查询面第三维**：Port 的 `query` 有 `proposed_by`；**三适配器同契约**
   （SQLite / PG / Fake **各自**带该维度）；**缺省不筛**；**未知作者空集**。
2. **EC-03 消费面可传 + 点名**：`memory_read` 可传作者、载荷**点名**（含**筛掉多少条**）；
   **缺省载荷逐字相同**；**序 17 的 `scope` 支一字不动**。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…065）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…33）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_memory_author_is_selectable.py", 10),
    ("tests/postgres/test_memory_conflict_timeliness_pg.py", 3),
    ("tests/adapters/canonical/test_memory_read_dispositions.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_memory_author_read_faces.py",
    "tests/application/memory/test_dangling_reference_read_faces.py",
    "tests/domain/test_conflict_timeliness.py",
)

#: EC-02 / EC-03 落点。
PORT = "packages/application/ports/memory_store.py"
SQLITE = "adapters/sqlite/memory_store.py"
PG_STORE = "adapters/postgres/memory_store.py"
FAKE = "adapters/fakes/memory_store.py"
READ_FACE = "adapters/canonical/memory_read.py"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
FIELD = "proposed_by"
SCOPE_BRANCH = 'payload["scope"] = scope'

#: EC-04 判据 / 归档落点。
SELECT_JUDGE = "tests/application/memory/test_memory_author_is_selectable.py"
PG_JUDGE = "tests/postgres/test_memory_conflict_timeliness_pg.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-066-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal066_closeout.py"
ASSERTIONS = "tools/goal066_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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
    """EC-02：Port **有第三维** + **三适配器各自带它** + **未知作者空集**（**不**当全选）。"""
    port = _text(root, PORT)
    sqlite = _text(root, SQLITE)
    pg = _text(root, PG_STORE)
    fake = _text(root, FAKE)
    return [
        toolbox.verdict(
            "ec02-the-port-carries-the-third-dimension",
            f"{FIELD}: str | None = None" in port,
            "Port 的 `query` 必须有该可选形参（改动前直接 TypeError）",
        ),
        toolbox.verdict(
            "ec02-all-three-adapters-filter-on-it",
            # **判关系**：三个适配器**各自**用它做过滤（少一个 ⇒ 该路径判据假绿）。
            all(f"record.{FIELD} ==" in item or f"{FIELD}=" in item for item in (sqlite, pg, fake)),
            "三适配器同契约（各自**真的**按它筛）",
        ),
        toolbox.verdict(
            "ec02-the-default-is-not-a-filter",
            # **判关系**：缺省是 `None` ⇒ 不加子句 / 不进条件（**不**筛，不是筛空集）。
            "= None" in port and f"if {FIELD} is not None:" in (sqlite + pg + fake),
            "缺省必须是「不筛」（既有行为逐字不变）",
        ),
        toolbox.verdict(
            "ec02-an-unknown-author-is-not-a-guess",
            # **判关系**：只按**已声明**的作者筛 ⇒ 未知自然为空（**不**回退成全选）。
            "or" not in f"x{port}x".split("proposed_by")[0][-6:],
            "未知作者 ⇒ 空结果（**不**把未知当「全选」）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：消费面**可传** + **点名**（含筛掉多少）+ **缺省逐字** + **`scope` 支不动**。"""
    read_face = _text(root, READ_FACE)
    return [
        toolbox.verdict(
            "ec03-the-consumption-face-passes-the-author",
            f"selection.{FIELD}" in read_face,
            "消费面必须把作者维度交给 Port（**可传**）",
        ),
        toolbox.verdict(
            "ec03-the-payload-names-the-author-and-the-count",
            f'payload["{FIELD}"]' in read_face and 'payload["filtered_out"]' in read_face,
            "载荷必须**点名**筛了什么与**筛掉了多少**（不静默丢）",
        ),
        toolbox.verdict(
            "ec03-the-author-keys-are-conditional",
            # **判关系**：两个键**只在传了作者时**加（缺省载荷逐字相同）。
            f"if selection.{FIELD} is not None:" in read_face,
            "**只有传了作者**才加这两键（缺省载荷与改动前**逐字相同**）",
        ),
        toolbox.verdict(
            "ec03-the-scope-branch-is-untouched",
            SCOPE_BRANCH in read_face and "if scope is not None:" in read_face,
            "序 17 的 `scope` 支**语义一字不动**（本轮只**加**第三维）",
        ),
        toolbox.verdict(
            "ec03-the-selection-is-a-value-object",
            "class _Selection" in read_face,
            "三个维度合成参数对象（守 `max-args` 门 —— 承序 24…33 的手法）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    select = _text(root, SELECT_JUDGE)
    pg = _text(root, PG_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-ignore-arm-is-asserted",
            "test_the_author_selects_exactly_its_own_records" in select,
            "`X-1` 的受判面必须在树（按作者真出对应的那些）",
        ),
        toolbox.verdict(
            "ec04-the-adapter-arm-is-asserted",
            "test_the_sqlite_adapter_shares_the_contract" in select
            and "test_the_author_dimension_selects_on_pg" in pg,
            "`X-2` 的受判面必须在（两库同契约）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_the_default_selection_is_verbatim" in select
            and "test_the_consumption_face_default_payload_is_verbatim" in select,
            "`X-3` 的受判面必须在（两处缺省形态逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-disclosure-arm-is-asserted",
            "test_the_consumption_face_can_pass_the_author" in select,
            "`X-4` 的受判面必须在（消费面点名 + 筛掉条数）",
        ),
        toolbox.verdict(
            "ec04-the-prior-scope-arm-is-asserted",
            "test_the_scope_disclosure_is_untouched" in select,
            "序 17 的 `scope` 回归臂必须在树",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…065 的教训）。"""
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
