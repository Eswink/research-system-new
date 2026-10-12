#!/usr/bin/env python3
"""GOAL-20261012-064 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…063 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-064 特有的断言**。

三条主轴（逐条对 GOAL-064 的 EC）：

1. **EC-02 悬空索引与两方向**：`dangling_reference_index` 在位
   （扫同批记录，与序 30/31 同一手法）；
   两个方向**各自报**（`supersedes` / `contradictions`）；
   **既有键一字不动**（`terminal` 取值不变）。
2. **EC-03 两读面同源**：两个读面**都引用**同一纯函数；
   两个悬空键**都在**（另键披露）；
   DTO + 快照同轮。
3. **EC-04 两向反证**：判据在树 + **四条按压 + 基线门**逐条对得上；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…063）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24…31）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_dangling_reference_read_faces.py", 10),
    ("tests/application/memory/test_resolved_pair_read_faces.py", 10),
    ("tests/api/test_memory_api.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_reverse_conflict_read_faces.py",
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
INDEX = "dangling_reference_index"
KEYS: tuple[str, ...] = ("dangling_supersedes", "dangling_contradictions")
POSITIVE: tuple[str, ...] = ("supersedes", "contradictions")

#: EC-04 判据 / 归档落点。
FACES_JUDGE = "tests/application/memory/test_dangling_reference_read_faces.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-064-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal064_closeout.py"
ASSERTIONS = "tools/goal064_closeout_assertions.py"


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
    """EC-02：**悬空索引**在位 + **两个方向各自报** + **既有键一字不动**。"""
    disposition = _text(root, DISPOSITION)
    orch = _text(root, ORCH_FACE)
    return [
        toolbox.verdict(
            "ec02-the-dangling-index-exists",
            f"def {INDEX}" in disposition,
            "悬空索引必须单列（与序 30/31 同一手法）",
        ),
        toolbox.verdict(
            "ec02-the-index-checks-both-directions",
            # **判关系**：两个方向各自算缺失（而不是只查一个方向）。
            "missing_supersedes = [" in disposition and "missing_contradictions = [" in disposition,
            "悬空判定必须**两个方向各自**算（`supersedes` / `contradictions` 语义不同）",
        ),
        toolbox.verdict(
            "ec02-the-index-scope-is-the-batch",
            # **判关系**：存在性按**本批记录**判（不猜「它一定被删」）。
            "present = {str(record.id) for record in records}" in disposition,
            "存在性必须按**本批**判（看不见 ≠ 不存在 ⇒ 如实报、不猜）",
        ),
        toolbox.verdict(
            "ec02-the-existing-keys-are-untouched",
            # **判关系**：`terminal` 的既有取值**不**参与悬空（本轮的加法是另键）。
            all(item in orch for item in POSITIVE),
            "`supersedes` / `contradictions` 的既有读法必须逐字仍在",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两读面**同源** + **两个悬空键都在**（另键披露）+ DTO/快照同轮。"""
    orch = _text(root, ORCH_FACE)
    router = _text(root, HTTP_ROUTER)
    dto = _text(root, HTTP_DTO)
    return [
        toolbox.verdict(
            "ec03-the-orchestration-face-uses-the-shared-index",
            INDEX in orch,
            "编排读面必须**扫同批记录**算出悬空（与序 30/31 同一手法）",
        ),
        toolbox.verdict(
            "ec03-the-http-face-uses-the-same-index",
            INDEX in router,
            "HTTP 读面必须调**同一个**函数（两处各写一套 = 漂移无从发现）",
        ),
        toolbox.verdict(
            "ec03-both-dangling-keys-are-disclosed",
            all(key in orch for key in KEYS),
            "两个方向**各自一个键**（混一个列表会让读者分不出是哪一种）",
        ),
        toolbox.verdict(
            "ec03-the-dtos-carry-both-keys",
            all(key in dto for key in KEYS),
            "HTTP DTO 必须披露两个键（与编排面同源同值）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-both-keys",
            all(key in _text(root, SNAPSHOT) for key in KEYS),
            "OpenAPI 快照必须含这两个键（动 DTO ⇒ 同轮同步）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    faces = _text(root, FACES_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-dangling-index-arm-is-asserted",
            "test_the_dangling_index_names_both_directions" in faces,
            "`V-1` 的受判面必须在树（两个方向各自报）",
        ),
        toolbox.verdict(
            "ec04-the-deleted-record-arm-is-asserted",
            "test_a_deleted_record_leaves_a_named_dangling_reference" in faces,
            "`V-2` 的受判面必须在树（被删 ⇒ 逐条点名）",
        ),
        toolbox.verdict(
            "ec04-the-verbatim-arm-is-asserted",
            "test_the_default_form_is_verbatim_for_clean_records" in faces,
            "`V-3` 的受判面必须在树（缺省形态逐字不变）",
        ),
        toolbox.verdict(
            "ec04-the-two-direction-arm-is-asserted",
            "test_the_dangling_index_names_both_directions" in faces
            and "test_the_existing_keys_are_unchanged_when_a_record_is_deleted" in faces,
            "`V-4` 的受判面必须在（两方向不混用 + 既有键不动）",
        ),
        toolbox.verdict(
            "ec04-the-scope-arm-is-on-the-face",
            "test_the_range_scope_is_not_guessed" in faces,
            "跨范围（看不见 ≠ 不存在）的受判面必须在树",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…063 的教训）。"""
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
