"""Postgres parity: acquire 也守退避 deadline（GOAL-003 cycle 17 / PLAN-20260915-080）。

与 `tests/adapters/sqlite/test_workflow_acquire_backoff.py` 逐条对应。差别只在时钟来源：
PG 的 deadline 比较用 `server_now`（生产=数据库时钟、测试=注入时钟），deadline 的写入
（cycle 16）也来自同一个源——这里把"未到期拒绝 / 到期放行"钉住。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

pytestmark = pytest.mark.postgres

START = datetime(2026, 9, 17, 9, 0, 0, tzinfo=timezone.utc)


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


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        required_capability="workspace.read",
    )


def _contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id="acquire-backoff-contract",
        version="1.0",
        purpose="acquire must respect the retry deadline",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _rescheduled(*, backoff: int | None, engine: PostgresWorkflowEngine) -> ResearchTask:
    task = _task()
    engine.submit(task, _contract(backoff=backoff))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    return task


def test_pg_acquire_refuses_a_task_that_is_still_waiting_for_its_backoff() -> None:
    engine = _engine()
    task = _rescheduled(backoff=600, engine=engine)

    with pytest.raises(InvalidInputError, match="waiting for its retry backoff"):
        engine.acquire_lease(task.id.value)

    later = _engine(now=START.replace(hour=10))
    lease = later.acquire_lease(task.id.value)

    assert lease.fence == 2, "到期后（注入时钟推过 deadline）是可租的第二次交付"


def test_pg_acquire_without_a_declared_backoff_is_unchanged() -> None:
    engine = _engine()
    task = _rescheduled(backoff=None, engine=engine)

    lease = engine.acquire_lease(task.id.value)

    assert lease.fence == 2
