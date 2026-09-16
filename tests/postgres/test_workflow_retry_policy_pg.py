"""Postgres parity for the retry policy (GOAL-003 cycle 15 / PLAN-20260915-078).

同一 Port 的两个实现对同一场景必须给出同一结论：`TaskContract.retry_policy` 在
SQLite 侧被真正消费之后，PG 侧必须一致（可重试 ⇒ RETRY_SCHEDULED 且能再被 claim；
次数用尽 ⇒ DEAD_LETTER）。判据与 `tests/adapters/sqlite/test_workflow_retry_policy.py`
逐条对应——这是"两个 adapter 同一语义"的证据，不是另写一套断言。

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


def _contract(max_attempts: int, *categories: FailureCategory) -> TaskContract:
    return TaskContract(
        id="retry-contract",
        version="1.0",
        purpose="retry semantics",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(max_attempts=max_attempts, retryable_categories=list(categories)),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _attempt(engine: PostgresWorkflowEngine, task: ResearchTask) -> int:
    row = next(r for r in engine.list_tasks(task.run_id.value) if r.task.id.value == task.id.value)
    return int(row.task.attempt)


def _fail(engine: PostgresWorkflowEngine, task: ResearchTask, category: FailureCategory) -> None:
    lease = engine.claim_next(_request())
    assert lease is not None
    engine.complete(
        lease,
        TaskCompletion(task_id=task.id.value, outcome="FAILED", failure_category=category),
    )


def test_pg_reschedules_a_retryable_failure_like_sqlite() -> None:
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, FailureCategory.MODEL_TIMEOUT)

    rows = engine.list_tasks(task.run_id.value)
    assert rows[0].task.status == ResearchTaskState.State.RETRY_SCHEDULED
    assert _attempt(engine, task) == 1, "attempt 计已开始的尝试：这次已经跑完"
    assert EventType.TASK_RETRY_SCHEDULED in [e.event_type for e in engine.pending_outbox()]
    lease = engine.claim_next(_request())
    assert lease is not None and lease.task_id == task.id.value
    assert _attempt(engine, task) == 2, "再次 claim = 第二次尝试开始"


def test_pg_dead_letters_an_exhausted_retry_like_sqlite() -> None:
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(2, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, FailureCategory.MODEL_TIMEOUT)
    _fail(engine, task, FailureCategory.MODEL_TIMEOUT)

    rows = engine.list_tasks(task.run_id.value)
    assert rows[0].task.status == ResearchTaskState.State.DEAD_LETTER
    assert _attempt(engine, task) == 2
    assert engine.claim_next(_request()) is None, "死信任务不该再被派发"
