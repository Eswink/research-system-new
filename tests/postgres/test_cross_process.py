"""M14 cross-process E2E for PostgresWorkflowEngine.

True OS-level process isolation is covered by `tests/postgres/test_cross_process_real.py`
(real subprocess workers, real wall-clock TTL, hard kill). This module only keeps
the unit-level invariants that do not require process isolation (submit dedup,
fencing with injected clocks) — all cross-process simulation assertions that
presumed "two connections share one lease" have been removed.

See PLAN-20260828-021 WP-A3/B2/C2/H3 for the real cross-process matrix.
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


class TestConcurrentLeaseOwnerFencing:
    """Same-engine re-acquire is dedup; a foreign engine must be rejected."""

    def test_same_engine_reacquire_is_dedup(self) -> None:
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

    def test_foreign_engine_acquisition_rejected(self) -> None:
        """Different engine instance (different connection) must not receive a live lease."""
        engine_a = PostgresWorkflowEngine(dsn=_dsn())
        engine_b = PostgresWorkflowEngine(dsn=_dsn())
        try:
            task = research_task()
            engine_a.submit(task, task_contract())
            lease_a = engine_a.acquire_lease(task.id.value)
            with pytest.raises(InvalidInputError):
                engine_b.acquire_lease(task.id.value)
            # A still owns the lease; can complete
            engine_a.complete(lease_a, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
            rows = engine_a.list_tasks(task.run_id.value)
            assert rows[0].task.status == ResearchTaskState.State.SUCCEEDED
        finally:
            engine_a.close()
            engine_b.close()


class TestStaleWriterFencing:
    """Stale writer (recovered lease) must be rejected; new owner completes."""

    def test_stale_complete_after_new_lease_rejected(self) -> None:
        clock = {"now": START}
        engine_setup = PostgresWorkflowEngine(
            dsn=_dsn(), lease_ttl_seconds=60, now=lambda: clock["now"]
        )
        _truncate()
        task = research_task()
        engine_setup.submit(task, task_contract())
        lease_old = engine_setup.acquire_lease(task.id.value)
        engine_setup.close()

        # Simulate expiry + recovery by a different engine
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
