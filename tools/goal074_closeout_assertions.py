#!/usr/bin/env python3
"""GOAL-20261013-074 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…073 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-074 特有的断言**。

三条主轴（逐条对 GOAL-074 的 EC）：

1. **EC-02 重复臂接通**：守卫用 **`multi_items()`** 计数（`keys()` 去重 ⇒ 数不到重复，
   首版实现即此误）；**射程由声明类型导出**（`scalar_query_params` 判**签名注解**的
   `list[...]`）；措辞含「accept exactly one value」（与「未知参数」**分辨**）。
2. **EC-03 射程如实**：三面判据（序 37/40/41）与写面体（序 39）仍在树；
   `list` 声明的边界（`expected_digests`）在判据面；快照在树（零 diff 的理由）。
3. **EC-04 两向反证**：四条按压的受判面逐条在树（W5-1…W5-4）；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…073）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_duplicate_scalar_query_params_are_refused.py", 7),
    ("tests/api/test_unknown_query_params_cover_every_declared_route.py", 11),
    ("tests/api/test_undeclared_query_params_are_refused.py", 6),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal073_closeout.py",
    "tests/api/test_write_face_query_params_are_refused.py",
    "tests/api/test_write_body_typos_are_named.py",
)

#: EC-02 / EC-03 落点。
GUARD = "services/api/query_param_guard.py"
NEW_JUDGE = "tests/api/test_duplicate_scalar_query_params_are_refused.py"
PRIOR_DECLARED_JUDGE = "tests/api/test_unknown_query_params_cover_every_declared_route.py"
PRIOR_UNDECLARED_JUDGE = "tests/api/test_undeclared_query_params_are_refused.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的形态（**逐条点名**；缺一即判红）。
MULTI_ITEMS = "multi_items()"
TYPE_EXPORT = "def scalar_query_params("
WORDING = "accept exactly one value"

#: EC-04 归档落点。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-074-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal074_closeout.py"
ASSERTIONS = "tools/goal074_closeout_assertions.py"

#: W5-1…W5-4 各自的**受判面用例名**（判据面必须在树；按压读数由归档承担）。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("W5-1", "test_a_repeated_scalar_param_is_named"),
    ("W5-2", "test_the_list_declared_param_may_repeat"),
    ("W5-3", "test_the_single_and_default_forms_are_verbatim"),
    ("W5-4", "test_the_prior_faces_do_not_regress"),
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
    """EC-02：`multi_items()` 计数 + 类型导出面 + 措辞分辨 + 判据面覆盖。"""
    guard = _text(root, GUARD)
    judge = _text(root, NEW_JUDGE)
    return [
        toolbox.verdict(
            "ec02-the-count-uses-multi-items",
            MULTI_ITEMS in guard,
            "计数必须用 `multi_items()`（`keys()` 去重 ⇒ 数不到重复 —— 首版实现的真实误）",
        ),
        toolbox.verdict(
            "ec02-the-scope-is-derived-from-declared-types",
            TYPE_EXPORT in guard and "list[" in guard,
            "射程必须**由声明类型导出**（`list[...]` 注解判型；射程边界）",
        ),
        toolbox.verdict(
            "ec02-the-wording-distinguishes-repeated",
            WORDING in guard and "known:" in guard,
            "「重复」措辞必须与「未知参数」**分辨**（读者要能区分「名字不对」与「给多了」）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-the-boundary",
            "test_the_list_declared_param_may_repeat" in judge,
            "`list` 声明边界的受判面必须在判据面（射程越界会假绿）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：旧面判据在树 + 快照在树 + 提取面自检在判据面。"""
    judge = _text(root, NEW_JUDGE)
    return [
        toolbox.verdict(
            "ec03-the-prior-judges-still-exist",
            (root / PRIOR_DECLARED_JUDGE).is_file()
            and (root / PRIOR_UNDECLARED_JUDGE).is_file()
            and (root / "tests/api/test_write_face_query_params_are_refused.py").is_file(),
            "序 37/40/41 三面判据必须都仍在树",
        ),
        toolbox.verdict(
            "ec03-the-export-face-self-check-is-in-the-judge",
            "test_a_list_declared_export_and_scalar_export_agree" in judge,
            "提取函数本身的机制判（`list[...]` 被识别 / 无 endpoint 不推断）必须在判据面",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…073 的教训）。"""
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
