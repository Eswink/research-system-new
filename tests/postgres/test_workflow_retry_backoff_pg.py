"""Postgres parity for the retry backoff (GOAL-003 cycle 16 / PLAN-20260915-079).

与 `tests/adapters/sqlite/test_workflow_retry_backoff.py` 逐条对应：声明了退避的重排任务
在 deadline 之前不能被 claim，到点后与首次排队同权；没声明退避的契约立即可 claim。

差别只在**时钟来源**：PG 用数据库时钟（complete 写 `now() + 时延`，claim 与 `now()` 比较），
所以这里不推进假时钟，而是直接把 `retry_at` 挪到过去 / 观察它被写成未来——这样断言的是
"数据库里的事实"，不是测试进程里的时间。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.events import EventType
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


def _engine() -> PostgresWorkflowEngine:
    return PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START)


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _contract(*, backoff_seconds: int | None, max_attempts: int = 5) -> TaskContract:
    return TaskContract(
        id="backoff-contract",
        version="1.0",
        purpose="retry backoff",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff_seconds,
        ),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _fail_once(engine: PostgresWorkflowEngine, task: ResearchTask) -> None:
    lease = engine.claim_next(_request())
    assert lease is not None
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )


def _retry_at(task: ResearchTask) -> datetime | None:
    """库里真实的 deadline（None = 没在等退避）。"""
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    try:
        row = conn.execute(
            "SELECT retry_at FROM tasks WHERE task_id = %s", (task.id.value,)
        ).fetchone()
        assert row is not None
        return row[0] if isinstance(row[0], datetime) else None
    finally:
        conn.close()


def _set_retry_at_in_the_past(task: ResearchTask) -> None:
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    try:
        conn.execute(
            "UPDATE tasks SET retry_at = now() - interval '1 second' WHERE task_id = %s",
            (task.id.value,),
        )
    finally:
        conn.close()


def test_pg_holds_a_rescheduled_task_until_its_deadline() -> None:
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(backoff_seconds=3600))
    _fail_once(engine, task)

    stored = _retry_at(task)
    assert stored is not None and stored > START, f"重排要写下未来的 deadline，实际 {stored}"

    assert engine.claim_next(_request()) is None, "deadline 之前不该被派发"

    _set_retry_at_in_the_past(task)
    lease = engine.claim_next(_request())

    assert lease is not None and lease.task_id == task.id.value, "到点后与首次排队同权"
    assert lease.fence == 2, "第二次交付"


def test_pg_clears_the_deadline_on_hand_out() -> None:
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(backoff_seconds=60))
    _fail_once(engine, task)
    _set_retry_at_in_the_past(task)

    assert engine.claim_next(_request()) is not None

    assert _retry_at(task) is None, "交付即清"


def test_pg_without_backoff_is_still_claimable_immediately() -> None:
    """向后兼容（与 SQLite 逐条对应）：没写退避字段 ⇒ 重排后立即可 claim。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(backoff_seconds=None))
    _fail_once(engine, task)

    assert EventType.TASK_RETRY_SCHEDULED in [e.event_type for e in engine.pending_outbox()]
    lease = engine.claim_next(_request())

    assert lease is not None and lease.task_id == task.id.value
