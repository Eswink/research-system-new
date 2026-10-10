#!/usr/bin/env python3
"""GOAL-20261010-046 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…045 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal046_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-046 特有的断言**。

三条主轴（逐条对 GOAL-046 的 EC）：

1. **EC-02 声明面**：域有**可选** `human_gate_at_index`（缺省 `None`）+ **两库同契约**
   （SQLite schema / PG INSERT）+ 迁移 020 只加列 + DTO/路由透传（逐条点名）。
2. **EC-03 判定与推进**：`declared_gate_pending` 的语义**照抄** phase 面
   （声明的闸门 **−** 已裁决审批）；判定面**只读**审批面；缺审批面 ⇒ 点名。
3. **EC-04 两向**：判据在树，且**三向**都被断言（绕过 / 轮前误拦 / 已裁决仍拦）。

**两条纪律**（承 GOAL-027…045 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）：实现面可能被规模门拆走
  ⇒ 用「可能落点」清单找，而不是钉死单一文件。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_program_waiting_on_the_run_path.py", 14),
    ("tests/domain/test_research_program.py", 10),
    # 修复轮补的**行为面**用例（EC-02 声明的「两库往返 + 缺省 + 非法」与
    # EC-04 声明的「实跑」此前只有文本在场、没有用例 ⇒ 本轮补齐，此处钉住例数）。
    ("tests/adapters/sqlite/test_program_store_sqlite.py", 5),
    ("tests/postgres/test_program_store_pg.py", 3),
    ("tests/e2e/test_program_advance_on_the_run_path.py", 9),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/adapters/sqlite/test_program_store_sqlite.py",
    "tests/postgres/test_program_store_pg.py",
    "tests/e2e/test_program_advance_on_the_run_path.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（域 / 两库 / 迁移 / 接口面）。
DOMAIN = "packages/domain/program.py"
SQLITE_STORE = "adapters/sqlite/program_store.py"
PG_STORE = "adapters/postgres/program_store.py"
MIGRATION = "adapters/postgres/migrations/020_program_human_gate.sql"
DTOS = "services/api/dto/programs.py"
ROUTER = "services/api/routers/programs.py"

#: EC-03 落点（判定面；**可能落点清单** —— 承 MEM-20261010-215）。
WAITING_SOURCES: tuple[str, ...] = ("packages/application/run_orchestration/program_waiting.py",)
RUNNER = "packages/application/run_orchestration/program_runner.py"

#: EC-04 落点（判据）。
GATE_JUDGE = "tests/application/run_orchestration/test_program_waiting_on_the_run_path.py"

#: EC-03 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "未提供审批面",
    "list_for_run",
    '"PENDING"',
)

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal046_closeout.py"
ASSERTIONS = "tools/goal046_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-046-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-046-verdict-clean.txt"

#: 声明面的下游同步面（EC-02 的字段必须出现在提交态的 OpenAPI 快照里）。
SNAPSHOT = "docs/api/openapi.m13.json"
SNAPSHOT_GENERATOR = "tools/gen_openapi.py"


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


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：域可选声明 + 两库同契约 + 迁移只加列 + 接口面透传（逐条点名）。"""
    domain = _text(root, DOMAIN)
    migration = _text(root, MIGRATION)
    return [
        toolbox.verdict(
            "ec02-the-domain-declares-an-optional-gate",
            "human_gate_at_index: int | None = None" in domain,
            "域必须**可选**声明（缺省 None ⇒ 逐字不变）",
        ),
        toolbox.verdict(
            "ec02-the-out-of-range-declaration-is-named",
            "human_gate_at_index must be within" in domain,
            "非法声明必须**点名**（不是静默当成无闸门）",
        ),
        toolbox.verdict(
            "ec02-the-sqlite-store-carries-the-column",
            "human_gate_at_index" in _text(root, SQLITE_STORE),
        ),
        toolbox.verdict(
            "ec02-the-pg-store-carries-the-column",
            "human_gate_at_index" in _text(root, PG_STORE),
        ),
        toolbox.verdict(
            "ec02-the-migration-only-adds-a-column",
            "ADD COLUMN IF NOT EXISTS human_gate_at_index" in migration
            and "DROP COLUMN" not in migration,
            "迁移必须**只加列**（无缺省回填：NULL 就是缺省语义）",
        ),
        toolbox.verdict(
            "ec02-the-create-face-declares-it",
            "human_gate_at_index" in _text(root, DTOS)
            and "human_gate_at_index" in _text(root, ROUTER),
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：判定面语义照抄 phase 面 + 只读 + 点名（多落点合并，判关系）。"""
    waiting = _joined(root, WAITING_SOURCES)
    names = _function_names(waiting)
    return [
        toolbox.verdict(
            "ec03-the-gate-pending-helper-exists",
            {"declared_gate_pending", "declared_gate_verdict"} <= names,
            ",".join(sorted(names & {"declared_gate_pending", "declared_gate_verdict"})),
        ),
        toolbox.verdict(
            "ec03-the-semantics-are-declared-minus-decided",
            "status" in waiting and "PENDING" in waiting,
            "语义必须**照抄** phase 面（声明的闸门 − 已裁决审批）",
        ),
        toolbox.verdict(
            "ec03-every-missing-form-is-named",
            all(marker in waiting for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in waiting),
        ),
        toolbox.verdict(
            "ec03-only-checks-the-declared-index",
            "human_gate_at_index" in waiting and "last_index" in waiting,
            "只在**声明的那个序号**上生效（轮前不停）",
        ),
        toolbox.verdict(
            "ec03-the-driver-dispatches-the-gate-before-the-conclusion-face",
            _gate_precedes_conclusion_face(_text(root, RUNNER)),
        ),
        toolbox.verdict(
            "ec03-the-approval-face-is-read-only",
            "list_for_run" in waiting and "register(" not in waiting and "replace(" not in waiting,
            "判定面**只读**（不自动放行 / 不消耗审批）",
        ),
    ]


def _gate_precedes_conclusion_face(runner: str) -> bool:
    """闸门判定是否**先于**结论面求值（**按被调名取行号**，与实参/位置无关）。

    **判的是「求值顺序」这件事，不是「某个定义在哪一行」**（承 `MEM-20261010-215` 的同族
    教训）。GOAL-20261010-047 把闸门求值抽成 `_declared_gate_evaluation`（规模门逼出的搬迁）
    ⇒ 原来钉 `declared_gate_verdict` 的**定义行**会随搬迁挪到结论面之后，从而**假红**。
    正确的落点有二，取**任一**在结论面之前即可：

    - 闸门求值的**调用点**（`_declared_gate_evaluation(...)`）；
    - 或直调 `declared_gate_verdict(...)`（未经抽出的形态）。

    **结论面的坐标**是**它自己的分派点**（`_after_hit`），不是落库判词的**读取行**：
    GOAL-20261010-048 把判词读一次供两处共用（条件闸门与结论面看到同一批事实）
    ⇒ 拿读取行当坐标会**假红**（实测）。

    两种形态都认 ⇒ 搬迁**不**改变结论；若有人把闸门挪到结论面**之后**，本条仍判红。
    """
    gate = _first_call_line_any(runner, {"declared_gate_verdict", "_declared_gate_evaluation"})
    conclusion = _first_call_line_any(runner, {"_after_hit"})
    if gate is None or conclusion is None:
        return False
    return gate < conclusion


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


def _first_call_line(source: str, function_name: str) -> int | None:
    """源码里**首次调用**该函数名的行号（AST；看被调名，不看实参）。"""
    if not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    lines = [
        node.lineno
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
    ]
    return min(lines) if lines else None


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：判据在树，且**三向**都被断言（绕过 / 轮前误拦 / 已裁决仍拦）。"""
    judge = _text(root, GATE_JUDGE)
    return [
        toolbox.verdict("ec04-the-gate-judge-is-in-tree", bool(judge)),
        toolbox.verdict(
            "ec04-the-stop-and-name-case-is-asserted",
            "test_a_declared_gate_stops_the_advance_and_names_the_index" in judge
            and "human_gate_at_index=1" in judge,
        ),
        toolbox.verdict(
            "ec04-the-before-its-round-case-is-asserted",
            "test_the_gate_does_not_fire_before_its_round" in judge,
        ),
        toolbox.verdict(
            "ec04-the-undeclared-case-is-asserted",
            "test_an_undeclared_gate_leaves_the_advance_unchanged" in judge,
        ),
        toolbox.verdict(
            "ec04-the-decided-satisfies-the-gate",
            "test_a_decided_approval_satisfies_the_gate" in judge and '"APPROVED"' in judge,
            "已裁决 ⇒ 不再拦（与 phase 面同语义）",
        ),
        toolbox.verdict(
            "ec04-the-missing-face-is-named",
            "test_a_gate_without_an_approval_face_is_named_not_skipped" in judge,
        ),
        toolbox.verdict(
            "ec04-the-read-only-case-is-asserted",
            "test_the_gate_never_touches_the_approval_face" in judge,
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…045 的教训）。"""
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


def _snapshot_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """声明面的**下游同步**（本轮真红教训）：OpenAPI 快照必须已按生成器重生成。

    为什么把这条放进本 GOAL 的断言集：cycle 1 改了建程序 DTO 却**没有**重生成并提交
    `docs/api/openapi.m13.json` ⇒ 被 `tests/contracts/test_openapi_snapshot` 在 **CI 上**
    判红（本地该判据会**自我修复**地把文件重写一遍 ⇒ 只看本地永远看不见）。判据读
    **提交态的字节**（`snapshot-lists-the-gate`）+ **生成器在场**（`snapshot-generator-present`）
    —— 「快照与生成器同源」由既有受保护判据判（本处不重复）。
    """
    snapshot = _text(root, SNAPSHOT)
    generator = _text(root, SNAPSHOT_GENERATOR)
    return [
        toolbox.verdict(
            "snapshot-lists-the-gate",
            "human_gate_at_index" in snapshot,
            "OpenAPI 快照必须含本轮新字段（漏了 ⇒ CI 的 snapshot 判据红）",
        ),
        toolbox.verdict(
            "snapshot-generator-present",
            "gen_openapi" in generator and bool(generator),
            "快照必须由生成器产出（手写快照 = 单一 schema truth 被破坏）",
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
        *_snapshot_verdicts(root, toolbox),
    ]
