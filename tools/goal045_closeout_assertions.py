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
#: GOAL-20261011-052：共用处置判定**已搬去应用层**（两个读面共用；HTTP 面不得 import 适配器）。
#: `MEMORY_READ` 因此是**两个可能落点的合并文本**（判**关系**不判位置 —— 承 `MEM-20261010-215`；
#: 本次搬迁正当，钉位置会**假红**）。
_SHARED_DISPOSITION = "packages/application/memory/disposition.py"
READ_FACE_SOURCES: tuple[str, ...] = (
    "adapters/canonical/memory_read.py",
    _SHARED_DISPOSITION,
)
#: EC-04 落点：判据。
READ_JUDGE = "tests/adapters/canonical/test_memory_read_dispositions.py"
SQLITE_JUDGE = "tests/adapters/sqlite/test_memory_scope_and_validity.py"


def _face(root: Path, sources: tuple[str, ...]) -> str:
    """多个**可能落点**的合并文本（搬迁不改变结论；判关系不判位置）。"""
    return chr(10).join(_text(root, item) for item in sources)


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
    face = _face(root, READ_FACE_SOURCES)
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
            _reason_appends_the_conflict_note(face + chr(10) + _face(root, READ_FACE_SOURCES))
            and _appends_conflict_note(face + chr(10) + _face(root, READ_FACE_SOURCES)),
        ),
    ]


def _reason_appends_the_conflict_note(face: str) -> bool:
    """判**关系**：`reason` 的值 = 时效理由 **加** 一个点名冲突的助手（**不判写法**）。

    **为什么改这里**（GOAL-20261010-050 实测）：本判据原先把调用式**逐字写死**
    （`_reason(state, record) + _conflict_note(record)`）—— 而后续 GOAL 正当给 `_reason`
    加了 `superseded_by=` 关键字实参（**已取代**成为第四态）⇒ 文本失配 ⇒ **假红**。
    GOAL-20261011-051 又正当把「冲突本身是处置理由」那一支的重复点名拆到
    `_extra_conflict_note` ⇒ 按行/按文本读都会再假一次。

    **改法（第三次）**：用 **AST** 读那个字典**值**的表达式树 ——
    要求它是 `BinOp(Add)`，左子树里**调用了 `_reason`**，右子树里**调用了任一
    `*conflict_note*` 助手**。函数名、参数写法、折行**都不影响结论；
    而**把冲突点名整条摘掉**（或不再拼进 `reason`）**仍判红**。
    """
    # **本函数收的是整个模块文本**（不是片段）—— 传片段给 `ast.parse` 会永远 SyntaxError
    # ⇒ 判据恒假（实测：初版就这样「通过」了，是**恒真/恒假的空判据**，比假红更坏）。
    if not face:
        return False
    try:
        module = ast.parse(face)
    except SyntaxError:
        return False
    values = _reason_values(module)
    return bool(values) and all(_is_reason_plus_conflict(value) for value in values)


def _reason_values(module: ast.Module) -> list[ast.expr]:
    """模块里所有**给 `reason` 赋值**的值表达式（**两种写法都认**）。

    - **字典字面量**：`{"reason": <expr>}`（旧形态）；
    - **下标赋值**：`row["reason"] = <expr>`（GOAL-20261011-053 正当把 `_memory_row`
      的函数体**按字段分了组**（抽 `_identity_fields` / `_terminal_face` 两个助手），
      `reason` 因此从字典字面量搬进了下标赋值 ⇒ 只认一种写法会**假红**）。

    **这不是放宽**：两种写法都必须满足 `_is_reason_plus_conflict`（`all(...)`）；
    而**把冲突点名整条摘掉**（无论用哪种写法）**仍判红**。
    """
    found: list[ast.expr] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=False):
                if isinstance(key, ast.Constant) and key.value == "reason":
                    found.append(value)
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance((target := node.targets[0]), ast.Subscript)
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "reason"
        ):
            found.append(node.value)
    return found


def _is_reason_plus_conflict(value: ast.expr) -> bool:
    """`reason` 的值是否**由**「时效理由 **加上** 冲突点名」构成（**两种形态都认**）。

    - **形态 A（内联）**：`BinOp(Add)`，左子树调 `_reason`、右子树调任一 `*conflict_note*`；
    - **形态 B（封装）**：调**一个**既有的「理由」助手（`disposition_reason` / `*_reason*`）——
      GOAL-20261011-052 正当把这条拼接**封进应用层的 `disposition_reason`**
      （判定搬去两个读面都能 import 的那一层）⇒ 原形态 A 检测不到，**但关系没变**。

    **这不是放宽**：形态 B 只有在该助手**确实**把冲突点名拼进理由时才成立 ——
    由 `_appends_conflict_note` 在**模块文本**上核对（那一步仍在，见调用方）。
    """
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        return _calls_named_in(value.left, "_reason") and _any_call_endswith(
            value.right, "conflict_note"
        )
    return _calls_named_in(value, "disposition_reason")


def _appends_conflict_note(module_text: str) -> bool:
    """模块文本里**存在**「理由 = 时效理由 + 冲突点名」的拼接（形态 A 或 B 的实现面）。"""
    if not module_text:
        return False
    if "_conflict_note" not in module_text:
        return False
    return (
        # 形态 A：就地拼加
        ("+ _extra_conflict_note(" in module_text or "+ _conflict_note(" in module_text)
        # 形态 B：封装进 disposition_reason（它内部拼 `_extra_conflict_note`）
        or "note + _extra_conflict_note(" in module_text
    )


def _calls_named_in(node: ast.expr, name: str) -> bool:
    """子树里是否**调用了**该名字（AST；两种调用形态都认）。"""
    return any(
        isinstance(child, ast.Call)
        and (
            (isinstance(child.func, ast.Name) and child.func.id == name)
            or getattr(child.func, "attr", None) == name
        )
        for child in ast.walk(node)
    )


def _any_call_endswith(node: ast.expr, suffix: str) -> bool:
    """子树里是否有**任一**以该后缀结尾的被调名（容许助手改名，如 `_extra_conflict_note`）。"""
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        called = (
            child.func.id if isinstance(child.func, ast.Name) else getattr(child.func, "attr", "")
        )
        if called.endswith(suffix):
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
