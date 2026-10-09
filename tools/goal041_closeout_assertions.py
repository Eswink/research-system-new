#!/usr/bin/env python3
"""GOAL-20261009-041 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…040 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal041_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-041 特有的断言**。

三条主轴（逐条对 GOAL-041 的 EC）：

1. **EC-01 勘察定稿 + EC-02/EC-03 去重与计数**：新判定种类 `DEDUP_FAILED_RUN` 在域里
   （带 docstring）；`_retry_face_state` 在驱动力且**同时**认两类认领；`_failed_round`
   的**分派顺序**是「用尽 → 去重 → 重试」（交换即不收敛）。
2. **EC-02 的第二个缺陷：决策自然键的单调 tie-breaker**：`_record` 把 `decided_at`
   归一为**该程序内严格递增**（挂钟不单调 ⇒ 同刻度多条决策被静默顶掉）。
3. **EC-04 实跑取证**：判据文件在树且例数达下界；反证臂（无界重试不再出现）在判据里。

**两条纪律**（承 GOAL-027…040 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_program_runner.py", 18),
    ("tests/e2e/test_program_retry_bound_on_the_run_path.py", 6),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/e2e/test_program_idempotency_on_the_run_path.py",
    "tests/e2e/test_program_advance_on_the_run_path.py",
    "tests/adapters/sqlite/test_program_store_sqlite.py",
    "tests/postgres/test_program_store_pg.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-01/EC-02 落点（判定种类 + 计数口径 + 分派顺序）。
DOMAIN = "packages/domain/program.py"
RUNNER = "packages/application/run_orchestration/program_runner.py"
DRIVER_JUDGE = "tests/application/run_orchestration/test_program_runner.py"
JUDGE = "tests/e2e/test_program_retry_bound_on_the_run_path.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal041_closeout.py"
ASSERTIONS = "tools/goal041_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261009-041-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261009-041-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def _ec01_02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/EC-02：新种类 + 计数口径（两类认领都计入）+ 分派顺序（用尽先于去重）。"""
    domain = _text(root, DOMAIN)
    runner = _text(root, RUNNER)
    return [
        toolbox.verdict(
            "ec02-new-kind-registered",
            "DEDUP_FAILED_RUN" in domain and 'DEDUP_FAILED_RUN = "DEDUP_FAILED_RUN"' in domain,
        ),
        toolbox.verdict(
            "ec02-face-is-documented-as-distinct",
            "同类不同面" in domain and "未落库" in domain,
        ),
        toolbox.verdict(
            "ec02-both-claim-kinds-counted",
            "RETRY_FAILED_RUN," in runner
            and "DEDUP_FAILED_RUN," in runner
            and "_retry_face_state" in runner,
        ),
        toolbox.verdict(
            "ec02-claim-is-counted-when-not-landed",
            "claimed not in landed_ids" in runner and "attempts += 1" in runner,
        ),
        toolbox.verdict(
            "ec03-bound-decided-before-the-dedup-branch",
            runner.index("if attempts >= allowed:") < runner.index("if outstanding is not None:"),
        ),
    ]


def _ec02_second_defect_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 的第二个缺陷：决策时点的**单调 tie-breaker**（挂钟会把同刻决策静默顶掉）。"""
    runner = _text(root, RUNNER)
    driver = _text(root, DRIVER_JUDGE)
    return [
        toolbox.verdict(
            "ec02-decided-at-is-monotone-within-the-program",
            "latest + timedelta(microseconds=1)" in runner
            and "if latest is not None and now <= latest:" in runner,
        ),
        toolbox.verdict(
            "ec02-tie-breaker-is-asserted-by-a-judge",
            "test_every_advance_leaves_a_decision_even_in_the_same_clock_tick" in driver,
        ),
        toolbox.verdict(
            "ec02-judge-asserts-stamps-are-distinct",
            "len(set(stamps)) == len(stamps)" in driver,
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：实跑判据在树，且**两向**都被断言（收口 + 反证臂）。"""
    judge = _text(root, JUDGE)
    return [
        toolbox.verdict(
            "ec04-judge-runs-on-the-http-face",
            "advance(client" in judge and "read_program(client" in judge,
        ),
        toolbox.verdict(
            "ec04-judge-asserts-convergence",
            "STOP_RUN_FAILED" in judge and "len(kinds) <= allowed" in judge,
        ),
        toolbox.verdict(
            "ec04-judge-asserts-dedup-is-distinguishable",
            "DEDUP_FAILED_RUN" in judge and '!= "DEDUP"' in judge,
        ),
        toolbox.verdict(
            "ec04-judge-asserts-the-default-path-is-unchanged",
            "未声明重试" in judge,
        ),
        toolbox.verdict(
            "ec04-judge-asserts-no-second-run-at-the-index",
            '[row["program_index"] for row in detail["runs"]] == [1]' in judge,
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…040 的教训）。"""
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
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """`IN_SCOPE` 纯收紧：本轮两个新脚本都在必备清单里（**只查在不在**）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec01_02_verdicts(root, toolbox),
        *_ec02_second_defect_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
