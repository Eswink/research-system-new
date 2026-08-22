"""SqliteWorkflowEngine：WorkflowEngine Port 的 SQLite 持久化实现。

at-least-once + idempotency（PORTS.md §1）：submit/acquire 静默去重，complete
对已终止任务幂等 noop，cancel 对终止态 noop；任务级事件与状态同事务写 outbox；
重启恢复：recover_expired_leases() 置回 QUEUED（EXPIRE_LEASE 转换）。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.cancel_run import cancel_run_tasks, cancel_task
from adapters.sqlite.db import connect, now_iso
from adapters.sqlite.leases import iso, lease_from_row, new_lease, request_digest
from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.projections import (
    cancelled,
    completed,
    deliveries,
    list_tasks,
    mark_outbox_published,
    pending_outbox,
)
from adapters.sqlite.serialization import (
    TaskRow,
    encode_task,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    TaskLease,
)
from packages.domain.events import EventEnvelope, EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask, TaskContract


class SqliteWorkflowEngine(SqliteAdapterBase):
    """SQLite 持久化 WorkflowEngine；`now` 可注入用于确定性测试。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
        lease_ttl_seconds: int = 300,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("workflow_engine")
        self._lease_ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._outbox = OutboxWriter(self._conn, self._now)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def submit(self, task: ResearchTask, contract: TaskContract) -> None:
        self._ensure_open()
        with self._conn:
            if self._task_exists(task) or self._idempotency_exists(task):
                self._record("submit", task.id.value, result="deduped")
                return
            task_json, contract_json = encode_task(task, contract)
            self._conn.execute(
                "INSERT INTO tasks (task_id, run_id, idempotency_key, attempt, status,"
                " assigned_agent_id, task_json, contract_json, cancelled, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    task.id.value,
                    task.run_id.value,
                    task.idempotency_key,
                    task.attempt,
                    task.status,
                    task.assigned_agent_id,
                    task_json,
                    contract_json,
                    now_iso(self._now),
                ),
            )
            if task.idempotency_key is not None:
                self._conn.execute(
                    "INSERT INTO idempotency_records (operation_key, task_id, request_digest,"
                    " created_at) VALUES (?, ?, ?, ?)",
                    (
                        task.idempotency_key,
                        task.id.value,
                        request_digest(task, contract),
                        now_iso(self._now),
                    ),
                )
        self._record("submit", task.id.value)

    def acquire_lease(self, task_id: str) -> TaskLease:
        self._ensure_open()
        row = self._conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            self._record("acquire_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown task: {task_id}")
        # 终止态任务不可重新租约：cancel 后重放 / complete 后重放必须拒绝，
        # 否则 CANCELLED/SUCCEEDED 任务会被复活（terminal 状态无出边）。
        if row["status"] in ResearchTaskState.terminal():
            self._record("acquire_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(
                f"task {task_id} is terminal ({row['status']}); cannot acquire lease"
            )
        existing = self._conn.execute(
            "SELECT * FROM leases WHERE task_id = ?", (task_id,)
        ).fetchone()
        if existing is not None:
            self._record("acquire_lease", task_id, result="deduped")
            return lease_from_row(existing)
        lease = new_lease(task_id, row["assigned_agent_id"], self._lease_ttl, self._now)
        assert lease.expires_at is not None and lease.heartbeat_at is not None
        with self._conn:
            self._conn.execute(
                "INSERT INTO leases (task_id, lease_id, agent_id, expires_at, heartbeat_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    task_id,
                    lease.lease_id,
                    lease.agent_id,
                    iso(lease.expires_at),
                    iso(lease.heartbeat_at),
                ),
            )
            self._conn.execute(
                "UPDATE tasks SET status = ? WHERE task_id = ?",
                (ResearchTaskState.State.LEASED, task_id),
            )
            self._outbox.publish(
                EventType.TASK_LEASED,
                {"task_id": task_id, "lease_id": lease.lease_id},
                run_id=row["run_id"],
                task_id=task_id,
            )
        self._record("acquire_lease", task_id, result=lease.lease_id)
        return lease

    def heartbeat(self, lease: TaskLease) -> TaskLease:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT * FROM leases WHERE task_id = ?", (lease.task_id,)
        ).fetchone()
        if row is None or row["lease_id"] != lease.lease_id:
            self._record("heartbeat", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
        renewed = new_lease(lease.task_id, lease.agent_id, self._lease_ttl, self._now)
        assert renewed.expires_at is not None and renewed.heartbeat_at is not None
        with self._conn:
            self._conn.execute(
                "UPDATE leases SET lease_id = ?, expires_at = ?, heartbeat_at = ?"
                " WHERE task_id = ?",
                (
                    renewed.lease_id,
                    iso(renewed.expires_at),
                    iso(renewed.heartbeat_at),
                    lease.task_id,
                ),
            )
        self._record("heartbeat", lease.task_id)
        return renewed

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._ensure_open()
        task_row = self._conn.execute(
            "SELECT run_id, status FROM tasks WHERE task_id = ?", (lease.task_id,)
        ).fetchone()
        if task_row is None:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown task: {lease.task_id}")
        # at-least-once：已终止任务重放 complete 是幂等 noop（lease 已删）。
        done = (ResearchTaskState.State.SUCCEEDED, ResearchTaskState.State.FAILED)
        if task_row["status"] in done:
            self._record("complete", lease.task_id, result="deduped")
            return
        row = self._conn.execute(
            "SELECT * FROM leases WHERE task_id = ?", (lease.task_id,)
        ).fetchone()
        if row is None or row["lease_id"] != lease.lease_id:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
        status = (
            ResearchTaskState.State.SUCCEEDED
            if completion.outcome == "SUCCEEDED"
            else ResearchTaskState.State.FAILED
        )
        with self._conn:
            self._conn.execute("DELETE FROM leases WHERE task_id = ?", (lease.task_id,))
            self._conn.execute(
                "UPDATE tasks SET status = ? WHERE task_id = ?",
                (status, lease.task_id),
            )
            self._outbox.publish(
                EventType.TASK_COMPLETED,
                {"task_id": lease.task_id, "outcome": completion.outcome},
                run_id=str(task_row["run_id"]),
                task_id=lease.task_id,
            )
        self._record("complete", lease.task_id, result=completion.outcome)

    def cancel(self, task_id: str) -> None:
        self._ensure_open()
        outcome = cancel_task(self._conn, self._outbox, task_id)
        self._record("cancel", task_id, result=outcome)

    def cancel_run(self, run_id: str) -> int:
        """取消 run 下所有未终止任务（协作式）；返回实际取消数量。"""
        self._ensure_open()
        cancelled_count = cancel_run_tasks(self._conn, self._outbox, run_id)
        self._record("cancel_run", run_id, result=f"{cancelled_count} cancelled")
        return cancelled_count

    def recover_expired_leases(self) -> int:
        """超时 lease 任务置回 QUEUED（EXPIRE_LEASE 转换，非绕过状态机）；返回恢复数。"""
        self._ensure_open()
        expired = self._conn.execute(
            "SELECT leases.task_id FROM leases WHERE leases.expires_at < ?",
            (now_iso(self._now),),
        ).fetchall()
        recovered = 0
        for row in expired:
            task_id = row["task_id"]
            task_row = self._conn.execute(
                "SELECT run_id FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            with self._conn:
                self._conn.execute("DELETE FROM leases WHERE task_id = ?", (task_id,))
                self._conn.execute(
                    "UPDATE tasks SET status = ? WHERE task_id = ?",
                    (ResearchTaskState.State.QUEUED, task_id),
                )
                self._outbox.publish(
                    EventType.TASK_RETRY_SCHEDULED,
                    {"task_id": task_id, "reason": "lease_expired"},
                    run_id=str(task_row["run_id"]),
                    task_id=task_id,
                )
            recovered += 1
        self._record("recover_expired_leases", f"{recovered} recovered")
        return recovered

    def list_tasks(self, run_id: str) -> tuple[TaskRow, ...]:
        """run 内任务投影（canonical state 读取，非审计事件）。"""
        return list_tasks(self._conn, run_id)

    @property
    def deliveries(self) -> dict[str, int]:
        """投递投影：每个 idempotency key（或 task id）恰一次（M5 语义对齐）。"""
        return deliveries(self._conn)

    @property
    def completed(self) -> dict[str, TaskCompletion]:
        """完成投影：status 为 SUCCEEDED/FAILED 的任务（M5 语义对齐）。"""
        return completed(self._conn)

    @property
    def cancelled(self) -> set[str]:
        """取消投影：cancelled=1 的任务（M5 语义对齐）。"""
        return cancelled(self._conn)

    def pending_outbox(self) -> tuple[EventEnvelope, ...]:
        """未投递的 outbox 事件（供 EventPublisher 轮询）。"""
        return pending_outbox(self._conn)

    def mark_outbox_published(self, event_ids: tuple[str, ...]) -> None:
        """标记事件已投递（幂等）。"""
        mark_outbox_published(self._conn, event_ids, self._now)

    def _task_exists(self, task: ResearchTask) -> bool:
        return (
            self._conn.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task.id.value,)).fetchone()
            is not None
        )

    def _idempotency_exists(self, task: ResearchTask) -> bool:
        if task.idempotency_key is None:
            return False
        return (
            self._conn.execute(
                "SELECT 1 FROM idempotency_records WHERE operation_key = ?",
                (task.idempotency_key,),
            ).fetchone()
            is not None
        )
