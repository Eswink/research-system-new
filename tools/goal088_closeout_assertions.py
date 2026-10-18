#!/usr/bin/env python3
"""GOAL-20261018-088 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…087 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 读取器**：`design_from_retrieval` 在树；按 `RETRIEVED` 性质过滤；
   按 `run_id` 过滤；只认 `tool-result:` 前缀；多份设计**点名**（不取最后一条）。
2. **EC-03 声明面**：`DESIGN_SOURCE_RETRIEVAL` 与 `DESIGN_SOURCES` 在装配面；
   `_arms_for` 按来源**分派**且缺 ledger **点名**；`plan` 分支**逐字仍在**。
3. **EC-04 共享解析器 + 零回归**：两个来源共用 `design_block_in`；既有实验判据仍在树；
   新判据文件与例数下界在位。

**判据规则**（承 GOAL-027…087）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_experiment_design_from_retrieval.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal087_closeout.py",
    "tests/application/test_experiment_design_decides.py",
)

#: 落点常量（逐条点名；缺一即判红）。
RETRIEVAL = "packages/application/experiments/design_from_retrieval.py"
PLAN = "packages/application/experiments/design_from_plan.py"
SUPPORT = "services/api/experiment_support.py"
TEST = "tests/application/test_experiment_design_from_retrieval.py"

#: EC-01/EC-02 的形态。
READER_ENTRY = "def read_design_from_retrieval("
RETRIEVED_FILTER = "TrustLabel.RETRIEVED"
RUN_FILTER = "item.run_id != run_id"
TOOL_PREFIX = 'TOOL_RESULT_PREFIX = "tool-result:"'
NATURE_REFUSAL = "no system-retrieved evidence"
MULTI_REFUSAL = "more than one retrieved record carries an experiment design"
NO_BLOCK_REFUSAL = "carries a"
WHITELIST = "ALLOWED_PARAMETERS"
SOURCE_ATTRIBUTION = "arm_source_evidence"

#: EC-03 的形态（声明面）。
SOURCE_CONST = 'DESIGN_SOURCE_RETRIEVAL = "retrieval"'
SOURCES_TUPLE = "DESIGN_SOURCES: tuple[str, ...] = (DESIGN_SOURCE_PLAN, DESIGN_SOURCE_RETRIEVAL)"
DISPATCH = "if source not in DESIGN_SOURCES:"
LEDGER_REFUSAL = "a retrieval-derived experiment design needs an evidence ledger"
PLAN_BRANCH = "from packages.application.experiments.design_from_plan import read_design_from_plan"
ARMS_MUTEX = "undecidable"

#: EC-04 的形态（共享解析器 + 零回归）。
SHARED_PARSER = "def design_block_in("
SHARED_USE = "design = design_block_in(payload)"
PLAN_ALIAS = "_design_block = design_block_in"

#: 成对用例（逐条点名）。
PAIR_CASES: tuple[tuple[str, str], ...] = (
    (TEST, "test_the_arms_come_from_the_retrieved_record"),
    (TEST, "test_a_different_record_yields_a_different_design"),
    (TEST, "test_the_design_names_the_evidence_it_came_from"),
    (TEST, "test_a_provided_record_is_not_retrieval"),
    (TEST, "test_another_runs_record_is_out_of_view"),
    (TEST, "test_retrieval_source_plus_declared_arms_is_refused"),
    (TEST, "test_two_designs_are_refused_instead_of_guessed"),
    (TEST, "test_a_parameter_outside_the_whitelist_is_named"),
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_`；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _reader_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/EC-02：读取器的**性质面与作用域面**逐条在位。"""
    verdict = toolbox.verdict
    reader = _text(root, RETRIEVAL)
    return [
        verdict("reader-is-in-tree", READER_ENTRY in reader, READER_ENTRY),
        verdict("reader-filters-by-nature", RETRIEVED_FILTER in reader, RETRIEVED_FILTER),
        verdict("reader-filters-by-run", RUN_FILTER in reader, RUN_FILTER),
        verdict("reader-only-reads-tool-results", TOOL_PREFIX in reader, TOOL_PREFIX),
        verdict("reader-names-a-missing-nature", NATURE_REFUSAL in reader, NATURE_REFUSAL),
        verdict("reader-refuses-two-designs", MULTI_REFUSAL in reader, MULTI_REFUSAL),
        verdict("reader-refuses-a-missing-block", NO_BLOCK_REFUSAL in reader, NO_BLOCK_REFUSAL),
        verdict("reader-uses-the-whitelist", WHITELIST in reader, WHITELIST),
        verdict("reader-names-its-source", SOURCE_ATTRIBUTION in reader, SOURCE_ATTRIBUTION),
    ]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：声明面是**并列新增**的，`plan` 分支逐字仍在。"""
    verdict = toolbox.verdict
    support = _text(root, SUPPORT)
    return [
        verdict("support-declares-the-second-source", SOURCE_CONST in support, SOURCE_CONST),
        verdict("support-lists-both-sources", SOURCES_TUPLE in support, SOURCES_TUPLE),
        verdict("support-dispatches-on-the-list", DISPATCH in support, DISPATCH),
        verdict("support-refuses-a-missing-ledger", LEDGER_REFUSAL in support, LEDGER_REFUSAL),
        verdict("the-plan-branch-is-untouched", PLAN_BRANCH in support, PLAN_BRANCH),
        verdict("arms-and-source-are-mutually-exclusive", ARMS_MUTEX in support, ARMS_MUTEX),
    ]


def _sharing_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：两个来源**共用同一个**设计块解析器（不漂成两套口径）。"""
    verdict = toolbox.verdict
    plan = _text(root, PLAN)
    return [
        verdict("the-parser-is-public", SHARED_PARSER in plan, SHARED_PARSER),
        verdict("the-plan-reader-uses-it", SHARED_USE in plan, SHARED_USE),
        verdict("the-private-name-is-an-alias", PLAN_ALIAS in plan, PLAN_ALIAS),
        verdict(
            "the-retrieval-reader-imports-it",
            "design_block_in" in _text(root, RETRIEVAL),
            "design_block_in",
        ),
    ]


def _case_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """成对用例在位 + 例数下界（删掉任一条用例即判红）。"""
    verdict = toolbox.verdict
    verdicts: list[Any] = []
    for relative, name in PAIR_CASES:
        verdicts.append(
            verdict(f"case-{name}", f"def {name}(" in _text(root, relative), f"{relative}:{name}")
        )
    for relative, floor in CASE_FLOORS:
        count = collected_case_count(root, relative)
        verdicts.append(
            verdict(
                f"case-floor-{Path(relative).stem}",
                count >= floor,
                f"{count} < {floor}" if count < floor else "",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file()))
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（逐条一个判词；按 EC 分组，每组一个函数）。"""
    return [
        *_reader_verdicts(root, toolbox),
        *_declaration_verdicts(root, toolbox),
        *_sharing_verdicts(root, toolbox),
        *_case_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "PAIR_CASES",
    "assertion_verdicts",
    "collected_case_count",
]
