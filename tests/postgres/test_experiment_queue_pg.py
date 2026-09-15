"""PostgresExperimentStore 队列语义（G14）——与 SQLite 实现同一契约矩阵。

覆盖：条目往返、认领原子性（SKIP LOCKED 单赢家）、到期顺序、认领过期重认领、
取消/改期只作用于 QUEUED、计划列表。真实 PG（canonical state）跑，不用替身。
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.experiment_store import PostgresExperimentStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry, QueueProtocolSource
from packages.domain.experiment_state import ExperimentPlanState, ExperimentQueueState
from packages.domain.experiments import ExperimentPlan

pytestmark = pytest.mark.postgres

NOW = Timestamp(datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc))
TTL = 300.0


def _at(offset_seconds: float) -> Timestamp:
    return Timestamp(NOW.value + timedelta(seconds=offset_seconds))


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


@pytest.fixture
def store() -> Generator[PostgresExperimentStore, None, None]:
    migrate(_dsn())
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE experiment_plans, experiment_runs, reproducibility_audits")
    conn.execute("TRUNCATE experiment_queue")
    conn.commit()
    conn.close()
    s = PostgresExperimentStore(dsn=_dsn())
    yield s
    s.close()


def _plan(store: PostgresExperimentStore, *, archived: bool = False) -> ExperimentPlan:
    plan = ExperimentPlan(id=ID.generate(), name="queue-bench").transition(
        ExperimentPlanState.Transition.PREREGISTER
    )
    if archived:
        plan = plan.transition(ExperimentPlanState.Transition.ARCHIVE)
    store.save_plan(plan)
    return plan


def _entry(
    plan: ExperimentPlan,
    *,
    not_before: Timestamp | None = None,
    project_id: str = f"proj-{uuid.uuid4().hex[:8]}",
    created_at: Timestamp = NOW,
) -> ExperimentQueueEntry:
    return ExperimentQueueEntry(
        id=ID.generate(),
        project_id=project_id,
        plan_id=plan.id,
        source=QueueProtocolSource(draft_id="draft-1", draft_revision=2),
        not_before=not_before,
        created_at=created_at,
        updated_at=created_at,
    )


def test_queue_entry_roundtrip_preserves_draft_source(
    store: PostgresExperimentStore,
) -> None:
    plan = _plan(store)
    entry = _entry(plan, not_before=_at(3600))
    store.save_queue_entry(entry)
    loaded = store.get_queue_entry(entry.id.value)
    assert loaded == entry
    assert loaded.source.draft_ref == ("draft-1", 2)


def test_unknown_entry_raises_invalid_input(store: PostgresExperimentStore) -> None:
    with pytest.raises(InvalidInputError):
        store.get_queue_entry("nope")
    with pytest.raises(InvalidInputError):
        store.reschedule_queue_entry("nope", not_before=None, now=NOW)


def test_claim_none_when_not_due_then_claimed_once(
    store: PostgresExperimentStore,
) -> None:
    plan = _plan(store)
    scheduled = _entry(plan, not_before=_at(3600))
    store.save_queue_entry(scheduled)
    assert store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL) is None
    due = _entry(plan)
    store.save_queue_entry(due)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None
    assert claimed.state == ExperimentQueueState.State.DISPATCHING
    assert claimed.claimed_at == NOW
    assert store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL) is None


def test_expired_claim_is_requeued_then_reclaimed(store: PostgresExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert store.claim_due_entry(now=_at(TTL - 1), claim_ttl_seconds=TTL) is None
    reclaimed = store.claim_due_entry(now=_at(TTL + 1), claim_ttl_seconds=TTL)
    assert reclaimed is not None
    assert reclaimed.id == entry.id
    assert reclaimed.claimed_at == _at(TTL + 1)


def test_cancel_and_reschedule_only_apply_to_queued(
    store: PostgresExperimentStore,
) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    moved = store.reschedule_queue_entry(entry.id.value, not_before=_at(60), now=NOW)
    assert moved.not_before == _at(60)
    store.claim_due_entry(now=_at(120), claim_ttl_seconds=TTL)
    with pytest.raises(InvalidInputError):
        store.cancel_queue_entry(entry.id.value, now=NOW)
    with pytest.raises(InvalidInputError):
        store.reschedule_queue_entry(entry.id.value, not_before=None, now=NOW)


def test_dispatch_then_list_is_project_scoped(store: PostgresExperimentStore) -> None:
    plan = _plan(store)
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    first = _entry(plan, project_id=project_id, created_at=_at(1))
    second = _entry(plan, project_id=project_id, created_at=_at(2))
    foreign = _entry(plan, created_at=_at(3))
    for entry in (second, first, foreign):
        store.save_queue_entry(entry)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None and claimed.id == first.id
    store.save_queue_entry(claimed.mark_dispatched("run-99"))
    listed = store.list_queue_entries(project_id)
    assert [entry.id for entry in listed] == [first.id, second.id]
    assert listed[0].state == ExperimentQueueState.State.DISPATCHED
    assert listed[0].run_id == "run-99"


def test_list_plans_by_state(store: PostgresExperimentStore) -> None:
    active = _plan(store)
    archived = _plan(store, archived=True)
    preregistered = ExperimentPlanState.State.PREREGISTERED
    archived_state = ExperimentPlanState.State.ARCHIVED
    active_ids = {plan.id for plan in store.list_plans(state=preregistered)}
    archived_ids = {plan.id for plan in store.list_plans(state=archived_state)}
    assert active.id in active_ids
    assert archived.id in archived_ids
    assert archived.id not in active_ids
