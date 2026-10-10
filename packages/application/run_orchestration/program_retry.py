"""失败重试面的**计数口径**与认领检测（GOAL-20261009-041 EC-02/EC-03）。

**为什么单列**：`program_runner.py` 有 **450 行硬上限**（规模门），本 GOAL 的闸门判定接进来后
越界 ⇒ 与全仓既有的「判定面拆出去」同一手法（`phase_capability_triggers` /
`program_waiting` 之于它们的执行面）。

**它判什么**：本序号上「推进试图做出进展」的**次数** ——

    已用尝试数 = 落库行数 + 未落库的认领数 + 被阻塞的推进数

**为什么必须这么算**（实测的失真）：只数落库行时，认领后未落库的那一次**不计入** ⇒
反复「认领即崩」可把声明的上界**无限绕过**（实测：声明 `2`、连推 5 次全部
`RETRY_FAILED_RUN` 且 `attempts=1/2` 原样不动）。把「没落地的推进」也计入 ⇒
**上界在任意崩溃模式下都成立**，且推进序列**必然**在 ≤ `allowed` 次内收口到失败停。
"""

from __future__ import annotations

from typing import Any

from packages.domain.program import ProgramDecisionKind

#: 失败重试面「认领了同序号」的判定种类（本模块两个函数的受判面）。
RETRY_CLAIM_KINDS: frozenset[ProgramDecisionKind] = frozenset({
    ProgramDecisionKind.RETRY_FAILED_RUN,
    ProgramDecisionKind.DEDUP_FAILED_RUN,
})


def retry_face_state(
    programs: Any, program_id: str, index: int, landed_ids: set[str]
) -> tuple[int, str | None]:
    """失败重试面的 `(已用尝试数, 未落库的认领 run id)`（口径见模块 docstring）。"""
    attempts = len(landed_ids)
    outstanding: str | None = None
    for decision in programs.decisions_of(program_id):
        if decision.after_index != index:
            continue
        if decision.kind not in RETRY_CLAIM_KINDS:
            continue
        claimed = str(decision.cited_run_id) if decision.cited_run_id else None
        if decision.kind is ProgramDecisionKind.DEDUP_FAILED_RUN:
            # 被阻塞的推进：没有起新 run，但**确实推进过一次**（否则序列不收敛）。
            attempts += 1
            outstanding = claimed or outstanding
            continue
        if claimed is not None and claimed not in landed_ids:
            attempts += 1
            outstanding = claimed
    return attempts, outstanding


def claimed_but_missing(
    programs: Any, program_id: str, after_index: int, known: set[str]
) -> str | None:
    """上一条 `CONTINUE` 认领的 run id（若它**没有**落库 ⇒ 返回它，供 DEDUP 点名）。"""
    for decision in reversed(programs.decisions_of(program_id)):
        if decision.after_index != after_index:
            continue
        if decision.kind is ProgramDecisionKind.CONTINUE and decision.cited_run_id:
            return None if str(decision.cited_run_id) in known else str(decision.cited_run_id)
        return None
    return None


__all__ = ["RETRY_CLAIM_KINDS", "claimed_but_missing", "retry_face_state"]
