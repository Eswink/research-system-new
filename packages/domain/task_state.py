"""ResearchTask 状态机。

状态集合来自 `docs/reliability/RUN_STATE_MACHINE.md` 迁移表。
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
        SUCCEED = "SUCCEED"
        FAIL = "FAIL"
        DEAD_LETTER = "DEAD_LETTER"
        CANCEL = "CANCEL"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.CREATED, Transition.ENQUEUE): State.QUEUED,
        (State.QUEUED, Transition.LEASE): State.LEASED,
        (State.LEASED, Transition.START): State.RUNNING,
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
