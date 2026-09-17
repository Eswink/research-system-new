"""Postgres parity: `retry_schedule` 与 SQLite/Fake 同判据、同时钟源（GOAL-004 cycle 2）。

与 `tests/adapters/sqlite/test_workflow_retry_schedule.py` 逐条对应：deadline 之前算
`scheduled`（并回带那条期限），推过 deadline 才算 `due`；没有 deadline 的立即重排是
`due`；计数按 run 回答，未知 run 全零。

差别只在时钟来源——PG 的 deadline 写入与分类都走 `server_now`（生产=数据库时钟、
测试=注入时钟），所以这里同样是注入固定时钟、不推进墙钟。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
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

pytestmark = pytest.mark.postgres

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


@pytest.fixture(autouse=True, scope="function")
def _clean_postgres() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def _engine(*, now: datetime = START) -> PostgresWorkflowEngine:
    return PostgresWorkflowEngine(dsn=_dsn(), now=lambda: now)


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


def _rescheduled(
    engine: PostgresWorkflowEngine, task: ResearchTask, *, backoff: int | None
) -> None:
    engine.submit(task, _contract(backoff=backoff))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value, outcome="FAILED", failure_category=FailureCategory.MODEL_TIMEOUT
        ),
    )


def test_pg_a_waiting_retry_reports_its_deadline() -> None:
    run_id = ID.generate()
    _rescheduled(_engine(), _task(run_id), backoff=600)

    assert _engine().retry_schedule(run_id.value) == RetrySchedule(
        scheduled=1, due=0, next_retry_at=Timestamp(START + timedelta(seconds=600))
    )
    assert _engine().due_retry_task_ids(run_id.value) == (), "还在等时钟 ⇒ 不是 due"


def test_pg_passing_the_deadline_moves_it_from_scheduled_to_due() -> None:
    run_id = ID.generate()
    _rescheduled(_engine(), _task(run_id), backoff=600)

    just_before = START + timedelta(seconds=599)
    assert _engine(now=just_before).retry_schedule(run_id.value) == RetrySchedule(
        scheduled=1, due=0, next_retry_at=Timestamp(START + timedelta(seconds=600))
    )

    at_deadline = START + timedelta(seconds=600)
    at_face = _engine(now=at_deadline)
    assert at_face.retry_schedule(run_id.value) == RetrySchedule(scheduled=0, due=1)
    assert at_face.due_retry_task_ids(run_id.value) != (), "同一时刻两个读面必须同判"


def test_pg_an_immediate_retry_is_due_without_a_deadline() -> None:
    run_id = ID.generate()
    _rescheduled(_engine(), _task(run_id), backoff=None)

    assert _engine().retry_schedule(run_id.value) == RetrySchedule(scheduled=0, due=1)


def test_pg_the_read_face_counts_both_kinds_at_once() -> None:
    run_id = ID.generate()
    engine = _engine()
    _rescheduled(engine, _task(run_id), backoff=600)
    _rescheduled(engine, _task(run_id), backoff=3600)

    schedule = _engine(now=START + timedelta(seconds=600)).retry_schedule(run_id.value)

    assert schedule.scheduled == 1
    assert schedule.due == 1
    assert schedule.next_retry_at == Timestamp(START + timedelta(seconds=3600))


def test_pg_a_run_without_retries_reads_all_zero() -> None:
    run_id = ID.generate()
    engine = _engine()
    engine.submit(_task(run_id), _contract(backoff=600))

    assert engine.retry_schedule(run_id.value) == RetrySchedule()
    assert engine.retry_schedule(ID.generate().value) == RetrySchedule(), "未知 run 全零，不是异常"
