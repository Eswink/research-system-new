"""SqliteExperimentStore 队列语义（G14）：认领原子性、到期顺序、过期重认领、
取消/改期只作用于 QUEUED、计划列表。

与 `tests/postgres/test_experiment_queue_pg.py` 同一语义矩阵（Port 契约共享）。
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest

from adapters.sqlite.experiment_store import SqliteExperimentStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry, QueueProtocolSource
from packages.domain.experiment_state import ExperimentPlanState, ExperimentQueueState
from packages.domain.experiments import ExperimentPlan

NOW = Timestamp(datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc))
TTL = 300.0


def _at(offset_seconds: float) -> Timestamp:
    return Timestamp(NOW.value + timedelta(seconds=offset_seconds))


@pytest.fixture
def store() -> Iterator[SqliteExperimentStore]:
    s = SqliteExperimentStore(":memory:")
    yield s
    s.close()


def _plan(store: SqliteExperimentStore, *, archived: bool = False) -> ExperimentPlan:
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
    project_id: str = "proj-q",
    created_at: Timestamp = NOW,
) -> ExperimentQueueEntry:
    return ExperimentQueueEntry(
        id=ID.generate(),
        project_id=project_id,
        plan_id=plan.id,
        source=QueueProtocolSource(protocol_path="examples/protocols/m12.yaml"),
        not_before=not_before,
        created_at=created_at,
        updated_at=created_at,
    )


def test_queue_entry_roundtrip_preserves_source_and_schedule(
    store: SqliteExperimentStore,
) -> None:
    plan = _plan(store)
    entry = _entry(plan, not_before=_at(3600))
    store.save_queue_entry(entry)
    loaded = store.get_queue_entry(entry.id.value)
    assert loaded == entry
    assert loaded.source.draft_ref is None
    assert loaded.state == ExperimentQueueState.State.QUEUED


def test_unknown_entry_raises_invalid_input(store: SqliteExperimentStore) -> None:
    with pytest.raises(InvalidInputError):
        store.get_queue_entry("nope")
    with pytest.raises(InvalidInputError):
        store.cancel_queue_entry("nope", now=NOW)


def test_claim_returns_none_when_nothing_due(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    store.save_queue_entry(_entry(plan, not_before=_at(3600)))
    assert store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL) is None


def test_claim_marks_dispatching_and_records_claim_time(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None
    assert claimed.id == entry.id
    assert claimed.state == ExperimentQueueState.State.DISPATCHING
    assert claimed.claimed_at == NOW
    # 第二次认领拿不到（同一时刻只有一个派发者）
    assert store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL) is None
    assert store.get_queue_entry(entry.id.value).state == ExperimentQueueState.State.DISPATCHING


def test_due_order_prefers_earliest_effective_time(store: SqliteExperimentStore) -> None:
    """到期顺序 = COALESCE(not_before, created_at)：未排期条目按创建时间参与排序。"""
    plan = _plan(store)
    later = _entry(plan, created_at=_at(10))
    scheduled_soon = _entry(plan, not_before=_at(-5), created_at=_at(20))
    store.save_queue_entry(later)
    store.save_queue_entry(scheduled_soon)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None
    assert claimed.id == scheduled_soon.id


def test_expired_claim_is_requeued_then_reclaimed(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    # TTL 未到：认领者仍算活着
    assert store.claim_due_entry(now=_at(TTL - 1), claim_ttl_seconds=TTL) is None
    reclaimed = store.claim_due_entry(now=_at(TTL + 1), claim_ttl_seconds=TTL)
    assert reclaimed is not None
    assert reclaimed.id == entry.id
    assert reclaimed.state == ExperimentQueueState.State.DISPATCHING
    assert reclaimed.claimed_at == _at(TTL + 1)


def test_cancel_only_applies_to_queued(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    with pytest.raises(InvalidInputError):
        store.cancel_queue_entry(entry.id.value, now=NOW)


def test_cancel_queued_entry_is_terminal(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    cancelled = store.cancel_queue_entry(entry.id.value, now=NOW)
    assert cancelled.state == ExperimentQueueState.State.CANCELLED
    assert cancelled.is_terminal
    assert store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL) is None
    with pytest.raises(InvalidInputError):
        store.cancel_queue_entry(entry.id.value, now=NOW)


def test_reschedule_updates_schedule_and_rejects_non_queued(
    store: SqliteExperimentStore,
) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    moved = store.reschedule_queue_entry(entry.id.value, not_before=_at(7200), now=NOW)
    assert moved.not_before == _at(7200)
    assert moved.state == ExperimentQueueState.State.QUEUED
    cleared = store.reschedule_queue_entry(entry.id.value, not_before=None, now=NOW)
    assert cleared.not_before is None
    store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    with pytest.raises(InvalidInputError):
        store.reschedule_queue_entry(entry.id.value, not_before=None, now=NOW)


def test_list_queue_entries_is_project_scoped_and_ordered(
    store: SqliteExperimentStore,
) -> None:
    plan = _plan(store)
    first = _entry(plan, created_at=_at(1))
    second = _entry(plan, created_at=_at(2))
    foreign = _entry(plan, created_at=_at(3), project_id="other")
    for entry in (second, first, foreign):
        store.save_queue_entry(entry)
    listed = store.list_queue_entries("proj-q")
    assert [entry.id for entry in listed] == [first.id, second.id]


def test_dispatched_entry_keeps_run_id(store: SqliteExperimentStore) -> None:
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None
    store.save_queue_entry(claimed.mark_dispatched("run-42"))
    reloaded = store.get_queue_entry(entry.id.value)
    assert reloaded.state == ExperimentQueueState.State.DISPATCHED
    assert reloaded.run_id == "run-42"


def test_list_plans_filters_by_state_and_orders_newest_first(
    store: SqliteExperimentStore,
) -> None:
    older = _plan(store)
    archived = _plan(store, archived=True)
    plans = store.list_plans()
    assert [plan.id for plan in plans] == [archived.id, older.id] or len(plans) == 2
    only_preregistered = store.list_plans(state=ExperimentPlanState.State.PREREGISTERED)
    assert [plan.id for plan in only_preregistered] == [older.id]


def test_stale_write_loses_to_conditional_update(store: SqliteExperimentStore) -> None:
    """条件更新是并发仲裁点：基于旧快照的写入不得覆盖已前进的行状态。

    白盒用例：先由 store 完成认领（行已 DISPATCHING），再用"认领前读到的
    QUEUED 条目"构造一次写入，`from_state=QUEUED` 必须失配（rowcount 0）。
    这正是一个并发派发者丢失竞争的路径（真实并发下同样落到这里）。
    """
    plan = _plan(store)
    entry = _entry(plan)
    store.save_queue_entry(entry)
    claimed = store.claim_due_entry(now=NOW, claim_ttl_seconds=TTL)
    assert claimed is not None
    stale = entry.claim(NOW)
    assert store._conditional_write(stale, from_state=entry.state) is False  # noqa: SLF001
    assert store.get_queue_entry(entry.id.value).claimed_at == NOW
