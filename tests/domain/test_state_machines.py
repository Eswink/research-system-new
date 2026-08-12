"""状态机迁移表测试。

覆盖：合法迁移、非法迁移、terminal 不可回退、Cancellation 子状态机、
初始状态与 terminal 集合。
"""

from __future__ import annotations

from typing import Protocol

import pytest

from packages.domain.state_machines import (
    AgentSessionState,
    CancellationState,
    InvalidTransitionError,
    PhaseRunState,
    ResearchRunState,
    ResearchTaskState,
    is_terminal,
)


class _StateMachine(Protocol):
    @staticmethod
    def initial() -> str: ...

    @staticmethod
    def transition(current: str, event: str) -> str: ...

    @staticmethod
    def terminal() -> frozenset[str]: ...


@pytest.mark.parametrize(
    ("machine", "path", "expected"),
    [
        (
            ResearchRunState,
            [ResearchRunState.Transition.START_COMPILE, ResearchRunState.Transition.COMPILE_OK],
            ResearchRunState.State.PREFLIGHT,
        ),
        (
            ResearchRunState,
            [
                ResearchRunState.Transition.START_COMPILE,
                ResearchRunState.Transition.COMPILE_OK,
                ResearchRunState.Transition.PREFLIGHT_OK,
                ResearchRunState.Transition.START,
            ],
            ResearchRunState.State.RUNNING,
        ),
        (
            ResearchRunState,
            [ResearchRunState.Transition.CANCEL],
            ResearchRunState.State.CANCELLED,
        ),
        (
            PhaseRunState,
            [
                PhaseRunState.Transition.ACTIVATE,
                PhaseRunState.Transition.START,
                PhaseRunState.Transition.WAIT,
                PhaseRunState.Transition.RESUME,
            ],
            PhaseRunState.State.RUNNING,
        ),
        (
            ResearchTaskState,
            [
                ResearchTaskState.Transition.ENQUEUE,
                ResearchTaskState.Transition.LEASE,
                ResearchTaskState.Transition.START,
                ResearchTaskState.Transition.SCHEDULE_RETRY,
                ResearchTaskState.Transition.ENQUEUE,
                ResearchTaskState.Transition.LEASE,
                ResearchTaskState.Transition.START,
            ],
            ResearchTaskState.State.RUNNING,
        ),
        (
            AgentSessionState,
            [
                AgentSessionState.Transition.INITIALIZE,
                AgentSessionState.Transition.START,
                AgentSessionState.Transition.STUCK,
                AgentSessionState.Transition.UNSTUCK,
            ],
            AgentSessionState.State.RUNNING,
        ),
        (
            CancellationState,
            [
                CancellationState.Transition.ESCALATE,
                CancellationState.Transition.COMPENSATE,
                CancellationState.Transition.COMPLETE,
            ],
            CancellationState.State.CANCELLED,
        ),
    ],
)
def test_legal_transition_paths(machine: _StateMachine, path: list[str], expected: str) -> None:
    current = machine.initial()
    for event in path:
        current = machine.transition(current, event)
    assert current == expected


@pytest.mark.parametrize(
    ("machine", "current", "event"),
    [
        (ResearchRunState, ResearchRunState.State.RUNNING, ResearchRunState.Transition.START),
        (ResearchRunState, ResearchRunState.State.DRAFT, ResearchRunState.Transition.SUCCEED),
        (PhaseRunState, PhaseRunState.State.PENDING, PhaseRunState.Transition.START),
        (PhaseRunState, PhaseRunState.State.RUNNING, PhaseRunState.Transition.ACTIVATE),
        (ResearchTaskState, ResearchTaskState.State.CREATED, ResearchTaskState.Transition.START),
        (ResearchTaskState, ResearchTaskState.State.RUNNING, ResearchTaskState.Transition.LEASE),
        (AgentSessionState, AgentSessionState.State.CREATED, AgentSessionState.Transition.START),
        (
            AgentSessionState,
            AgentSessionState.State.RUNNING,
            AgentSessionState.Transition.INITIALIZE,
        ),
        (
            CancellationState,
            CancellationState.State.REQUESTED,
            CancellationState.Transition.COMPENSATE,
        ),
    ],
)
def test_illegal_transitions_raise(machine: _StateMachine, current: str, event: str) -> None:
    with pytest.raises(InvalidTransitionError):
        machine.transition(current, event)


@pytest.mark.parametrize(
    ("machine", "terminal", "event"),
    [
        (ResearchRunState, ResearchRunState.State.SUCCEEDED, ResearchRunState.Transition.CANCEL),
        (ResearchRunState, ResearchRunState.State.FAILED, ResearchRunState.Transition.RESUME),
        (PhaseRunState, PhaseRunState.State.SKIPPED, PhaseRunState.Transition.START),
        (
            ResearchTaskState,
            ResearchTaskState.State.DEAD_LETTER,
            ResearchTaskState.Transition.ENQUEUE,
        ),
        (AgentSessionState, AgentSessionState.State.CANCELLED, AgentSessionState.Transition.RESUME),
        (
            CancellationState,
            CancellationState.State.CANCELLED,
            CancellationState.Transition.COMPLETE,
        ),
    ],
)
def test_terminal_states_are_final(machine: _StateMachine, terminal: str, event: str) -> None:
    with pytest.raises(InvalidTransitionError):
        machine.transition(terminal, event)


def test_terminal_state_helper() -> None:
    assert is_terminal(ResearchRunState.State.SUCCEEDED, ResearchRunState.terminal())
    assert is_terminal(ResearchTaskState.State.DEAD_LETTER, ResearchTaskState.terminal())
    assert not is_terminal(ResearchRunState.State.RUNNING, ResearchRunState.terminal())


def test_run_approval_flow() -> None:
    state = ResearchRunState.State.RUNNING
    state = ResearchRunState.transition(state, ResearchRunState.Transition.REQUEST_APPROVAL)
    assert state == ResearchRunState.State.WAITING_FOR_APPROVAL
    state = ResearchRunState.transition(state, ResearchRunState.Transition.APPROVAL_REJECTED)
    assert state == ResearchRunState.State.FAILED
    assert is_terminal(state, ResearchRunState.terminal())


def test_preflight_failure_transitions_run_to_failed() -> None:
    state = ResearchRunState.initial()
    state = ResearchRunState.transition(state, ResearchRunState.Transition.START_COMPILE)
    state = ResearchRunState.transition(state, ResearchRunState.Transition.COMPILE_OK)
    state = ResearchRunState.transition(state, ResearchRunState.Transition.PREFLIGHT_FAILED)
    assert state == ResearchRunState.State.FAILED
    assert is_terminal(state, ResearchRunState.terminal())


def test_preflight_failure_blocks_ready_state() -> None:
    state = ResearchRunState.transition(
        ResearchRunState.State.PREFLIGHT,
        ResearchRunState.Transition.PREFLIGHT_FAILED,
    )
    assert state == ResearchRunState.State.FAILED
    with pytest.raises(InvalidTransitionError):
        ResearchRunState.transition(state, ResearchRunState.Transition.START)
