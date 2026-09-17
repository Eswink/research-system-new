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

from adapters.sqlite.completion import RetryNotice, publish_completion_outcome
from adapters.sqlite.db import now_iso
from adapters.sqlite.leases import (
    iso,
    lease_from_row,
    new_lease,
    request_digest,
    timestamp_now,
)
from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.serialization import decode_contract, encode_task
from adapters.sqlite.workflow_claim import (
    CLAIMABLE_STATUSES,
    claim_candidates,
    first_matching_candidate,
    persist_new_lease,
)
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import record_metric_safely
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    TaskCompletion,
    TaskLease,
)
from packages.domain.core import Timestamp
from packages.domain.enums import FailureAction
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import FailureDisposition, ResearchTask, TaskContract

_HostCalls = Callable[..., None]
_Predicate = Callable[[ResearchTask], bool]

# 这次完成**已经落账**的状态（lease 已删）：重放同一完成必须是幂等 noop。
# RETRY_SCHEDULED 也在内——它表示完成已被处置（排了下一次尝试），不是"还没完成"。
_COMPLETION_ALREADY_APPLIED = (
    ResearchTaskState.State.SUCCEEDED,
    ResearchTaskState.State.FAILED,
    ResearchTaskState.State.DEAD_LETTER,
    ResearchTaskState.State.RETRY_SCHEDULED,
)

# 失败处置 → 落库状态（RETRY 走 RETRY_SCHEDULED，不在这张表里）。
_FAILURE_STATUS = {
    FailureAction.FAIL: ResearchTaskState.State.FAILED,
    FailureAction.DEAD_LETTER: ResearchTaskState.State.DEAD_LETTER,
}


def _before_retry_deadline(row: Any, now: datetime) -> bool:
    """这条任务是不是还在等退避（PLAN-20260915-080）。

    `retry_at` 与 `now` 都是同一格式的 UTC ISO 文本（`iso()` / `now_iso()`），
    字符串比较即时间比较——与 claim 候选扫描里的 SQL 比较同一口径。
    """
    retry_at = row["retry_at"] if "retry_at" in row.keys() else None
    if retry_at is None:
        return False
    return str(retry_at) > iso(Timestamp(now))


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
        # 退避 deadline 对**每个交付入口**成立，不只是 claim 的候选扫描
        # （PLAN-20260915-080）：按 task_id 直接租也不能把没到期的重试提前放出去。
        if _before_retry_deadline(row, timestamp_now(self._now).value):
            self._record("acquire_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(
                f"task {task_id} is waiting for its retry backoff until {row['retry_at']}"
            )
        lease = new_lease(
            task_id,
            row["assigned_agent_id"],
            self._lease_ttl,
            self._now,
            fence=int(row["fence_seq"] or 0) + 1,
        )
        with self._conn:
            persist_new_lease(self._conn, self._outbox, lease, run_id=str(row["run_id"]))
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
        chosen = first_matching_candidate(
            claim_candidates(self._conn, timestamp_now(self._now).value), request
        )
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
            if fresh is None or fresh["status"] not in CLAIMABLE_STATUSES:
                self._record("claim_next", request.worker_id, result="contended")
                return None
            persist_new_lease(self._conn, self._outbox, lease, run_id=str(chosen["run_id"]))
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

    def _require_current_lease(self, lease: TaskLease) -> None:
        """完成前必须持有**当前**租约：lease_id 匹配且 fence 是这一代（M16 §8）。"""
        row = self._conn.execute(
            "SELECT lease_id, fence FROM leases WHERE task_id = ?", (lease.task_id,)
        ).fetchone()
        if row is None or row["lease_id"] != lease.lease_id:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
        if int(row["fence"] or 0) != lease.fence:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(
                f"stale fence for task {lease.task_id}: lease generation superseded"
            )

    def _complete_impl(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._ensure_open()
        task_row = self._conn.execute(
            "SELECT run_id, status, created_at, attempt, contract_json FROM tasks"
            " WHERE task_id = ?",
            (lease.task_id,),
        ).fetchone()
        if task_row is None:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown task: {lease.task_id}")
        # at-least-once：这次完成已经落账（lease 已删）时，重放是幂等 noop。
        # RETRY_SCHEDULED 也在内：它表示完成**已被处置**（排了下一次尝试），
        # 重放同一次完成不能变成异常。
        done = _COMPLETION_ALREADY_APPLIED
        if task_row["status"] in done:
            self._record("complete", lease.task_id, result="deduped")
            return
        self._require_current_lease(lease)
        # 失败完成的处置由 Domain 的判据决定（PLAN-20260915-078）：
        # 可重试且还有次数 ⇒ RETRY_SCHEDULED（再次可被 claim）；次数用尽 ⇒ 死信。
        # `attempt` 是**本次**尝试的序号，由交付路径维护（persist_new_lease 每交付一次
        # 就把它推进一代），所以这里读列即可——不是提交时的快照。
        attempt = int(task_row["attempt"] or 1)
        contract = decode_contract(task_row["contract_json"])
        plan = contract.disposition(
            outcome=completion.outcome, attempt=attempt, category=completion.failure_category
        )
        with self._conn:
            self._conn.execute("DELETE FROM leases WHERE task_id = ?", (lease.task_id,))
            retry_at = self._write_disposition(lease, plan, contract, attempt)
            # 事件必须留在**同一个提交块内**：连接上只有一个隐式事务，块外的 publish 会
            # 停在没有提交的事务里，另一个连接（如重启后的 outbox 读取方）看不到它。
            publish_completion_outcome(
                self._outbox,
                plan,
                run_id=str(task_row["run_id"]),
                completion=completion,
                retry=RetryNotice(next_attempt=attempt + 1, retry_at=retry_at),
            )
        self._note_task_duration(str(task_row["created_at"]))
        self._record("complete", lease.task_id, result=str(plan.action))

    def _write_disposition(
        self, lease: TaskLease, plan: FailureDisposition, contract: TaskContract, attempt: int
    ) -> str | None:
        """把处置写进任务行：状态 + 重排时的退避 deadline（返回 deadline 文本）。

        完成不改 attempt：一次尝试从**拿到 lease** 才算开始，序号在交付时写定
        （域不变量：attempt > 1 必须带 lease_id，完成时租约已删）。
        重排则写下 `retry_at`（PLAN-20260915-079）：时延由 Domain 纯函数算，
        claim 的候选扫描按它过滤——没到期的重试不占候选窗口。
        """
        delay = contract.retry_delay(attempt=attempt) if plan.retrying else timedelta(0)
        retry_at = (
            iso(Timestamp(timestamp_now(self._now).value + delay))
            if plan.retrying and delay
            else None
        )
        self._conn.execute(
            "UPDATE tasks SET status = ?, retry_at = ? WHERE task_id = ?",
            (plan.status, retry_at, lease.task_id),
        )
        return retry_at

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
