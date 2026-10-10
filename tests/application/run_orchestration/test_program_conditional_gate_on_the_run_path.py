"""GOAL-20261010-048 EC-02/EC-03 判据：**条件式**程序闸门（按落库事实触发，不按序号）。

**为什么单列**：规模门对 `tests/**` 同样生效（单文件 ≤ 450 行），而
`test_program_waiting_on_the_run_path.py` 承载序 12/14/15 三轮的判定面 ⇒ 本轮的条件面单列
（与 `tests/e2e/*_support.py` 的拆分同一手法）。

**靶子**：`declared_gate_trigger` ——
**命中声明的判词取值** ⇒ 触发（等人，且**点名**条件与命中依据）；**不命中** ⇒ 逐字走结论面。
条件与**序号**声明**互斥**（域层点名拒绝）⇒ 两条声明不会同时对同一轮求值。

**两向反证**：① 命中必触发（且注册）；② 不该触发时**不**触发（判词照常走结论面）；
③ 未声明 ⇒ 注册面**零调用**；④ 条件触发也走**同一**注册面（`action` 前缀一致）。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.approval_store import ApprovalSpec
from packages.application.run_orchestration.program_gate_registration import PROGRAM_GATE_ACTION
from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.program import ProgramContinueRule, ProgramDecisionKind
from tests.application.run_orchestration.test_program_runner import _Harness


class _WritableApprovals:
    """带**写面**的极小审批面（`list_for_run` + `register`）—— 条件触发要能注册。"""

    def __init__(self) -> None:
        self.rows: list[Any] = []
        self.registered: list[ApprovalSpec] = []

    def list_for_run(self, run_id: str) -> tuple[Any, ...]:
        return tuple(self.rows)

    def register(self, spec: Any) -> object:
        row = type(
            "Rec",
            (),
            {"id": f"apr-{len(self.registered) + 1}", "status": "PENDING", "action": spec.action},
        )()
        self.registered.append(spec)
        self.rows.append(row)
        return row


def _conditional(*, conditions: list[str] | None, verdict: str = "PASS") -> Any:
    """一个声明了（或不声明）**条件式**闸门的程序 + 一条跑完的 run（判词可指定）。

    `continue_rule` 调成接住 `PASS` ⇒「不触发的臂」落到 `CONTINUE`（若沿用 `_Harness`
    的 `ACCEPT`，那一臂会走 `STOP_RULE` —— 那是**结论面**的决定，会掩盖条件闸门的臂）。
    """
    from dataclasses import replace as _replace

    h = _Harness(max_runs=3)
    h.program = _replace(
        h.program,
        continue_rule=ProgramContinueRule(verdict_in=("PASS",)),
        human_gate_on_verdicts=None if conditions is None else tuple(conditions),
    )
    h.programs.create(h.program)
    run_id = h.seed_run(1, state="SUCCEEDED")
    h._run_id = run_id  # type: ignore[attr-defined]
    h._verdict = verdict  # type: ignore[attr-defined]
    return h


def _advance_conditional(h: Any, approvals: Any) -> Any:
    return advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({h._run_id: h._verdict}),
        approvals=approvals,
        start_run=h.start_run,
    )


def test_a_conditional_gate_fires_when_the_landed_verdicts_hit() -> None:
    """**本轮的靶子**：声明条件 = `REJECT`，落库判词 `REJECT` ⇒ 触发（等人）且**点名条件**。"""
    h = _conditional(conditions=["REJECT"], verdict="REJECT")
    result = _advance_conditional(h, _WritableApprovals())
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "human_gate_on_verdicts" in result.decision.reason, result.decision.reason
    assert "命中" in result.decision.reason, result.decision.reason


def test_a_conditional_gate_stays_out_of_the_way_when_not_hit() -> None:
    """**反证臂**：声明条件 = `REJECT`，落库判词 `PASS` ⇒ **不触发**，逐字走结论面。"""
    h = _conditional(conditions=["REJECT"], verdict="PASS")
    result = _advance_conditional(h, _WritableApprovals())
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert result.decision.cited_facts == ("verdict PASS",), result.decision


def test_a_conditional_gate_names_the_evidence_it_judged_on() -> None:
    """**点名依据**：被引事实必须列出**命中哪条落库判词**与**声明的条件**。"""
    h = _conditional(conditions=["REJECT", "ABORT"], verdict="REJECT")
    result = _advance_conditional(h, _WritableApprovals())
    facts = result.decision.cited_facts
    assert "human_gate_on_verdicts=['REJECT', 'ABORT']" in facts, facts
    assert "verdict REJECT" in facts, ("必须点名命中的那一条落库事实", facts)


def test_a_conditional_gate_registers_a_decidable_approval() -> None:
    """条件触发**也要注册**（否则和序号闸门一样接不回）—— 走**同一**注册面。"""
    h = _conditional(conditions=["REJECT"], verdict="REJECT")
    approvals = _WritableApprovals()
    _advance_conditional(h, approvals)
    assert len(approvals.registered) == 1, approvals.registered

    assert approvals.registered[0].action == f"{PROGRAM_GATE_ACTION}{h.program.id}", (
        "条件触发也必须用**同一个** action 前缀（接回面按它裁决）",
        approvals.registered[0].action,
    )


def test_an_undeclared_condition_changes_nothing() -> None:
    """**反证臂**：未声明条件 ⇒ 注册面零调用、判定逐字走结论面（判词照常命中 ⇒ `CONTINUE`）。"""
    h = _conditional(conditions=None, verdict="PASS")
    approvals = _WritableApprovals()
    result = _advance_conditional(h, approvals)
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert approvals.registered == [], approvals.registered
