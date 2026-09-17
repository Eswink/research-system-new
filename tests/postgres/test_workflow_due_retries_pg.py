"""Postgres parity: `due_retry_task_ids` 与 SQLite 同判据、同时钟源（GOAL-003 cycle 19）。

与 `tests/adapters/sqlite/test_workflow_due_retries.py` 逐条对应。差别只在时钟来源：
PG 的比较用 `server_now`（生产=数据库时钟、测试=注入时钟），deadline 的写入（cycle 16）
也来自同一个源——这里把"未到期不是 due / 到期才是 due / 无重排永远不是 due"钉住。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
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

pytestmark = pytest.mark.postgres

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)
BACKOFF_SECONDS = 600


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


def test_pg_a_retry_is_due_only_after_its_deadline() -> None:
    run_id = ID.generate()
    task = _task(run_id)
    _rescheduled(_engine(), task, backoff=BACKOFF_SECONDS)

    assert _engine().due_retry_task_ids(run_id.value) == (), "deadline 未到 ⇒ 不是 due"

    later = START.replace(hour=10)  # START + 3600s > 600s 退避
    assert _engine(now=later).due_retry_task_ids(run_id.value) == (task.id.value,)


def test_pg_tasks_without_a_scheduled_retry_are_never_reported() -> None:
    run_id = ID.generate()
    engine = _engine()
    queued = _task(run_id)
    engine.submit(queued, _contract())

    assert engine.due_retry_task_ids(run_id.value) == ()
    assert engine.due_retry_task_ids(ID.generate().value) == (), "未知 run 是空，不是异常"
