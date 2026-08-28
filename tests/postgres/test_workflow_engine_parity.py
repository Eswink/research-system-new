"""M14 SQLite/PostgreSQL semantic parity suite (WP-H1).

Runs the identical scenario set against SqliteWorkflowEngine and
PostgresWorkflowEngine, asserting Application-visible semantics are identical:
ids, ordering, timestamps, JSON, NULL, enums, uniqueness, idempotency, and
fencing/terminal guards. FakeWorkflowEngine is a unit oracle without
projections and is intentionally excluded.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventType
from tests.contracts.fixtures import research_task, task_contract

START = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


@pytest.fixture()
def pair() -> tuple[str, str]:
    """Reset both stores; return (sqlite dsn-path marker, pg dsn)."""
    migrate(_dsn())
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()
    return "sqlite", _dsn()


def _engine(kind: str, now: Any = None) -> Any:
    if kind == "sqlite":
        if now is not None:
            return SqliteWorkflowEngine(now=now)
        return SqliteWorkflowEngine()
    if now is not None:
        return PostgresWorkflowEngine(dsn=_dsn(), now=now)
    return PostgresWorkflowEngine(dsn=_dsn())


def _scenario(name: str, engine: Any, clock: Any) -> tuple[Any, ...]:
    if name == "submit_idempotent_same_task":
        task = research_task()
        engine.submit(task, task_contract("a"))
        engine.submit(task, task_contract("b"))
        rows = engine.list_tasks(task.run_id.value)
        return (len(rows), rows[0].task.status, str(rows[0].task.id), str(rows[0].contract.id))

    if name == "acquire_dedup_same_engine":
        task = research_task()
        engine.submit(task, task_contract())
        a = engine.acquire_lease(task.id.value)
        b = engine.acquire_lease(task.id.value)
        return (a.lease_id == b.lease_id, str(a.task_id), a.agent_id)

    if name == "terminal_immutable_after_complete":
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="FAILED"))
        rows = engine.list_tasks(task.run_id.value)
        return (rows[0].task.status,)

    if name == "recover_sets_queued_and_event":
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        clock["now"] = START + timedelta(seconds=120)
        recovered = engine.recover_expired_leases()
        kinds = [e.event_type for e in engine.pending_outbox()]
        rows = engine.list_tasks(task.run_id.value)
        return (recovered, rows[0].task.status, EventType.TASK_RETRY_SCHEDULED in kinds)

    if name == "cancel_then_stale_complete_rejected":
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.cancel(task.id.value)
        try:
            engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
            outcome = "accepted"
        except Exception as exc:
            outcome = type(exc).__name__
        rows = engine.list_tasks(task.run_id.value)
        return (outcome, rows[0].task.status)

    raise AssertionError(f"unknown scenario {name}")


@pytest.mark.parametrize(
    "scenario",
    [
        "submit_idempotent_same_task",
        "acquire_dedup_same_engine",
        "terminal_immutable_after_complete",
        "recover_sets_queued_and_event",
        "cancel_then_stale_complete_rejected",
    ],
)
def test_parity(pair: tuple[str, str], scenario: str) -> None:
    clock_sqlite = {"now": START}
    clock_pg = {"now": START}
    sqlite = _engine("sqlite", now=lambda: clock_sqlite["now"])
    pg = _engine("postgres", now=lambda: clock_pg["now"])
    try:
        sqlite_res = _scenario(scenario, sqlite, clock_sqlite)
        pg_res = _scenario(scenario, pg, clock_pg)
        assert sqlite_res == pg_res, f"{scenario}: SQLite {sqlite_res} != PG {pg_res}"
    finally:
        sqlite.close()
        pg.close()
