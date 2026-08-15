"""Experiment 状态机（M9 Real Experiment Runtime）。

ExperimentPlanState：DRAFT → PREREGISTERED → ARCHIVED。
ExperimentRunState：PENDING → RUNNING → SUCCEEDED | NEGATIVE_RESULT |
FAILED | TIMED_OUT | CANCELLED。

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
