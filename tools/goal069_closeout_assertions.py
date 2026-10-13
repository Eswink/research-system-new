#!/usr/bin/env python3
"""GOAL-20261013-069 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…068 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-069 特有的断言**。

三条主轴（逐条对 GOAL-069 的 EC）：

1. **EC-02 全员覆盖**：导出面**从签名读**（不是手写清单：守卫模块里**没有**已知参数的字面量）；
   注册点 = **构造期应用级依赖**（`Depends(reject_unknown_query_params)` 在 `create_app` 里）；
   判据面覆盖**每条已声明路由**（逐条清单 **9** 条 + 与 app 的全部声明面**相等**的断言在位）。
2. **EC-03 射程如实**：对照臂在位（未声明参数的路由一字不动）；序 36 的记忆读面判据**仍在树**
   且**未被删改**（例数下界）；快照无差分（guard 不进 schema）。
3. **EC-04 两向反证**：四条按压的受判面逐条在树（W-1…W-4 各自的用例名）；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…068）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_unknown_query_params_cover_every_declared_route.py", 11),
    ("tests/api/test_memory_unknown_query_params_are_named.py", 8),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/observability/test_privacy_exit_census.py",
    "tests/api/test_memory_api.py",
)

#: EC-02 / EC-03 落点。
GUARD_MODULE = "services/api/query_param_guard.py"
APP_FACTORY = "services/api/app.py"
NEW_JUDGE = "tests/api/test_unknown_query_params_cover_every_declared_route.py"
CENSUS = "tests/observability/test_privacy_exit_census.py"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
EXPORT = "declared_query_params"
GUARD = "reject_unknown_query_params"
SIGNATURE_SOURCE = "dependant.query_params"

#: EC-04 归档落点。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-069-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal069_closeout.py"
ASSERTIONS = "tools/goal069_closeout_assertions.py"

#: W-1…W-4 各自的**受判面用例名**（判据面必须在树；按压的读数由归档承担）。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("W-1", "test_every_declared_read_route_names_its_unknown_parameters"),
    ("W-2", "test_the_known_forms_are_verbatim"),
    ("W-3", "test_the_default_form_is_verbatim"),
    ("W-4", "test_routes_without_declared_parameters_are_untouched"),
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


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：导出面（签名读）+ 注册点（构造期应用级依赖）+ 判据的受判面。"""
    guard = _text(root, GUARD_MODULE)
    app = _text(root, APP_FACTORY)
    judge = _text(root, NEW_JUDGE)
    literals = _module_string_literals(guard)
    hand_written = [name for name in ("limit", "scope", "horizon_days") if name in literals]
    export_verdicts = [
        toolbox.verdict(
            "ec02-the-export-face-exists",
            f"def {EXPORT}(" in guard,
            "导出面必须在树（已知集**从签名读**的那一半）",
        ),
        toolbox.verdict(
            "ec02-the-known-set-comes-from-the-signature",
            SIGNATURE_SOURCE in guard,
            "已知集必须**从匹配路由的签名**读（不手写清单 ⇒ 加参数自动跟着走）",
        ),
        toolbox.verdict(
            "ec02-the-known-set-is-not-hand-written",
            not hand_written,
            ",".join(hand_written),
        ),
        toolbox.verdict(
            "ec02-the-registration-is-a-constructor-time-dependency",
            f"Depends({GUARD})" in app,
            "注册点 = **构造期**应用级依赖（实测：事后 append 不生效 —— 装配顺序 = 契约）",
        ),
        toolbox.verdict(
            "ec02-the-verdict-names-every-unknown",
            "join(unknown)" in guard,
            "点名必须**逐个**（只报第一个会让「还有哪些打错了」读不出来）",
        ),
    ]
    return [*export_verdicts, *_ec02_judge_verdicts(guard, judge, toolbox)]


def _ec02_judge_verdicts(guard: str, judge: str, toolbox: Any) -> list[Any]:
    """EC-02 的后半：判词形态 + 判据面的覆盖形态。"""
    return [
        toolbox.verdict(
            "ec02-the-verdict-gives-the-known-set",
            "join(sorted(known))" in guard and f'"{GUARD}(' not in guard,
            "正文给出**该路由**的已知集（供自纠）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-every-declared-route",
            # 受判面 = **逐条 9 条 + 与 app 全部声明面相等**两条断言都在。
            judge.count("_DECLARED") >= 3
            and "test_the_judged_list_matches_every_declared_route_in_the_app" in judge,
            "判据面要**逐条**覆盖且与 app 的声明面**相等**（不是抽样清单）",
        ),
        toolbox.verdict(
            "ec02-the-drift-arm-is-behavioral",
            "test_a_route_added_later_is_covered_without_editing_any_list" in judge,
            "「不手写清单」要有**行为**证据（事后注册的新路由自动受纪律）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：射程如实（对照臂）+ 旧面回归（序 36 判据未动）+ 普查同轮。"""
    judge = _text(root, NEW_JUDGE)
    census = _text(root, CENSUS)
    return [
        toolbox.verdict(
            "ec03-the-control-arm-is-in-the-judge",
            "test_routes_without_declared_parameters_are_untouched" in judge,
            "对照臂必须在树（未声明参数的路由一字不动）",
        ),
        toolbox.verdict(
            "ec03-the-scope-is-derived-from-the-route-signature",
            # **GOAL-20261013-073 改签**（逐条申报）：序 37 钉的是「方法闸门字面量
            # `"GET", "HEAD"`」——那是**当时**的射程实现（写面不在射程）。序 41
            # **有意**去掉该闸门（写面接通，射程**扩大**）⇒ 字面锚失效。
            # 改判**关系**：射程仍**从路由签名导出**（不手写清单），这是序 37 的本体。
            "dependant.query_params" in _text(root, GUARD_MODULE)
            and "request.query_params" in _text(root, GUARD_MODULE),
            "射程必须仍**从路由签名导出**（不手写清单；GOAL-073 起方法不再收窄射程 —— 射程扩大）",
        ),
        toolbox.verdict(
            "ec03-the-prior-memory-judge-still-exists",
            (root / "tests/api/test_memory_unknown_query_params_are_named.py").is_file(),
            "序 36 的记忆读面判据必须仍在树（本轮**不**改它）",
        ),
        toolbox.verdict(
            "ec03-the-new-emitter-is-classified-in-the-census",
            GUARD_MODULE in census,
            "新写 `raise ApiError` 的模块要进隐私出口普查（同轮）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…068 的教训）。"""
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
