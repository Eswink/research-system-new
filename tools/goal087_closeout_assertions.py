#!/usr/bin/env python3
"""GOAL-20261018-087 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…086 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 组级判定面**：`failure_policy` 有**并列**键 `review_panel`（唯一取值）；
   `FailurePolicyView.panel_completes_before_judging` 在树；`on_task_failure` 的两个既有
   取值**仍在**；`phase_runner` 两条失败路径各有一个分支（声明 ⇒ 记账继续 / 未声明 ⇒
   既有 fail-fast）。
2. **EC-03 分歧可见**：`dissent` 在**平票**时也逐条列出（不再是空）；失败消息逐条点名
   目标与 verdict；`failure_step` 的 `verdict` 参数把门的裁决交回。
3. **EC-04 零回归**：`on_task_failure: CONTINUE` 的既有语义仍在（两个声明面互不越界：
   组末判定只认本模块记账的判负）；既有面板判据与既有容忍用例都还在树。

**判据规则**（承 GOAL-027…086）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py", 3),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal086_closeout.py",
    "tests/application/run_orchestration/test_failure_policy_consumer.py",
)

#: 落点常量（逐条点名；缺一即判红）。
POLICY = "packages/domain/failure_policy.py"
JUDGING = "packages/application/run_orchestration/review_panel_judging.py"
RUNNER = "packages/application/run_orchestration/phase_runner.py"
HELPERS = "packages/application/run_orchestration/task_phase_helpers.py"
PANEL = "packages/application/evaluation/panel_verdict.py"
TEST = "tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py"

#: EC-01/EC-02 的形态。
PANEL_KEY = '"review_panel": ReviewPanelFailure.VALUES,'
PANEL_PROPERTY = "def panel_completes_before_judging(self) -> bool:"
PANEL_VALUE = 'COMPLETE_THEN_JUDGE = "COMPLETE_THEN_JUDGE"'
LEGACY_FAIL_RUN = 'FAIL_RUN = "FAIL_RUN"'
LEGACY_CONTINUE = 'CONTINUE = "CONTINUE"'
#: 两条失败路径的接线（与 `phase_runner` 的实际形态同源）。
RUNNER_RECORDS = "record_rejection(run, task, step)"
RUNNER_JUDGES = "rejection = panel_rejection(deps, group, run, ctx.run_id)"
RUNNER_GATE = "if panel_plan(group):"

#: EC-03 的形态（分歧可见）。
DISSENT_ON_TIE = "if advisory is None:"
DISSENT_NAMED = 'f"{_speaker(item)}:{item.verdict.strip().upper()}"'
PANEL_MESSAGE = "review panel rejected the artifact after every reviewer finished"
VERDICT_PARAM = "verdict: str | None = None,"
GATE_VERDICT = "verdict=gate.verdict,"
#: 两个声明面互不越界（组末只认本模块记账的判负）。
SCOPE_GUARD = "outcome.failure_policy != COMPLETE_THEN_JUDGE"
TOLERATED = "if tctx.contract.failure_policy_view().tolerated:"

#: 成对用例（逐条点名）。
PAIR_CASES: tuple[tuple[str, str], ...] = (
    (TEST, "test_a_rejecting_reviewer_does_not_cancel_the_panel"),
    (TEST, "test_without_the_declaration_the_first_rejection_stops_the_group"),
    (TEST, "test_a_split_panel_names_the_dissent_and_presses_to_unanimity"),
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_`；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/EC-02：声明面是**并列新增**的，既有两值不被改写。"""
    verdict = toolbox.verdict
    policy = _text(root, POLICY)
    runner = _text(root, RUNNER)
    return [
        verdict("policy-declares-the-panel-key", PANEL_KEY in policy, PANEL_KEY),
        verdict("panel-value-is-the-only-value", PANEL_VALUE in policy, PANEL_VALUE),
        verdict("view-exposes-the-panel-question", PANEL_PROPERTY in policy, PANEL_PROPERTY),
        verdict("legacy-fail-run-still-declared", LEGACY_FAIL_RUN in policy, LEGACY_FAIL_RUN),
        verdict("legacy-continue-still-declared", LEGACY_CONTINUE in policy, LEGACY_CONTINUE),
        verdict("runner-records-instead-of-failing", RUNNER_RECORDS in runner, RUNNER_RECORDS),
        verdict("runner-judges-at-the-end-of-the-group", RUNNER_JUDGES in runner, RUNNER_JUDGES),
        verdict("runner-gates-on-the-declaration", RUNNER_GATE in runner, RUNNER_GATE),
        verdict(
            "judging-is-a-separate-module",
            "def panel_plan(" in _text(root, JUDGING),
            "def panel_plan(",
        ),
    ]


def _visibility_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：分歧在**平票**时也读得到；失败消息逐条点名。"""
    verdict = toolbox.verdict
    panel = _text(root, PANEL)
    judging = _text(root, JUDGING)
    helpers = _text(root, HELPERS)
    return [
        verdict("dissent-is-named-on-a-tie", DISSENT_ON_TIE in panel, DISSENT_ON_TIE),
        verdict("dissent-carries-speaker-and-verdict", DISSENT_NAMED in panel, DISSENT_NAMED),
        verdict("the-panel-failure-names-everyone", PANEL_MESSAGE in judging, PANEL_MESSAGE),
        verdict("failure-steps-carry-the-gate-verdict", VERDICT_PARAM in helpers, VERDICT_PARAM),
        verdict("the-gate-verdict-is-passed-through", GATE_VERDICT in helpers, GATE_VERDICT),
    ]


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：两个声明面**互不越界**（首轮那处真回归的机械防线）。"""
    verdict = toolbox.verdict
    return [
        verdict(
            "panel-rejection-ignores-tolerated-failures",
            SCOPE_GUARD in _text(root, JUDGING),
            SCOPE_GUARD,
        ),
        verdict(
            "tolerated-semantics-untouched",
            TOLERATED in _text(root, HELPERS),
            TOLERATED,
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
        *_declaration_verdicts(root, toolbox),
        *_visibility_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
        *_case_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "PAIR_CASES",
    "assertion_verdicts",
    "collected_case_count",
]
