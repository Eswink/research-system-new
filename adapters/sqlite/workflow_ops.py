"""SqliteWorkflowEngine 的 impl 方法与 telemetry note(M15 拆分,规模阈值)。

由 `SqliteWorkflowEngine` 继承;依赖宿主(SqliteAdapterBase)提供的
`_conn / _outbox / _record / _ensure_open` 与构造期注入的
`_telemetry / _now / _lease_ttl`。业务语义与拆分前完全一致。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from adapters.sqlite.db import now_iso
from adapters.sqlite.leases import iso, lease_from_row, new_lease, request_digest
from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.serialization import encode_task
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import record_metric_safely
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import TaskCompletion, TaskLease
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask, TaskContract

_HostCalls = Callable[..., None]
_Predicate = Callable[[ResearchTask], bool]


def _lag_ms_since(created_at: object) -> float | None:
    """created_at → 现在的毫秒时延;解析失败返回 None(telemetry 不阻断)。

    **不使用注入的业务时钟**:telemetry 计时读 `self._now` 会消费确定性测试时钟的
    tick,从而改变持久化的 domain event 时间戳(M15 复审实测每次 run 偏移 14 个
    时间戳)。观测必须旁观业务时间,不参与推进它。PG 侧
    (`adapters/postgres/telemetry_notes.py`)一直用挂钟,这里与之对齐。
    """
    try:
        text = str(created_at).replace("Z", "+00:00")
        created = datetime.fromisoformat(text)
        return max(0.0, (datetime.now(created.tzinfo) - created).total_seconds() * 1000.0)
    except (TypeError, ValueError):
        return None


class SqliteWorkflowOps:
    """SQLite workflow 的写路径 impl 与 telemetry note(供 engine 继承)。"""

    # 宿主提供(SqliteAdapterBase / engine __init__)
    _conn: sqlite3.Connection
    _outbox: OutboxWriter
    _record: _HostCalls
    _ensure_open: Callable[[], None]
    _task_exists: _Predicate
    _idempotency_exists: _Predicate
    _telemetry: TelemetrySink | None
    _now: Callable[[], datetime] | None
    _lease_ttl: timedelta

    def _submit_impl(self, task: ResearchTask, contract: TaskContract) -> None:
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

    def _acquire_lease_impl(self, task_id: str) -> TaskLease:
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
        self._note_queue_lag(row)
        self._record("acquire_lease", task_id, result=lease.lease_id)
        return lease

    def _heartbeat_impl(self, lease: TaskLease) -> TaskLease:
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

    def _complete_impl(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._ensure_open()
        task_row = self._conn.execute(
            "SELECT run_id, status, created_at FROM tasks WHERE task_id = ?", (lease.task_id,)
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
        self._note_task_duration(str(task_row["created_at"]))
        self._record("complete", lease.task_id, result=completion.outcome)

    def _recover_impl(self) -> int:
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
        if recovered:
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.WORKFLOW_LEASE_EXPIRED,
                    kind=MetricKind.COUNTER,
                    value=recovered,
                ),
            )
        self._record("recover_expired_leases", f"{recovered} recovered")
        return recovered

    def _note_queue_lag(self, row: Any) -> None:
        """claim 时的排队时延(created_at → 挂钟);telemetry off 时零开销。"""
        if self._telemetry is None:
            return
        lag = _lag_ms_since(row["created_at"])
        if lag is None:
            return
        record_metric_safely(
            self._telemetry,
            lambda: MetricSample(
                name=MetricName.WORKFLOW_QUEUE_LAG_MS, kind=MetricKind.HISTOGRAM, value=lag
            ),
        )

    def _note_task_duration(self, created_at: str) -> None:
        """任务总时长(created_at → complete);telemetry off 时零开销。"""
        if self._telemetry is None:
            return
        duration = _lag_ms_since(created_at)
        if duration is None:
            return
        record_metric_safely(
            self._telemetry,
            lambda: MetricSample(
                name=MetricName.WORKFLOW_TASK_DURATION_MS,
                kind=MetricKind.HISTOGRAM,
                value=duration,
            ),
        )
