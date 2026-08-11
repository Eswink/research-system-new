"""AgentSession 状态机 + Cancellation 子状态机。

AgentSession 上游状态不是 Domain enum，由 adapter 显式映射（AGENT_RUNTIME.md）。
状态集合来自 `docs/reliability/RUN_STATE_MACHINE.md` 迁移表。
"""

from __future__ import annotations

from packages.domain.state_base import InvalidTransitionError


class AgentSessionState:
    """AgentSession 状态机。"""

    class State:
        CREATED = "CREATED"
        INITIALIZING = "INITIALIZING"
        RUNNING = "RUNNING"
        WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
        PAUSED = "PAUSED"
        STUCK = "STUCK"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    class Transition:
        INITIALIZE = "INITIALIZE"
        START = "START"
        REQUEST_APPROVAL = "REQUEST_APPROVAL"
        APPROVAL_GRANTED = "APPROVAL_GRANTED"
        APPROVAL_REJECTED = "APPROVAL_REJECTED"
        PAUSE = "PAUSE"
        RESUME = "RESUME"
        STUCK = "STUCK"
        UNSTUCK = "UNSTUCK"
        SUCCEED = "SUCCEED"
        FAIL = "FAIL"
        CANCEL = "CANCEL"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.CREATED, Transition.INITIALIZE): State.INITIALIZING,
        (State.INITIALIZING, Transition.START): State.RUNNING,
        (State.RUNNING, Transition.REQUEST_APPROVAL): State.WAITING_FOR_APPROVAL,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_GRANTED): State.RUNNING,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_REJECTED): State.FAILED,
        (State.RUNNING, Transition.PAUSE): State.PAUSED,
        (State.PAUSED, Transition.RESUME): State.RUNNING,
        (State.RUNNING, Transition.STUCK): State.STUCK,
        (State.STUCK, Transition.UNSTUCK): State.RUNNING,
        (State.RUNNING, Transition.SUCCEED): State.SUCCEEDED,
        (State.INITIALIZING, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.CANCEL): State.CANCELLED,
        (State.WAITING_FOR_APPROVAL, Transition.CANCEL): State.CANCELLED,
        (State.PAUSED, Transition.CANCEL): State.CANCELLED,
        (State.STUCK, Transition.CANCEL): State.CANCELLED,
        (State.INITIALIZING, Transition.FAIL): State.FAILED,
        (State.RUNNING, Transition.FAIL): State.FAILED,
        (State.STUCK, Transition.FAIL): State.FAILED,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return AgentSessionState.State.CREATED

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            AgentSessionState.State.SUCCEEDED,
            AgentSessionState.State.FAILED,
            AgentSessionState.State.CANCELLED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return AgentSessionState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None


class CancellationState:
    """Cancellation 子状态机（WORKFLOW_RELIABILITY.md）。"""

    class State:
        REQUESTED = "REQUESTED"
        COOPERATIVE = "COOPERATIVE"
        FORCED = "FORCED"
        COMPENSATING = "COMPENSATING"
        CANCELLED = "CANCELLED"

    class Transition:
        ACCEPT = "ACCEPT"
        ESCALATE = "ESCALATE"
        COMPENSATE = "COMPENSATE"
        COMPLETE = "COMPLETE"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.REQUESTED, Transition.ACCEPT): State.COOPERATIVE,
        (State.REQUESTED, Transition.ESCALATE): State.FORCED,
        (State.FORCED, Transition.COMPENSATE): State.COMPENSATING,
        (State.COMPENSATING, Transition.COMPLETE): State.CANCELLED,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return CancellationState.State.REQUESTED

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({CancellationState.State.CANCELLED})

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return CancellationState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None
