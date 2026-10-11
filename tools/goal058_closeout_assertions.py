#!/usr/bin/env python3
"""GOAL-20261012-058 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…057 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-058 特有的断言**。

三条主轴（逐条对 GOAL-058 的 EC）：

1. **EC-02 消解可记录**：域上有 `ConflictResolution` / `resolutions`；四种坏形态校验判词在位；
   **逐对消解**（`unresolved_conflicts`）在位。
2. **EC-03 读面披露**：编排读面 `conflict_resolutions` 键；**未消解逐字不变**（`conflicted`
   按**未消解**判 —— `record.unresolved_conflicts` 在两个读面都在）。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**五条纪律**（承 GOAL-027…057）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红 —— 承序 24/25）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_conflict_resolution_lifecycle.py", 8),
    ("tests/application/memory/test_conflict_resolution_read_faces.py", 3),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_gate_adversarial.py",
    "tests/domain/test_research_program.py",
    "tests/api/test_memory_resolutions_on_the_http_face.py",
)

#: EC-02/EC-03 落点。
DOMAIN = "packages/domain/memory.py"
LIFECYCLE = "packages/application/memory/lifecycle.py"
DISPOSITION = "packages/application/memory/disposition.py"
READ_FACE = "adapters/canonical/memory_read.py"
HTTP_DTO = "services/api/dto/memory.py"
SNAPSHOT = "docs/api/openapi.m13.json"
SQLITE = "adapters/sqlite/memory_store.py"
PG_MIGRATION = "adapters/postgres/migrations/023_memory_conflict_resolutions.sql"

#: EC-02：域名字（逐条点名；缺一即判红）。
DOMAIN_NAMES: tuple[str, ...] = ("ConflictResolution",)
FIELD = "resolutions"

#: EC-02：四种坏形态的判词**片段**（f-string ⇒ 子串核对）。
REJECT_FRAGMENTS: tuple[str, ...] = (
    "not declared in contradictions",
    "cannot resolve a conflict with itself",
    "resolution other_id must not be empty",
    "resolution resolved_by must not be empty",
)

#: EC-03：读面键 + **同源**的判据坐标。
READ_KEY = "conflict_resolutions"
UNRESOLVED = "unresolved_conflicts"

#: EC-04 判据 / 归档落点。
LIFECYCLE_JUDGE = "tests/application/memory/test_conflict_resolution_lifecycle.py"
READ_FACES_JUDGE = "tests/application/memory/test_conflict_resolution_read_faces.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261012-058-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261012-058-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261012-058-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal058_closeout.py"
ASSERTIONS = "tools/goal058_closeout_assertions.py"


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
            return {
                target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance((target := item.target), ast.Name)
            }
    return set()


def _defines(source: str, name: str) -> bool:
    """该模块里有**任何**同名函数（**含类方法** —— 承序 23）。"""
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(parsed)
    )


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：域对象 + 字段 + 四种坏形态判词 + **逐对消解** + **两根落库**。"""
    domain = _text(root, DOMAIN)
    domain_literals = _module_string_literals(domain)
    missing_names = [name for name in DOMAIN_NAMES if f"class {name}" not in domain]
    missing_reject = [item for item in REJECT_FRAGMENTS if not _contains(domain_literals, item)]
    sqlite_ok = "resolutions" in _text(root, SQLITE)
    pg_ok = "resolutions" in _text(root, PG_MIGRATION) and "ADD COLUMN IF NOT EXISTS" in _text(
        root, PG_MIGRATION
    )
    return [
        toolbox.verdict(
            "ec02-the-resolution-object-is-declared",
            not missing_names,
            ",".join(missing_names),
        ),
        toolbox.verdict(
            "ec02-the-record-carries-the-resolution-list",
            FIELD in _class_annotations(domain, "MemoryRecord"),
            f"记录上必须有 \`{FIELD}\`（缺省空 ⇒ 既有行为逐字不变）",
        ),
        toolbox.verdict(
            "ec02-every-bad-shape-is-named",
            not missing_reject,
            ",".join(missing_reject),
        ),
        toolbox.verdict(
            "ec02-per-pair-resolution-is-decidable",
            "def unresolved_conflicts" in domain and "unresolved_conflicts" in domain,
            "逐对消解必须可判定（\`unresolved_conflicts\` 属性在位）",
        ),
        toolbox.verdict(
            "ec02-the-lifecycle-use-case-exists",
            _defines(_text(root, LIFECYCLE), "resolve_memory_conflict"),
            "消解必须有**写路径**（\`lifecycle\` 用例；此前三路径都不碰冲突维）",
        ),
        toolbox.verdict(
            "ec02-both-stores-persist-the-resolution",
            sqlite_ok and pg_ok,
            "两根都要落库（SQLite 列 + PG 迁移）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：读面披露 + **同源**（两读面都按 `unresolved_conflicts` 分派）+ 快照同轮。"""
    read_face = _text(root, READ_FACE)
    router = _text(root, "services/api/routers/memory.py")
    return [
        toolbox.verdict(
            "ec03-the-orchestration-face-discloses-resolutions",
            READ_KEY in read_face,
            "编排读面必须逐对披露消解",
        ),
        toolbox.verdict(
            "ec03-the-http-face-discloses-resolutions",
            READ_KEY in _text(root, HTTP_DTO),
            "HTTP 读面必须披露消解（与编排面同源）",
        ),
        toolbox.verdict(
            "ec03-both-faces-judge-by-unresolved-conflicts",
            # **判关系**：两处都用**同一属性**判 conflicted（同源 ⇒ 同值）。
            read_face.count(UNRESOLVED) >= 1 and router.count(UNRESOLVED) >= 1,
            "两个读面都要按 \`unresolved_conflicts\` 分派（同一处不新写第二套）",
        ),
        toolbox.verdict(
            "ec03-the-disposition-module-stays-pure",
            # **判关系**：处置面**不得**引用消解记载（它只吃 bool）⇒ 判据在序 19 那一侧。
            _defines(_text(root, DISPOSITION), "disposition_of")
            and RESOLVE_TOKEN_MARK not in _text(root, DISPOSITION),
            "处置面保持既有签名（消解逻辑在域层，处置面**只吃布尔**）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-resolution-facts",
            READ_KEY in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含消解披露（动 DTO ⇒ 同轮同步）",
        ),
    ]


#: 处置面**不得**出现的候选标识（消解逻辑留在域层）。
RESOLVE_TOKEN_MARK = "resolve_memory_conflict"


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    judge = _text(root, LIFECYCLE_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-delivery-case-is-asserted",
            "test_a_resolution_is_recorded_with_who_and_when" in judge,
            "\`U-2\` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-declaration-untouched-case-is-asserted",
            "test_the_declaration_is_untouched_by_a_resolution" in judge,
            "\`U-3\` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-unknown-pair-case-is-asserted",
            "test_an_unknown_pair_is_rejected_by_name" in judge,
            "\`U-4\` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-unresolved-read-case-is-asserted",
            "test_an_unresolved_conflict_still_reads_conflicted_verbatim"
            in _text(root, READ_FACES_JUDGE),
            "\`U-1\` 的受判面必须在**读面**判据文件里",
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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…057 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", VERDICT_CURRENT), ("clean", VERDICT_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    press_path = root / PRESS_ARCHIVE
    press_raw = press_path.read_bytes() if press_path.is_file() else b""
    verdicts.append(
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(press_raw) and not _has_carriage_return(press_raw),
            "missing/empty" if not press_raw else "contains CR",
        )
    )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：\`IN_SCOPE\`（四道门）与**射程分区清单**（判据面）。"""
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
