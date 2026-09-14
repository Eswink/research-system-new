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
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    TaskCompletion,
    TaskLease,
)
from packages.domain.enums import TaskKind
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
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


def _first_matching_candidate(candidates: Any, request: ClaimRequest) -> Any:
    """First QUEUED EXECUTION row whose capability/partition match the claim.

    Python-side filter over a static-SQL scan (M16 §7): a task with NULL
    required_capability matches any worker; partition is a filter, not
    ownership. `relax_partitions` (starvation fallback) ignores the partition
    filter and matches by capability only.
    """
    for row in candidates:
        required = row["required_capability"]
        if required is not None and required not in request.capabilities:
            continue
        if not request.relax_partitions:
            part = row["partition"]
            if part is not None and part not in request.partitions:
                continue
        return row
    return None


def _claim_candidates(conn: sqlite3.Connection) -> Any:
    """QUEUED EXECUTION 候选扫描（静态 SQL；PAUSED run 的排除在扫描内完成）。

    暂停过滤必须作用在候选集而不是扫描之后：否则被暂停 run 的任务会占满
    候选窗口，把其他 run 的可派发任务饿死。
    """
    return conn.execute(
        "SELECT task_id, run_id, assigned_agent_id, fence_seq, required_capability,"
        " partition FROM tasks WHERE kind = ? AND status = ? AND cancelled = 0"
        " AND NOT EXISTS (SELECT 1 FROM runs WHERE runs.run_id = tasks.run_id"
        " AND json_extract(runs.run_json, '$.state') = ?)"
        " ORDER BY created_at",
        (
            TaskKind.EXECUTION.value,
            ResearchTaskState.State.QUEUED,
            ResearchRunState.State.PAUSED,
        ),
    ).fetchall()


def _persist_new_lease(
    conn: sqlite3.Connection,
    outbox: OutboxWriter,
    lease: TaskLease,
    *,
    run_id: str,
) -> None:
    """Insert a fresh lease row, mark the task LEASED, publish TASK_LEASED."""
    task_id = lease.task_id
    assert lease.expires_at is not None and lease.heartbeat_at is not None
    conn.execute(
        "INSERT INTO leases (task_id, lease_id, agent_id, expires_at, heartbeat_at,"
        " worker_id, fence) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            task_id,
            lease.lease_id,
            lease.agent_id,
            iso(lease.expires_at),
            iso(lease.heartbeat_at),
            lease.worker_id,
            lease.fence,
        ),
    )
    conn.execute(
        "UPDATE tasks SET status = ?, fence_seq = ? WHERE task_id = ?",
        (ResearchTaskState.State.LEASED, lease.fence, task_id),
    )
    outbox.publish(
        EventType.TASK_LEASED,
        {"task_id": task_id, "lease_id": lease.lease_id, "fence": lease.fence},
        run_id=run_id,
        task_id=task_id,
    )


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
                " assigned_agent_id, task_json, contract_json, cancelled, created_at,"
                " kind, partition, required_capability)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)",
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
                    task.kind.value,
                    task.partition,
                    task.required_capability,
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
        lease = new_lease(
            task_id,
            row["assigned_agent_id"],
            self._lease_ttl,
            self._now,
            fence=int(row["fence_seq"] or 0) + 1,
        )
        with self._conn:
            _persist_new_lease(self._conn, self._outbox, lease, run_id=str(row["run_id"]))
        self._note_queue_lag(row)
        self._record("acquire_lease", task_id, result=lease.lease_id)
        return lease

    def _claim_next_impl(self, request: ClaimRequest) -> TaskLease | None:
        """Single-process claim_next (honest limitation, M16 §7).

        SQLite has no `FOR UPDATE SKIP LOCKED`, so this serializes claims via
        the per-connection write lock and is correct only within one process.
        Cross-process distributed claims are the PostgreSQL adapter's job; the
        contract suite exercises claim semantics on both.

        Capability/partition filtering happens in Python over a static-SQL
        candidate scan (no dynamic query string is ever assembled), then the
        chosen task is re-verified QUEUED inside the write transaction.

        Paused runs (PLAN-20260914-048) are excluded in that same static scan
        (NOT EXISTS over the shared `runs` row), so a cooperatively paused run
        stops being dispatched rather than being filtered after the fact.
        """
        self._ensure_open()
        chosen = _first_matching_candidate(_claim_candidates(self._conn), request)
        if chosen is None:
            self._record("claim_next", request.worker_id, result="none")
            return None
        task_id = chosen["task_id"]
        new_fence = int(chosen["fence_seq"] or 0) + 1
        lease = new_lease(
            task_id,
            chosen["assigned_agent_id"],
            self._lease_ttl,
            self._now,
            worker_id=request.worker_id,
            fence=new_fence,
        )
        with self._conn:
            fresh = self._conn.execute(
                "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if fresh is None or fresh["status"] != ResearchTaskState.State.QUEUED:
                self._record("claim_next", request.worker_id, result="contended")
                return None
            _persist_new_lease(self._conn, self._outbox, lease, run_id=str(chosen["run_id"]))
        self._record("claim_next", request.worker_id, result=f"{task_id}@fence={new_fence}")
        return lease

    def _heartbeat_impl(self, lease: TaskLease) -> TaskLease:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT * FROM leases WHERE task_id = ?", (lease.task_id,)
        ).fetchone()
        if row is None or row["lease_id"] != lease.lease_id:
            self._record("heartbeat", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
        renewed = new_lease(
            lease.task_id,
            lease.agent_id,
            self._lease_ttl,
            self._now,
            worker_id=lease.worker_id,
            fence=lease.fence,
        )
        assert renewed.expires_at is not None and renewed.heartbeat_at is not None
        with self._conn:
            self._conn.execute(
                "UPDATE leases SET lease_id = ?, expires_at = ?, heartbeat_at = ?,"
                " worker_id = ?, fence = ? WHERE task_id = ?",
                (
                    renewed.lease_id,
                    iso(renewed.expires_at),
                    iso(renewed.heartbeat_at),
                    renewed.worker_id,
                    renewed.fence,
                    lease.task_id,
                ),
            )
        self._record("heartbeat", lease.task_id)
        return renewed

    def renew_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        """Extend an active EXECUTION lease in place (M16 re-audit F-7); SQLite mirror."""
        self._ensure_open()
        probe = new_lease(
            task_id, None, self._lease_ttl, self._now, worker_id=worker_id, fence=fence
        )
        assert probe.expires_at is not None
        with self._conn:
            cur = self._conn.execute(
                "UPDATE leases SET expires_at = ?, heartbeat_at = ?"
                " WHERE task_id = ? AND lease_id = ? AND fence = ? AND worker_id = ?",
                (iso(probe.expires_at), iso(probe.expires_at), task_id, lease_id, fence, worker_id),
            )
            if cur.rowcount == 0:
                self._record("renew_lease", task_id, error="InvalidInputError")
                raise InvalidInputError(f"no active lease to renew for task: {task_id}")
        self._record("renew_lease", task_id, result="extended")

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
        if int(row["fence"] or 0) != lease.fence:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(
                f"stale fence for task {lease.task_id}: lease generation superseded"
            )
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
        # Single lease authority (M16 §5): expired OR owned-by-a-LOST-worker.
        expired = self._conn.execute(
            "SELECT leases.task_id FROM leases "
            "WHERE leases.expires_at < ? "
            "OR leases.worker_id IN (SELECT worker_id FROM workers WHERE state = 'LOST')",
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
