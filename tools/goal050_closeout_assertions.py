#!/usr/bin/env python3
"""GOAL-20261010-050 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…049 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal050_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-050 特有的断言**。

三条主轴（逐条对 GOAL-050 的 EC）：

1. **EC-02 读面披露**：`memory_read` 的逐条投影**两个方向**都披露
   （`supersedes` / `superseded_by`）；无关系 ⇒ 空列表；反向链接**从同一批记录算**
   （不新增 Port 方法）。
2. **EC-03 处置面**：新增第四态 `SUPERSEDED`（与「已过期」**理由可区分**、优先级固定）；
   **消费端真的分派**（处置同 `SKIP` 但判词**分开点名**）；未知态仍 fail closed。
3. **EC-04 两向**：判据在树，四条按压（仍报 USE / 凭空报取代 / 单向链接 / 两因混用）
   逐条对得上用例；归档进树。

**两条纪律**（承 GOAL-027…049 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/canonical/test_memory_read_dispositions.py", 27),
    ("tests/application/run_orchestration/test_memory_validity_gate.py", 15),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（读面；**可能落点清单**）。
READ_FACE = "adapters/canonical/memory_read.py"

#: EC-03 落点（消费端）。
CONSUMER = "packages/application/run_orchestration/phase_capability_triggers.py"

#: EC-03 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "DISPOSITION_SUPERSEDED",
    "MEMORY_SUPERSEDED",
    '"superseded_by"',
)

#: EC-04 判据文件（逐条点名按压各自的用例）。
READ_JUDGE = "tests/adapters/canonical/test_memory_read_dispositions.py"
CONSUMER_JUDGE = "tests/application/run_orchestration/test_memory_validity_gate.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal050_closeout.py"
ASSERTIONS = "tools/goal050_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-050-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-050-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261010-050-press-two-way.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _function_names(source: str) -> set[str]:
    """模块里定义的函数名（AST 读，不靠文本巧合）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


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


def _calls_named(source: str, name: str) -> int:
    """源码里**调用**该名字的次数（AST；`Name` 与 `Attribute` 两种形态都认）。

    **不**用文本包含（承 GOAL-20261010-049 的实测：文本判据会把注释里的提及当违规）。
    """
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == name)
            or getattr(node.func, "attr", None) == name
        )
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：读面两向披露 + 反向链接从同一批记录算（不新增 Port 方法）。"""
    face = _text(root, READ_FACE)
    names = _function_names(face)
    return [
        toolbox.verdict(
            "ec02-the-two-directions-are-disclosed",
            '"supersedes": list(record.supersedes)' in face
            and '"superseded_by": list(superseded_by or ())' in face,
            "两个方向都要披露（正向 + 反向）",
        ),
        toolbox.verdict(
            "ec02-the-reverse-links-come-from-one-pass",
            "_reverse_links" in names,
            "反向链接必须**从同一批记录算一次**（不新增 Port 方法、不 N+1 查询）",
        ),
        toolbox.verdict(
            "ec02-the-four-states-are-counted-separately",
            "DISPOSITION_SUPERSEDED: 0" in face,
            "计数摘要要把「已取代」与「已过期」**分开报**",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：第四态 + 消费端真的分派 + 未知态仍 fail closed。"""
    face = _text(root, READ_FACE)
    consumer = _text(root, CONSUMER)
    return [
        toolbox.verdict(
            "ec03-every-required-form-is-named",
            all(marker in face + consumer for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in face + consumer),
        ),
        toolbox.verdict(
            "ec03-the-disposition-takes-the-superseded-dimension",
            # 判**关系**：`disposition_of` 收一个**可选**的 `superseded` 维（缺省 False）。
            # **不**钉整行签名 —— GOAL-20261011-051 正当又加了 `conflicted` 维。
            "superseded: bool = False" in face
            and "def disposition_of(" in face
            and _calls_named(face, "disposition_of") >= 1,
            "缺省 `superseded=False` ⇒ 既有行为逐字不变",
        ),
        toolbox.verdict(
            "ec03-the-consumer-splits-the-two-reasons",
            # 判**关系**：`_split_by_disposition` 的**分组结果**里有 superseded，
            # 且两个理由**各自成句**（**不**钉解包变量个数/名字 —— GOAL-20261011-051 正当
            # 加了第四组 `conflicted`）。
            "superseded" in consumer
            and "superseded memory record(s)" in consumer
            and "expired memory record(s)" in consumer
            and "parts.append" in consumer,
            "消费端要为**两个理由**分别点名（不得共用一句）",
        ),
        toolbox.verdict(
            "ec03-the-unknown-state-still-fails-closed",
            "expected USE / ANNOTATE / SKIP / SUPERSEDED" in consumer,
            "未知态仍 fail closed（新增已知态**不是**放宽那条）",
        ),
        toolbox.verdict(
            "ec03-the-reason-names-both-when-both-hold",
            "已不是当前版本（不照用）" in face and "**并且**" in face,
            "两者皆有时**都点名**（读者要能一次看全）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的用例逐条点名 + 归档形态。"""
    read = _text(root, READ_JUDGE)
    consumer = _text(root, CONSUMER_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-superseded-is-not-used-case-is-asserted",
            "test_a_superseded_record_is_no_longer_used" in read,
        ),
        toolbox.verdict(
            "ec04-the-both-directions-case-is-asserted",
            "test_both_link_directions_are_disclosed" in read,
        ),
        toolbox.verdict(
            "ec04-the-no-relation-case-is-asserted",
            "test_no_relation_keeps_the_previous_answer_verbatim" in read,
        ),
        toolbox.verdict(
            "ec04-the-two-reasons-are-distinguishable",
            "test_superseded_and_expired_are_distinguishable" in read,
        ),
        toolbox.verdict(
            "ec04-the-counts-are-separated",
            "test_the_count_summary_separates_the_two_reasons" in read,
        ),
        toolbox.verdict(
            "ec04-the-consumer-arms-are-asserted",
            "test_a_superseded_record_skips_the_step" in consumer
            and "test_the_two_reasons_are_named_separately" in consumer
            and "test_a_superseded_only_step_names_that_reason" in consumer,
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…049 的教训）。"""
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
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
