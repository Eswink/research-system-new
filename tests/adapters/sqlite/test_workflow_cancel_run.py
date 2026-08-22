"""SA-1R 新增回归：run 级取消与终止态 lease 拒绝（SqliteWorkflowEngine）。

- B001: cancel_run 必须按 run_id 到达 run 下所有未终止任务（修复前只按
  task_id 取消，service.cancel_run(run_id) 对生产路径完全无效）；
- B002: 终止态任务不可重新 acquire_lease（修复前 cancel/complete 后
  重放可复活任务，产生 cancelled-but-completed / completed-but-retried）。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import research_task, task_contract

START = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)


def _engine() -> SqliteWorkflowEngine:
    clock = {"now": START}
    return SqliteWorkflowEngine(lease_ttl_seconds=60, now=lambda: clock["now"])


def _second_task(task_id: str, idem_key: str) -> ResearchTask:
    return replace(research_task(), id=ID(task_id), idempotency_key=idem_key)


class TestCancelRun:
    def test_cancel_run_cancels_all_tasks_in_run(self) -> None:
        """SA-1R-B001：run 级取消必须到达 run 下所有未终止任务。"""
        engine = _engine()
        task = research_task()
        second = _second_task("7f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d91", "idem-2")
        engine.submit(task, task_contract())
        engine.submit(second, task_contract())
        engine.acquire_lease(task.id.value)
        engine.acquire_lease(second.id.value)
        assert engine.cancel_run(task.run_id.value) == 2
        rows = engine.list_tasks(task.run_id.value)
        assert {row.task.status for row in rows} == {ResearchTaskState.State.CANCELLED}
        kinds = [envelope.event_type for envelope in engine.pending_outbox()]
        assert kinds.count(EventType.TASK_CANCELLED) == 2

    def test_cancel_run_skips_terminal_tasks(self) -> None:
        """SA-1R-B001：run 级取消跳过已终止任务（SUCCEEDED/FAILED），不覆盖终态。"""
        engine = _engine()
        task = research_task()
        second = _second_task("7f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d92", "idem-2")
        engine.submit(task, task_contract())
        engine.submit(second, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        engine.acquire_lease(second.id.value)
        assert engine.cancel_run(task.run_id.value) == 1
        rows = engine.list_tasks(task.run_id.value)
        statuses = {row.task.status for row in rows}
        assert statuses == {ResearchTaskState.State.SUCCEEDED, ResearchTaskState.State.CANCELLED}

    def test_cancel_run_unknown_run_is_noop(self) -> None:
        engine = _engine()
        assert engine.cancel_run("missing-run") == 0

    def test_cancel_run_is_idempotent(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        assert engine.cancel_run(task.run_id.value) == 1
        assert engine.cancel_run(task.run_id.value) == 0


class TestTerminalLeaseRejection:
    def test_acquire_after_cancel_raises(self) -> None:
        """SA-1R-B002：CANCELLED 任务不可重新租约（否则取消后重放会复活任务）。"""
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        engine.cancel(task.id.value)
        with pytest.raises(InvalidInputError):
            engine.acquire_lease(task.id.value)

    def test_acquire_after_complete_raises(self) -> None:
        """SA-1R-B002：SUCCEEDED 任务不可重新租约（否则 completed-but-retried）。"""
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        with pytest.raises(InvalidInputError):
            engine.acquire_lease(task.id.value)

    def test_acquire_after_fail_raises(self) -> None:
        engine = _engine()
        task = research_task()
        engine.submit(task, task_contract())
        lease = engine.acquire_lease(task.id.value)
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="FAILED"))
        with pytest.raises(InvalidInputError):
            engine.acquire_lease(task.id.value)
