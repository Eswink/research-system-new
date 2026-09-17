"""读面：`due_retry_task_ids` 只回答"这个 run 现在有没有可以再交付的重排"。

GOAL-003 cycle 19：调度器靠这一句判断停车中的 run 能不能续跑。判定必须与 claim 候选
扫描同一判据、同一个时钟源——所以这里钉住三件事：

1. deadline 之前**不是** due；推过 deadline 之后才是（注入时钟，非墙钟）；
2. 没有重排的任务（首次排队/成功/已死信）永远不在结果里；
3. 只回答本 run 的任务（另一个 run 的重排不串台）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)
BACKOFF_SECONDS = 600


class _Clock:
    def __init__(self, value: datetime = START) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def _task(run_id: ID) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=f"task-{ID.generate().value}",
    )


def _contract(*, backoff: int | None = BACKOFF_SECONDS) -> TaskContract:
    return TaskContract(
        id="due-retry-contract",
        version="1.0",
        purpose="due retries are readable per run",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _rescheduled(engine: SqliteWorkflowEngine, task: ResearchTask, *, backoff: int | None) -> None:
    engine.submit(task, _contract(backoff=backoff))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value, outcome="FAILED", failure_category=FailureCategory.MODEL_TIMEOUT
        ),
    )


def test_a_retry_is_due_only_after_its_deadline() -> None:
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=clock)
    run_id = ID.generate()
    task = _task(run_id)
    _rescheduled(engine, task, backoff=BACKOFF_SECONDS)

    assert engine.due_retry_task_ids(run_id.value) == ()

    clock.value = START + timedelta(seconds=BACKOFF_SECONDS - 1)
    assert engine.due_retry_task_ids(run_id.value) == (), "还差一秒就不是 due"

    clock.value = START + timedelta(seconds=BACKOFF_SECONDS)
    assert engine.due_retry_task_ids(run_id.value) == (task.id.value,)
    engine.close()


def test_tasks_without_a_scheduled_retry_are_never_reported() -> None:
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=_Clock())
    run_id = ID.generate()
    queued = _task(run_id)
    engine.submit(queued, _contract())

    dead = _task(run_id)
    _rescheduled(engine, dead, backoff=None)  # 立即重排，但在进程内会继续尝试
    engine.complete(
        engine.acquire_lease(dead.id.value),
        TaskCompletion(task_id=dead.id.value, outcome="SUCCEEDED"),
    )

    assert engine.due_retry_task_ids(run_id.value) == ()
    engine.close()


def test_the_read_face_is_per_run() -> None:
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=_Clock())
    mine, other = ID.generate(), ID.generate()
    waiting = _task(mine)
    _rescheduled(engine, waiting, backoff=BACKOFF_SECONDS)
    _rescheduled(engine, _task(other), backoff=BACKOFF_SECONDS)

    assert engine.due_retry_task_ids(other.value) == ()
    assert engine.due_retry_task_ids(mine.value) == ()
    assert engine.due_retry_task_ids(ID.generate().value) == (), "未知 run 是空，不是异常"
    engine.close()
