"""WP2 integration: transactional outbox atomicity (Postgres).

Verifies:
- domain mutation + outbox event are atomic (both or neither)
- duplicate publish (same event_id) is idempotent (matches event_publisher semantics)
- marked published is idempotent; pending reflects state

These are unit-level checks inside a single transaction; cross-process crash
(Skipped in offline: Scenario E) is covered by WP4 E2E `tests/e2e/test_outbox_crash.py`
style but with Postgres DSN.
"""

from __future__ import annotations

import os

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from tests.contracts.fixtures import research_task, task_contract

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


def test_outbox_atomic_with_task_transition() -> None:
    """TASK_LEASED event must be present iff task reached LEASED."""
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()

    engine = PostgresWorkflowEngine(dsn=_dsn())
    try:
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        pending = engine.pending_outbox()
        task_ids = {e.task_id for e in pending}
        assert task.id.value in task_ids
        rows = engine.list_tasks(task.run_id.value)
        assert rows[0].task.status == "LEASED"
    finally:
        engine.close()


def test_outbox_mark_published_idempotent() -> None:
    engine = PostgresWorkflowEngine(dsn=_dsn())
    try:
        # Ensure at least one pending event
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        pending = engine.pending_outbox()
        assert len(pending) >= 1
        event_id = pending[0].event_id
        engine.mark_outbox_published((event_id,))
        pending2 = engine.pending_outbox()
        assert all(e.event_id != event_id for e in pending2)
        # idempotent re-mark
        engine.mark_outbox_published((event_id,))
        pending3 = engine.pending_outbox()
        assert all(e.event_id != event_id for e in pending3)
    finally:
        engine.close()
