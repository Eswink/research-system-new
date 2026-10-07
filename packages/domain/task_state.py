"""ResearchTask 状态机。

状态集合来自 `docs/reliability/RUN_STATE_MACHINE.md` 迁移表。

`DEAD_LETTER` 的语义（ADR-0033，R26-1）：它仍在 `terminal()` 里 ——
**对自动路径终态**（claim / acquire / 恢复面都不会碰它），但**可以人工显式恢复**：
唯一出边 `DEAD_LETTER --REQUEUE--> QUEUED` 只由恢复入口（`requeue`）触发，
自动派发链**不**引用 `Transition.REQUEUE`。
"""

from __future__ import annotations

from packages.domain.state_base import InvalidTransitionError


class ResearchTaskState:
    """ResearchTask 状态机。"""

    class State:
        CREATED = "CREATED"
        QUEUED = "QUEUED"
        LEASED = "LEASED"
        RUNNING = "RUNNING"
        WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
        WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
        RETRY_SCHEDULED = "RETRY_SCHEDULED"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        DEAD_LETTER = "DEAD_LETTER"
        CANCELLED = "CANCELLED"

    class Transition:
        ENQUEUE = "ENQUEUE"
        LEASE = "LEASE"
        START = "START"
        WAIT_FOR_TOOL = "WAIT_FOR_TOOL"
        TOOL_READY = "TOOL_READY"
        REQUEST_APPROVAL = "REQUEST_APPROVAL"
        APPROVAL_GRANTED = "APPROVAL_GRANTED"
        APPROVAL_REJECTED = "APPROVAL_REJECTED"
        SCHEDULE_RETRY = "SCHEDULE_RETRY"
        EXPIRE_LEASE = "EXPIRE_LEASE"
        SUCCEED = "SUCCEED"
        FAIL = "FAIL"
        DEAD_LETTER = "DEAD_LETTER"
        CANCEL = "CANCEL"
        # ADR-0033（R26-1）：唯一从 DEAD_LETTER 出发的迁移事件，**只由人工恢复入口**
        # （`WorkflowEngine.requeue`）消费；自动派发链不引用它。
        REQUEUE = "REQUEUE"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.CREATED, Transition.ENQUEUE): State.QUEUED,
        (State.QUEUED, Transition.LEASE): State.LEASED,
        (State.LEASED, Transition.START): State.RUNNING,
        # lease 超时/worker 崩溃后由 recover_expired_leases 回到 QUEUED
        (State.LEASED, Transition.EXPIRE_LEASE): State.QUEUED,
        (State.RUNNING, Transition.WAIT_FOR_TOOL): State.WAITING_FOR_TOOL,
        (State.WAITING_FOR_TOOL, Transition.TOOL_READY): State.RUNNING,
        (State.RUNNING, Transition.REQUEST_APPROVAL): State.WAITING_FOR_APPROVAL,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_GRANTED): State.RUNNING,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_REJECTED): State.FAILED,
        (State.RUNNING, Transition.SCHEDULE_RETRY): State.RETRY_SCHEDULED,
        (State.RETRY_SCHEDULED, Transition.ENQUEUE): State.QUEUED,
        (State.RUNNING, Transition.SUCCEED): State.SUCCEEDED,
        (State.RUNNING, Transition.FAIL): State.FAILED,
        (State.RETRY_SCHEDULED, Transition.FAIL): State.FAILED,
        (State.RETRY_SCHEDULED, Transition.DEAD_LETTER): State.DEAD_LETTER,
        # ADR-0033（R26-1）：**唯一**从终态出发的迁移 —— 人工恢复一条死信任务。
        # 只由恢复入口（`WorkflowEngine.requeue`）触发；自动路径（claim / acquire /
        # 退避派发 / 租约恢复）不引用 `Transition.REQUEUE`。
        (State.DEAD_LETTER, Transition.REQUEUE): State.QUEUED,
        (State.WAITING_FOR_APPROVAL, Transition.FAIL): State.FAILED,
        (State.CREATED, Transition.CANCEL): State.CANCELLED,
        (State.QUEUED, Transition.CANCEL): State.CANCELLED,
        (State.LEASED, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.CANCEL): State.CANCELLED,
        (State.WAITING_FOR_TOOL, Transition.CANCEL): State.CANCELLED,
        (State.WAITING_FOR_APPROVAL, Transition.CANCEL): State.CANCELLED,
        (State.RETRY_SCHEDULED, Transition.CANCEL): State.CANCELLED,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return ResearchTaskState.State.CREATED

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            ResearchTaskState.State.SUCCEEDED,
            ResearchTaskState.State.FAILED,
            ResearchTaskState.State.DEAD_LETTER,
            ResearchTaskState.State.CANCELLED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return ResearchTaskState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None
