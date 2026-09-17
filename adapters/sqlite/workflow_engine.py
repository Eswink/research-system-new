"""SqliteWorkflowEngine：WorkflowEngine Port 的 SQLite 持久化实现。

at-least-once + idempotency（PORTS.md §1）：submit/acquire 静默去重，complete
对已终止任务幂等 noop，cancel 对终止态 noop；任务级事件与状态同事务写 outbox；
重启恢复：recover_expired_leases() 置回 QUEUED（EXPIRE_LEASE 转换）。
M15 观测:公共方法经 `operation()` 发 WORKFLOW_QUEUE/LEASE_RECOVERY span,
queue-lag/task-duration/lease-expired metric 由 impl 与 note 提供(规模阈值
拆分见 workflow_ops.py)。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.cancel_run import cancel_run_tasks, cancel_task
from adapters.sqlite.db import connect
from adapters.sqlite.leases import iso, timestamp_now
from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.projections import (
    cancelled,
    completed,
    deliveries,
    due_retries,
    list_tasks,
    mark_outbox_published,
    pending_outbox,
)
from adapters.sqlite.projections import task_identities as select_task_identities
from adapters.sqlite.serialization import TaskRow
from adapters.sqlite.workflow_ops import SqliteWorkflowOps
from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    TaskCompletion,
    TaskIdentity,
    TaskLease,
)
from packages.domain.events import EventEnvelope
from packages.domain.tasks import ResearchTask, TaskContract


class SqliteWorkflowEngine(SqliteAdapterBase, SqliteWorkflowOps):
    """SQLite 持久化 WorkflowEngine；`now` 可注入用于确定性测试。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
        lease_ttl_seconds: int = 300,
        now: Callable[[], datetime] | None = None,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        super().__init__("workflow_engine")
        self._lease_ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        self._telemetry = telemetry
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._outbox = OutboxWriter(self._conn, self._now)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def submit(self, task: ResearchTask, contract: TaskContract) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.submit",
            correlation=CorrelationRef(task_id=task.id.value, run_id=task.run_id.value),
        ):
            self._submit_impl(task, contract)

    def acquire_lease(self, task_id: str) -> TaskLease:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.acquire_lease",
            correlation=CorrelationRef(task_id=task_id),
        ):
            return self._acquire_lease_impl(task_id)

    def claim_next(self, request: ClaimRequest) -> TaskLease | None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKER_DISPATCH,
            name="workflow.claim_next",
            correlation=CorrelationRef(),
        ):
            return self._claim_next_impl(request)

    def heartbeat(self, lease: TaskLease) -> TaskLease:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.heartbeat",
            correlation=CorrelationRef(task_id=lease.task_id),
        ):
            return self._heartbeat_impl(lease)

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.complete",
            correlation=CorrelationRef(task_id=lease.task_id),
        ):
            return self._complete_impl(lease, completion)

    def cancel(self, task_id: str) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.cancel",
            correlation=CorrelationRef(task_id=task_id),
        ):
            self._ensure_open()
            outcome = cancel_task(self._conn, self._outbox, task_id)
            self._record("cancel", task_id, result=outcome)

    def cancel_run(self, run_id: str) -> int:
        """取消 run 下所有未终止任务（协作式）；返回实际取消数量。"""
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.cancel_run",
            correlation=CorrelationRef(run_id=run_id),
        ):
            self._ensure_open()
            cancelled_count = cancel_run_tasks(self._conn, self._outbox, run_id)
            self._record("cancel_run", run_id, result=f"{cancelled_count} cancelled")
            return cancelled_count

    def cancelled_task_ids(self, run_id: str) -> tuple[str, ...]:
        """该 run 的取消任务 id（canonical task projection，只读）。"""
        self._ensure_open()
        ids = tuple(
            row.task.id.value
            for row in self.list_tasks(run_id)
            if row.task.id.value in self.cancelled
        )
        self._record("cancelled_task_ids", run_id, result=str(len(ids)))
        return ids

    def due_retry_task_ids(self, run_id: str) -> tuple[str, ...]:
        """该 run 已到期的重排任务（调度器判断"停车中的 run 能不能再交付"）。

        比较用 `timestamp_now`（生产：DB 时钟；测试：注入时钟），与写 `retry_at`
        同一个源——调度器不自己拿"现在"来比。
        """
        self._ensure_open()
        ids = due_retries(self._conn, run_id, iso(timestamp_now(self._now)))
        self._record("due_retry_task_ids", run_id, result=str(len(ids)))
        return ids

    def task_identities(self, run_id: str) -> tuple[TaskIdentity, ...]:
        """该 run 已登记任务的稳定身份（重启后续跑按 idempotency key 对齐）。"""
        self._ensure_open()
        identities = tuple(
            TaskIdentity(idempotency_key=key, task_id=task_id, status=status)
            for key, task_id, status in select_task_identities(self._conn, run_id)
        )
        self._record("task_identities", run_id, result=str(len(identities)))
        return identities

    def run_state(self, run_id: str) -> str | None:
        """该 run 的 canonical 状态（未知 run → None）；派发面暂停协调只读视图。"""
        self._ensure_open()
        row = self._conn.execute(
            "SELECT json_extract(run_json, '$.state') AS state FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        state = None if row is None else row["state"]
        self._record("run_state", run_id, result=str(state))
        return str(state) if state is not None else None

    def recover_expired_leases(self) -> int:
        """超时 lease 任务置回 QUEUED（EXPIRE_LEASE 转换，非绕过状态机）；返回恢复数。"""
        with operation(
            self._telemetry,
            scope=OperationScope.LEASE_RECOVERY,
            name="lease_recovery.recover",
        ):
            return self._recover_impl()

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
