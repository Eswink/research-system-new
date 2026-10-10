#!/usr/bin/env python3
"""GOAL-20261010-043 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…042 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal043_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-043 特有的断言**。

三条主轴（逐条对 GOAL-043 的 EC）：

1. **EC-02 加载面**：三处修复后的验证器**加载各自的断言集**（逐条对拍）；
   且**修复本身的痕迹在位**（各自的文件名出现在加载式里）。
2. **EC-03 崩溃面**：`goal040_closeout_assertions.py` 用 **AST 结构判据**
   （`_first_call_line` / `_dispatch_precedes_conclusion_face`）而不再按文本 index 匹配签名。
3. **EC-04 机器判据**：新判据文件在树、含三条主判据与两向反例（按断言名**逐条**点名）。

**两条纪律**（承 GOAL-027…042 的实测教训）：

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
    ("tests/tooling/test_closeout_verifiers_run_their_own_assertions.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_tooling_scripts_meet_product_gates.py",
    "tests/tooling/test_closeout_assertions_are_in_tree.py",
    "tests/tooling/test_two_tree_recheck_entry.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（三处加载面）。
FIXED_VERIFIERS: tuple[str, ...] = (
    "tools/verify_goal038_closeout.py",
    "tools/verify_goal039_closeout.py",
    "tools/verify_goal040_closeout.py",
)
#: EC-03 落点（崩溃面）。
GOAL040_ASSERTIONS = "tools/goal040_closeout_assertions.py"
#: EC-04 落点（机器判据）。
NEW_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: EC-04 必须点名的三条主判据（按断言**函数名**逐条，不靠文本巧合）。
REQUIRED_JUDGES: tuple[str, ...] = (
    "test_every_verifier_declares_the_assertion_set_it_actually_loads",
    "test_every_named_assertion_set_is_executable_on_this_tree",
    "test_the_verifiers_list_partitions_every_verifier_explicitly",
)

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal043_closeout.py"
ASSERTIONS = "tools/goal043_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-043-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-043-verdict-clean.txt"


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


def _has_text_anchor_on_the_call(source: str) -> bool:
    """**代码里**是否还按文本 index 匹配那个调用签名（**AST 判，不判 docstring 散文**）。

    **为什么用 AST 而不是子串搜索**（本判据的第一版实测假红）：`goal040_closeout_assertions.py`
    的 docstring 里**引述**了旧锚点（说明「为什么改它」）—— 那是**说明文字**，不是判据调用。
    子串搜索会把说明误判成缺陷（与 GOAL-20261009-042 的「判散文 vs 判调用」同一课）。
    """
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return True
    anchors = _string_constants_outside_docstrings(parsed)
    return any("_non_success_terminal(program, existing, last)" in item for item in anchors)


def _string_constants_outside_docstrings(parsed: ast.AST) -> list[str]:
    """模块里**非 docstring** 的字符串常量（判据用得上的是这些；docstring 是说明文字）。

    为什么必须排除 docstring（本判据第一版**实测假红**）：`goal040_closeout_assertions.py`
    的 docstring **引述**了旧锚点来说明「为什么改它」—— 那是说明，不是判据调用。
    **判散文与判调用是两件事**（承 GOAL-20261009-042 的同一课）。
    """
    docstrings: set[int] = set()
    for node in ast.walk(parsed):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    return [
        node.value
        for node in ast.walk(parsed)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：三处验证器加载**各自的**断言集（逐条对拍，不靠注释）。"""
    verdicts: list[Any] = []
    for relative in FIXED_VERIFIERS:
        goal_no = "".join(ch for ch in relative.split("verify_goal", 1)[1] if ch.isdigit())
        expected = f"goal{goal_no}_closeout_assertions.py"
        source = _text(root, relative)
        verdicts.append(
            toolbox.verdict(
                f"ec02-loads-its-own-assertions-{goal_no}",
                expected in source and "goal037_closeout_assertions.py" not in source,
                f"expected {expected}",
            )
        )
    return verdicts


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：崩溃面改 AST 结构判据（且**不再**按文本 index 匹配调用签名）。"""
    source = _text(root, GOAL040_ASSERTIONS)
    names = _function_names(source)
    return [
        toolbox.verdict(
            "ec03-structure-criterion-is-in-tree",
            {"_dispatch_precedes_conclusion_face", "_first_call_line"} <= names,
            ",".join(sorted(names & {"_dispatch_precedes_conclusion_face", "_first_call_line"})),
        ),
        toolbox.verdict(
            "ec03-no-text-anchor-on-the-changed-signature",
            not _has_text_anchor_on_the_call(source),
            "文本锚点仍在**代码**里 ⇒ 会随签名演进崩溃",
        ),
        toolbox.verdict(
            "ec03-the-criterion-is-called-by-the-verdict-list",
            "_dispatch_precedes_conclusion_face(runner)" in source,
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：机器判据在树且**三条主判据逐条在场**（按函数名读，不靠文本）。"""
    source = _text(root, NEW_JUDGE)
    names = _function_names(source)
    verdicts: list[Any] = [
        toolbox.verdict("ec04-the-judge-is-in-tree", bool(source)),
        toolbox.verdict(
            "ec04-both-directions-are-asserted",
            "declared" in source
            and "loaded" in source
            and "executable" in source
            and "raises" in source,
            "两向反例（声明≠实载 / 断言集抛异常）必须被断言",
        ),
    ]
    missing = [name for name in REQUIRED_JUDGES if name not in names]
    verdicts.append(
        toolbox.verdict("ec04-the-three-main-criteria-are-named", not missing, ",".join(missing))
    )
    return verdicts


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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…042 的教训）。"""
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
