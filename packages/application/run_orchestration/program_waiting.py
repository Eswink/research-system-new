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


def declared_gate_pending(
    program: Any, last_index: int, approvals: ApprovalReader | None, run_id: str
) -> str | None:
    """**声明的人工闸门**是否仍在等人拍板（是 ⇒ 返回**点名句**，否 ⇒ `None`）。

    语义**照抄 phase/run 面的 `pending_human_gates`**（少写一套判断）：
    「声明的闸门 **−** 已裁决的审批（`status != "PENDING"`）」——

    - 声明点 = `program.human_gate_at_index`（`None` ⇒ **不设闸门** ⇒ 直接 `None`，
      既有行为逐字不变）；**且**只在**该序号那一轮跑完之后**才生效（`last_index` 相等）；
    - 已裁决 ⇒ 闸门**已满足** ⇒ `None`（继续走结论面）；
    - 仍有 `PENDING` ⇒ 返回**点名句**（等的是这一轮的闸门）；
    - **缺审批面** ⇒ 也返回**点名句**（**不**静默当成「没有闸门」—— 那会让声明闸门的程序
      悄悄绕过人）；
    - **只读**：本函数**不**改任何审批状态（人没拍板就是没拍板；批准发生在**审批面**）。
    """
    declared = getattr(program, "human_gate_at_index", None)
    if declared is None or int(declared) != int(last_index):
        return None
    if approvals is None:
        return (
            f"第 {last_index} 轮是**声明的人工闸门**，但本装配未提供审批面"
            "（点名：声明了闸门却没有可查的审批面）"
        )
    try:
        rows = approvals.list_for_run(run_id)
    except Exception as error:  # noqa: BLE001 - 审批面故障必须**点名**，不得静默放行
        return (
            f"第 {last_index} 轮是**声明的人工闸门**，但审批面查询失败"
            f"（{type(error).__name__}: {error}）"
        )
    pending = [str(row.id) for row in rows if str(getattr(row, "status", "")) == "PENDING"]
    if pending:
        return (
            f"第 {last_index} 轮是**声明的人工闸门**（`human_gate_at_index={declared}`）"
            f"⇒ 等人拍板待审批 id={','.join(pending)}（不自动放行）"
        )
    decided = [row for row in rows if str(getattr(row, "status", "")) != "PENDING"]
    if decided:
        return None
    return (
        f"第 {last_index} 轮是**声明的人工闸门**（`human_gate_at_index={declared}`）"
        "⇒ 等人拍板（该 run 名下尚无审批记录；批准发生在审批面，本处不自动放行）"
    )


def declared_gate_verdict(
    program: Any,
    last: Any,
    approvals: ApprovalReader | None,
    gate_registration: tuple[str | None, str | None] | None = None,
) -> tuple[str, str, tuple[str, ...]] | None:
    """**声明的闸门**是否要拦住本次推进；要 ⇒ `(kind, reason, cited_facts)`，不要 ⇒ `None`。

    **返回判定值而不是值对象**：调用方（`program_runner`）自己构它的 `_Evaluation`
    —— 本模块**不** import 它（避免导入环，也让 mypy 不必接受 `Any` 作为返回）。

    GOAL-20261010-047 EC-02：注册（`program_gate_registration`，**有副作用**）由调用方
    先做，本函数只**读**它的结果并把它写进判词 —— 本模块因此保持**只读**
    （承序 12/14 的判据：判定面不得出现写方法）。
    """
    index = last.program_index or 0
    registered, register_note = gate_registration or (None, None)
    note = declared_gate_pending(program, index, approvals, last.id.value)
    if note is None:
        return None
    facts = [f"state={last.state}", f"human_gate_at_index={program.human_gate_at_index}"]
    if registered is not None:
        facts.append(f"approval_id={registered}")
    note = note if register_note is None else f"{note}；{register_note}"
    return (
        ProgramDecisionKind.WAIT_FOR_APPROVAL.value,
        note + "；本轮不推进（不自动放行）",
        tuple(facts),
    )


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


__all__ = [
    "AWAITING_HUMAN",
    "ApprovalReader",
    "declared_gate_pending",
    "declared_gate_verdict",
    "pending_approval",
    "waiting_round_decision",
]
