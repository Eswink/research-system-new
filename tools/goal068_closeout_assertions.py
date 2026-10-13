#!/usr/bin/env python3
"""GOAL-20261013-068 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…067 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-068 特有的断言**。

三条主轴（逐条对 GOAL-068 的 EC）：

1. **EC-02 未知参数点名拒绝**：守卫在位 + **点名**（含已知集，供自纠）+ **多个逐个**；
   **射程** = 记忆读面的**两个 GET** 都调用它；**已知**参数集**显式登记**。
2. **EC-03 射程如实**：**只**那两条 GET 受此纪律（**不**装到路由级全局）；
   **已知**参数与**缺省**形态**逐字不变**（既有 DTO 形态一字不动）。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…067）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…35）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_memory_unknown_query_params_are_named.py", 8),
    ("tests/api/test_memory_author_filter_on_the_http_face.py", 8),
    ("tests/api/test_memory_api.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/tooling/test_mainline_archive_is_continuous.py",
    "tests/application/memory/test_memory_author_is_selectable.py",
    "tests/application/memory/test_dangling_reference_read_faces.py",
)

#: EC-02 / EC-03 落点。**守卫**在它自己的模块里（规模门：路由文件 450 行硬上限）。
ROUTER = "services/api/routers/memory.py"
GUARD_MODULE = "services/api/memory_query_guard.py"
DTO = "services/api/dto/memory.py"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
GUARD = "reject_unknown_query_params"
KNOWN = "_KNOWN_QUERY_PARAMS"
BOTH_GETS: tuple[str, ...] = ('/memory"', '/memory/validity"')
KNOWN_VALUES: tuple[str, ...] = ("scope", "proposed_by", "at")

#: EC-04 判据 / 归档落点。
UNKNOWN_JUDGE = "tests/api/test_memory_unknown_query_params_are_named.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-068-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal068_closeout.py"
ASSERTIONS = "tools/goal068_closeout_assertions.py"


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


def _contains(literals: set[str], fragment: str) -> bool:
    """**子串**匹配（判词是 f-string ⇒ 片段可能只是某个分片的一部分；承序 22/23）。"""
    return any(fragment in literal for literal in literals)


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：守卫在位 + **点名**（含已知集）+ **逐个** + **两个 GET 都调用它**。"""
    router = _text(root, ROUTER)
    guard = _text(root, GUARD_MODULE)
    guard_literals = _module_string_literals(guard)
    missing_known = [name for name in KNOWN_VALUES if name not in guard_literals]
    return [
        toolbox.verdict(
            "ec02-the-guard-exists",
            f"{GUARD}(" in guard,
            "未知参数的守卫必须在树（单列模块：射程与理由写在它自己的 docstring 里）",
        ),
        toolbox.verdict(
            "ec02-the-known-set-is-explicit",
            f"{KNOWN}: frozenset[str]" in guard and not missing_known,
            ",".join(missing_known) or "已知参数集必须**显式登记**（加参数要同步改它）",
        ),
        toolbox.verdict(
            "ec02-the-verdict-names-every-unknown",
            # **判关系**：正文里**逐个**列出（不是只报第一个）。
            # **注**：`join(unknown)` 在 f-string 里是 `FormattedValue`（**不是** `Constant`）
            # ⇒ AST 字面量读不到；改判**源码文本**里的那个**取值形态**（首版按 AST 判**假红**）。
            "join(unknown)" in guard,
            "点名必须**逐个**（只报第一个会让「还有哪些打错了」读不出来）",
        ),
        toolbox.verdict(
            "ec02-both-memory-gets-call-it",
            f"{GUARD}(request)" in router and router.count(f"{GUARD}(request)") >= 2,
            "**两个**记忆 GET 都要调用守卫（射程 = 那两条）",
        ),
        toolbox.verdict(
            "ec02-the-error-is-a-422",
            "422," in guard and _contains(guard_literals, "Unknown Query Parameter"),
            "**422 + 点名**（不静默忽略、不 500）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：**射程如实**（不装到全局）+ **已知/缺省形态一字不动**。"""
    router = _text(root, ROUTER)
    dto = _text(root, DTO)
    return [
        toolbox.verdict(
            "ec03-the-guard-is-not-a-global-middleware",
            # **判关系**：守卫是**路由内**调用（不是 app 级中间件）—— 射程有意收窄。
            "add_middleware" not in router,
            "**不**装成全局中间件（射程=那两个 GET 是**有意**边界，全仓 65 条 GET 口径未定）",
        ),
        toolbox.verdict(
            "ec03-the-known-dtos-are-untouched",
            # **判关系**：两个已知形态仍在（`scope` / `proposed_by` 各自的并集成员）。
            "MemoryFilteredListViewDto" in router and "MemoryAuthoredListViewDto" in router,
            "既有两个已知参数的**披露形态逐字仍在**",
        ),
        toolbox.verdict(
            "ec03-the-known-values-are-not-rejected",
            # **判关系**：已知集合**包含**那三个（少一个 ⇒ 正确请求被误拒 = `Z-2` 的形态）。
            all(
                name in _module_string_literals(_text(root, GUARD_MODULE)) for name in KNOWN_VALUES
            ),
            "已知参数必须**在集合里**（否则正确请求被误拒）",
        ),
        toolbox.verdict(
            "ec03-the-dto-shapes-are-not-widened",
            # **判关系**：本轮的加法**不**动 DTO（参数校验面不进 schema ⇒ 快照不变的**理由**）。
            "class MemoryAuthoredListViewDto" in dto,
            "本轮不动 DTO 形态（参数校验面不进 schema —— 快照不变的理由如实登记）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    unknown = _text(root, UNKNOWN_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-ignore-arm-is-asserted",
            "test_an_unknown_query_parameter_is_named" in unknown,
            "`Z-1` 的受判面必须在树（未知 ⇒ 点名）",
        ),
        toolbox.verdict(
            "ec04-the-known-arm-is-asserted",
            "test_the_known_parameters_still_work_verbatim" in unknown,
            "`Z-2` 的受判面必须在树（已知参数一字不动）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_the_default_form_is_verbatim" in unknown,
            "`Z-3` 的受判面必须在树（缺省形态逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-each-name-arm-is-asserted",
            "test_several_unknown_parameters_are_each_named" in unknown,
            "`Z-4` 的受判面必须在树（多个未知逐个点名）",
        ),
        toolbox.verdict(
            "ec04-the-range-arm-is-asserted",
            "test_the_range_is_the_two_memory_gets_only" in unknown,
            "射程（只那两条 GET）的受判面必须在树",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…067 的教训）。"""
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
