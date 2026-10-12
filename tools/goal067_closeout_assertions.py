#!/usr/bin/env python3
"""GOAL-20261013-067 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…066 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-067 特有的断言**。

三条主轴（逐条对 GOAL-067 的 EC）：

1. **EC-02 HTTP 读面按作者筛**：路由有该可选参数 + **真的传给 Port**（不吞）；
   **披露两键**（`proposed_by` + `filtered_out`）；**缺省不筛**（既有请求逐字不变）。
2. **EC-03 三形态与快照**：缺省 / 按范围 / 按作者**三个形态**都在并集里（少一个 ⇒
   FastAPI 收窄载荷、**静默抹掉**该维披露键）；`?scope=` 的既有语义**一字不动**；快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…066）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…34）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_memory_author_filter_on_the_http_face.py", 8),
    ("tests/api/test_memory_api.py", 10),
    ("tests/application/memory/test_memory_author_is_selectable.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_memory_author_read_faces.py",
    "tests/adapters/canonical/test_memory_read_dispositions.py",
    "tests/domain/test_conflict_timeliness.py",
)

#: EC-02 / EC-03 落点。
ROUTER = "services/api/routers/memory.py"
DTO = "services/api/dto/memory.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
FIELD = "proposed_by"
AUTHORED_DTO = "MemoryAuthoredListViewDto"
SCOPED_DTO = "MemoryFilteredListViewDto"

#: EC-04 判据 / 归档落点。
HTTP_JUDGE = "tests/api/test_memory_author_filter_on_the_http_face.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-067-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal067_closeout.py"
ASSERTIONS = "tools/goal067_closeout_assertions.py"


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
    """EC-02：路由有该参数 + **真的传给 Port** + **披露** + **缺省不筛**。"""
    router = _text(root, ROUTER)
    return [
        toolbox.verdict(
            "ec02-the-route-accepts-the-author",
            f"{FIELD}: str | None = None" in router,
            "路由必须接受该可选参数（改动前它被**静默吞掉**）",
        ),
        toolbox.verdict(
            "ec02-the-route-passes-it-to-the-port",
            # **判关系**：把它**交给** Port（吞掉就是本 GOAL 的靶子形态）。
            f"store.query(scope=scope, {FIELD}={FIELD})" in router,
            "路由必须把它**交给** Port（不吞 —— 静默忽略正是本轮的靶子）",
        ),
        toolbox.verdict(
            "ec02-the-payload-discloses-both-keys",
            f"{FIELD}={FIELD}," in router and "filtered_out=" in router,
            "载荷必须披露**筛了什么**与**筛掉多少条**",
        ),
        toolbox.verdict(
            "ec02-the-default-does-not-filter",
            f"if scope is None and {FIELD} is None:" in router,
            "**缺省 ⇒ 走缺省形态**（既有请求逐字不变）",
        ),
        toolbox.verdict(
            "ec02-the-scope-branch-is-untouched",
            "MemoryFilteredListViewDto(" in router and "scope=scope," in router,
            "序 17 的 `?scope=` 支**语义一字不动**（本轮只**加**第二个维度）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：**三形态都在并集里** + 专用 DTO 在位 + 快照同轮。"""
    router = _text(root, ROUTER)
    dto = _text(root, DTO)
    return [
        toolbox.verdict(
            "ec03-the-authored-shape-exists",
            f"class {AUTHORED_DTO}" in dto,
            "作者维的**专用形态**必须在（与范围形态同一手法）",
        ),
        toolbox.verdict(
            "ec03-the-union-lists-all-three-shapes",
            # **判关系**：并集里**三个都在**（少一个 ⇒ 载荷被收窄、披露键静默消失）。
            all(name in router for name in ("MemoryListViewDto |", SCOPED_DTO, AUTHORED_DTO)),
            "响应并集必须含**三个**形态（少一个就静默丢键）",
        ),
        toolbox.verdict(
            "ec03-the-no-recursive-exclude-switch",
            # **判关系**：判**调用形态**（`exclude_none=True` 这种**参数**写法），
            # **不**按短语出现与否判 —— 它在本文件里以**注释**形式出现（解释「为何不用」），
            # 按出现判会**假红**（首版即如此，已按实测改准）。
            "exclude_none=True" not in router,
            "**不**用递归排除开关（那会抹掉别的读面上有意义的 `null`）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-authored-shape",
            AUTHORED_DTO in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该形态（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    http = _text(root, HTTP_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-ignore-arm-is-asserted",
            "test_the_author_filter_selects_and_discloses" in http,
            "`Y-1` 的受判面必须在树（传作者 ⇒ 真筛 + 披露）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_the_default_payload_is_verbatim" in http,
            "`Y-2` 的受判面必须在树（缺省载荷逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-disclosure-arm-is-asserted",
            "test_the_three_shapes_are_distinguishable" in http,
            "`Y-3` 的受判面必须在树（三个形态各自的键集）",
        ),
        toolbox.verdict(
            "ec04-the-unguessed-arm-is-asserted",
            "test_an_unknown_author_is_empty_not_everything" in http,
            "`Y-4` 的受判面必须在树（未知作者 ⇒ 空集，不猜）",
        ),
        toolbox.verdict(
            "ec04-the-prior-scope-arm-is-asserted",
            "test_the_scope_disclosure_is_untouched" in http,
            "序 17 的 `?scope=` 回归臂必须在树",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…066 的教训）。"""
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
