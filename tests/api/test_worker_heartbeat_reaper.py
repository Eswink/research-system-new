"""M16 WP1 heartbeat/clock-authority tests.

Covers: WorkerReaperScheduler marking stale workers LOST from server time,
idempotent/out-of-order heartbeat rules, and (PostgreSQL) that a LOST worker's
lease is released through the single `recover_expired_leases` authority.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from adapters.fakes.worker_registry import FakeWorkerRegistry
from packages.domain.workers import WorkerRegistration, WorkerState
from services.api.scheduler import WorkerReaperScheduler


class _Clock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


def _reg(worker_id: str = "w1") -> WorkerRegistration:
    return WorkerRegistration(
        worker_id=worker_id,
        protocol_version="1",
        runtime_version="0.1.0",
        capabilities=frozenset({"docker"}),
        backend_kinds=frozenset({"DOCKER"}),
        platform="linux/amd64",
        partition_slots=frozenset({0}),
        max_concurrency=1,
    )


def test_reaper_marks_stale_worker_lost() -> None:
    clock = _Clock(datetime(2026, 1, 1, tzinfo=timezone.utc))
    registry = FakeWorkerRegistry(now=clock)
    registry.register(_reg())
    registry.transition("w1", WorkerState.Transition.HANDSHAKE_OK)
    reaper = WorkerReaperScheduler(registry, stale_threshold_seconds=30.0, interval_seconds=15.0)
    # fresh: not stale
    assert reaper.run_once() == 0
    clock.advance(31)
    assert reaper.run_once() == 1
    lost = registry.get("w1")
    assert lost is not None
    assert lost.state == WorkerState.State.LOST


def test_reaper_ignores_offline_workers() -> None:
    clock = _Clock(datetime(2026, 1, 1, tzinfo=timezone.utc))
    registry = FakeWorkerRegistry(now=clock)
    registry.register(_reg())
    registry.transition("w1", WorkerState.Transition.HANDSHAKE_OK)
    registry.drain("w1")
    registry.transition("w1", WorkerState.Transition.OWNED_WORK_SETTLED)  # OFFLINE
    clock.advance(1000)
    reaper = WorkerReaperScheduler(registry, stale_threshold_seconds=30.0)
    assert reaper.run_once() == 0  # terminal OFFLINE is never reaped


def test_heartbeat_idempotent_does_not_roll_back_clock() -> None:
    clock = _Clock(datetime(2026, 1, 1, tzinfo=timezone.utc))
    registry = FakeWorkerRegistry(now=clock)
    stored = registry.register(_reg())
    gen = stored.registration_generation
    assert registry.heartbeat("w1", gen) is True
    first_hb = registry.get("w1")
    assert first_hb is not None
    first = first_hb.last_heartbeat
    clock.advance(10)
    assert registry.heartbeat("w1", gen) is True
    second_hb = registry.get("w1")
    assert second_hb is not None
    second = second_hb.last_heartbeat
    assert first is not None and second is not None
    assert second.value >= first.value  # never rolls back


def test_out_of_order_heartbeat_rejected_after_reregister() -> None:
    clock = _Clock(datetime(2026, 1, 1, tzinfo=timezone.utc))
    registry = FakeWorkerRegistry(now=clock)
    first = registry.register(_reg())
    registry.register(_reg())  # generation 2
    # old-generation heartbeat fails closed and does not touch last_heartbeat
    before_hb = registry.get("w1")
    assert before_hb is not None
    before = before_hb.last_heartbeat
    assert registry.heartbeat("w1", first.registration_generation) is False
    after_hb = registry.get("w1")
    assert after_hb is not None
    assert after_hb.last_heartbeat == before


def test_reaper_rejects_bad_intervals() -> None:
    registry = FakeWorkerRegistry()
    with pytest.raises(ValueError):
        WorkerReaperScheduler(registry, interval_seconds=0)
    with pytest.raises(ValueError):
        WorkerReaperScheduler(registry, stale_threshold_seconds=0)


@pytest.mark.postgres
def test_lost_worker_lease_released_by_single_recovery_authority() -> None:
    """A LOST worker's lease is reclaimed via recover_expired_leases (M16 §5)."""
    import os

    import psycopg

    from adapters.postgres.db import migrate
    from adapters.postgres.worker_registry import PostgresWorkerRegistry
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine
    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask
    from tests.contracts.fixtures import task_contract

    dsn = os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    try:
        probe = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
        probe.close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")
    migrate(dsn)
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, workers CASCADE")
    conn.commit()
    conn.close()

    registry = PostgresWorkerRegistry(dsn=dsn)
    engine = PostgresWorkflowEngine(dsn=dsn, lease_ttl_seconds=1)
    task = ResearchTask(id=ID.generate(), run_id=ID.generate())
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    # bind the lease to a worker, then mark that worker LOST
    registry.register(_reg("w1"))
    registry.transition("w1", WorkerState.Transition.HANDSHAKE_OK)
    bind = psycopg.connect(dsn, autocommit=True)
    bind.execute("UPDATE leases SET worker_id = 'w1' WHERE task_id = %s", (task.id.value,))
    bind.commit()
    bind.close()
    registry.mark_lost("w1")

    # lease has NOT expired by wall clock (ttl=1 but we just created it);
    # recovery must still release it because the owner is LOST.
    recovered = engine.recover_expired_leases()
    assert recovered >= 1
    assert lease.task_id == task.id.value
    registry.close()
    engine.close()
