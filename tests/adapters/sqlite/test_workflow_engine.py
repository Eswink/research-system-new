"""SqliteWorkflowEngine 单元测试：at-least-once、lease、recovery、outbox。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from tests.contracts.fixtures import research_task, task_contract

START = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)


def _clock() -> dict[str, datetime]:
    return {"now": START}


def _engine(clock: dict[str, datetime] | None = None) -> SqliteWorkflowEngine:
    if clock is None:
        return SqliteWorkflowEngine(lease_ttl_seconds=60)
    return SqliteWorkflowEngine(lease_ttl_seconds=60, now=lambda: clock["now"])


class TestSubmitIdempotency:
    def test_duplicate_submit_same_task_is_silent(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        engine.submit(task, task_contract("other"))
        rows = engine.list_tasks(task.run_id.value)
        assert len(rows) == 1
        assert engine.calls[-1].result_summary == "deduped"

    def test_duplicate_submit_same_idempotency_key_is_silent(self) -> None:
        engine = _engine()
        engine.submit(research_task(), task_contract())
        other = research_task()
        engine.submit(other, task_contract())
        rows = engine.list_tasks(other.run_id.value)
        assert len(rows) == 1

    def test_task_roundtrip_preserves_fields(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        (row,) = engine.list_tasks(task.run_id.value)
        assert row.task.id == task.id
        assert row.task.attempt == task.attempt
        assert row.task.idempotency_key == task.idempotency_key
        assert row.contract.id == task_contract().id
        assert row.contract.acceptance_criteria[0].type.value == "ARTIFACT_EXISTS"


class TestLeaseLifecycle:
    def test_acquire_lease_is_deduped(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        first = engine.acquire_lease(task.id.value)
        second = engine.acquire_lease(task.id.value)
        assert second.lease_id == first.lease_id
        assert engine.calls[-1].result_summary == "deduped"

    def test_acquire_unknown_task_raises(self) -> None:
        engine = _engine()
        with pytest.raises(InvalidInputError):
            engine.acquire_lease("missing")

    def test_heartbeat_renews_expiry(self) -> None:
        clock = _clock()
        engine = _engine(clock)
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        assert lease.expires_at is not None
        initial_expiry = lease.expires_at.value
        clock["now"] = START + timedelta(seconds=10)
        renewed = engine.heartbeat(lease)
        assert renewed.expires_at is not None
        assert renewed.expires_at.value > initial_expiry
        assert renewed.lease_id != lease.lease_id

    def test_heartbeat_without_lease_raises(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.cancel(task.id.value)
        with pytest.raises(InvalidInputError):
            engine.heartbeat(lease)

    def test_complete_requires_matching_lease(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(
            lease,
            TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"),
        )
        with pytest.raises(InvalidInputError):
            engine.complete(
                lease,
                TaskCompletion(task_id=task.id.value, outcome="FAILED"),
            )

    def test_lease_expires_and_recovers(self) -> None:
        clock = _clock()
        engine = _engine(clock)
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        clock["now"] = START + timedelta(seconds=120)
        recovered = engine.recover_expired_leases()
        assert recovered == 1
        (row,) = engine.list_tasks(task.run_id.value)
        assert row.task.status == ResearchTaskState.State.QUEUED
        lease = engine.acquire_lease(task.id.value)
        assert lease.lease_id != ""


class TestCancel:
    def test_cancel_is_idempotent(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        engine.cancel(task.id.value)
        engine.cancel(task.id.value)
        assert engine.calls[-1].result_summary == "deduped"
        (row,) = engine.list_tasks(task.run_id.value)
        assert row.task.status == ResearchTaskState.State.CANCELLED

    def test_cancel_unknown_task_is_silent(self) -> None:
        engine = _engine()
        engine.cancel("missing")


class TestOutbox:
    def test_events_are_written_transactionally(self) -> None:
        connection = connect(":memory:")
        engine = SqliteWorkflowEngine(connection=connection)
        publisher = SqliteOutboxEventPublisher(connection=connection)
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        kinds = [envelope.event_type for envelope in publisher.published]
        assert EventType.TASK_LEASED in kinds
        assert EventType.TASK_COMPLETED in kinds
        completed = [e for e in publisher.published if e.event_type is EventType.TASK_COMPLETED]
        assert completed[0].task_id == task.id.value
        assert completed[0].run_id == task.run_id.value

    def test_cancel_writes_cancelled_event(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        engine.cancel(task.id.value)
        kinds = [envelope.event_type for envelope in engine.pending_outbox()]
        assert EventType.TASK_CANCELLED in kinds

    def test_recovery_writes_retry_event(self) -> None:
        clock = _clock()
        engine = _engine(clock)
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        clock["now"] = START + timedelta(seconds=120)
        engine.recover_expired_leases()
        kinds = [envelope.event_type for envelope in engine.pending_outbox()]
        assert EventType.TASK_RETRY_SCHEDULED in kinds

    def test_publish_dedup_and_mark_published(self) -> None:
        connection = connect(":memory:")
        publisher = SqliteOutboxEventPublisher(connection=connection)
        from tests.contracts.fixtures import event_envelope

        publisher.publish(event_envelope("evt-1"))
        publisher.publish(event_envelope("evt-1"))
        assert len(publisher.published) == 1
        assert publisher.calls[-1].result_summary == "deduped"
        publisher.mark_published(("evt-1",))
        assert publisher.pending() == ()


class TestRestartRecovery:
    def test_recovery_across_engine_instances(self, tmp_path: object) -> None:
        import os

        db_path = os.fspath(tmp_path / "queue.db")  # type: ignore[operator]
        clock = _clock()
        first = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
        task = research_task()
        first.submit(task, task_contract())
        first.acquire_lease(task.id.value)
        first.close()
        clock["now"] = START + timedelta(seconds=120)
        second = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
        assert second.recover_expired_leases() == 1
        (row,) = second.list_tasks(task.run_id.value)
        assert row.task.status == ResearchTaskState.State.QUEUED
        lease = second.acquire_lease(task.id.value)
        assert lease.task_id == task.id.value
        second.close()
