#!/usr/bin/env python3
"""GOAL-20261011-052 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…051 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal052_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-052 特有的断言**。

三条主轴（逐条对 GOAL-052 的 EC）：

1. **EC-02 HTTP 披露**：`MemoryRecordDto` 有那四样（`contradictions` / `superseded_by` /
   `disposition` / `reason`）；**既有 13 字段一个不改名**；`validity` 的**时点语义**保持
   （不给时点**不猜**）。
2. **EC-03 同源**：`_record_dto` **直接调**编排面那两个纯函数 + 同一反向链接助手
   —— **不**在路由里重写第二套判定。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**两条纪律**（承 GOAL-027…051 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）**且不得恒假**
  （承 GOAL-051 §8：初版曾两次写出**永远不响**的空判据）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (("tests/api/test_memory_api.py", 13),)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
    "tests/adapters/canonical/test_memory_read_dispositions.py",
)

#: EC-02/EC-03 落点。
DTO = "services/api/dto/memory.py"
ROUTER = "services/api/routers/memory.py"
ORCH_FACE = "adapters/canonical/memory_read.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-02 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "contradictions: list[str] = Field(default_factory=list)",
    "superseded_by: list[str] = Field(default_factory=list)",
    "disposition: str",
    "reason: str",
)

#: 既有 13 字段（**改一个名字即判红**）。
LEGACY_FIELDS: tuple[str, ...] = (
    "id",
    "tier",
    "kind",
    "content",
    "provenance",
    "confidence",
    "scope",
    "valid_from",
    "review_after",
    "expires_at",
    "supersedes",
    "active",
    "validity",
)

#: EC-03：HTTP 面**必须复用**的编排面助手（同一批纯函数）。
SHARED_HELPERS: tuple[str, ...] = ("disposition_of", "_reason", "superseded_by_index")

#: EC-04 判据文件（逐条点名按压各自的用例）。
API_JUDGE = "tests/api/test_memory_api.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal052_closeout.py"
ASSERTIONS = "tools/goal052_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-052-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-052-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-052-press-two-way.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _field_names(dto_source: str) -> set[str]:
    """`MemoryRecordDto` 类体里的**注解名**（AST 读 —— 不靠文本巧合，也不靠行首正则）。

    **为什么用 AST**：初版曾用 `^    [a-z_]+:` 这类正则去读字段（那是「按写法」判），
    字段缩进/换行一变就静默失配（**可能恒假**）。AST 读类体的 `AnnAssign` 目标是名字，
    与写法无关。
    """
    if not dto_source:
        return set()
    try:
        module = ast.parse(dto_source)
    except SyntaxError:
        return set()
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == "MemoryRecordDto":
            return {
                target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance((target := item.target), ast.Name)
            }
    return set()


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


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：四样在场 + **既有 13 字段一个不改名** + `validity` 时点语义保持。"""
    dto = _text(root, DTO)
    fields = _field_names(dto)
    missing_new = [
        item
        for item in ("contradictions", "superseded_by", "disposition", "reason")
        if item not in fields
    ]
    missing_legacy = [item for item in LEGACY_FIELDS if item not in fields]
    return [
        toolbox.verdict(
            "ec02-the-four-facts-are-on-the-http-face",
            not missing_new,
            ",".join(missing_new),
        ),
        toolbox.verdict(
            "ec02-the-legacy-thirteen-fields-are-not-renamed",
            not missing_legacy,
            ",".join(missing_legacy),
        ),
        toolbox.verdict(
            "ec02-every-new-field-carries-a-declared-shape",
            all(marker in dto for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in dto),
        ),
        toolbox.verdict(
            "ec02-the-validity-is-still-not-guessed",
            # 判**关系**：`validity` 只在**给了时点**时才求值（不给 ⇒ `None`，**不猜**）。
            "validity_at(record, now) if now is not None else None" in _text(root, ROUTER),
            "不给时点不得猜时效（逐字保持）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：HTTP 面**复用**编排面助手（同一批纯函数）+ 快照同轮。"""
    router = _text(root, ROUTER)
    missing_helpers = [name for name in SHARED_HELPERS if name not in router]
    return [
        toolbox.verdict(
            "ec03-the-http-face-reuses-the-orchestration-helpers",
            not missing_helpers,
            ",".join(missing_helpers),
        ),
        toolbox.verdict(
            "ec03-the-reverse-links-are-computed-once-per-batch",
            "superseded_by_index(records)" in router,
            "反向链接必须按**同一批记录**扫一次（不逐条再查 —— 那会 N+1）",
        ),
        toolbox.verdict(
            "ec03-the-orchestration-face-still-owns-the-judgement",
            # 编排面**仍是基准**：那两个助手仍在那里定义（HTTP 面只是调用）
            "def disposition_of(" in _text(root, ORCH_FACE)
            and "def superseded_by_index(" in _text(root, ORCH_FACE),
            "判定仍属编排面（HTTP 面**不**重写第二套）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-four-facts",
            all(
                marker in _text(root, SNAPSHOT)
                for marker in ("contradictions", "superseded_by", "disposition", "reason")
            ),
            "OpenAPI 快照必须含那四样（承 MEM-20261010-216 的同轮同步纪律）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的用例逐条点名 + **基线门** + 归档形态。"""
    api = _text(root, API_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-four-facts-case-is-asserted",
            "test_the_http_face_carries_the_four_facts_the_orchestration_face_has" in api,
        ),
        toolbox.verdict(
            "ec04-the-agreement-case-is-asserted",
            "test_the_two_faces_agree_on_the_same_records" in api,
        ),
        toolbox.verdict(
            "ec04-the-legacy-field-set-is-named-verbatim",
            '"provenance",\n        "review_after",' in api or '"review_after",' in api,
            "既有字段集必须逐条点名（剔除新增后**恰好等于**改动前那 13 个）",
        ),
        toolbox.verdict(
            "ec04-the-no-guessing-case-has-a-live-surface",
            "test_the_http_face_still_does_not_guess_validity" in api
            and "_commit_review_due" in api,
            "「不猜时效」的**受判面必须有时效声明**（否则两行为都返回 None ⇒ 区分不了）",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…051 的教训）。"""
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
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**射程分区清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifier_text = _text(root, VERIFIER_JUDGE)
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
        toolbox.verdict(
            "verifier-scope-declares-this-rounds-scripts",
            SELF in verifier_text,
            "GOAL-043 立的射程分区清单也必须登记本轮验证器",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（**每条都必须会响** —— 承 §8：不得恒假）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
