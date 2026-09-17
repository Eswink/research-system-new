"""重排读面契约（GOAL-004 cycle 2）：两个读面不会各说各话，三实现同一个空判据。

`retry_schedule` 给运维读面计数与最近期限，`due_retry_task_ids` 给调度器 ids。它们由
不同调用方使用，但必须出自同一列同一时钟——所以这里钉**实现无关**的不变量：

1. 空 run / 未知 run：两个读面都是全零（三实现同形）；
2. 有重排的 run：`schedule.due` 永远等于 `due_retry_task_ids` 的长度，且
   `scheduled + due` 等于重排条数（**只在两个持久化实现上钉**：见下）；
3. `next_retry_at` 只在真有一条未到期重排时存在。

为什么第 2 条不含 Fake：Fake 没有任何写入 `RETRY_SCHEDULED` 的路径（`complete` 只记
完成），所以它的两个读面永远只能回答"没有重排"——这与 `due_retry_task_ids` 的既有
边界一致，本文件用单独的用例把这条限制钉成显式事实，而不是让它隐身。

具体 deadline 数字由各实现自己的测试钉：SQLite 用注入时钟
（tests/adapters/sqlite/test_workflow_retry_schedule.py），PG 同样注入
（tests/postgres/test_workflow_retry_schedule_pg.py）。
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.ports.workflow_engine import (
    RetrySchedule,
    TaskCompletion,
    WorkflowEngine,
)
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])
_PERSISTENT_FACTORIES: list[Callable[[], object]] = [
    factory for factory in _FACTORIES if factory is not FakeWorkflowEngine
]
RUN_ID = "5b1f2a90-7c3d-4e58-9b16-0a4d8e2c6f37"


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(RUN_ID),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=f"task-{ID.generate().value}",
    )


def _contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id="retry-schedule-contract",
        version="1.0",
        purpose="two read faces, one judgement",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _rescheduled(engine: WorkflowEngine, task: ResearchTask, *, backoff: int | None) -> None:
    engine.submit(task, _contract(backoff=backoff))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value, outcome="FAILED", failure_category=FailureCategory.MODEL_TIMEOUT
        ),
    )


@pytest.mark.parametrize("factory", _FACTORIES)
def test_an_empty_run_has_no_retry_face_at_all(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_task(), _contract(backoff=600))

    assert engine.retry_schedule(RUN_ID) == RetrySchedule()
    assert engine.due_retry_task_ids(RUN_ID) == ()
    assert engine.retry_schedule(ID.generate().value) == RetrySchedule(), "未知 run 与空 run 同形"


@pytest.mark.parametrize("factory", _PERSISTENT_FACTORIES)
def test_the_two_read_faces_always_agree(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _task()
    _rescheduled(engine, task, backoff=600)

    schedule = engine.retry_schedule(RUN_ID)

    assert schedule.scheduled + schedule.due == 1, "重排就该恰好算一条"
    assert (schedule.next_retry_at is not None) is (schedule.scheduled > 0)
    assert len(engine.due_retry_task_ids(RUN_ID)) == schedule.due, "调度器与读面同一判据"


@pytest.mark.parametrize("factory", _PERSISTENT_FACTORIES)
def test_an_immediate_retry_is_due_on_both_persistent_implementations(
    factory: Callable[[], object],
) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    _rescheduled(engine, _task(), backoff=None)

    schedule = engine.retry_schedule(RUN_ID)

    assert schedule.scheduled == 0 and schedule.next_retry_at is None
    assert schedule.due == 1, "没声明退避 ⇒ 立即可以再交付"
    assert len(engine.due_retry_task_ids(RUN_ID)) == schedule.due


def test_the_fake_never_reports_a_retry_it_cannot_write() -> None:
    """Fake 没有写 `RETRY_SCHEDULED` 的路径 ⇒ 两个读面都只能说"没有重排"。

    这是既有边界（与 `due_retry_task_ids` 同源），钉在这里是为了让它显式：看到 Fake
    上读面全零时，那不是"没有重排"，而是"Fake 不会产生重排"。
    """
    engine: WorkflowEngine = FakeWorkflowEngine()  # type: ignore[assignment]
    _rescheduled(engine, _task(), backoff=600)

    assert engine.retry_schedule(RUN_ID) == RetrySchedule()
    assert engine.due_retry_task_ids(RUN_ID) == ()
