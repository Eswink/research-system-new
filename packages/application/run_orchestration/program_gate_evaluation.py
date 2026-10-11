"""声明的人工闸门 → 判定值的**桥**（GOAL-20261109-056 从 `program_runner` 抽出）。

**为什么单列**：`program_runner.py` 有 **450 行硬上限**（规模门）；本轮为「等待时长」
加了时点透传，行数触顶 ⇒ 把「声明闸门 → 判定值」这一对（求值**先注册后判定**的顺序
说明在其中）原样搬到这里。**语义一字未动**，只换落点。

**副作用的位置（GOAL-20261011-057 起）**：本模块里**恰好一处**有副作用 ——
超期通知**交给端口**（`_deliver_nudge`）。它**不在**只读判定面里
（`program_waiting` 保持只读；那条纪律由序 12/14 起的既有判据钉住），而是在**调用方那侧**：
判定完、拿到判词之后再送。**送失败不改变判定**（连续性），但**被点名**（见 `_nudge_note`）。

其余仍是只读：不 import 服务层、不碰审批写入（注册仍在 `program_gate_registration`）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.nudge_sink import NudgeNotice, NudgeSink
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
class NudgeDelivery:
    """**超期信号交付**所需的上下文（GOAL-20261011-057）——合成一个参数对象守 `max-args`。

    三件都在这里（都属「要不要送、送给谁、怎么算」）：
    `index`（哪一轮）、`clock`（时长所需的两个时点）、`nudges`（出口）。

    `nudges=None` **不是故障**：没注入就是没人接 ⇒ 缺省不送（既有行为逐字不变）。
    `clock=None` ⇒ 算不出时长 ⇒ 也不送（**不猜**）。
    """

    index: int
    clock: GateClock | None = None
    nudges: NudgeSink | None = None


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
    delivery: NudgeDelivery | None = None,
) -> GateEvaluation | None:
    """**声明的人工闸门**是否拦住本次推进（是 ⇒ 条判定值，否 ⇒ `None`）。

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
    resolved = delivery or NudgeDelivery(index=last.program_index or 0)
    gate = declared_gate_verdict(
        program,
        last,
        approvals,
        GateInputs(verdicts=verdicts, clock=resolved.clock),
        registration,
    )
    if gate is None:
        return None
    return _gate_result(last, gate, program, delivery)


def _gate_result(
    last: ResearchRun,
    gate: tuple[str, str, tuple[str, ...]],
    program: ResearchProgram,
    delivery: NudgeDelivery | None,
) -> GateEvaluation:
    """把 `declared_gate_verdict` 的判定值包成 `GateEvaluation`（闸门拦住本次推进）。

    **副作用只在这一处**（GOAL-20261011-057）：判定**已经定了**，再决定要不要把「超期」
    交给端口。**送失败不改变判定**（闸门照样拦），但**被点名**（追加进被引事实）。
    """
    gate_kind, gate_reason, gate_facts = gate
    nudge_note = _deliver_nudge(program, last, delivery)
    facts = (*gate_facts, nudge_note) if nudge_note else gate_facts
    return GateEvaluation(
        kind=ProgramDecisionKind(gate_kind),
        reason=gate_reason,
        cited_run_id=last.id.value,
        cited_facts=facts,
    )


def _deliver_nudge(
    program: ResearchProgram,
    last: ResearchRun,
    delivery: NudgeDelivery | None,
) -> str:
    """**超期**（且只有超期）时把通知交给端口；返回**被引事实**（空串 = 无事可报）。

    **三态互不混用**（都**点名**，**不**静默）：

    - **未超期 / 未给时点 / 未声明界** ⇒ 空串（**不送** —— 缺省形态逐字不变）；
    - **超期 **且** 未注入端口** ⇒ 空串（**缺省不送**：没注入就是没人接，那不是故障）；
    - **超期且注入** ⇒ 交给端口；**成功** ⇒ 记一条「已交给出口」的被引事实；
      **失败** ⇒ 记一条**点名**「出口未送达」的被引事实（**不吞异常**、**不**改变判定）。

    **为什么不吞**（与 `TelemetrySink` 的 fail-open 关键差别）：观测面丢失可接受，
    而「该让人知道的事没送出去」**必须能被读出来** ⇒ 否则就是**静默降级**。
    业务路径仍**不**因送失败而断（返回的是事实串，不是异常）。
    """
    resolved = delivery or NudgeDelivery(index=last.program_index or 0)
    bound = getattr(program, "gate_nudge_after_seconds", None)
    if resolved.clock is None or bound is None:
        return ""
    seconds = int((resolved.clock.now.value - resolved.clock.waited_since.value).total_seconds())
    if seconds < int(bound):
        return ""
    if resolved.nudges is None:
        return ""
    notice = NudgeNotice(
        program_id=program.id,
        run_id=last.id.value,
        index=int(resolved.index),
        waited_seconds=seconds,
        declared_bound_seconds=int(bound),
    )
    try:
        resolved.nudges.nudge(notice)
    except Exception as error:  # noqa: BLE001 - **点名**而不是吞掉（见 docstring）
        return f"nudge not delivered（{type(error).__name__}: {error}）"
    return f"nudge delivered（waited={seconds}s, bound={int(bound)}s）"


__all__ = ["GateEvaluation", "NudgeDelivery", "declared_gate_evaluation", "gate_outcome"]


def gate_outcome(  # noqa: PLR0913 - 与调用点同一组只读输入（照抄既有豁免理由）
    program: ResearchProgram,
    last: ResearchRun,
    approvals: ApprovalReader | None,
    verdicts: tuple[str, ...],
    clock: GateClock | None,
    nudges: NudgeSink | None,
) -> tuple[str, str, tuple[str, ...]] | None:
    """闸门那一支的**结果**（拦住 ⇒ `(kind, reason, facts)`，不拦 ⇒ `None`）。

    **为什么单列**：`_evaluate` 有 **50 行**硬上限；把「调桥 + 显式转」收进这里，
    `_evaluate` 只剩一行调用。**语义一字未动**：仍是「先注册后判定」，仍把桥的返回值
    **判定值**）返回 —— 调用方自己构它的值对象（**不**跨模块传 `dataclass`）。
    """
    gated = declared_gate_evaluation(
        program,
        last,
        approvals,
        verdicts,
        NudgeDelivery(index=last.program_index or 0, clock=clock, nudges=nudges),
    )
    if gated is None:
        return None
    # **返回判定值而不是值对象**（与 `declared_gate_verdict` 同一手法）：调用方自己构它的
    # `_Evaluation` —— 本模块因此**不必**被对方 import（避免导入环，也让 mypy 不必接受
    # 两个不同的 `dataclass` 互转）。
    return str(gated.kind.value), gated.reason, gated.cited_facts
