"""程序推进的**等待面**判定（GOAL-20261010-044 EC-02/EC-03）。

**为什么单列**：`program_runner.py` 有 **450 行硬上限**（规模门），本轮的「等待理由可区分」
在它之上接不动 ⇒ 与全仓既有的「声明面 vs 执行面分列」同一手法
（`phase_capability_triggers.py` 之于 `phase_capabilities.py`）。

**它判什么**：**非终态**的两类等待**互不混用** ——

- 停在**人工闸门**（`WAITING_FOR_APPROVAL` / `PAUSED`）⇒ `WAIT_FOR_APPROVAL`：等**人**拍板，
  判词**点名**待审批的标识（经既有 `ApprovalStore.list_for_run` 查；**查不到也点名**）；
- 其余非终态 ⇒ `WAIT`：等**机器**跑完（理由串与 `cited_facts` **逐字保持**既有形态）。

**边界**：本模块**只读**审批面（`list_for_run`）—— **不**建第二套审批存储、
**不**改审批状态、**不**自动批准 / 自动跳过（那是 D 组审批通道面，触达即 BLOCKED）。
"""

from __future__ import annotations

from typing import Any

from packages.domain.program import ProgramDecisionKind
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

#: 审批读取面（`ApprovalStore` 的形状；只用到 `list_for_run` —— **不**新建第二套存储）。
ApprovalReader = Any

#: 停在**人工闸门**的 run 状态（等**人**拍板；与「还在跑」等**机器**互不混用）。
AWAITING_HUMAN: frozenset[str] = frozenset({
    ResearchRunState.State.WAITING_FOR_APPROVAL,
    ResearchRunState.State.PAUSED,
})


def pending_approval(approvals: ApprovalReader | None, run_id: str) -> str:
    """待审批的**点名**句（查得到就点名 id，查不到**也点名** —— 不静默、不编造）。

    **只返回一个字符串**（判据用的就是它）：早先的签名返回 `(id 串, 句)`，而调用方
    只用后者 —— 那个 id 串是**死值**（按压改它不影响任何判据 ⇒ 由本轮的按压发现并删除）。
    """
    if approvals is None:
        return "待审批：本装配未提供审批面（点名，不是「没有待审批」）"
    try:
        rows = approvals.list_for_run(run_id)
    except Exception as error:  # noqa: BLE001 - 审批面故障必须**点名**，不得静默降级
        return f"待审批：审批面查询失败（{type(error).__name__}: {error}）"
    pending = [str(row.id) for row in rows if str(getattr(row, "status", "")) == "PENDING"]
    if not pending:
        return "待审批：该 run 名下没有 PENDING 的审批记录（点名查不到）"
    return f"待审批 id={','.join(pending)}"


def waiting_round_decision(
    last: ResearchRun,
    last_index: int,
    approvals: ApprovalReader | None,
) -> tuple[ProgramDecisionKind, str, tuple[str, ...]]:
    """**非终态**的判定：返回 `(kind, reason, cited_facts)`（两类等待**互不混用**）。"""
    state = str(last.state)
    if state not in AWAITING_HUMAN:
        return (
            ProgramDecisionKind.WAIT,
            f"第 {last_index} 轮尚未终止（state={state}）⇒ 本轮不推进",
            (f"state={state}",),
        )
    fact = pending_approval(approvals, last.id.value)
    return (
        ProgramDecisionKind.WAIT_FOR_APPROVAL,
        (
            f"第 {last_index} 轮停在**人工闸门**（state={state}）⇒ 等**人**拍板{fact}"
            "；本轮不推进（不自动批准、不自动跳过）"
        ),
        (f"state={state}", fact.strip()),
    )


__all__ = ["AWAITING_HUMAN", "ApprovalReader", "pending_approval", "waiting_round_decision"]
