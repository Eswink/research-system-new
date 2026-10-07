"""人工恢复的**跨实现契约**（ADR-0033）：三实现同判据，行为臂只打持久化实现。

`tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py` 判 SQLite 的**行为**
（恢复→真交付、点名拒绝、零第二次副作用）；本文件判**实现无关**的三件事：

1. **声明集完整**：`PORT_IMPLEMENTATIONS["workflow_engine"]` 的**每一个**实现都有
   `requeue`（受判面 = 声明集本身 ⇒ 新增实现而不带该方法会判红）；
2. **点名拒绝同判**：三实现对「不存在的任务」与「非死信起态」都点名拒绝（`InvalidInputError`
   且消息含任务 id）；状态读数走 **Port 面**的 `task_identities`（`list_tasks` 是 adapter
   便利面，不在 Port 协议里 ⇒ Fake 没有）。
3. **Fake 的边界显式**：Fake 没有死信到达路径（`complete` 不跑 `disposition`）⇒ 行为臂
   在两个持久化实现上判；Fake 侧用 `mark_dead_letter` 造起态证明**它也同判**，而
   "死信怎么来的"这条差异被写成本文件的断言（与 `due_retry_task_ids` 的既有边界同源）。
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    WorkflowEngine,
)
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=f"recovery-{ID.generate().value}",
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="recovery-contract",
        version="1.0",
        purpose="cross-implementation manual recovery",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=2, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )


def _status_of(engine: WorkflowEngine, run_id: str, task_id: str) -> str:
    """按 **Port 面**读一条任务的状态（`task_identities` 是协议的一部分）。"""
    return next(item.status for item in engine.task_identities(run_id) if item.task_id == task_id)


@pytest.mark.parametrize("factory", _FACTORIES)
def test_every_declared_engine_exposes_requeue(factory: Callable[[], object]) -> None:
    """**声明集完整**：注册表里的每个 WorkflowEngine 实现都必须有 `requeue`。"""
    engine = factory()
    assert hasattr(engine, "requeue"), (
        f"{type(engine).__name__} 缺 requeue ⇒ 声明集不完整（ADR-0033 要求三实现同形）"
    )


@pytest.mark.parametrize("factory", _FACTORIES)
def test_requeue_refuses_an_unknown_task_on_every_implementation(
    factory: Callable[[], object],
) -> None:
    """**点名拒绝同判**：不存在的任务在三实现上都是 `InvalidInputError` 且消息含 id。"""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    ghost = ID.generate().value
    with pytest.raises(InvalidInputError) as caught:
        engine.requeue(ghost)
    assert ghost in str(caught.value), f"{type(engine).__name__} 的消息必须点名任务 id"


@pytest.mark.parametrize("factory", _FACTORIES)
def test_requeue_refuses_a_task_that_is_not_dead_letter_on_every_implementation(
    factory: Callable[[], object],
) -> None:
    """**点名拒绝同判**：非死信起态（`QUEUED`）在三实现上都被点名拒绝。"""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _task()
    engine.submit(task, _contract())
    with pytest.raises(InvalidInputError) as caught:
        engine.requeue(task.id.value)
    message = str(caught.value)
    assert task.id.value in message and "only DEAD_LETTER" in message
    assert _status_of(engine, task.run_id.value, task.id.value) == ResearchTaskState.State.QUEUED, (
        "被拒时状态不变"
    )


def test_the_fake_can_recover_from_a_marked_dead_letter() -> None:
    """**Fake 的边界显式**：它没有死信到达路径（`complete` 不跑 disposition）⇒ 用
    `mark_dead_letter` 造起态证明恢复语义同判；「死信怎么来的」这条差异写在这里。

    **持久化实现的对照**（同一事实的机械面）：`tests/adapters/sqlite/
    test_workflow_dead_letter_manual_recovery.py` 从真实失败路径打满预算进死信。
    """
    engine = FakeWorkflowEngine()
    task = _task()
    engine.submit(task, _contract())
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    assert _status_of(engine, task.run_id.value, task.id.value) != (
        ResearchTaskState.State.DEAD_LETTER
    ), "Fake 的 complete 不产出死信（与两个持久化实现的已知差异）"

    engine.mark_dead_letter(task.id.value)
    assert engine.requeue(task.id.value) == "restored"
    assert _status_of(engine, task.run_id.value, task.id.value) == ResearchTaskState.State.QUEUED
