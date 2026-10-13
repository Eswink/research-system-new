#!/usr/bin/env python3
"""GOAL-20261013-072 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…071 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-072 特有的断言**。

三条主轴（逐条对 GOAL-072 的 EC）：

1. **EC-02 未声明面接通**：守卫把**空集支**（读面但无声明）从「跳过」改成「拒绝」
   （`if not known: raise` 形态）；正文含「不接受查询参数」措辞；**`None` 支仍在**
   （非读面一字不动 —— 射程边界）；判据面覆盖「未声明拒绝 + 缺省不变 + 写面不受影响」。
2. **EC-03 射程如实**：已声明面（序 37/38 判据）与写面（序 39 判据）仍在树；
   两处**改签**的对照臂在树且含**改动申报**（射程扩大，非收窄）；快照在树（零 diff 的理由）。
3. **EC-04 两向反证**：四条按压的受判面逐条在树（Y-1…Y-4）；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…071）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_undeclared_query_params_are_refused.py", 6),
    ("tests/api/test_memory_unknown_query_params_are_named.py", 8),
    ("tests/api/test_unknown_query_params_cover_every_declared_route.py", 11),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal071_closeout.py",
    "tests/api/test_write_body_typos_are_named.py",
)

#: EC-02 / EC-03 落点。
GUARD = "services/api/query_param_guard.py"
NEW_JUDGE = "tests/api/test_undeclared_query_params_are_refused.py"
PRIOR_MEMORY_JUDGE = "tests/api/test_memory_unknown_query_params_are_named.py"
PRIOR_DECLARED_JUDGE = "tests/api/test_unknown_query_params_cover_every_declared_route.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的形态（**逐条点名**；缺一即判红）。
EMPTY_BRANCH = "if not known:"
NONE_BRANCH = "if known is None:"
NO_PARAMS_WORDING = "accepts no query parameters"

#: EC-04 归档落点。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-072-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal072_closeout.py"
ASSERTIONS = "tools/goal072_closeout_assertions.py"

#: Y-1…Y-4 各自的**受判面用例名**（判据面必须在树；按压读数由归档承担）。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("Y-1", "test_an_undeclared_read_route_refuses_any_query_parameter"),
    ("Y-2", "test_the_declared_routes_keep_their_own_shape"),
    ("Y-3", "test_the_default_form_is_verbatim"),
    # **GOAL-20261013-073 改签**（逐条申报）：序 41 把写面纳入射程 ⇒ 该用例
    # 改名为 `test_the_write_face_is_now_in_the_scope`（射程**扩大**，断言由
    # 「带查询参数 ⇒ 201」改为「⇒ 422」）。判词仍钉同一受判面（写面对照臂）。
    ("Y-4", "test_the_write_face_is_now_in_the_scope"),
)


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
    """EC-02：空集支改拒绝 + 措辞 + `None` 支仍在（射程边界）+ 判据面三臂。"""
    guard = _text(root, GUARD)
    judge = _text(root, NEW_JUDGE)
    return [
        toolbox.verdict(
            "ec02-the-empty-branch-rejects",
            EMPTY_BRANCH in guard and NO_PARAMS_WORDING in guard,
            "空集支必须**拒绝**且正文明写「不接受查询参数」（空集的已知集是空串）",
        ),
        toolbox.verdict(
            "ec02-the-none-branch-survives",
            NONE_BRANCH in guard,
            "`None` 支（非读面）必须仍在 —— 射程边界（写面一字不动）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-declared-shape",
            "known:" in judge,
            "判据面要判**已声明面照旧**（给 known 清单，不是「不接受」措辞）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-default-and-write",
            "test_the_default_form_is_verbatim" in judge
            and "test_the_write_face_is_now_in_the_scope" in judge,
            "缺省形态与写面对照臂都必须在判据面",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：旧面判据在树 + 两处改签含申报 + 快照在树。"""
    memory_judge = _text(root, PRIOR_MEMORY_JUDGE)
    declared_judge = _text(root, PRIOR_DECLARED_JUDGE)
    return [
        toolbox.verdict(
            "ec03-the-prior-memory-judge-still-exists",
            (root / PRIOR_MEMORY_JUDGE).is_file(),
            "序 36 的记忆读面判据必须仍在树",
        ),
        toolbox.verdict(
            "ec03-the-resigned-arms-declare-the-change",
            # 改签必须留下**申报**（射程扩大，不是收窄）—— 两处都点名序 40 的语义变化。
            "GOAL-20261013-072" in memory_judge and "GOAL-20261013-072" in declared_judge,
            "两处改签的对照臂必须含**改动申报**（射程扩大，非收窄）",
        ),
        toolbox.verdict(
            "ec03-the-declared-face-judge-exists",
            (root / PRIOR_DECLARED_JUDGE).is_file(),
            "序 37 的已声明面判据必须仍在树",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-is-in-tree",
            (root / SNAPSHOT).is_file(),
            "快照必须仍在树（本轮**零 diff** —— 不动签名，如实登记）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    verdicts: list[Any] = [
        toolbox.verdict(
            f"ec04-the-{label.lower()}-arm-is-asserted",
            name in judge,
            f"`{label}` 的受判面必须在树",
        )
        for label, name in _PRESS_JUDGES
    ]
    verdicts.extend([
        toolbox.verdict(
            "ec04-the-baseline-gate-is-in-the-archive",
            "BASELINE" in press and "GREEN" in press,
            "归档必须含**基线行**（未按压不得红 —— 一级纪律）",
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
        ),
        toolbox.verdict(
            "ec04-the-archive-records-byte-exact-restore",
            press.count("sha 复原一致=True") >= 4,
            "逐条 raw sha256 复原一致（二进制读写）",
        ),
    ])
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…071 的教训）。"""
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
        toolbox.verdict("scope-in-scope-pure-tightening", not missing, ",".join(missing)),
        toolbox.verdict("scope-verifier-registered", registered),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的特有断言（收口验证器唯一入口）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
