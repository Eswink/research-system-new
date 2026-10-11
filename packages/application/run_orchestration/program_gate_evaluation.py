"""声明的人工闸门 → `_Evaluation` 的**桥**（GOAL-20261109-056 从 `program_runner` 抽出）。

**为什么单列**：`program_runner.py` 有 **450 行硬上限**（规模门）；本轮为「等待时长」
加了时点透传，行数触顶 ⇒ 把「声明闸门 → 判定值」这一对（求值**先注册后判定**的顺序
说明在其中）原样搬到这里。**语义一字未动**，只换落点。

**只读**：本模块不 import 服务层、不碰审批写入（注册仍在 `program_gate_registration`）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.run_orchestration.program_gate_registration import (
    register_declared_gate,
)
from packages.application.run_orchestration.program_waiting import (
    ApprovalReader,
    GateClock,
    GateInputs,
    declared_gate_verdict,
)
from packages.domain.program import ProgramDecisionKind, ResearchProgram
from packages.domain.run import ResearchRun


@dataclass(frozen=True, slots=True)
class GateEvaluation:
    """一次闸门判定的结果（`start_index` 恒为 `None` —— 闸门只会「拦」，不会「起」）。"""

    kind: ProgramDecisionKind
    reason: str
    cited_run_id: str | None = None
    cited_facts: tuple[str, ...] = ()
    start_index: int | None = None


def declared_gate_evaluation(
    program: ResearchProgram,
    last: ResearchRun,
    approvals: ApprovalReader | None,
    verdicts: tuple[str, ...],
    clock: GateClock | None = None,
) -> GateEvaluation | None:
    """**声明的人工闸门**是否拦住本次推进（是 ⇒ 条 `_Evaluation`，否 ⇒ `None`）。

    GOAL-20261010-046 / 047 / 048 —— 三件事**分层**：

    1. **求值**（`program_waiting.declared_gate_trigger`，**只读**）：两条声明各自判是否触发
       —— 序号声明（序 14）与**条件声明**（GOAL-20261010-048：上一轮**落库判词**命中声明的
       取值集合）。`verdicts` 与结论面读的是**同一批落库事实**（`_verdicts`），不另读一遍。
    2. **注册**（`program_gate_registration.register_declared_gate`，**有副作用**）：
       把待决审批放进既有 `ApprovalStore` ⇒ 这条闸门**可被裁决**（不注册就永远关不上）；
    3. **判定**（`program_waiting.declared_gate_verdict`，**只读**）：据声明与审批面现状
       决定拦不拦，并把注册结果**写进判词**（点名 `approval_id`）。

    顺序固定（先注册后判定）：判定要读注册的结果。判定面**不得**出现写方法
    （序 12/14 的既有判据钉住这件事）⇒ 注册单列成模块。
    """
    registration = register_declared_gate(
        program, last.program_index or 0, approvals, last.id.value, verdicts
    )
    gate = declared_gate_verdict(
        program, last, approvals, GateInputs(verdicts=verdicts, clock=clock), registration
    )
    if gate is None:
        return None
    return _gate_result(last, gate)


def _gate_result(last: ResearchRun, gate: tuple[str, str, tuple[str, ...]]) -> GateEvaluation:
    """把 `declared_gate_verdict` 的判定值包成 `GateEvaluation`（闸门拦住本次推进）。"""
    gate_kind, gate_reason, gate_facts = gate
    return GateEvaluation(
        kind=ProgramDecisionKind(gate_kind),
        reason=gate_reason,
        cited_run_id=last.id.value,
        cited_facts=gate_facts,
    )


__all__ = ["GateEvaluation", "declared_gate_evaluation"]
