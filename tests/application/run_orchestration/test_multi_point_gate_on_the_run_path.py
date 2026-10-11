"""GOAL-20261011-055（`Z-1`）：**多点人工闸门**在**推进面**的行为（EC-03）。

**为什么单列**：`tests/application/run_orchestration/test_program_waiting_on_the_run_path.py`
已 401 行；本轮的靶子（多点求值）自成一组。

**判的是什么**：多点声明（`human_gate_at_indexes`）要**真的**在推进面上逐点生效 ——
每一个声明点各自拦住它那一轮，**未命中**的轮次**逐字不变**；判词**点名是哪一点**触发的。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from packages.domain.program import ProgramDecisionKind
from tests.application.run_orchestration.test_program_waiting_on_the_run_path import (
    _advance_with_verdict,
    _ApprovalRows,
    _Harness,
    _row,
)


def _multi_gated(*, indexes: tuple[int, ...], max_runs: int = 3, index: int = 1) -> Any:
    """一个声明了**多点**闸门的程序 + 一条已跑完的 run（返回 harness）。

    与既有 `_gated` 同形，只把声明字段换成多点那一支 ——
    **复用同一套 harness**（不另造装配），否则测的就不是产品路径。
    """
    h = _Harness(max_runs=max_runs)
    h.program = replace(h.program, human_gate_at_indexes=indexes)
    h.programs.create(h.program)
    run_id = h.seed_run(index, state="SUCCEEDED")
    h._run_id = run_id  # type: ignore[attr-defined]
    return h


def test_the_first_declared_point_stops_the_advance_and_names_it() -> None:
    """EC-03：多点的**第一个**点（第 1 轮）⇒ 拦住并**点名**那一组与命中的点。"""
    h = _multi_gated(indexes=(1, 3))
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-m1")]))
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "人工闸门" in result.decision.reason, result.decision.reason
    assert "[1, 3]" in result.decision.reason, ("要点名**那一组**", result.decision.reason)
    assert any("human_gate_at_indexes=[1, 3]" in item for item in result.decision.cited_facts), (
        result.decision.cited_facts
    )


def test_a_middle_round_that_is_not_a_declared_point_advances_unchanged() -> None:
    """EC-03 + 反证臂：第 2 轮**不在**声明的一组里 ⇒ **照常续**（不拦）。

    受判面**必须可区分**：本条与上一条的唯一差别是**这一轮在不在那一组里**
    ⇒ 两条放在一起才证明求值判的是**成员关系**而不是「有没有多点声明」。
    """
    h = _multi_gated(indexes=(1, 3), index=2)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-m2")]))
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert result.started_run_id, result


def test_the_last_declared_point_also_stops_the_advance() -> None:
    """EC-03：多点的**最后一个**点（第 3 轮）⇒ 同样拦住（不只是第一个点生效）。"""
    h = _multi_gated(indexes=(1, 3), index=3)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-m3")]))
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert any("gate index 3" in item for item in result.decision.cited_facts), (
        result.decision.cited_facts
    )


def test_an_undeclared_multi_point_gate_leaves_the_advance_unchanged() -> None:
    """EC-03：**未声明**多点闸门 ⇒ 推进逐字走结论面（与既有的缺省臂同形）。"""
    h = _Harness(max_runs=3)
    h.programs.create(h.program)
    run_id = h.seed_run(1, state="SUCCEEDED")
    h._run_id = run_id  # type: ignore[attr-defined]
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-none")]))
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert result.decision.cited_facts == ("verdict ACCEPT",), result.decision


def test_the_multi_point_form_is_named_in_the_reason_not_a_verdict_condition() -> None:
    """EC-03：多点与**条件式**在判词上**可区分**（点名的是序号，不是判词取值）。

    「为什么停」必须读得出是**哪一条**要求的 —— 两条声明互斥，但判词形态**不能混用**。
    """
    h = _multi_gated(indexes=(1, 3))
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-m4")]))
    reason = result.decision.reason
    assert "human_gate_at_indexes" in reason, reason
    assert "human_gate_on_verdicts" not in reason, ("不得把序号声明说成条件声明", reason)
