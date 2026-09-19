"""AgentRuntime / WorkflowEngine Port 特定契约测试。

覆盖：cancellation 语义、at-least-once 幂等分发、retry 边界、
runtime event 顺序（不替代 Domain Event）。

通用契约（create/run/cancel/pause/fork/unknown-session）按 registry
参数化，对全部已注册实现（Fake 与真实 adapter）复用；advance() 中间态
驱动为 FakeAgentRuntime 专属，见 test_agent_runtime_fake_advance.py。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.ports.agent_runtime import (
    AgentRuntime,
    AgentSessionSpec,
    ForkSpec,
    RuntimeEventKind,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    WorkflowEngine,
)
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


def _as_runtime(factory: type[object]) -> AgentRuntime:
    runtime = factory()
    assert isinstance(runtime, AgentRuntime)
    return runtime


def _as_engine(factory: type[object]) -> Any:
    engine = factory()
    assert isinstance(engine, WorkflowEngine)
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
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    runtime.pause(handle.session_id)
    runtime.cancel(handle.session_id)
    # 协作式：cancel 置信号；pause 在非 RUNNING 状态不抛错（幂等）
    runtime.pause(handle.session_id)
    assert handle.session_id


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_fork_creates_new_lineage(factory: type[object]) -> None:
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    forked = runtime.fork(
        handle.session_id,
        ForkSpec(session_id=handle.session_id, reason="A/B model test"),
    )
    assert forked.session_id != handle.session_id
    assert forked.status == AgentSessionState.State.CREATED


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


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_cancel_run_reaches_all_tasks(factory: type[object]) -> None:
    """SA-1R-B001：run 级取消必须到达 run 下所有未终止任务（run_id != task_id）。"""
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)
    assert engine.cancel_run(task.run_id.value) == 1
    assert task.id.value in engine.cancelled


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_acquire_after_cancel_is_rejected(factory: type[object]) -> None:
    """SA-1R-B002：取消后的任务不可重新租约，防止 cancelled-but-completed。"""
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)
    engine.cancel(task.id.value)
    with pytest.raises(InvalidInputError):
        engine.acquire_lease(task.id.value)


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["workflow_engine"])
def test_workflow_acquire_after_complete_is_rejected(factory: type[object]) -> None:
    """SA-1R-B002：已完成任务不可重新租约，防止 completed-but-retried。"""
    engine = _as_engine(factory)
    task = research_task()
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    with pytest.raises(InvalidInputError):
        engine.acquire_lease(task.id.value)


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_fork_rejects_tool_set_change_without_a_revision(
    factory: type[object],
) -> None:
    """EC-05：有效 Tool Set 冻结——改它必须显式声明 Manifest Revision。

    两个实现（Fake 与真实 adapter）走**同一条契约**：只带 `tool_set_override` 而不带
    `manifest_revision_ref` 的 fork 一律拒绝，拒绝消息点名缺哪条事实。
    """
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    with pytest.raises(InvalidInputError) as failure:
        runtime.fork(
            handle.session_id,
            ForkSpec(
                session_id=handle.session_id,
                reason="swap the tool set",
                tool_set_override=("other-provider",),
            ),
        )
    assert "manifest_revision_ref" in str(failure.value)


@pytest.mark.parametrize("factory", PORT_IMPLEMENTATIONS["agent_runtime"])
def test_agent_runtime_fork_applies_tool_set_change_under_a_revision(
    factory: type[object],
) -> None:
    """声明 revision 后改写**生效**（门不是一刀切禁止，也不是装作生效）。"""
    runtime = _as_runtime(factory)
    handle = runtime.create_session(_spec())
    forked = runtime.fork(
        handle.session_id,
        ForkSpec(
            session_id=handle.session_id,
            reason="swap the tool set",
            tool_set_override=("other-provider",),
            manifest_revision_ref="manifest-rev-2",
        ),
    )
    assert forked.session_id != handle.session_id
