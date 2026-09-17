"""SqliteWorkflowEngine 的 claim 侧助手（候选扫描 / 落租约 / 尝试序号同步）。

从 `workflow_ops.py` 拆出来（该文件触到 450 行硬上限），与
`adapters/postgres/workflow_claim.py` 同形：静态 SQL 扫描 + Python 侧能力/分区过滤 +
写事务内复核。可 claim 状态表只有一份（`CLAIMABLE_STATUSES`）：扫描与复核必须用
同一张表，否则重试任务会在复核那一步被判成 contended（PLAN-20260915-078 实测踩到）。
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime
from typing import Any

from adapters.sqlite.db import now_iso
from adapters.sqlite.leases import iso
from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.serialization import decode_task, encode_task
from packages.application.ports.workflow_engine import ClaimRequest, TaskLease
from packages.domain.enums import TaskKind
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState

# 可被 claim 的状态：首次排队 + 排了下一次尝试（PLAN-20260915-078）。
CLAIMABLE_STATUSES = (
    ResearchTaskState.State.QUEUED,
    ResearchTaskState.State.RETRY_SCHEDULED,
)


def first_matching_candidate(candidates: Any, request: ClaimRequest) -> Any:
    """First claimable EXECUTION row whose capability/partition match the claim.

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


def claim_candidates(conn: sqlite3.Connection, now: datetime) -> Any:
    """可 claim 的 EXECUTION 候选扫描（静态 SQL；暂停与未到期退避都在扫描内排除）。

    暂停过滤必须作用在候选集而不是扫描之后：否则被暂停 run 的任务会占满
    候选窗口，把其他 run 的可派发任务饿死。退避（PLAN-20260915-079）同理——
    没到 `retry_at` 的重试任务不该占窗口，到期后与首次排队同权。
    """
    return conn.execute(
        "SELECT task_id, run_id, assigned_agent_id, fence_seq, required_capability,"
        " partition FROM tasks WHERE kind = ? AND status IN (?, ?) AND cancelled = 0"
        " AND (retry_at IS NULL OR retry_at <= ?)"
        " AND NOT EXISTS (SELECT 1 FROM runs WHERE runs.run_id = tasks.run_id"
        " AND json_extract(runs.run_json, '$.state') = ?)"
        " ORDER BY created_at",
        (
            TaskKind.EXECUTION.value,
            *CLAIMABLE_STATUSES,
            now_iso(lambda: now),
            ResearchRunState.State.PAUSED,
        ),
    ).fetchall()


def _with_attempt(task_json: str, contract_json: str, lease: TaskLease) -> str:
    """交付一次 lease = 开始一次尝试：把 attempt 写进 canonical task JSON。

    交付代次（`fence_seq`，每交付一次前进一代）就是尝试序号，所以直接取
    `lease.fence`。域不变量（`attempt > 1` 必须带 `lease_id`）此刻成立——租约正握在
    手上。投影 `list_tasks` 读的是 task_json：它若落后于交付代次，重试产生的用量会
    一直记在上一次尝试的 entry id 上（`_attempt_scope` 的 attempt 后缀永不出现），
    `TaskContract.retry_policy` 消费到的次数也会与实际交付次数不符。
    """
    entry = decode_task(task_json, contract_json)
    task = replace(entry.task, attempt=lease.fence, lease_id=lease.lease_id)
    return encode_task(task, entry.contract)[0]


def persist_new_lease(
    conn: sqlite3.Connection,
    outbox: OutboxWriter,
    lease: TaskLease,
    *,
    run_id: str,
) -> None:
    """Insert a fresh lease row, mark the task LEASED, publish TASK_LEASED.

    同一次写里把 `attempt` 列与 task_json 一起推到本代（见 `_with_attempt`）——
    一次交付只有一个时刻，列与 JSON 不能各说一套。
    """
    task_id = lease.task_id
    assert lease.expires_at is not None and lease.heartbeat_at is not None
    row = conn.execute(
        "SELECT task_json, contract_json FROM tasks WHERE task_id = ?", (task_id,)
    ).fetchone()
    task_json = _with_attempt(row["task_json"], row["contract_json"], lease)
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
        "UPDATE tasks SET status = ?, fence_seq = ?, attempt = ?, retry_at = NULL,"
        " task_json = ? WHERE task_id = ?",
        (
            ResearchTaskState.State.LEASED,
            lease.fence,
            lease.fence,
            task_json,
            task_id,
        ),
    )
    outbox.publish(
        EventType.TASK_LEASED,
        {"task_id": task_id, "lease_id": lease.lease_id, "fence": lease.fence},
        run_id=run_id,
        task_id=task_id,
    )
