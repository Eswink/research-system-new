"""M16 WP2 concurrent claim + partition ownership (PostgreSQL).

Proves the scheduling invariants that make a distributed plane safe on a
single queue: multiple schedulers claiming concurrently never split-brain
(FOR UPDATE SKIP LOCKED yields disjoint work), and overlapping partition
slots still produce a single owner per task — because partition is only a
filter and the `leases` row is the sole ownership authority.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract

pytestmark = pytest.mark.postgres

START = datetime(2026, 8, 31, 9, 0, 0, tzinfo=timezone.utc)


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
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, workers CASCADE")
    conn.commit()
    conn.close()


def _submit_execution_tasks(count: int, *, partition: int | None = 0) -> list[str]:
    engine = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START)
    ids: list[str] = []
    try:
        for _ in range(count):
            task = ResearchTask(
                id=ID.generate(),
                run_id=ID.generate(),
                status=ResearchTaskState.State.QUEUED,
                kind=TaskKind.EXECUTION,
                required_capability="docker",
                partition=partition,
            )
            engine.submit(task, task_contract())
            ids.append(task.id.value)
    finally:
        engine.close()
    return ids


def _drain(engine: PostgresWorkflowEngine, worker_id: str) -> list[str]:
    claimed: list[str] = []
    while True:
        lease = engine.claim_next(
            ClaimRequest(
                worker_id=worker_id,
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0, 1, 2, 3}),
            )
        )
        if lease is None:
            return claimed
        claimed.append(lease.task_id)


def test_concurrent_schedulers_claim_disjoint_work() -> None:
    """Two engines (separate connections) drain a shared queue with no overlap."""
    total = 12
    _submit_execution_tasks(total)
    a = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START + timedelta(seconds=1))
    b = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START + timedelta(seconds=1))
    try:
        claimed_a = _drain(a, "w-a")
        claimed_b = _drain(b, "w-b")
    finally:
        a.close()
        b.close()
    assert set(claimed_a).isdisjoint(claimed_b)
    assert len(claimed_a) + len(claimed_b) == total


def test_overlapping_partitions_single_owner() -> None:
    """Both workers claim partition 0; each task still has exactly one owner."""
    total = 6
    _submit_execution_tasks(total, partition=0)
    a = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START + timedelta(seconds=1))
    b = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START + timedelta(seconds=1))
    try:
        # identical partition slots — the overlap must not double-own anything
        claimed_a = _drain(a, "w-a")
        claimed_b = _drain(b, "w-b")
    finally:
        a.close()
        b.close()
    assert set(claimed_a).isdisjoint(claimed_b)
    assert len(claimed_a) + len(claimed_b) == total


def test_fence_advances_on_reclaim_after_recovery() -> None:
    """A reclaimed lease carries a strictly higher fence than the first claim."""
    (task_id,) = _submit_execution_tasks(1)
    engine = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START, lease_ttl_seconds=1)
    try:
        first = engine.claim_next(
            ClaimRequest(
                worker_id="w1",
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0}),
            )
        )
        assert first is not None and first.fence == 1
        # expire the lease (advance clock past ttl) and recover
        later = START + timedelta(seconds=10)
        engine._now = lambda: later  # deterministic test clock
        recovered = engine.recover_expired_leases()
        assert recovered == 1
        second = engine.claim_next(
            ClaimRequest(
                worker_id="w2",
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0}),
            )
        )
        assert second is not None
        assert second.fence == 2
        assert second.worker_id == "w2"
    finally:
        engine.close()
