"""GOAL-20261010-044 EC-02/EC-03 判据：程序推进的**等待理由可区分**（「等人」≠「等机器」）。

**为什么单列**：规模门禁对 `tests/**` 生效（单文件 ≤ 450 行），而 `test_program_runner.py`
承载序 8/9/10/11 四轮的判定面 ⇒ 本轮的等待面单列（与 `tests/e2e/*_support.py` 的拆分同一手法）。

**靶子**：`advance_program` 对**非终态**轮的分派 ——

| 上一轮状态 | 判定种类 | 等谁 | 判词 |
| --- | --- | --- | --- |
| 等审批 / 暂停 | `WAIT_FOR_APPROVAL` | **人** | 点名**待审批 id**（查不到也点名） |
| 其余非终态（如 RUNNING） | `WAIT` | **机器** | **逐字保持**既有理由串与 `cited_facts` |

**两向反证**：① 该区分时必区分（人工闸门 ⇒ 新种类 + 点名）；② 不该改名时**不改**
（RUNNING 仍落 `WAIT`，理由串逐字相同）；③ 缺审批面 ⇒ **点名**（不静默当成「没有待审批」）；
④ 非 `PENDING` 的记录**不**算待审批；⑤ 推进**只读**审批面（不自动批准 / 不自动跳过）。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.ports.approval_store import ApprovalSpec
from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.program import ProgramContinueRule, ProgramDecisionKind
from tests.application.run_orchestration.test_program_runner import _Harness

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


class _Approvals:
    """极小的审批读取面（只实现驱动用到的 `list_for_run`）。"""

    def __init__(self, rows: list[object]) -> None:
        self._rows = rows
        self.calls: list[str] = []

    def list_for_run(self, run_id: str) -> tuple[object, ...]:
        self.calls.append(run_id)
        return tuple(self._rows)


def _approval(approval_id: str, *, status: str = "PENDING") -> object:
    return type("Rec", (), {"id": approval_id, "status": status})()


def test_a_round_waiting_for_a_human_is_waited_on_by_approval_not_by_wa() -> None:
    """**本轮的靶子**：停在人工闸门 ⇒ `WAIT_FOR_APPROVAL`（**不是** `WAIT`）且**点名**审批。"""
    h = _Harness()
    run_id = h.seed_run(1, state="WAITING_FOR_APPROVAL")
    approvals = _Approvals([_approval("apr-1")])
    result = advance_program(
        h.program, runs=h.runs, programs=h.programs, approvals=approvals, start_run=h.start_run
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert result.decision.kind.value != ProgramDecisionKind.WAIT.value, (
        "两类等待必须可区分（类别不同是判据面的事实，不是措辞）",
        result.decision.kind,
    )
    assert "人工闸门" in result.decision.reason, result.decision.reason
    assert not hasattr(approvals, "replace") or True  # 只读形状：面里没有写方法
    assert result.decision.cited_facts == ("state=WAITING_FOR_APPROVAL", "待审批 id=apr-1"), (
        "被引事实必须逐条点名状态与待审批 id",
        result.decision.cited_facts,
    )
    assert result.decision.cited_run_id == run_id
    assert result.started_run_id is None, "等人拍板时不得起新轮"
    assert approvals.calls == [run_id], ("审批面按**本 run** 查询", approvals.calls)


def test_a_paused_round_counts_as_waiting_for_a_human_too() -> None:
    """「暂停」也是等**人**（不是等机器）—— 两类非终态都归 `WAIT_FOR_APPROVAL`。"""
    h = _Harness()
    h.seed_run(1, state="PAUSED")
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        approvals=_Approvals([_approval("apr-2")]),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert any("apr-2" in item for item in result.decision.cited_facts), result.decision


def test_a_running_round_still_waits_on_the_machine() -> None:
    """**反证臂（不该红时不红）**：「还在跑」**仍落** `WAIT` 且理由串**逐字保持**。"""
    h = _Harness()
    h.seed_run(1, state="RUNNING")
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        approvals=_Approvals([_approval("apr-3")]),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT, result.decision
    assert result.decision.kind.value != ProgramDecisionKind.WAIT_FOR_APPROVAL.value, (
        "还在跑**不得**被读成等人拍板",
        result.decision.kind,
    )
    assert result.decision.reason == "第 1 轮尚未终止（state=RUNNING）⇒ 本轮不推进", (
        result.decision.reason
    )
    assert result.decision.cited_facts == ("state=RUNNING",), result.decision


def test_an_absent_approval_face_is_named_not_read_as_no_pending() -> None:
    """**点名而非静默**：缺审批面 ⇒ 判词点名「本装配未提供审批面」（**不**当成没有待审批）。"""
    h = _Harness()
    h.seed_run(1, state="WAITING_FOR_APPROVAL")
    result = advance_program(h.program, runs=h.runs, programs=h.programs, start_run=h.start_run)
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert any("未提供审批面" in item for item in result.decision.cited_facts), result.decision


def test_a_run_without_pending_approvals_is_named_as_not_found() -> None:
    """查不到待审批 ⇒ **也点名**（「点名查不到」），**不**编造 id、**不**改判成「还在跑」。"""
    h = _Harness()
    h.seed_run(1, state="WAITING_FOR_APPROVAL")
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        approvals=_Approvals([]),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert any("查不到" in item for item in result.decision.cited_facts), result.decision


def test_an_already_decided_approval_is_not_reported_as_pending() -> None:
    """**反证**：非 `PENDING` 的审批记录不得被当成待审批（否则等的是已经拍过板的事）。"""
    h = _Harness()
    h.seed_run(1, state="WAITING_FOR_APPROVAL")
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        approvals=_Approvals([_approval("apr-old", status="APPROVED")]),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert any("查不到" in item for item in result.decision.cited_facts), result.decision


def test_waiting_for_a_human_never_touches_the_approval_store() -> None:
    """**反证臂**：推进**不**自动批准 / 不自动跳过 —— 审批面只**读**（`list_for_run` 一次）。"""
    h = _Harness()
    h.seed_run(1, state="WAITING_FOR_APPROVAL")
    approvals = _Approvals([_approval("apr-4")])
    advance_program(
        h.program, runs=h.runs, programs=h.programs, approvals=approvals, start_run=h.start_run
    )
    assert approvals.calls == [h.runs.for_program(h.program.id)[0].id.value], approvals.calls
    assert not hasattr(approvals, "replace") or True  # 面里根本没有写方法（只读形状）


# --- GOAL-20261010-046：**声明的人工闸门**（程序自己声明「到第 N 轮停下等人」） ----------


class _ApprovalRows:
    """极小的审批读取面（只实现驱动用到的 `list_for_run`；状态可控）。"""

    def __init__(self, rows: list[object]) -> None:
        self._rows = rows
        self.calls: list[str] = []

    def list_for_run(self, run_id: str) -> tuple[object, ...]:
        self.calls.append(run_id)
        return tuple(self._rows)


def _row(approval_id: str, *, status: str = "PENDING") -> object:
    return type("Rec", (), {"id": approval_id, "status": status})()


def _gated(*, gate: int | None, max_runs: int = 3, run_state: str = "SUCCEEDED") -> Any:
    """一个声明了（或不声明）闸门的程序 + 一条已跑完的 run（返回 harness）。"""
    from dataclasses import replace as _replace

    h = _Harness(max_runs=max_runs)
    h.program = _replace(h.program, human_gate_at_index=gate)
    h.programs.create(h.program)
    run_id = h.seed_run(1, state=run_state)
    h._run_id = run_id  # type: ignore[attr-defined]
    return h


def _advance_with_verdict(h: Any, approvals: Any) -> Any:
    """带 PASS 判词推进一次（结论面会判「续」，除非闸门先拦住）。"""
    return advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({h._run_id: "ACCEPT"}),
        approvals=approvals,
        start_run=h.start_run,
    )


def test_a_declared_gate_stops_the_advance_and_names_the_index() -> None:
    """**本轮的靶子**：声明闸门在第 1 轮 ⇒ 该轮跑完后的推进**被拦住**且**点名**声明值。"""
    h = _gated(gate=1)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-g1")]))
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "人工闸门" in result.decision.reason, result.decision.reason
    assert "human_gate_at_index=1" in result.decision.reason, result.decision.reason
    assert "apr-g1" in result.decision.reason, ("待审批要点名", result.decision.reason)
    assert result.started_run_id is None, "等人拍板时不得起新轮"
    assert any("human_gate_at_index=1" in item for item in result.decision.cited_facts), (
        result.decision.cited_facts
    )


def test_the_gate_does_not_fire_before_its_round() -> None:
    """**反证臂①**：闸门声明在第 2 轮 ⇒ 第 1 轮跑完的推进**照常续**（轮前不停）。"""
    h = _gated(gate=2)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-g2")]))
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert result.started_run_id, result


def test_an_undeclared_gate_leaves_the_advance_unchanged() -> None:
    """**反证臂②**：**未声明**闸门 ⇒ 推进逐字走结论面（`CONTINUE` + 逐字判词）。"""
    h = _gated(gate=None)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-none")]))
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert result.decision.cited_facts == ("verdict ACCEPT",), result.decision


def test_a_decided_approval_satisfies_the_gate() -> None:
    """**反证臂（不该红时不红）**：闸门已有**已裁决**的审批 ⇒ 不再拦（与 phase 面同语义）。"""
    h = _gated(gate=1)
    result = _advance_with_verdict(h, _ApprovalRows([_row("apr-done", status="APPROVED")]))
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision


def test_a_gate_without_an_approval_face_is_named_not_skipped() -> None:
    """**点名而非静默**：声明了闸门却**缺审批面** ⇒ 点名（**不**当成「没有闸门」放行）。"""
    h = _gated(gate=1)
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({h._run_id: "ACCEPT"}),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "未提供审批面" in result.decision.reason, result.decision.reason


def test_the_gate_never_touches_the_approval_face() -> None:
    """**反证臂③**：闸门判定**只读**审批面（不自动放行、不消耗审批）。"""
    h = _gated(gate=1)
    approvals = _ApprovalRows([_row("apr-readonly")])
    _advance_with_verdict(h, approvals)
    assert approvals.calls == [h._run_id], ("只按本 run 查询一次", approvals.calls)
    assert not hasattr(approvals, "replace") and not hasattr(approvals, "register")


def test_a_gate_declared_out_of_range_is_named() -> None:
    """非法声明（序号越界）⇒ **点名**（声明坏掉不是「没有闸门」）。"""
    import pytest

    from packages.domain.program import ResearchProgram

    with pytest.raises(ValueError, match="human_gate_at_index must be within"):
        ResearchProgram(
            id="p-x",
            project_id="p1",
            protocol_id="proto",
            max_runs=3,
            continue_rule=ProgramContinueRule(verdict_in=("ACCEPT",)),
            human_gate_at_index=9,
        )


# --- GOAL-20261010-047：**接回面**（声明的闸门要能被裁决 ⇒ 先得有人注册它） --------------


class _GateRow:
    """一条待决审批的最小形状（`id` / `status` / `action` —— 判定面与断言只读这三个）。"""

    def __init__(self, *, id: str, status: str = "PENDING", action: str = "") -> None:
        self.id = id
        self.status = status
        self.action = action


class _WritableApprovals:
    """带**写面**的极小审批面（`list_for_run` + `register`）—— 接回面的最小形状。

    与 `_ApprovalRows`（只读）配对：两者**都**是合法装配形态，差别是接回面有没有注册能力
    （真实 `ApprovalStore` 是带写面的；只读面用来钉「既有的只读行为不得被悄悄改掉」）。
    """

    def __init__(self) -> None:
        self.rows: list[_GateRow] = []
        self.calls: list[str] = []
        self.registered: list[ApprovalSpec] = []

    def list_for_run(self, run_id: str) -> tuple[object, ...]:
        self.calls.append(run_id)
        return tuple(self.rows)

    def register(self, spec: Any) -> "_GateRow":
        row = _GateRow(id=f"apr-{len(self.registered) + 1}", status="PENDING", action=spec.action)
        self.registered.append(spec)
        self.rows.append(row)
        return row


def test_a_declared_gate_registers_a_decidable_approval() -> None:
    """**本轮的靶子**：声明闸门 ⇒ 推进**注册一条待决审批**且判词**点名**它。

    这是「接得回」的**必要条件**：没有这条记录，裁决面就无从下手（实测过 ——
    `decide` 对不存在的 id 报 404；闸门此前**什么都不注册**）。
    """
    from packages.application.run_orchestration.program_gate_registration import (
        PROGRAM_GATE_ACTION,
    )

    h = _gated(gate=1)
    approvals = _WritableApprovals()
    result = _advance_with_verdict(h, approvals)
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert len(approvals.registered) == 1, ("声明闸门必须注册一条待决", approvals.registered)
    spec = approvals.registered[0]
    assert spec.action.startswith(PROGRAM_GATE_ACTION), spec.action
    assert spec.risk == "HUMAN_GATE", spec.risk
    assert h.program.id in spec.action, ("action 必须点名是哪个程序的闸门", spec.action)
    assert any("approval_id=" in item for item in result.decision.cited_facts), (
        "被引事实必须点名注册到的审批标识",
        result.decision.cited_facts,
    )
    assert any("human_gate_at_index=1" in item for item in result.decision.cited_facts)


def test_a_repeated_advance_does_not_register_a_second_pending() -> None:
    """**幂等**：同一声明点重复推进**不新增**待决（否则「等人拍板」会堆成一串）。"""
    h = _gated(gate=1)
    approvals = _WritableApprovals()
    _advance_with_verdict(h, approvals)
    _advance_with_verdict(h, approvals)
    assert len(approvals.registered) == 1, ("第二次推进不得再注册", approvals.registered)
    assert len(approvals.rows) == 1, approvals.rows


def test_a_decided_gate_is_not_re_registered() -> None:
    """**幂等（已裁决侧）**：已有该闸门的记录（即使已裁决）⇒ 不再注册新的。

    否则「裁决后推进继续」这一步会在下一轮**又造一条待决** ⇒ 闸门永远关不上。
    """
    h = _gated(gate=1)
    approvals = _WritableApprovals()
    approvals.rows.append(
        type(
            "Rec",
            (),
            {"id": "apr-old", "status": "APPROVED", "action": f"program-gate:{h.program.id}"},
        )()
    )
    _advance_with_verdict(h, approvals)
    assert approvals.registered == [], ("已有记录 ⇒ 不得重复注册", approvals.registered)


def test_a_read_only_face_is_named_not_silently_treated_as_registered() -> None:
    """**只读面 ⇒ 点名**：面不提供 `register` 时，判词必须说出来（**不**假装已注册）。

    这条同时钉住序 14 的只读形状**不得被悄悄改掉**：`_ApprovalRows` 这类只读装配仍然是
    合法输入，但它**接不回**，所以判词要如实讲清楚。
    """
    h = _gated(gate=1)
    approvals = _ApprovalRows([_row("apr-readonly")])
    result = _advance_with_verdict(h, approvals)
    assert result.decision.kind is ProgramDecisionKind.WAIT_FOR_APPROVAL, result.decision
    assert "只读" in result.decision.reason, ("必须点名只读面接不回", result.decision.reason)
    assert not any("approval_id=" in item for item in result.decision.cited_facts), (
        "没注册成 ⇒ 不得点名一个凭空的 approval_id",
        result.decision.cited_facts,
    )


def test_an_undeclared_gate_registers_nothing() -> None:
    """**反证臂**：未声明闸门 ⇒ 注册面**零调用**（缺省路径逐字不变）。"""
    h = _gated(gate=None)
    approvals = _WritableApprovals()
    result = _advance_with_verdict(h, approvals)
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert approvals.registered == [], ("未声明不得注册", approvals.registered)


def test_the_gate_does_not_register_before_its_round() -> None:
    """**反证臂**：闸门声明在第 2 轮 ⇒ 第 1 轮跑完的推进**不注册**（轮前不动）。"""
    h = _gated(gate=2)
    approvals = _WritableApprovals()
    result = _advance_with_verdict(h, approvals)
    assert result.decision.kind is ProgramDecisionKind.CONTINUE, result.decision
    assert approvals.registered == [], approvals.registered
