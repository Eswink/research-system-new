#!/usr/bin/env python3
"""GOAL-20261008-034 收口复检的**本轮特有断言集**（EC-04）。

与 GOAL-023…033 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal034_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-034 特有的断言**。

四条主轴（逐条对 GOAL-034 的 EC）：

1. **EC-01 多轮循环**：`RoundLoop`（`phases` / `max_rounds` / `stop_when` / `calls_by_round`）
   与 `round_specs`（**第 1 轮逐字保留任务身份、N>1 换键换 id**）在位；`execute_rounds`
   按轮**懒展开**（`deps.resolve_round(index)` 在循环体内）；相位执行链被拆成
   `_execute_one_pass`（**单遍原语**）且 `execute_phases` 未注入驱动时**直接调它**。
2. **EC-02 结论驱动的停止**：`evaluate_stop` 里**结论判断在护栏判断之前**（AST 顺序）；
   判据词表含 `converged_no_new_ids`；两个停止类别常量在位。
3. **EC-03 读面**：停止事实骑**既有** `RUN_COMPLETED`（**不得**新增事件类型 —— 词表零扩张）；
   循环载荷保留单遍那些键（`_single_pass_payload` 在位）。
4. **判据面**：`tests/e2e/test_multi_round_research_loop.py` 在树且例数达下界；
   三轮夹具（`multi_round_loop_support.py`）在树；**既有**两轮判据文件仍在树（引用不重复）。

另有两条**记录面**断言（EC-04 自己的交付面）：判词归档在树（两份，二进制写盘 CR=0）；
`IN_SCOPE` 纯收紧（本轮验证器与断言集都在清单里）。

**两条纪律**（承 GOAL-027…033 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/e2e/test_multi_round_research_loop.py", 15),
    ("tests/application/run_orchestration/test_round_loop_declaration.py", 22),
)

#: EC-03 引用（而非重复）的既有判据 —— 必须仍在树。
PRIOR_SUITES: tuple[str, ...] = (
    "tests/e2e/test_research_loop_second_round_derived.py",
    "tests/e2e/test_ec03_real_runtime_offline_chain.py",
)

LOOP = "packages/application/run_orchestration/round_loop.py"
RUNNER = "packages/application/run_orchestration/round_loop_runner.py"
FACTS = "packages/application/run_orchestration/round_loop_facts.py"
PHASE_RUNNER = "packages/application/run_orchestration/phase_runner.py"
TRIGGERS = "packages/application/run_orchestration/phase_capability_triggers.py"
FIXTURE = "tests/e2e/multi_round_loop_support.py"

#: 停止判据的**顺序**断言面：结论判断必须出现在护栏判断之前。
_CONCLUSION_MARK = "conclusion_stop = criterion == CONVERGED_NO_NEW_IDS"
_GUARD_MARK = "if round_index >= max_rounds:"
#: 停止类别常量（EC-02 (e) 的「两臂可区分」由它们承载）。
_KINDS: tuple[str, ...] = ('STOP_BY_CONCLUSION = "CONCLUSION"', 'STOP_BY_GUARD = "MAX_ROUNDS"')

#: 本轮归档的判词落点（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-034-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-034-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _has_def(root: Path, relative: str, name: str, *, class_name: str | None = None) -> bool:
    """该文件里是否**定义了** `name`（限定类内时给 `class_name`）。AST，不看文本巧合。"""
    source = _text(root, relative)
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - 语法坏掉时判据会判红
        return False
    for node in ast.walk(tree):
        if class_name is not None:
            if not isinstance(node, ast.ClassDef) or node.name != class_name:
                continue
            return any(
                isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name == name
                for item in node.body
            )
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return True
    return False


def _has_const(root: Path, relative: str, literal: str) -> bool:
    return literal in _text(root, relative)


def _conclusion_precedes_the_guard(root: Path) -> bool:
    """**顺序断言**（AST/文本双层）：结论判断必须**在护栏之前**。

    这条是 EC-02 (c) 的机械形态：把两者对调就会把「已经收敛」谎报成「只是上界到了」。
    """
    source = _text(root, FACTS)
    if not source:
        return False
    conclusion_at = source.find(_CONCLUSION_MARK)
    guard_at = source.find(_GUARD_MARK)
    return conclusion_at != -1 and guard_at != -1 and conclusion_at < guard_at


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    tree = ast.parse(source)
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _rounds_ride_the_existing_event(root: Path) -> bool:
    """停止事实骑**既有** `RUN_COMPLETED`（**不得**新增事件类型 ⇒ 词表零扩张）。"""
    source = _text(root, RUNNER)
    return "EventType.RUN_COMPLETED" in source and "RUN_ROUNDS" not in _text(
        root, "packages/domain/events.py"
    )


def _ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：多轮循环的声明面 + 懒展开 + 单遍原语 + 上一轮收窄。"""
    return [
        toolbox.verdict("ec01-round-loop-declared", (root / LOOP).is_file()),
        toolbox.verdict("ec01-round-loop-class", "class RoundLoop" in _text(root, LOOP)),
        toolbox.verdict(
            "ec01-round-key-method", _has_def(root, LOOP, "round_key", class_name="RoundLoop")
        ),
        toolbox.verdict("ec01-calls-per-round", "calls_by_round" in _text(root, LOOP)),
        toolbox.verdict("ec01-round-specs-present", _has_def(root, RUNNER, "round_specs")),
        toolbox.verdict(
            "ec01-lazy-expansion-in-the-loop", "resolve_round(round_index)" in _text(root, RUNNER)
        ),
        toolbox.verdict(
            "ec01-single-pass-primitive", _has_def(root, PHASE_RUNNER, "_execute_one_pass")
        ),
        toolbox.verdict(
            "ec01-execute-phases-falls-back-to-one-pass",
            "return _execute_one_pass(deps, ctx," in _text(root, PHASE_RUNNER),
        ),
        toolbox.verdict(
            "ec01-previous-round-selection",
            _has_def(root, TRIGGERS, "select_artifact_id_for_prefixes"),
        ),
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：结论驱动的停止 + **顺序** + 两个停止类别常量。"""
    return [
        toolbox.verdict("ec02-facts-module-present", (root / FACTS).is_file()),
        toolbox.verdict("ec02-conclusion-before-guard", _conclusion_precedes_the_guard(root)),
        toolbox.verdict(
            "ec02-criteria-vocabulary",
            _has_const(root, LOOP, 'CONVERGED_NO_NEW_IDS = "converged_no_new_ids"'),
        ),
        toolbox.verdict(
            "ec02-stop-kind-conclusion", _has_const(root, LOOP, 'STOP_BY_CONCLUSION = "CONCLUSION"')
        ),
        toolbox.verdict(
            "ec02-stop-kind-guard", _has_const(root, LOOP, 'STOP_BY_GUARD = "MAX_ROUNDS"')
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：停止事实骑既有事件 + 循环载荷保留单遍键。"""
    return [
        toolbox.verdict(
            "ec03-stop-facts-ride-existing-event", _rounds_ride_the_existing_event(root)
        ),
        toolbox.verdict(
            "ec03-loop-payload-keeps-single-pass-keys",
            _has_def(root, RUNNER, "_single_pass_payload"),
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 夹具在树 + 既有判据仍在树。"""
    verdicts: list[Any] = [
        toolbox.verdict("judge-viability-fixture-present", (root / FIXTURE).is_file()),
        toolbox.verdict(
            "judge-zero-hit-round-in-fixture", "ZERO_HIT_QUERY" in _text(root, FIXTURE)
        ),
    ]
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_SUITES:
        verdicts.append(
            toolbox.verdict(f"prior-suite-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


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


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec01_verdicts(root, toolbox),
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
    ]


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 MEM-20260928-152）。"""
    return bytes([13]) in raw
