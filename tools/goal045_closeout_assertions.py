#!/usr/bin/env python3
"""GOAL-20261010-045 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…044 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal045_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-045 特有的断言**。

三条主轴（逐条对 GOAL-045 的 EC）：

1. **EC-02 声明与落库**：提案**可声明**这两个字段（`MemoryWriteProposal` 字段表）；
   **三个适配器**（SQLite / PG / Fake）的 `commit` **都**带上 —— 逐条点名（本条的核心：
   「同一条纪律会第二次生效」，一个适配器漏 ⇒ 该路径上判据假绿）。
2. **EC-03 读面与点名**：读面**逐条披露**两字段 + 理由**点名**冲突（`[]` ⇒ 不追加）。
3. **EC-04 两向**：判据在树，且**三向**都被断言（声明被丢 / 点名失效 / 凭空报冲突）。

**两条纪律**（承 GOAL-027…044 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/domain/test_memory_declaration_fields.py", 4),
    ("tests/adapters/sqlite/test_memory_scope_and_validity.py", 13),
    ("tests/adapters/canonical/test_memory_read_dispositions.py", 18),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/postgres/test_memory_scope_pg.py",
    "tests/adapters/sqlite/test_evidence_memory_persistence.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点：域 + **三个**适配器。
DOMAIN = "packages/domain/memory.py"
ADAPTERS: tuple[str, ...] = (
    "adapters/sqlite/memory_store.py",
    "adapters/postgres/memory_store.py",
    "adapters/fakes/memory_store.py",
)
#: EC-03 落点：读面。
READ_FACE = "adapters/canonical/memory_read.py"
#: EC-04 落点：判据。
READ_JUDGE = "tests/adapters/canonical/test_memory_read_dispositions.py"
SQLITE_JUDGE = "tests/adapters/sqlite/test_memory_scope_and_validity.py"

#: 两个声明字段（逐条；缺一即判红）。
DECLARED_FIELDS: tuple[str, ...] = ("contradictions", "valid_from")
#: PG 里被替换掉的**硬编码**（必须**不在树**——它是本轮的现场）。
PG_HARDCODED: tuple[str, ...] = ("# contradictions (empty at commit)",)

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal045_closeout.py"
ASSERTIONS = "tools/goal045_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-045-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-045-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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
    """EC-02：提案可声明（域）**且三个适配器都带上**（逐条点名，缺一即判红）。"""
    domain = _text(root, DOMAIN)
    verdicts: list[Any] = [
        toolbox.verdict(
            f"ec02-proposal-declares-{field}",
            f"{field}:" in domain,
            f"域里缺 {field}",
        )
        for field in DECLARED_FIELDS
    ]
    for relative in ADAPTERS:
        source = _text(root, relative)
        missing = [field for field in DECLARED_FIELDS if field not in source]
        verdicts.append(
            toolbox.verdict(
                f"ec02-{Path(relative).parent.parent.name}-commit-carries-both",
                not missing,
                ",".join(missing),
            )
        )
    verdicts.append(
        toolbox.verdict(
            "ec02-optional-with-unchanged-defaults",
            "contradictions: list[str] = field(default_factory=list)" in domain
            and "valid_from: Timestamp | None = None" in domain,
            "两个字段必须**可选**且缺省语义逐字不变",
        )
    )
    return verdicts


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：读面逐条披露 + 点名冲突（且**不**凭空：`[]` 分支返回空串）。"""
    face = _text(root, READ_FACE)
    names = _function_names(face)
    return [
        toolbox.verdict(
            "ec03-the-read-face-discloses-both-fields",
            all(f'"{field}"' in face for field in DECLARED_FIELDS),
        ),
        toolbox.verdict(
            "ec03-the-conflict-note-names-the-ids",
            "_conflict_note" in names and "声明与" in face and "未自动消解" in face,
        ),
        toolbox.verdict(
            "ec03-an-empty-list-adds-nothing",
            'if not conflicts:\n        return ""' in face,
            "`[]` ⇒ **不**追加任何文字（不得凭空说有冲突）",
        ),
        toolbox.verdict(
            "ec03-the-reason-carries-the-note",
            _reason_appends_the_conflict_note(face),
        ),
    ]


def _reason_appends_the_conflict_note(face: str) -> bool:
    """判**关系**：`reason` 的值仍是「时效理由 **加** 冲突点名」（**不判调用签名**）。

    **为什么改这里**（GOAL-20261010-050 实测）：本判据原先把调用式**逐字写死**
    （`_reason(state, record) + _conflict_note(record)`）—— 而后续 GOAL 正当给 `_reason`
    加了 `superseded_by=` 关键字实参（**已取代**成为第四态）⇒ 文本失配 ⇒ **假红**。
    与 `MEM-20261010-215` 同族：**判关系，不判位置/写法**。

    判据读的是「`reason` 那一行的值表达式里**两个调用都出现**」—— 函数名与参数写法变了
    都不影响结论；而**只要冲突点名被摘掉**（或不再拼进 `reason`）就**仍判红**。
    """
    for line in face.splitlines():
        if '"reason"' not in line:
            continue
        if "_reason(" in line and "_conflict_note(" in line and "+" in line:
            return True
    return False


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：判据在树，且**三向**都被断言。"""
    read_judge = _text(root, READ_JUDGE)
    sqlite_judge = _text(root, SQLITE_JUDGE)
    return [
        toolbox.verdict("ec04-the-read-judge-is-in-tree", bool(read_judge)),
        toolbox.verdict(
            "ec04-the-sqlite-round-trip-is-asserted",
            "round_trip" in sqlite_judge and bool(sqlite_judge),
        ),
        toolbox.verdict(
            "ec04-a-named-conflict-is-asserted",
            "memory:earlier-claim" in read_judge and "冲突" in read_judge,
            "冲突必须**点名**",
        ),
        toolbox.verdict(
            "ec04-the-undeclared-case-asserts-no-conflict",
            'assert "冲突" not in str(row["reason"])' in read_judge,
            "反证：未声明 ⇒ 理由**不得**出现「冲突」",
        ),
        toolbox.verdict(
            "ec04-the-pg-hardcoding-is-gone",
            all(
                marker not in _text(root, "adapters/postgres/memory_store.py")
                for marker in PG_HARDCODED
            ),
            "PG 的两处硬编码必须**不在树**",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…044 的教训）。"""
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
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
