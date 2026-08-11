"""ResearchRun 状态机。

状态集合来自 `docs/reliability/RUN_STATE_MACHINE.md` 迁移表。
"""

from __future__ import annotations

from packages.domain.state_base import InvalidTransitionError


class ResearchRunState:
    """ResearchRun 状态机。"""

    class State:
        DRAFT = "DRAFT"
        COMPILING = "COMPILING"
        PREFLIGHT = "PREFLIGHT"
        READY = "READY"
        RUNNING = "RUNNING"
        WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
        PAUSED = "PAUSED"
        DEGRADED = "DEGRADED"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    class Transition:
        START_COMPILE = "START_COMPILE"
        COMPILE_OK = "COMPILE_OK"
        START_PREFLIGHT = "START_PREFLIGHT"
        PREFLIGHT_OK = "PREFLIGHT_OK"
        START = "START"
        PAUSE = "PAUSE"
        RESUME = "RESUME"
        REQUEST_APPROVAL = "REQUEST_APPROVAL"
        APPROVAL_GRANTED = "APPROVAL_GRANTED"
        APPROVAL_REJECTED = "APPROVAL_REJECTED"
        DEGRADE = "DEGRADE"
        SUCCEED = "SUCCEED"
        FAIL = "FAIL"
        CANCEL = "CANCEL"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.DRAFT, Transition.START_COMPILE): State.COMPILING,
        (State.COMPILING, Transition.COMPILE_OK): State.PREFLIGHT,
        (State.PREFLIGHT, Transition.START_PREFLIGHT): State.READY,
        (State.READY, Transition.START): State.RUNNING,
        (State.RUNNING, Transition.PAUSE): State.PAUSED,
        (State.PAUSED, Transition.RESUME): State.RUNNING,
        (State.RUNNING, Transition.REQUEST_APPROVAL): State.WAITING_FOR_APPROVAL,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_GRANTED): State.RUNNING,
        (State.WAITING_FOR_APPROVAL, Transition.APPROVAL_REJECTED): State.FAILED,
        (State.RUNNING, Transition.DEGRADE): State.DEGRADED,
        (State.DEGRADED, Transition.RESUME): State.RUNNING,
        (State.RUNNING, Transition.SUCCEED): State.SUCCEEDED,
        (State.DEGRADED, Transition.SUCCEED): State.SUCCEEDED,
        (State.DRAFT, Transition.CANCEL): State.CANCELLED,
        (State.COMPILING, Transition.CANCEL): State.CANCELLED,
        (State.PREFLIGHT, Transition.CANCEL): State.CANCELLED,
        (State.READY, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.CANCEL): State.CANCELLED,
        (State.PAUSED, Transition.CANCEL): State.CANCELLED,
        (State.WAITING_FOR_APPROVAL, Transition.CANCEL): State.CANCELLED,
        (State.DEGRADED, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.FAIL): State.FAILED,
        (State.DEGRADED, Transition.FAIL): State.FAILED,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return ResearchRunState.State.DRAFT

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            ResearchRunState.State.SUCCEEDED,
            ResearchRunState.State.FAILED,
            ResearchRunState.State.CANCELLED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return ResearchRunState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None
