"""Experiment 状态机（M9 Real Experiment Runtime）。

ExperimentPlanState：DRAFT → PREREGISTERED → ARCHIVED。
ExperimentRunState：PENDING → RUNNING → SUCCEEDED | NEGATIVE_RESULT |
FAILED | TIMED_OUT | CANCELLED。
ExperimentQueueState（G14）：QUEUED → DISPATCHING → DISPATCHED | FAILED，
QUEUED → CANCELLED，DISPATCHING → QUEUED（仅认领过期重认领）。

与 ResearchRunState 相同模式：terminal 状态无出边，非法迁移抛
InvalidTransitionError。NEGATIVE_RESULT 是科学结论（执行成功、假设未获
支持），与执行失败 FAILED / TIMED_OUT 语义分离（AGENTS.md / M9 DoD）。
"""

from __future__ import annotations

from packages.domain.state_base import InvalidTransitionError


class ExperimentPlanState:
    """ExperimentPlan 生命周期。"""

    class State:
        DRAFT = "DRAFT"
        PREREGISTERED = "PREREGISTERED"
        ARCHIVED = "ARCHIVED"

    class Transition:
        PREREGISTER = "PREREGISTER"
        ARCHIVE = "ARCHIVE"

    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.DRAFT, Transition.PREREGISTER): State.PREREGISTERED,
        (State.DRAFT, Transition.ARCHIVE): State.ARCHIVED,
        (State.PREREGISTERED, Transition.ARCHIVE): State.ARCHIVED,
    }

    @staticmethod
    def initial() -> str:
        return ExperimentPlanState.State.DRAFT

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({ExperimentPlanState.State.ARCHIVED})

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return ExperimentPlanState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None


class ExperimentRunState:
    """ExperimentRun 生命周期；NEGATIVE_RESULT 为科学负结论终态。"""

    class State:
        PENDING = "PENDING"
        RUNNING = "RUNNING"
        SUCCEEDED = "SUCCEEDED"
        NEGATIVE_RESULT = "NEGATIVE_RESULT"
        FAILED = "FAILED"
        TIMED_OUT = "TIMED_OUT"
        CANCELLED = "CANCELLED"

    class Transition:
        START = "START"
        COMPLETE_SUCCESS = "COMPLETE_SUCCESS"
        COMPLETE_NEGATIVE = "COMPLETE_NEGATIVE"
        COMPLETE_FAILED = "COMPLETE_FAILED"
        COMPLETE_TIMED_OUT = "COMPLETE_TIMED_OUT"
        CANCEL = "CANCEL"

    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.PENDING, Transition.START): State.RUNNING,
        (State.RUNNING, Transition.COMPLETE_SUCCESS): State.SUCCEEDED,
        (State.RUNNING, Transition.COMPLETE_NEGATIVE): State.NEGATIVE_RESULT,
        (State.RUNNING, Transition.COMPLETE_FAILED): State.FAILED,
        (State.RUNNING, Transition.COMPLETE_TIMED_OUT): State.TIMED_OUT,
        (State.PENDING, Transition.CANCEL): State.CANCELLED,
        (State.RUNNING, Transition.CANCEL): State.CANCELLED,
    }

    @staticmethod
    def initial() -> str:
        return ExperimentRunState.State.PENDING

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            ExperimentRunState.State.SUCCEEDED,
            ExperimentRunState.State.NEGATIVE_RESULT,
            ExperimentRunState.State.FAILED,
            ExperimentRunState.State.TIMED_OUT,
            ExperimentRunState.State.CANCELLED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return ExperimentRunState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None


class ExperimentQueueState:
    """实验队列条目生命周期（G14）。

    QUEUED → DISPATCHING 是**原子认领**（存储层条件更新，同一时刻只有一个派发者
    拿到条目）；DISPATCHING 的出口三分：派发成功 DISPATCHED、派发失败 FAILED、
    认领过期 CLAIM_EXPIRED 回到 QUEUED（进程崩溃/停机中断的条目重新可派发，
    at-least-once，不假装 exactly-once）。QUEUED → CANCELLED 是操作员取消；
    DISPATCHING 不可取消（run 已开始，处置该 run 用 run 的 cancel 面）。
    """

    class State:
        QUEUED = "QUEUED"
        DISPATCHING = "DISPATCHING"
        DISPATCHED = "DISPATCHED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    class Transition:
        CLAIM = "CLAIM"
        COMPLETE_DISPATCH = "COMPLETE_DISPATCH"
        COMPLETE_FAILURE = "COMPLETE_FAILURE"
        CLAIM_EXPIRED = "CLAIM_EXPIRED"
        CANCEL = "CANCEL"

    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.QUEUED, Transition.CLAIM): State.DISPATCHING,
        (State.DISPATCHING, Transition.COMPLETE_DISPATCH): State.DISPATCHED,
        (State.DISPATCHING, Transition.COMPLETE_FAILURE): State.FAILED,
        (State.DISPATCHING, Transition.CLAIM_EXPIRED): State.QUEUED,
        (State.QUEUED, Transition.CANCEL): State.CANCELLED,
    }

    @staticmethod
    def initial() -> str:
        return ExperimentQueueState.State.QUEUED

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({
            ExperimentQueueState.State.DISPATCHED,
            ExperimentQueueState.State.FAILED,
            ExperimentQueueState.State.CANCELLED,
        })

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return ExperimentQueueState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None
