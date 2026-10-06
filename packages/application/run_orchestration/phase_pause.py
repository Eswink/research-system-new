"""Phase 边界的两种「停车」处置（GOAL-004/PLAN-048；GOAL-031 EC-03 从 `phase_runner` 拆出）。

**为什么单列**：`phase_runner.py` 有 450 行硬上限（规模门），EC-03 要把「声明式跳过」
串到任务终局读面上（`_execute_one_task` / `_run_group_task` 各加几行）——先按全仓既有的
「行为独立即单列」手法把这两个 parking 路径搬出来，执行循环本体因此留出余量。
**语义逐字节不变**：两个函数的判定、事件、返回的 `RunOutcome` 与搬迁前一致
（搬迁时逐行搬运，未改一个字符的判定）。

（`deps` / `ctx` 标注为 `Any`：两个参数对象定义在 `phase_runner`，从那边 import 会形成
导入环；本模块只按**属性**使用它们 —— `pause_requested` / `on_pause` / `human_gated` /
`approvals` / `emit` / `run_id` / `trace_id` / `frozen_manifest_digest`。）
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.approval_store import ApprovalSpec
from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState

SessionSpec = tuple[Any, Any, Any]


def pause_if_requested(
    deps: Any,
    ctx: Any,
    remaining: "list[tuple[SessionSpec, ...]]",
    outcomes: "list[TaskOutcome]",
) -> RunOutcome | None:
    """协作式暂停（PLAN-20260914-048）：组边界观测到暂停信号 → **零任务执行**
    返回 PAUSED，剩余 specs（含当前组）经 on_pause 交回 service 暂存。

    只读 canonical run state（service 注入谓词），不自己造暂停事实；
    已持租约的任务不受影响（不在本函数职责内撤销）。
    """
    if deps.pause_requested is None or not deps.pause_requested():
        return None
    if deps.on_pause is not None:
        deps.on_pause(tuple(spec for group in remaining for spec in group))
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.PAUSED,
        message="paused at phase boundary (cooperative pause)",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
        system_failure=False,
    )


def pause_for_human_gate(
    deps: Any,
    ctx: Any,
    group: "tuple[SessionSpec, ...]",
    remaining: "list[tuple[SessionSpec, ...]]",
    outcomes: "list[TaskOutcome]",
) -> RunOutcome | None:
    """声明的 human gate：注册 ApprovalRecord + APPROVAL_REQUESTED 事件 +
    WAITING_FOR_APPROVAL outcome（剩余 specs 经 on_pause 交回 service 暂存）。
    没有 approvals store 时 service 不会给出 human_gated 集（fail-closed）。"""
    phase_id = group[0][2].phase_id
    if not phase_id or phase_id not in deps.human_gated or deps.approvals is None:
        return None
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=ctx.run_id,
            action=f"human-gate:{phase_id}",
            risk="HUMAN_GATE",
            context=phase_id,
            policy_source="protocol-gate",
            # requested_event_id 关联本应指向 approval.requested 事件，但发布在
            # register 之后且 publish 不回传 id；留空（审批记录本身即真相源）。
            requested_event_id="",
        )
    )
    deps.emit(
        EventType.APPROVAL_REQUESTED,
        {"run_id": ctx.run_id, "phase_id": phase_id, "approval_id": approval.id},
        ctx.run_id,
        ctx.trace_id,
        None,
    )
    if deps.on_pause is not None:
        deps.on_pause(tuple(spec for chunk in remaining for spec in chunk))
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.WAITING_FOR_APPROVAL,
        message=f"awaiting human approval for phase {phase_id} (approval {approval.id})",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
    )


__all__ = ["pause_for_human_gate", "pause_if_requested"]
