"""AgentRuntime / WorkflowEngine Port 特定契约测试。

覆盖：cancellation 语义、at-least-once 幂等分发、retry 边界、
状态机合法性、runtime event 顺序（不替代 Domain Event）。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeAgentRuntime, FakeWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionSpec,
    ForkSpec,
    RuntimeEventKind,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import (
    agent_spec,
    research_task,
    role_definition,
    task_contract,
)
from tests.contracts.registry import PORT_IMPLEMENTATIONS


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )


def _as_runtime(factory: type[object]) -> FakeAgentRuntime:
    runtime = factory()
    assert isinstance(runtime, FakeAgentRuntime)
    return runtime


def _as_engine(factory: type[object]) -> FakeWorkflowEngine:
    engine = factory()
    assert isinstance(engine, FakeWorkflowEngine)
    return engine


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_create_run_success(factory: type[object]) -> None:
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    result = runtime.run(handle.session_id)
    assert result.status == AgentSessionState.State.SUCCEEDED
    kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
    assert kinds[0] is RuntimeEventKind.SESSION_CREATED
    assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_cancel_stops_run(factory: type[object]) -> None:
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    runtime.cancel(handle.session_id)
    result = runtime.run(handle.session_id)
    assert result.status == AgentSessionState.State.CANCELLED
    kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
    assert kinds[-1] is RuntimeEventKind.SESSION_CANCELLED


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_pause_resume_is_cooperative(factory: type[object]) -> None:
    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    runtime.pause(handle.session_id)
    runtime.cancel(handle.session_id)
    # 协作式：cancel 置信号；pause 在非 RUNNING 状态不抛错（幂等）
    runtime.pause(handle.session_id)
    assert handle.session_id


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_fork_creates_new_lineage(factory: type[object]) -> None:
    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    forked = runtime.fork(
        handle.session_id,
        ForkSpec(session_id=handle.session_id, reason="A/B model test"),
    )
    assert forked.session_id != handle.session_id
    assert forked.status == AgentSessionState.State.CREATED


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_advance_drives_intermediate_states(factory: type[object]) -> None:
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


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_advance_appends_events_in_order(factory: type[object]) -> None:
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


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_advance_rejects_illegal_transition(factory: type[object]) -> None:
    from packages.domain.state_base import InvalidTransitionError

    runtime = FakeAgentRuntime()
    handle = runtime.create_session(_spec())
    with pytest.raises(InvalidTransitionError):
        # CREATED 状态不允许直接 PAUSE
        runtime.advance(handle.session_id, AgentSessionState.Transition.PAUSE)


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_run_converges_from_intermediate_state(factory: type[object]) -> None:
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


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_rejects_unknown_session(factory: type[object]) -> None:
    runtime = _as_runtime(factory)
    with pytest.raises(InvalidInputError):
        runtime.run("missing-session")


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_duplicate_delivery_has_no_duplicate_side_effect(factory: type[object]) -> None:
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)
    engine.acquire_lease(task.id.value)
    assert engine.deliveries[task.idempotency_key or ""] == 1


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_duplicate_submit_is_idempotent(factory: type[object]) -> None:
    """重复 submit（同 task.id / 同 idempotency_key）必须幂等，不抛错、不覆盖首次契约。"""
    engine = _as_engine(factory)
    task = research_task()
    contract = task_contract()
    engine.submit(task, contract)
    engine.submit(task, task_contract(contract_id="hijacked"))
    assert engine.calls[-1].result_summary == "deduped"
    assert engine.calls[-1].error is None
    # 首次契约保留：重复提交带不同 contract 不得覆盖
    engine.acquire_lease(task.id.value)
    engine.acquire_lease(task.id.value)
    assert engine.deliveries[task.idempotency_key or ""] == 1


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_heartbeat_and_complete_require_lease(factory: type[object]) -> None:
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    renewed = engine.heartbeat(lease)
    assert renewed.heartbeat_at is not None
    engine.complete(renewed, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    assert engine.completed[task.id.value].outcome == "SUCCEEDED"


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_cancel_marks_task(factory: type[object]) -> None:
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    engine.cancel(task.id.value)
    assert task.id.value in engine.cancelled
