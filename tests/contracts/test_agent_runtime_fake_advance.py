"""FakeAgentRuntime 专属测试：advance() 中间态驱动器（非 Protocol 方法）。

真实 adapter（OpenHandsRuntimeAdapter）无 advance()；这些测试直接实例化
FakeAgentRuntime，不通过 registry 参数化。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeAgentRuntime
from packages.application.ports.agent_runtime import AgentSessionSpec, RuntimeEventKind
from packages.application.ports.errors import InvalidInputError
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )


def test_agent_runtime_advance_drives_intermediate_states() -> None:
    """P2-1：advance 显式驱动全部中间态（INITIALIZING/WAITING_FOR_APPROVAL/STUCK）。"""
    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    session_id = handle.session_id
    assert runtime.advance(session_id, AgentSessionState.Transition.INITIALIZE) == (
        AgentSessionState.State.INITIALIZING
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.START) == (
        AgentSessionState.State.RUNNING
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.REQUEST_APPROVAL) == (
        AgentSessionState.State.WAITING_FOR_APPROVAL
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.APPROVAL_GRANTED) == (
        AgentSessionState.State.RUNNING
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.STUCK) == (
        AgentSessionState.State.STUCK
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.UNSTUCK) == (
        AgentSessionState.State.RUNNING
    )
    assert runtime.advance(session_id, AgentSessionState.Transition.PAUSE) == (
        AgentSessionState.State.PAUSED
    )


def test_agent_runtime_advance_appends_events_in_order() -> None:
    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    session_id = handle.session_id
    runtime.advance(session_id, AgentSessionState.Transition.INITIALIZE)
    runtime.advance(session_id, AgentSessionState.Transition.START)
    runtime.advance(session_id, AgentSessionState.Transition.REQUEST_APPROVAL)
    kinds = [event.kind for event in runtime.stream_events(session_id)]
    assert kinds == [
        RuntimeEventKind.SESSION_CREATED,
        RuntimeEventKind.SESSION_STARTED,
        RuntimeEventKind.APPROVAL_REQUESTED,
    ]


def test_agent_runtime_advance_rejects_illegal_transition() -> None:
    from packages.domain.state_base import InvalidTransitionError

    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    with pytest.raises(InvalidTransitionError):
        # CREATED 状态不允许直接 PAUSE
        runtime.advance(handle.session_id, AgentSessionState.Transition.PAUSE)


def test_agent_runtime_run_converges_from_intermediate_state() -> None:
    """P2-1：从 WAITING_FOR_APPROVAL 中间态 run 仍收敛到 outcome 终态。"""
    runtime = FakeAgentRuntime(outcome=AgentSessionState.State.SUCCEEDED)
    handle = runtime.create_session(_spec())
    session_id = handle.session_id
    runtime.advance(session_id, AgentSessionState.Transition.INITIALIZE)
    runtime.advance(session_id, AgentSessionState.Transition.START)
    runtime.advance(session_id, AgentSessionState.Transition.REQUEST_APPROVAL)
    result = runtime.run(session_id)
    assert result.status == AgentSessionState.State.SUCCEEDED
    kinds = [event.kind for event in runtime.stream_events(session_id)]
    assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED


def test_agent_runtime_advance_rejects_unknown_session() -> None:
    runtime = FakeAgentRuntime()
    with pytest.raises(InvalidInputError):
        runtime.advance("missing-session", AgentSessionState.Transition.START)
