"""Postgres integration: engine unit tests against live DB.

Skipped automatically if PostgreSQL is not reachable (see tests/postgres/conftest.py).
Reuses the same fixture shapes as tests/adapters/sqlite/test_workflow_engine.py
but boots a project-scoped DSN (one DB per pytest session).

Each test truncates tables for isolation (no per-test DB creation).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from tests.contracts.fixtures import research_task, task_contract

pytestmark = pytest.mark.postgres


START = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


def _truncate(conn: object) -> None:
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")  # type: ignore[attr-defined]
    conn.commit()  # type: ignore[attr-defined]


@pytest.fixture(autouse=True, scope="function")
def _clean_postgres() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    _truncate(conn)
    conn.close()


class TestSubmitIdempotencyPg:
    def test_duplicate_submit_same_task_is_silent(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        try:
            task = research_task()
            engine.submit(task, task_contract())
            engine.submit(task, task_contract("other"))
            rows = engine.list_tasks(task.run_id.value)
            assert len(rows) == 1
            assert engine.calls[-1].result_summary == "deduped"
        finally:
            engine.close()

    def test_duplicate_submit_same_idempotency_key_is_silent(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        try:
            engine.submit(research_task(), task_contract())
            other = research_task()
            engine.submit(other, task_contract())
            rows = engine.list_tasks(other.run_id.value)
            assert len(rows) == 1
        finally:
            engine.close()


class TestLeaseLifecyclePg:
    def test_acquire_lease_is_deduped(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        try:
            task = research_task()
            engine.submit(task, task_contract())
            first = engine.acquire_lease(task.id.value)
            second = engine.acquire_lease(task.id.value)
            assert second.lease_id == first.lease_id
            assert engine.calls[-1].result_summary == "deduped"
        finally:
            engine.close()

    def test_heartbeat_renews_expiry(self) -> None:
        clock = {"now": START}
        engine = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"])
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            assert lease.expires_at is not None
            initial = lease.expires_at.value
            clock["now"] = START + timedelta(seconds=10)
            renewed = engine.heartbeat(lease)
            assert renewed.expires_at is not None
            assert renewed.expires_at.value > initial
            assert renewed.lease_id != lease.lease_id
        finally:
            engine.close()

    def test_complete_is_idempotent_after_success(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
            engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="FAILED"))
            assert engine.calls[-1].result_summary == "deduped"
            (row,) = engine.list_tasks(task.run_id.value)
            assert row.task.status == ResearchTaskState.State.SUCCEEDED
        finally:
            engine.close()

    def test_lease_expires_and_recovers(self) -> None:
        clock = {"now": START}
        engine = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"])
        try:
            task = research_task()
            engine.submit(task, task_contract())
            engine.acquire_lease(task.id.value)
            clock["now"] = START + timedelta(seconds=120)
            recovered = engine.recover_expired_leases()
            assert recovered == 1
            (row,) = engine.list_tasks(task.run_id.value)
            assert row.task.status == ResearchTaskState.State.QUEUED
        finally:
            engine.close()


class TestOutboxPg:
    def test_cancel_writes_cancelled_event(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        try:
            task = research_task()
            engine.submit(task, task_contract())
            engine.cancel(task.id.value)
            kinds = [e.event_type for e in engine.pending_outbox()]
            assert EventType.TASK_CANCELLED in kinds
        finally:
            engine.close()

    def test_recovery_writes_retry_event(self) -> None:
        clock = {"now": START}
        engine = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"])
        try:
            task = research_task()
            engine.submit(task, task_contract())
            engine.acquire_lease(task.id.value)
            clock["now"] = START + timedelta(seconds=120)
            engine.recover_expired_leases()
            kinds = [e.event_type for e in engine.pending_outbox()]
            assert EventType.TASK_RETRY_SCHEDULED in kinds
        finally:
            engine.close()
