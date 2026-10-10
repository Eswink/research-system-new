#!/usr/bin/env python3
"""GOAL-20261011-051 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…050 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal051_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-051 特有的断言**。

三条主轴（逐条对 GOAL-051 的 EC）：

1. **EC-02 处置面**：读面新增第五态 `CONFLICTED`（与四态**互不混用**且**可区分**）；
   判词**点名**冲突的 id；优先级**固定**（已取代 > 已过期 > 有冲突 > 待复核）；
   **无冲突 ⇒ 逐字不变**。
2. **EC-03 消费端**：`CONFLICTED` 落 `ANNOTATE`（**执行但带标注** —— 冲突不等于不可用）；
   与「待复核」**同类不同因** ⇒ 判词**分开点名**；未知处置仍 **fail closed**。
3. **EC-04 两向**：判据在树，四条按压（仍报 USE / 凭空报冲突 / 与过期混用 / 点名缺失）
   逐条对得上用例；归档进树。

**两条纪律**（承 GOAL-027…050 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`；本仓已多次踩到
  「按写法/文本写死 ⇒ 正当演进后假红」）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/canonical/test_memory_conflict_disposition.py", 5),
    ("tests/application/run_orchestration/test_memory_validity_gate.py", 18),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
    "tests/adapters/canonical/test_memory_read_dispositions.py",
)

#: EC-02 落点（读面）。
READ_FACE = "adapters/canonical/memory_read.py"

#: EC-03 落点（消费端）。
CONSUMER = "packages/application/run_orchestration/phase_capability_triggers.py"

#: EC-03 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "DISPOSITION_CONFLICTED",
    "MEMORY_CONFLICTED",
    "未自动消解",
)

#: EC-04 判据文件（逐条点名按压各自的用例）。
CONFLICT_JUDGE = "tests/adapters/canonical/test_memory_conflict_disposition.py"
CONSUMER_JUDGE = "tests/application/run_orchestration/test_memory_validity_gate.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal051_closeout.py"
ASSERTIONS = "tools/goal051_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-051-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-051-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-051-press-two-way.txt"


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


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：第五态 + 点名 + 优先级固定 + 缺省逐字不变。"""
    face = _text(root, READ_FACE)
    names = _function_names(face)
    return [
        toolbox.verdict(
            "ec02-the-fifth-disposition-exists",
            'DISPOSITION_CONFLICTED = "CONFLICTED"' in face,
            "第五态必须有自己的常量（**不**复用 `ANNOTATE` 靠措辞区分）",
        ),
        toolbox.verdict(
            "ec02-the-disposition-takes-the-conflicted-dimension",
            # **判关系**：`disposition_of` **是**本模块定义的函数（集合里查**裸名**），
            # 且它收了**可选**的 `conflicted` 维（缺省 False ⇒ 既有行为逐字不变）。
            # （初版写成 `"disposition_of(" in names` ⇒ 带括号查裸名集合**恒假**，
            #  **被收口验证器自己的首跑当场报出** —— 空判据比假红更坏：它会静默掩盖真回归。）
            "conflicted: bool = False" in face and "disposition_of" in names,
            "缺省 `conflicted=False` ⇒ 既有行为逐字不变",
        ),
        toolbox.verdict(
            "ec02-the-priority-is-fixed-and-declared",
            # 优先级：已取代 → 已过期 → 有冲突 → 待复核（读面文档里写明，代码里同序）
            "优先级**固定**" in face and "已取代" in face and "已过期" in face,
            "并存优先级必须**固定且写明**",
        ),
        toolbox.verdict(
            "ec02-the-conflict-ids-are-named",
            "未自动消解" in face and "conflicts" in face,
            "必须点名冲突的 id 与「未自动消解」",
        ),
        toolbox.verdict(
            "ec02-the-counts-carry-the-fifth-cell",
            "DISPOSITION_CONFLICTED: 0" in face,
            "计数摘要要把「有冲突」**单独一格**报",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：消费端真的分派为「执行但带标注」+ 两因分开点名 + 未知态仍 fail closed。"""
    consumer = _text(root, CONSUMER)
    return [
        toolbox.verdict(
            "ec03-every-required-form-is-named",
            all(marker in consumer + _text(root, READ_FACE) for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in consumer + _text(root, READ_FACE)),
        ),
        toolbox.verdict(
            "ec03-the-conflicted-arm-is-a-distinct-group",
            "MEMORY_CONFLICTED" in consumer and "conflicted: list[str]" in consumer,
            "冲突必须单独成组（不并进「待复核」那一格）",
        ),
        toolbox.verdict(
            "ec03-the-unresolved-conflict-reason-is-named",
            "unresolved contradictions" in consumer,
            "判词必须点名「有未消解冲突」",
        ),
        toolbox.verdict(
            "ec03-the-unknown-state-still-fails-closed",
            "USE / ANNOTATE / SKIP / SUPERSEDED / CONFLICTED" in consumer,
            "未知态仍 fail closed（新增已知态**不是**放宽那条）",
        ),
        toolbox.verdict(
            "ec03-the-two-annotate-reasons-are-separate",
            "due for review" in consumer and "unresolved contradictions" in consumer,
            "「待复核」与「有冲突」**同类不同因** ⇒ 判词分开",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的用例逐条点名 + 归档形态。"""
    conflict = _text(root, CONFLICT_JUDGE)
    consumer = _text(root, CONSUMER_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-conflicted-is-not-plainly-used-case-is-asserted",
            "test_a_conflicting_record_is_flagged_not_plainly_used" in conflict,
        ),
        toolbox.verdict(
            "ec04-the-no-conflict-case-is-asserted",
            "test_no_conflict_keeps_the_previous_answer_verbatim" in conflict,
        ),
        toolbox.verdict(
            "ec04-the-five-constants-are-distinct",
            "test_the_five_dispositions_are_distinct_constants" in conflict,
        ),
        toolbox.verdict(
            "ec04-the-priority-order-is-asserted",
            "test_the_priority_order_is_fixed_and_declared" in conflict,
        ),
        toolbox.verdict(
            "ec04-the-consumer-arms-are-asserted",
            "test_a_conflicting_record_does_not_skip_the_step" in consumer
            and "test_conflict_and_review_due_are_named_separately" in consumer
            and "test_a_conflicting_only_step_names_that_reason" in consumer,
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…050 的教训）。"""
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
