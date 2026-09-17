"""读面：`retry_schedule` 回答"还得等多久、现在能不能走"（GOAL-004 cycle 2 = EC-02）。

`due_retry_task_ids` 给调度器 ids；这一句给运维读面计数与最近期限。两者必须同一判据、
同一个时钟源，所以这里钉住：

1. deadline 之前是 `scheduled`（并带上那条期限），推过 deadline 才是 `due`；
2. 没有 deadline 的立即重排算 `due`（与 claim 候选扫描同义）；
3. 计数按 run 回答（另一个 run 的重排不串台），未知 run 是全零而不是异常；
4. 两个读面不会各说各话：`due` 永远等于 `due_retry_task_ids` 的长度。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import RetrySchedule, TaskCompletion
from packages.domain.core import ID, Timestamp
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)


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


def _contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id="retry-schedule-contract",
        version="1.0",
        purpose="the read face knows what the dispatcher knows",
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


def test_a_waiting_retry_reports_its_deadline() -> None:
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=clock)
    run_id = ID.generate()
    _rescheduled(engine, _task(run_id), backoff=600)

    assert engine.retry_schedule(run_id.value) == RetrySchedule(
        scheduled=1, due=0, next_retry_at=Timestamp(START + timedelta(seconds=600))
    )
    assert engine.due_retry_task_ids(run_id.value) == (), "还在等时钟 ⇒ 不是 due"
    engine.close()


def test_passing_the_deadline_moves_it_from_scheduled_to_due() -> None:
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=clock)
    run_id = ID.generate()
    _rescheduled(engine, _task(run_id), backoff=600)

    clock.value = START + timedelta(seconds=599)
    assert engine.retry_schedule(run_id.value).scheduled == 1, "差一秒就还在 scheduled"

    clock.value = START + timedelta(seconds=600)
    assert engine.retry_schedule(run_id.value) == RetrySchedule(scheduled=0, due=1)
    assert engine.due_retry_task_ids(run_id.value) != (), "同一时刻两个读面必须同判"
    engine.close()


def test_an_immediate_retry_is_due_without_a_deadline() -> None:
    """没声明退避 ⇒ 重排即刻可交付（与 claim 候选扫描、Fake 同义）。"""
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=_Clock())
    run_id = ID.generate()
    _rescheduled(engine, _task(run_id), backoff=None)

    assert engine.retry_schedule(run_id.value) == RetrySchedule(scheduled=0, due=1)
    engine.close()


def test_the_read_face_counts_both_kinds_at_once() -> None:
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=clock)
    run_id = ID.generate()
    _rescheduled(engine, _task(run_id), backoff=600)
    _rescheduled(engine, _task(run_id), backoff=3600)

    clock.value = START + timedelta(seconds=600)
    schedule = engine.retry_schedule(run_id.value)

    assert schedule.scheduled == 1, "还有一条在等更晚的期限"
    assert schedule.due == 1
    assert schedule.next_retry_at == Timestamp(START + timedelta(seconds=3600)), "最近一条未到期"
    assert len(engine.due_retry_task_ids(run_id.value)) == schedule.due, "两个读面同判"
    engine.close()


def test_a_run_without_retries_reads_all_zero() -> None:
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=_Clock())
    run_id = ID.generate()
    engine.submit(_task(run_id), _contract(backoff=600))

    assert engine.retry_schedule(run_id.value) == RetrySchedule()
    assert engine.retry_schedule(ID.generate().value) == RetrySchedule(), "未知 run 全零，不是异常"
    engine.close()


def test_the_read_face_is_per_run() -> None:
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=_Clock())
    mine, other = ID.generate(), ID.generate()
    _rescheduled(engine, _task(mine), backoff=600)
    _rescheduled(engine, _task(other), backoff=None)

    assert engine.retry_schedule(mine.value) == RetrySchedule(
        scheduled=1, due=0, next_retry_at=Timestamp(START + timedelta(seconds=600))
    )
    assert engine.retry_schedule(other.value) == RetrySchedule(scheduled=0, due=1)
    engine.close()
