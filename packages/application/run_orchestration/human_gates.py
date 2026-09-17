"""HUMAN_GATE 待裁决判定（GOAL-004 cycle 7 从 `service.py` 拆出：450 行硬上限）。

一个纯函数：声明的 `HUMAN_GATE` phase 减去本 run 已裁决的审批 = 还需要人工放行的 gate。
没有审批 store ⇒ 空集（既有语义：不因缺 store 而暂停）。
"""

from __future__ import annotations

from typing import Any

from packages.domain.enums import GateType


def pending_human_gates(approvals: Any, plan: Any, run_id: str) -> frozenset[str]:
    """声明的 HUMAN_GATE phase − 本 run 已裁决审批（无 store 则不暂停）。"""
    if approvals is None:
        return frozenset()
    declared = {gate.phase_id for gate in plan.gates if gate.gate is GateType.HUMAN_GATE}
    decided = {
        approval.context
        for approval in approvals.list_for_run(run_id)
        if approval.status != "PENDING"
    }
    return frozenset(declared - decided)
