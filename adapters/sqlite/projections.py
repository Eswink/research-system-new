"""SqliteWorkflowEngine 的可观察投影（M5 Fake 语义对齐 + outbox 读取）。"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from adapters.sqlite.db import now_iso
from adapters.sqlite.serialization import TaskRow, decode_envelope, decode_task
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventEnvelope
from packages.domain.task_state import ResearchTaskState


def list_tasks(conn: sqlite3.Connection, run_id: str) -> tuple[TaskRow, ...]:
    """run 内任务投影（canonical state 读取，非审计事件）。"""
    rows = conn.execute(
        "SELECT task_json, contract_json, status FROM tasks WHERE run_id = ? ORDER BY created_at",
        (run_id,),
    ).fetchall()
    result: list[TaskRow] = []
    for row in rows:
        entry = decode_task(row["task_json"], row["contract_json"])
        result.append(
            TaskRow(task=replace(entry.task, status=row["status"]), contract=entry.contract)
        )
    return tuple(result)


def deliveries(conn: sqlite3.Connection) -> dict[str, int]:
    """投递投影：每个 idempotency key（或 task id）恰一次（M5 语义对齐）。"""
    keys = [
        row["idempotency_key"]
        for row in conn.execute(
            "SELECT idempotency_key FROM tasks WHERE idempotency_key IS NOT NULL"
        )
    ]
    task_ids = [
        row["task_id"]
        for row in conn.execute("SELECT task_id FROM tasks WHERE idempotency_key IS NULL")
    ]
    return {key: 1 for key in [*keys, *task_ids]}


def completed(conn: sqlite3.Connection) -> dict[str, TaskCompletion]:
    """完成投影：status 为 SUCCEEDED/FAILED 的任务（M5 语义对齐）。"""
    rows = conn.execute(
        "SELECT task_id, status FROM tasks WHERE status IN ('SUCCEEDED', 'FAILED')"
    ).fetchall()
    return {
        row["task_id"]: TaskCompletion(task_id=row["task_id"], outcome=row["status"])
        for row in rows
    }


def cancelled(conn: sqlite3.Connection) -> set[str]:
    """取消投影：cancelled=1 的任务（M5 语义对齐）。"""
    rows = conn.execute("SELECT task_id FROM tasks WHERE cancelled = 1").fetchall()
    return {row["task_id"] for row in rows}


def due_retries(conn: sqlite3.Connection, run_id: str, now_text: str) -> tuple[str, ...]:
    """该 run 里**已经到期**的重排任务（与 claim 候选扫描同一判据）。

    任务投影不携带 `retry_at`（期限只在任务行/事件里），所以"能不能再交付一次"只能
    问这一句。`now_text` 由调用方按权威时钟给出（生产：DB 时钟；测试：注入时钟），
    与写 `retry_at` 时同一个源。
    """
    rows = conn.execute(
        "SELECT task_id FROM tasks WHERE run_id = ? AND status = ?"
        " AND (retry_at IS NULL OR retry_at <= ?) ORDER BY task_id",
        (run_id, ResearchTaskState.State.RETRY_SCHEDULED, now_text),
    ).fetchall()
    return tuple(str(row["task_id"]) for row in rows)


def retry_schedule(
    conn: sqlite3.Connection, run_id: str, now_text: str
) -> tuple[int, int, str | None]:
    """该 run 的重排读面：(未到期条数, 已到期条数, 最近未到期期限)。

    与 `due_retries` 同一判据（同一列、同一个 `now_text`），只是回答"还剩几条在等
    时钟、几条现在就能走、下一个期限是什么"。`now_text` 由调用方按权威时钟给出
    （生产：DB 时钟；测试：注入时钟），与写 `retry_at` 时同一个源。
    """
    rows = conn.execute(
        "SELECT retry_at FROM tasks WHERE run_id = ? AND status = ?",
        (run_id, ResearchTaskState.State.RETRY_SCHEDULED),
    ).fetchall()
    scheduled = 0
    due = 0
    next_retry_at: str | None = None
    for row in rows:
        deadline = row["retry_at"]
        text = None if deadline is None else str(deadline)
        if text is None or text <= now_text:
            due += 1
            continue
        scheduled += 1
        if next_retry_at is None or text < next_retry_at:
            next_retry_at = text
    return scheduled, due, next_retry_at


def live_lease_holders(
    conn: sqlite3.Connection, run_id: str, now_text: str
) -> tuple[tuple[str, str | None, int, str | None], ...]:
    """该 run 里**活着**的租约持有者：(task_id, worker_id, fence, expires_at)。

    "活"= `recover_expired_leases` 回收判据的**补集**：未过期（`expires_at >= now`）
    且持有者不是 LOST worker。回收会动手的那条不算持有——读面不许把"马上要被回收"
    说成"有人在派发"。`now_text` 由调用方按权威时钟给出（生产：DB 时钟；测试：注入
    时钟），与写 `expires_at`、与回收方同一个源。

    `worker_id` 为空 = 控制面自己持有（agent session 投递），非空 = worker plane claim。
    `lease_id` 有意不读：它是作业面提交结果的凭据，读面不复制能力面。
    """
    rows = conn.execute(
        "SELECT l.task_id AS task_id, l.worker_id AS worker_id, l.fence AS fence,"
        " l.expires_at AS expires_at FROM leases AS l JOIN tasks AS t ON t.task_id = l.task_id"
        " WHERE t.run_id = ? AND l.expires_at >= ?"
        " AND (l.worker_id IS NULL OR l.worker_id NOT IN"
        " (SELECT worker_id FROM workers WHERE state = 'LOST'))"
        " ORDER BY l.task_id",
        (run_id, now_text),
    ).fetchall()
    return tuple(
        (
            str(row["task_id"]),
            None if row["worker_id"] is None else str(row["worker_id"]),
            int(row["fence"] or 0),
            None if row["expires_at"] is None else str(row["expires_at"]),
        )
        for row in rows
    )


def task_identities(conn: sqlite3.Connection, run_id: str) -> tuple[tuple[str, str, str], ...]:
    """该 run 已登记任务的 (idempotency_key, task_id, status)（确定性排序）。

    specs 每次解析都会生成新的 task id，只有 idempotency key（`run:phase:agent`）
    是稳定身份 ⇒ 重启后的续跑靠这一句把解析结果对齐回 canonical 任务（已成功的不重跑、
    其余用 canonical id 交付）。
    """
    rows = conn.execute(
        "SELECT idempotency_key, task_id, status FROM tasks WHERE run_id = ?"
        " AND idempotency_key IS NOT NULL ORDER BY idempotency_key",
        (run_id,),
    ).fetchall()
    return tuple(
        (str(row["idempotency_key"]), str(row["task_id"]), str(row["status"])) for row in rows
    )


def pending_outbox(conn: sqlite3.Connection) -> tuple[EventEnvelope, ...]:
    """未投递的 outbox 事件（供 EventPublisher 轮询）。"""
    rows = conn.execute(
        "SELECT envelope_json FROM outbox_events WHERE published_at IS NULL ORDER BY created_at"
    ).fetchall()
    return tuple(decode_envelope(row["envelope_json"]) for row in rows)


def mark_outbox_published(
    conn: sqlite3.Connection, event_ids: tuple[str, ...], now: Callable[[], datetime] | None
) -> None:
    """标记事件已投递（幂等）。"""
    if not event_ids:
        return
    with conn:
        for event_id in event_ids:
            conn.execute(
                "UPDATE outbox_events SET published_at = ? WHERE event_id = ?",
                (now_iso(now), event_id),
            )
