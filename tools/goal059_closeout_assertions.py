#!/usr/bin/env python3
"""GOAL-20261012-059 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…058 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-059 特有的断言**。

三条主轴（逐条对 GOAL-059 的 EC）：

1. **EC-02 界可声明、可落库**：两个 DTO 都有该键；SQLite 列 + 加法式补齐 + 编解码；
   PG 迁移 `024` 只加列 + `INSERT` / `_PROGRAM_SELECT` 带列。
2. **EC-03 出口可注入**：组合根有该可注入字段（缺省静默）；推进路由**真的交下去**。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…058）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24/25/26）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/sqlite/test_program_nudge_bound_reachability.py", 12),
    ("tests/e2e/test_program_nudge_bound_on_the_run_path.py", 4),
    ("tests/postgres/test_program_store_pg.py", 5),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/run_orchestration/test_nudge_exit_on_the_run_path.py",
    "tests/application/run_orchestration/test_gate_nudge_on_the_run_path.py",
    "tests/domain/test_research_program.py",
)

#: EC-02 落点。
CREATE_DTO = "services/api/dto/programs.py"
ROUTER = "services/api/routers/programs.py"
ADVANCE = "services/api/program_advance.py"
SQLITE = "adapters/sqlite/program_store.py"
PG_STORE = "adapters/postgres/program_store.py"
PG_MIGRATION = "adapters/postgres/migrations/024_program_gate_nudge_bound.sql"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-03 落点。
COMPOSITION = "services/api/composition.py"
PORT = "packages/application/ports/nudge_sink.py"
EVALUATION = "packages/application/run_orchestration/program_gate_evaluation.py"

#: 本轮引入的键名（**逐条点名**；缺一即判红）。
FIELD = "gate_nudge_after_seconds"
PORT_NAMES: tuple[str, ...] = ("NudgeNotice", "NudgeSink", "NullNudgeSink")

#: EC-04 判据 / 归档落点。
REACHABILITY_JUDGE = "tests/adapters/sqlite/test_program_nudge_bound_reachability.py"
PRODUCT_JUDGE = "tests/e2e/test_program_nudge_bound_on_the_run_path.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-059-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal059_closeout.py"
ASSERTIONS = "tools/goal059_closeout_assertions.py"


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
    """EC-02：**界可声明**（两 DTO）+ **可落库**（两库同契约）+ 迁移只加列。"""
    dto = _text(root, CREATE_DTO)
    create_fields = _class_annotations(dto, "ProgramCreateDto")
    detail_fields = _class_annotations(dto, "ProgramDetailDto")
    sqlite = _text(root, SQLITE)
    pg = _text(root, PG_STORE)
    migration = _text(root, PG_MIGRATION)
    return [
        toolbox.verdict(
            "ec02-the-create-dto-accepts-the-bound",
            FIELD in create_fields,
            f"建程序面必须**可声明**界（缺 `{FIELD}`）",
        ),
        toolbox.verdict(
            "ec02-the-detail-dto-discloses-the-bound",
            FIELD in detail_fields,
            f"读面必须**披露**界（缺 `{FIELD}`）",
        ),
        toolbox.verdict(
            "ec02-the-sqlite-store-carries-the-column",
            FIELD in sqlite and "INTEGER" in sqlite,
            "SQLite 侧必须落该列（此前 round-trip 静默丢弃）",
        ),
        toolbox.verdict(
            "ec02-the-sqlite-store-upgrades-old-files-and-writes-both-paths",
            # **判关系**：加法式补齐 + 两条 SQL（`get` / `for_project`）都带列。
            '"gate_nudge_after_seconds": "INTEGER"' in sqlite and sqlite.count(FIELD + ",") >= 3,
            "旧库文件必须补列，且**两条** SELECT / INSERT 路径都要带列",
        ),
        toolbox.verdict(
            "ec02-the-pg-store-carries-the-column-and-the-migration-adds-it",
            FIELD in pg and FIELD in migration and "ADD COLUMN IF NOT EXISTS" in migration,
            "PG 侧必须落该列（迁移只加列）",
        ),
        toolbox.verdict(
            "ec02-the-router-passes-the-declaration-through",
            # **判关系**：写侧读 `payload`、读侧读 `program` —— **不**钉字面写法
            # （GOAL-060 把转换抽进 `declared_gate_fields` 后，原字面锚点假红 ⇒ 改判关系；
            #  两向实测：抽走任一侧的引用 ⇒ 该条判红）。
            "payload." + FIELD in _text(root, ROUTER) and "program." + FIELD in _text(root, ROUTER),
            "路由必须把声明透传（建侧读载荷、读侧读域对象）",
        ),
        toolbox.verdict(
            "ec02-the-snapshot-carries-the-bound",
            FIELD in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该键（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：**出口可注入**（组合根）+ **真的交下去**（推进路由）+ 端口契约一字未动。"""
    composition = _text(root, COMPOSITION)
    router = _text(root, ROUTER)
    port = _text(root, PORT)
    waiting = _text(root, "packages/application/run_orchestration/program_waiting.py")
    return [
        toolbox.verdict(
            "ec03-the-port-still-has-its-three-names",
            all(f"class {name}" in port for name in PORT_NAMES),
            "序 25 的端口契约必须逐字仍在（本轮只接线，不改端口）",
        ),
        toolbox.verdict(
            "ec03-the-composition-root-can-inject-a-sink",
            "NudgeSink" in composition and "NullNudgeSink" in composition,
            "组合根必须有可注入字段 + **静默**缺省",
        ),
        toolbox.verdict(
            "ec03-the-composition-default-is-silent",
            "default_factory=NullNudgeSink" in composition,
            "缺省必须是**静默**实现（未注入 ⇒ 逐字不变）",
        ),
        toolbox.verdict(
            # GOAL-20261019-089 EC-03 的落点迁移（逐条申报）：推进装配抽成
            # `program_advance.advance_for`（端点与周期作业共用）；断言意图与判词
            # 一字未改，只把受判文件换成真正做连接的那个 + 加判端点调用它。
            "ec03-the-advance-route-hands-the-sink-over",
            "nudges=deps.nudges" in _text(root, ADVANCE)
            and "advance_for(deps, program_id)" in router,
            "推进装配必须把出口**交下去**（此前 `nudges=` 零命中 ⇒ 不可达）",
        ),
        toolbox.verdict(
            "ec03-the-judgement-face-stays-read-only",
            ".nudge(" not in waiting and "NudgeSink" not in waiting,
            "只读判定面**不得**出现出口（序 12/14 起的既有判据钉住它）",
        ),
        toolbox.verdict(
            "ec03-the-tri-state-discipline-is-untouched",
            # **判关系**：三态的两条早退仍在（未超期 / 未注入 ⇒ 空串），且失败**点名**。
            "if resolved.nudges is None:" in _text(root, EVALUATION)
            and "nudge not delivered" in _text(root, EVALUATION),
            "序 25 的三态纪律（缺省不送 / 失败点名）**一字未动**",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    reach = _text(root, REACHABILITY_JUDGE)
    product = _text(root, PRODUCT_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-storage-arm-is-asserted",
            "test_the_bound_survives_a_sqlite_round_trip" in reach,
            "`V-1` 的受判面必须在树（落库面）",
        ),
        toolbox.verdict(
            "ec04-the-declaration-arm-is-asserted",
            "test_both_dtos_expose_the_key_now" in reach,
            "`V-2` 的受判面必须在树（声明面）",
        ),
        toolbox.verdict(
            "ec04-the-exit-arm-is-asserted-on-the-product-path",
            "test_an_injected_sink_receives_the_overdue_signal_on_the_product_path" in product,
            "`V-3` 的受判面必须在**产品路径**判据里（只有真接线才可能绿）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_without_a_declared_bound_the_sink_stays_empty" in product,
            "`V-4` 的受判面必须在树（缺省形态）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…058 的教训）。"""
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
