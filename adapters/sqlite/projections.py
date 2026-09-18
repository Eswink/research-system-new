"""SqliteWorkflowEngine 的可观察投影（M5 Fake 语义对齐 + outbox 读取）。"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime

from adapters.sqlite.db import now_iso
from adapters.sqlite.serialization import TaskRow, decode_envelope, decode_task, decode_timestamp
from packages.application.ports.workflow_engine import (
    DispatchOwnership,
    LeaseHolder,
    RetrySchedule,
    TaskCompletion,
)
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

    单 run 版就是批量版的一条（`retry_schedules`）——判据只有一处，不会两套漂移。
    """
    return retry_schedules(conn, (run_id,), now_text)[run_id]


def retry_schedules(
    conn: sqlite3.Connection, run_ids: tuple[str, ...], now_text: str
) -> dict[str, tuple[int, int, str | None]]:
    """一批 run 的重排读面：一次读回答整批。

    取数走 `_dispatch_facts`（**一条语句**，与租约面同语句）——过滤仍走 `json_each(?)`
    （**绑定参数**，SQL 里没有拼进去的值）；每个请求到的 run_id 都有条目
    （未知/无重排行 ⇒ `(0, 0, None)`）。分类与单 run 版共用 `_summarize_retries`。
    """
    deadlines, _ = _dispatch_facts(conn, run_ids, now_text)
    return {run_id: _summarize_retries(items, now_text) for run_id, items in deadlines.items()}


def _summarize_retries(
    deadlines: Sequence[str | None], now_text: str
) -> tuple[int, int, str | None]:
    """重排行分类：(未到期条数, 已到期条数, 最近未到期期限)——单 run 与批量共用。"""
    scheduled = 0
    due = 0
    next_retry_at: str | None = None
    for text in deadlines:
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

    单 run 版就是批量版的一条（`live_lease_holders_many`）。
    """
    return live_lease_holders_many(conn, (run_id,), now_text)[run_id]


def live_lease_holders_many(
    conn: sqlite3.Connection, run_ids: tuple[str, ...], now_text: str
) -> dict[str, tuple[tuple[str, str | None, int, str | None], ...]]:
    """一批 run 的活租约持有者：一次读回答整批。

    判据与单 run 版逐字相同（同一列、同一个 `now_text`、同一条 LOST 排除子查询）；
    取数走 `_dispatch_facts`（**一条语句**，与重排面同语句），过滤走 `json_each(?)`
    绑定参数；每个请求到的 run_id 都有条目（无持有 ⇒ 空元组）。
    """
    _, holders = _dispatch_facts(conn, run_ids, now_text)
    return holders


_FACTS_SQL = (
    "SELECT kind, run_id, retry_at, task_id, worker_id, fence, expires_at FROM ("
    " SELECT 'RETRY' AS kind, run_id, retry_at,"
    " NULL AS task_id, NULL AS worker_id, NULL AS fence, NULL AS expires_at FROM tasks"
    " WHERE run_id IN (SELECT value FROM json_each(?)) AND status = ?"
    " UNION ALL"
    " SELECT 'LEASE' AS kind, t.run_id, NULL AS retry_at,"
    " l.task_id, l.worker_id, l.fence, l.expires_at"
    " FROM leases AS l JOIN tasks AS t ON t.task_id = l.task_id"
    " WHERE t.run_id IN (SELECT value FROM json_each(?)) AND l.expires_at >= ?"
    " AND (l.worker_id IS NULL OR l.worker_id NOT IN"
    " (SELECT worker_id FROM workers WHERE state = 'LOST'))"
    ") AS facts ORDER BY kind, run_id, task_id"
)


def _dispatch_facts(
    conn: sqlite3.Connection, run_ids: tuple[str, ...], now_text: str
) -> tuple[
    dict[str, list[str | None]],
    dict[str, tuple[tuple[str, str | None, int, str | None], ...]],
]:
    """派发读面的两件事实：**一条语句**取出，调用方各取所需的一面。

    存在理由：`_dispatch_ownerships` 必须把两件事实组合成**一个**答案，而
    `SerializedConnection` 的锁与"行取尽"只保证**单条语句**的自洽
    （`adapters/sqlite/db.py`）——语句之间别的连接可以提交，两次独立查询会撕裂。单条
    语句（`UNION ALL` + 判别列 `kind`）把一致性交给语句本身，锁与事务边界都不用动。

    代价（有意）：单面调用（`retry_schedules` / `live_lease_holders_many`）也会读到另一
    面的行——换来"判据只有一处"与同一个快照语义；行数由 `run_id` 集合界住。

    每个请求到的 run_id 两面都有条目（无行 ⇒ 空列表）；空入参不读库。
    """
    ordered = tuple(dict.fromkeys(run_ids))
    deadlines: dict[str, list[str | None]] = {run_id: [] for run_id in ordered}
    holders: dict[str, list[tuple[str, str | None, int, str | None]]] = {
        run_id: [] for run_id in ordered
    }
    if not ordered:
        return deadlines, {run_id: () for run_id in ordered}
    rows = conn.execute(
        _FACTS_SQL,
        (
            json.dumps(list(ordered)),
            ResearchTaskState.State.RETRY_SCHEDULED,
            json.dumps(list(ordered)),
            now_text,
        ),
    ).fetchall()
    for row in rows:
        run_id = str(row["run_id"])
        if row["kind"] == "RETRY":
            value = row["retry_at"]
            deadlines[run_id].append(None if value is None else str(value))
            continue
        holders[run_id].append((
            str(row["task_id"]),
            None if row["worker_id"] is None else str(row["worker_id"]),
            int(row["fence"] or 0),
            None if row["expires_at"] is None else str(row["expires_at"]),
        ))
    return deadlines, {run_id: tuple(items) for run_id, items in holders.items()}


def dispatch_ownerships(
    conn: sqlite3.Connection, run_ids: tuple[str, ...], now_text: str
) -> dict[str, DispatchOwnership]:
    """一批 run 的统一派发读面：一趟读一条语句、一个快照回答整批。

    两件 canonical 事实（重排 + 活租约）由 `_dispatch_facts` 的**同一条语句**取出：
    `SerializedConnection` 只保证单条语句的自洽，所以组合 `kind` 的两件事实必须同刻
    ——不会出现"重排面已前移、租约面仍是旧值"的撕裂读。装配与单 run 读共用这一处
    （`SqliteWorkflowEngine._dispatch_ownerships` 只负责 `_ensure_open` 与记账）。
    """
    deadlines_by_run, holders_by_run = _dispatch_facts(conn, run_ids, now_text)
    ownerships: dict[str, DispatchOwnership] = {}
    for run_id, deadlines in deadlines_by_run.items():
        schedule = _summarize_retries(deadlines, now_text)
        ownerships[run_id] = DispatchOwnership(
            retry=RetrySchedule(
                scheduled=schedule[0],
                due=schedule[1],
                next_retry_at=(decode_timestamp(schedule[2]) if schedule[2] is not None else None),
            ),
            leases=tuple(
                LeaseHolder(
                    task_id=task_id,
                    worker_id=worker_id,
                    fence=fence,
                    expires_at=(None if expires_at is None else decode_timestamp(expires_at)),
                )
                for task_id, worker_id, fence, expires_at in holders_by_run[run_id]
            ),
        )
    return ownerships


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
