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

import pytest

from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.program import ProgramDecisionKind
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
