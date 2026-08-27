"""Cross-process E2E for PostgresWorkflowEngine (M14 WP4 Scenarios).

Each test uses two `psycopg` connections (two processes simulated via
two connections + injected `now`). Real subprocess E2E (two python
processes) is covered by `tests/e2e/test_workflow_restart_recovery.py`
for SQLite and will be extended for PG with `docker compose` when
available. These tests lock the same invariants with two connections.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
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


def _truncate() -> None:
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True, scope="function")
def _clean() -> None:
    migrate(_dsn())
    _truncate()


class TestConcurrentLeaseTwoConnections:
    """Two connections racing to acquire same task — exactly one wins."""

    def test_two_connections_same_task_one_wins(self) -> None:
        import psycopg

        # Shared task in DB
        setup = PostgresWorkflowEngine(dsn=_dsn())
        task = research_task()
        setup.submit(task, task_contract())
        setup.close()

        conn_a = psycopg.connect(_dsn(), autocommit=False)
        conn_b = psycopg.connect(_dsn(), autocommit=False)
        engine_a = PostgresWorkflowEngine(connection=conn_a)
        engine_b = PostgresWorkflowEngine(connection=conn_b)
        try:
            lease_a = engine_a.acquire_lease(task.id.value)
            lease_b = engine_b.acquire_lease(task.id.value)
            # At least one must succeed; the second either dedups to same lease_id
            # or is blocked then returns same. Both should see same lease_id (dedup).
            assert lease_a.lease_id == lease_b.lease_id
            assert lease_a.task_id == task.id.value
        finally:
            engine_a.close()
            engine_b.close()
            conn_a.close()
            conn_b.close()


class TestStaleWriterFencingTwoConnections:
    def test_stale_complete_after_new_lease_rejected(self) -> None:
        import psycopg

        clock = {"now": START}
        conn_setup = psycopg.connect(_dsn(), autocommit=True)
        migrate(_dsn())
        conn_setup.close()

        engine_setup = PostgresWorkflowEngine(
            dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"]
        )
        _truncate()
        task = research_task()
        engine_setup.submit(task, task_contract())
        lease_old = engine_setup.acquire_lease(task.id.value)
        engine_setup.close()

        # Simulate expiry + recovery by second worker
        clock["now"] = START + timedelta(seconds=120)
        engine_b = PostgresWorkflowEngine(
            dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"]
        )
        try:
            recovered = engine_b.recover_expired_leases()
            assert recovered == 1
            lease_new = engine_b.acquire_lease(task.id.value)
            assert lease_new.lease_id != lease_old.lease_id
            # Stale writer (lease_old) must be rejected
            with pytest.raises(InvalidInputError):
                engine_b.complete(
                    lease_old,
                    TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"),
                )
            # New owner can complete
            engine_b.complete(lease_new, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
            rows = engine_b.list_tasks(task.run_id.value)
            assert rows[0].task.status == ResearchTaskState.State.SUCCEEDED
        finally:
            engine_b.close()
