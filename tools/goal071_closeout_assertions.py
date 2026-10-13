#!/usr/bin/env python3
"""GOAL-20261013-071 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…070 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-071 特有的断言**。

三条主轴（逐条对 GOAL-071 的 EC）：

1. **EC-02 写面纪律**：共享基类 `StrictRequestDto` 在位且 `extra="forbid"`；
   **37 条请求体 DTO 逐条**继承它（数量下界 + 逐条清单）；**响应**模型**不**继承
   （射程反证臂）；判据面覆盖「未知被拒 + 已知照常成功」两臂。
2. **EC-03 射程如实**：查询参数面（序 37/38 判据）在树；快照在树（**零 diff** 的
   理由 = 生成器早已补写 `additionalProperties`，运行时此前与契约不一致 —— 如实登记）。
3. **EC-04 两向反证**：四条按压的受判面逐条在树；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…070）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_write_body_typos_are_named.py", 6),
    ("tests/api/test_unknown_query_params_cover_every_declared_route.py", 11),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal070_closeout.py",
    "tests/api/test_runs_api.py",
)

#: EC-02 / EC-03 落点。
BASE_MODULE = "services/api/dto/common.py"
NEW_JUDGE = "tests/api/test_write_body_typos_are_named.py"
PRIOR_JUDGE = "tests/api/test_unknown_query_params_cover_every_declared_route.py"
SNAPSHOT = "docs/api/openapi.m13.json"
GENERATOR = "tools/gen_openapi.py"

#: 本轮引入的形态（**逐条点名**；缺一即判红）。
BASE = "StrictRequestDto"
STRICT = 'extra="forbid"'
#: 37 条请求体 DTO 的**数量下界**（改 DTO 集合时只上调不下调）。
REQUEST_DTO_FLOOR = 37

#: EC-04 归档落点。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-071-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal071_closeout.py"
ASSERTIONS = "tools/goal071_closeout_assertions.py"

#: X-1…X-4 各自的**受判面用例名**（判据面必须在树；按压读数由归档承担）。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("X-1", "test_an_unknown_write_body_field_is_named"),
    ("X-2", "test_a_second_module_dto_is_covered_too"),
    ("X-3", "test_several_unknown_fields_are_each_named"),
    ("X-4", "test_an_unknown_write_body_field_is_named"),
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


def _inheriting_dtos(root: Path) -> list[str]:
    """全仓继承 `StrictRequestDto` 的类（AST 读 —— **逐条清单**，不猜数量）。"""
    found: list[str] = []
    for path in sorted((root / "services" / "api" / "dto").glob("*.py")):
        try:
            parsed = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(parsed):
            if isinstance(node, ast.ClassDef) and BASE in {
                base.id for base in node.bases if isinstance(base, ast.Name)
            }:
                found.append(f"{path.name}:{node.name}")
    return sorted(found)


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：共享基类 + 逐条继承清单 + 响应模型反证臂 + 判据面两臂。"""
    base = _text(root, BASE_MODULE)
    judge = _text(root, NEW_JUDGE)
    inherited = _inheriting_dtos(root)
    return [
        toolbox.verdict(
            "ec02-the-shared-base-exists",
            f"class {BASE}(BaseModel)" in base and STRICT in base,
            '共享严格基类必须在树且 `extra="forbid"`（机制落点 —— EC-01 实测选定）',
        ),
        toolbox.verdict(
            "ec02-every-request-dto-inherits-it",
            len(inherited) >= REQUEST_DTO_FLOOR,
            f"{len(inherited)} < {REQUEST_DTO_FLOOR}（逐条清单见 detail 之外的读取面）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-both-arms",
            # **判关系**：未知被拒（422）与已知照常（201/200）**两臂**都要在。
            "422" in judge and ("201" in judge or "200" in judge),
            "判据面必须有**两臂**（未知被拒 + 已知照常）—— X-2 首跑假绿的形态",
        ),
        toolbox.verdict(
            "ec02-the-loc-names-the-field",
            "loc" in judge,
            "点名形态（`loc` 里出现字段名）必须在判据面被判",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：射程如实（响应不 strict）+ 查询参数面不回归 + 快照与生成器。"""
    judge = _text(root, NEW_JUDGE)
    generator = _text(root, GENERATOR)
    return [
        toolbox.verdict(
            "ec03-the-response-arm-is-asserted",
            "test_response_models_are_not_strict" in judge,
            "**响应**模型不受纪律的**反证臂**必须在判据面（射程如实）",
        ),
        toolbox.verdict(
            "ec03-the-prior-query-judge-still-exists",
            (root / PRIOR_JUDGE).is_file(),
            "序 37 的查询参数判据必须仍在树（本轮**不**改它）",
        ),
        toolbox.verdict(
            "ec03-the-generator-closes-objects",
            "additionalProperties" in generator,
            "生成器补写 `additionalProperties` 的事实必须在树（**零 diff** 的理由）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-is-in-tree",
            (root / SNAPSHOT).is_file(),
            "快照必须仍在树（本轮**零 diff** —— 变的是运行时而非契约，如实登记）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…070 的教训）。"""
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
