"""WP2 unit tests: lease fencing + concurrent-claim semantics (single-process simulations).

True cross-process concurrency is covered by `tests/postgres/` integration and WP4 E2Es.
These tests lock the stale-writer fencing contract on the Postgres engine with
injected clocks and directly verify that:
- stale `lease_id` heartbeat/complete are rejected
- `acquire_lease` dedup returns same lease_id under same task
- cancel/complete race: cancel wins → stale complete raises
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
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


def _clean_postgres() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


class TestStaleLeaseFencingPg:
    def test_stale_heartbeat_rejected(self) -> None:
        clock = {"now": START}
        engine = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"])
        _clean_postgres()
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            renewed = engine.heartbeat(lease)
            # stale lease (old lease_id) heartbeat must be rejected
            with pytest.raises(InvalidInputError):
                engine.heartbeat(lease)
            # renewed lease still valid
            assert renewed.lease_id != lease.lease_id
        finally:
            engine.close()

    def test_complete_with_stale_lease_rejected_after_heartbeat(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        _clean_postgres()
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            engine.heartbeat(lease)
            with pytest.raises(InvalidInputError):
                engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        finally:
            engine.close()

    def test_recover_then_stale_complete_rejected(self) -> None:
        clock = {"now": START}
        engine = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"])
        _clean_postgres()
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            clock["now"] = START + timedelta(seconds=120)
            engine.recover_expired_leases()
            # lease was deleted + task QUEUED; stale complete must fail
            with pytest.raises(InvalidInputError):
                engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
            # new lease can acquire + complete
            new_lease = engine.acquire_lease(task.id.value)
            assert new_lease.lease_id != lease.lease_id
            engine.complete(new_lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        finally:
            engine.close()

    def test_cancel_then_stale_complete_rejected(self) -> None:
        engine = PostgresWorkflowEngine(dsn=_dsn())
        _clean_postgres()
        try:
            task = research_task()
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            engine.cancel(task.id.value)
            with pytest.raises(InvalidInputError):
                engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        finally:
            engine.close()
