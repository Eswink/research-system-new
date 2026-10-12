#!/usr/bin/env python3
"""GOAL-20261012-062 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…061 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-062 特有的断言**。

三条主轴（逐条对 GOAL-062 的 EC）：

1. **EC-02 反向索引与分派**：`conflicted_by_index` 在位（**扫同批记录**，与序 18 同一手法）；
   处置面按 `conflicted_by` 分派；**两种成因**在判词里**可区分**。
2. **EC-03 两读面同源 + 缺省逐字不变**：两个读面**都引用**同一纯函数；既有键逐字仍在；
   DTO + 快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…061）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…29）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_reverse_conflict_link.py", 9),
    ("tests/application/memory/test_reverse_conflict_read_faces.py", 7),
    ("tests/api/test_memory_api.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_conflict_timeliness_read_faces.py",
    "tests/application/memory/test_conflict_resolution_read_faces.py",
    "tests/domain/test_conflict_timeliness.py",
)

#: EC-02 / EC-03 落点。
DISPOSITION = "packages/application/memory/disposition.py"
ORCH_FACE = "adapters/canonical/memory_read.py"
HTTP_ROUTER = "services/api/routers/memory.py"
HTTP_DTO = "services/api/dto/memory.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的名字（**逐条点名**；缺一即判红）。
INDEX = "conflicted_by_index"
FIELD = "conflicted_by"
POSITIVE = "contradictions"

#: EC-02：两种成因的判词片段（f-string ⇒ 按**子串**核对）。
REASON_FORMS: tuple[str, ...] = ("声明与 ", "**被 ", "声明与它冲突**")

#: EC-04 判据 / 归档落点。
LINK_JUDGE = "tests/application/memory/test_reverse_conflict_link.py"
FACES_JUDGE = "tests/application/memory/test_reverse_conflict_read_faces.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-062-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal062_closeout.py"
ASSERTIONS = "tools/goal062_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def _class_annotations(source: str, class_name: str) -> set[str]:
    """类体的**注解名**（AST 读 —— 不 import 那个包）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            names: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    names.add(item.target.id)
            return names
    return set()


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
    """EC-02：**反向索引**在位（同一手法）+ 处置面**按它分派** + 两种成因**可区分**。"""
    disposition = _text(root, DISPOSITION)
    literals = _module_string_literals(disposition)
    missing_forms = [item for item in REASON_FORMS if not _contains(literals, item)]
    return [
        toolbox.verdict(
            "ec02-the-reverse-index-exists",
            f"def {INDEX}" in disposition,
            "反向索引必须单列（与序 18 的 `superseded_by_index` 同一手法）",
        ),
        toolbox.verdict(
            "ec02-the-index-scan-is-the-same-hand",
            # **判关系**：索引按**声明**扫同批记录（与序 18 逐字同形：正向链接在**别人**身上）。
            f"for other_id in record.{POSITIVE}" in disposition,
            "索引必须扫**声明**字段（正向链接写在声明方身上）",
        ),
        toolbox.verdict(
            "ec02-the-disposition-dispatches-on-being-declared-against",
            # **判关系**：两条成因**并列**进同一支（同类不同因的前提）。
            "if conflicted or conflicted_by:" in disposition,
            "处置面必须按反向声明分派（只看正向 ⇒ 被声明方仍照用）",
        ),
        toolbox.verdict(
            "ec02-both-causes-are-named-in-the-reason",
            not missing_forms,
            ",".join(missing_forms),
        ),
        toolbox.verdict(
            "ec02-the-default-parameter-keeps-the-form-verbatim",
            # **判关系**：新参数有**缺省值** ⇒ 既有调用点逐字不变。
            "conflicted_by: bool = False" in disposition,
            "新参数必须有缺省（否则既有调用点全断 = 不是加法）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两读面**同源** + **正向读法一字不动** + DTO/快照同轮。"""
    orch = _text(root, ORCH_FACE)
    router = _text(root, HTTP_ROUTER)
    dto = _text(root, HTTP_DTO)
    return [
        toolbox.verdict(
            "ec03-the-orchestration-face-uses-the-shared-index",
            INDEX in orch,
            "编排读面必须**扫同批记录**算出反向链接（与序 18 同一手法）",
        ),
        toolbox.verdict(
            "ec03-the-http-face-uses-the-same-index",
            INDEX in router,
            "HTTP 读面必须调**同一个**函数（两处各写一套 = 漂移无从发现）",
        ),
        toolbox.verdict(
            "ec03-the-positive-reading-is-untouched",
            # **判关系**：两处仍是「读**声明**字段」的正向披露（本轮的加法不改它）。
            f"record.{POSITIVE}" in orch and f"record.{POSITIVE}" in router,
            "`contradictions` 的**正向**读法必须逐字仍在（本轮**不**改它）",
        ),
        toolbox.verdict(
            "ec03-the-dtos-carry-the-reverse-key",
            FIELD in dto,
            "HTTP DTO 必须披露反向键（与编排面同源同值）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-reverse-key",
            FIELD in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含该键（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    link = _text(root, LINK_JUDGE)
    faces = _text(root, FACES_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-reverse-index-arm-is-asserted",
            "test_the_reverse_index_reports_who_declared_a_conflict" in link,
            "`Y-1` 的受判面必须在树（反向索引报出声明方）",
        ),
        toolbox.verdict(
            "ec04-the-dispatch-arm-is-asserted",
            "test_being_declared_against_produces_conflicted_not_use" in link,
            "`Y-2` 的受判面必须在树（按反向分派）",
        ),
        toolbox.verdict(
            "ec04-the-default-arm-is-asserted",
            "test_the_default_disposition_is_verbatim_when_nobody_declared" in link,
            "`Y-3` 的受判面必须在树（缺省形态逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-two-causes-arm-is-asserted",
            "test_the_two_causes_are_distinguishable_in_the_reason" in link
            and "test_the_reason_does_not_double_report_the_same_cause" in link,
            "`Y-4` 的受判面必须在树（两种成因可区分且不重复）",
        ),
        toolbox.verdict(
            "ec04-the-declared-against-arm-is-on-the-face",
            "test_the_declared_against_record_is_no_longer_used_verbatim" in faces,
            "被声明方的判据必须在**读面**那一组（受判面 = 披露面）",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…061 的教训）。"""
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
