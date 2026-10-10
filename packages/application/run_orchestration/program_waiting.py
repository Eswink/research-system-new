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

from packages.application.ports.approval_store import ApprovalSpec
from packages.domain.program import ProgramDecisionKind
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

#: 审批读取面（`ApprovalStore` 的形状；只用到 `list_for_run` —— **不**新建第二套存储）。
ApprovalReader = Any

#: 程序级闸门的 `action` 前缀（GOAL-20261010-047 EC-02）。
#: **必须**与 phase 面的 `human-gate:` 区分：裁决面的准入条件不同（本前缀允许 run 已终态）。
PROGRAM_GATE_ACTION = "program-gate:"
#: `policy_source`（与 `context` 一起让审批记录**自证**它是谁注册的）。
PROGRAM_GATE_POLICY_SOURCE = "program-gate"

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
    program: Any, last: Any, approvals: ApprovalReader | None
) -> tuple[str, str, tuple[str, ...]] | None:
    """**声明的闸门**是否要拦住本次推进；要 ⇒ `(kind, reason, cited_facts)`，不要 ⇒ `None`。

    **返回判定值而不是值对象**：调用方（`program_runner`）自己构它的 `_Evaluation`
    —— 本模块**不** import 它（避免导入环，也让 mypy 不必接受 `Any` 作为返回）。

    GOAL-20261010-047 EC-02：闸门**先注册**（`register_declared_gate`）再判 —— 注册是
    「这条闸门**可被裁决**」的全部依据；**只读面**（缺 `register` 方法）⇒ 注册被跳过且
    **判词点名**，此时仍按「等人拍板」拦住（**不**静默当成无闸门）。
    """
    index = last.program_index or 0
    registered, register_note = register_declared_gate(program, index, approvals, last.id.value)
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


def register_declared_gate(
    program: Any, last_index: int, approvals: ApprovalReader | None, run_id: str
) -> tuple[str | None, str | None]:
    """为**声明在该轮**的闸门注册一条待决审批；返回 `(审批标识 | None, 点名句 | None)`。

    `(None, None)` = **不需要注册**（未声明闸门 / 不在该轮 / 已有待决记录 ⇒ 幂等命中）。
    `(None, <点名句>)` = **该注册却注册不了**（缺审批面、查询失败、面不提供 `register`）。

    **语义与 phase 面同源**（`phase_pause.pause_for_human_gate` 的 `ApprovalSpec` 逐字段对照）：
    `risk="HUMAN_GATE"`、`policy_source` 同名、`context` 换成程序侧的轮次标识；
    `action` 用**本 GOAL 自己的前缀** `program-gate:` 与 phase 面的 `human-gate:`
    **区分开** —— 裁决面的准入条件不同（本前缀允许 run 已终态，见 `routers/approvals.py`），
    混用前缀会让两种语义互相串台。

    **幂等**：查 `list_for_run` 里**同 action 前缀**的记录 —— 已有（无论待决或已裁决）即
    视为**已注册**，不再新增（重复推进不得堆积待决记录）。
    """
    declared = getattr(program, "human_gate_at_index", None)
    if declared is None or int(declared) != int(last_index):
        return None, None
    if approvals is None:
        return None, "（尚无可注册的审批面）"
    register = getattr(approvals, "register", None)
    if not callable(register):
        return None, "（该审批面**只读**，无法注册等待项）"
    action = f"{PROGRAM_GATE_ACTION}{getattr(program, 'id', '')}"
    try:
        rows = approvals.list_for_run(run_id)
    except Exception as error:  # noqa: BLE001 - 注册前的查询失败必须**点名**
        return None, f"（注册前查询失败：{type(error).__name__}: {error}）"
    if any(str(getattr(row, "action", "")) == action for row in rows):
        return None, None
    try:
        record = register(
            ApprovalSpec(
                run_id=run_id,
                action=action,
                risk="HUMAN_GATE",
                context=f"program-round:{last_index}",
                policy_source=PROGRAM_GATE_POLICY_SOURCE,
                requested_event_id="",
            )
        )
    except Exception as error:  # noqa: BLE001 - 注册失败必须**点名**（不静默当成已注册）
        return None, f"（注册失败：{type(error).__name__}: {error}）"
    return str(getattr(record, "id", "")) or None, None


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
    "PROGRAM_GATE_ACTION",
    "PROGRAM_GATE_POLICY_SOURCE",
    "ApprovalReader",
    "declared_gate_pending",
    "declared_gate_verdict",
    "pending_approval",
    "register_declared_gate",
    "waiting_round_decision",
]
