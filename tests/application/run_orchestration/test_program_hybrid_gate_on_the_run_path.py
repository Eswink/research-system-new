"""GOAL-20261012-060（序 28）：**混合式的两维在推进面上各自点名** —— EC-03 的判据。

**为什么单列**：域的判据（`tests/domain/test_program_hybrid_gate.py`）判「写不写得出来」；
本文件判「**跑起来之后判词读不读得出是哪一维命中**」—— 这是本形态成立的前提
（两维的理由不同：一维是「这一轮本来就该停」，另一维是「落库事实长成了声明的样子」）。

**受判面 = 三个可区分形态**（缺一即「各自点名」不成立）：

1. **只序号维命中** ⇒ 判词点 `at_indexes` 与命中的点，**不**出现条件维措辞；
2. **只条件维命中** ⇒ 判词点 `on_verdicts` 与命中的取值，**不**出现序号维措辞；
3. **两维都命中** ⇒ **两条都点名**（不静默取先命中的那一条）。

**缺省形态逐字不变**：未声明 ⇒ 走结论面（与改动前逐字相同）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.program import HybridGateDeclaration, ProgramDecisionKind
from tests.application.run_orchestration.test_program_waiting_on_the_run_path import (
    _ApprovalRows,
    _Harness,
    _row,
)


def _hybrid(*, at_indexes: tuple[int, ...], on_verdicts: tuple[str, ...]) -> Any:
    """带混合式声明的 harness（第 1 轮已跑完，落库判词由调用方给）。"""
    h = _Harness(max_runs=3)
    h.program = replace(
        h.program,
        human_gate_hybrid=HybridGateDeclaration(at_indexes=at_indexes, on_verdicts=on_verdicts),
    )
    h.programs.create(h.program)
    run_id = h.seed_run(1, state="SUCCEEDED")
    h._run_id = run_id  # type: ignore[attr-defined]
    return h


def _advance(h: Any, *, verdict: str) -> Any:
    """推进一次（落库判词由调用方给 —— 与结论面读的是**同一批事实**）。"""
    return advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({h._run_id: verdict}),
        approvals=_ApprovalRows([_row("apr-hybrid")]),
        start_run=h.start_run,
    )


def test_the_index_dimension_alone_is_named() -> None:
    """EC-03 ①：**只序号维**命中 ⇒ 判词点 `at_indexes` 与命中的点，且**不带**条件维措辞。"""
    h = _hybrid(at_indexes=(1, 3), on_verdicts=("REJECT",))
    result = _advance(h, verdict="ACCEPT")  # 判词不命中条件维 ⇒ 只有序号维
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "at_indexes=[1, 3]" in result.decision.reason, result.decision.reason
    assert "本轮命中 [1]" in result.decision.reason, result.decision.reason
    assert "on_verdicts" not in result.decision.reason, (
        "只序号维命中时不得带条件维措辞（否则读者看不出是哪一维）",
        result.decision.reason,
    )


def test_the_condition_dimension_alone_is_named() -> None:
    """EC-03 ②：**只条件维**命中 ⇒ 判词点 `on_verdicts` 与命中的取值，且**不带**序号维措辞。"""
    h = _hybrid(at_indexes=(3,), on_verdicts=("REJECT",))
    result = _advance(h, verdict="REJECT")  # 第 1 轮不是声明的点 ⇒ 只有条件维
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "on_verdicts=['REJECT']" in result.decision.reason, result.decision.reason
    assert "命中 ['REJECT']" in result.decision.reason, result.decision.reason
    assert "at_indexes" not in result.decision.reason, (
        "只条件维命中时不得带序号维措辞",
        result.decision.reason,
    )


def test_both_dimensions_are_named_when_both_hit() -> None:
    """EC-03 ③：**两维都命中** ⇒ **两条都点名**（不静默取先命中的那一条）。"""
    h = _hybrid(at_indexes=(1,), on_verdicts=("REJECT",))
    result = _advance(h, verdict="REJECT")
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "at_indexes=[1]" in result.decision.reason, result.decision.reason
    assert "on_verdicts=['REJECT']" in result.decision.reason, result.decision.reason
    assert " 且 " in result.decision.reason, ("两维命中必须显式并列", result.decision.reason)


def test_neither_dimension_hits_so_the_program_continues() -> None:
    """EC-03 反证臂：**两维都不命中** ⇒ 闸门**不拦**，推进照常走结论面。

    受判面与上面三条**只差两个声明值**（同一声明形态、同一实跑）：
    序号不是本轮、判词不在集合里 ⇒ 必须照常 `CONTINUE`。
    """
    h = _hybrid(at_indexes=(3,), on_verdicts=("REJECT",))
    result = _advance(h, verdict="ACCEPT")
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert "混合式" not in result.decision.reason, (
        "未命中时判词不得出现闸门措辞",
        result.decision.reason,
    )


def test_an_undeclared_hybrid_leaves_the_advance_verbatim() -> None:
    """EC-03 反证臂：**未声明混合式** ⇒ 逐字走结论面（缺省形态不变）。"""
    h = _Harness(max_runs=3)
    run_id = h.seed_run(1, state="SUCCEEDED")
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({run_id: "ACCEPT"}),
        approvals=_ApprovalRows([_row("apr-none")]),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert "混合式" not in result.decision.reason, result.decision.reason
