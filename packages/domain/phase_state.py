"""PhaseRun 状态机。

状态集合来自 `docs/reliability/RUN_STATE_MACHINE.md` 迁移表。
"""

from __future__ import annotations

from packages.domain.state_base import InvalidTransitionError


class PhaseRunState:
    """PhaseRun 状态机。"""

    class State:
        PENDING = "PENDING"
        READY = "READY"
        RUNNING = "RUNNING"
        WAITING = "WAITING"
        PAUSED = "PAUSED"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"
        SKIPPED = "SKIPPED"

    class Transition:
        ACTIVATE = "ACTIVATE"
        START = "START"
        WAIT = "WAIT"
        PAUSE = "PAUSE"
        RESUME = "RESUME"
        SUCCEED = "SUCCEED"
        FAIL = "FAIL"
        CANCEL = "CANCEL"
        SKIP = "SKIP"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.PENDING, Transition.ACTIVATE): State.READY,
        (State.READY, Transition.START): State.RUNNING,
        (State.RUNNING, Transition.WAIT): State.WAITING,
        (State.WAITING, Transition.RESUME): State.RUNNING,
        (State.RUNNING, Transition.PAUSE): State.PAUSED,
        (State.PAUSED, Transition.RESUME): State.RUNNING,
        (State.RUNNING, Transition.SUCCEED): State.SUCCEEDED,
        (State.RUNNING, Transition.FAIL): State.FAILED,
        (State.PENDING, Transition.CANCEL): State.CANCELLED,
        (State.READY, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.CANCEL): State.CANCELLED,
        (State.WAITING, Transition.CANCEL): State.CANCELLED,
        (State.PAUSED, Transition.CANCEL): State.CANCELLED,
        (State.PENDING, Transition.SKIP): State.SKIPPED,
        (State.READY, Transition.SKIP): State.SKIPPED,
        (State.WAITING, Transition.FAIL): State.FAILED,
        (State.PAUSED, Transition.FAIL): State.FAILED,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return PhaseRunState.State.PENDING

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            PhaseRunState.State.SUCCEEDED,
            PhaseRunState.State.FAILED,
            PhaseRunState.State.CANCELLED,
            PhaseRunState.State.SKIPPED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return PhaseRunState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None
