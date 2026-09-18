"""Postgres projections (mirrors sqlite/projections.py).

Reads use JSONB/ TIMESTAMPTZ columns; decodes via postgres serialization helpers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from adapters.postgres.serialization import (
    TaskRow,
    decode_envelope,
    decode_task,
    decode_timestamp_pg,
)
from packages.application.ports.workflow_engine import (
    DispatchOwnership,
    LeaseHolder,
    RetrySchedule,
    TaskCompletion,
)
from packages.domain.events import EventEnvelope
from packages.domain.task_state import ResearchTaskState


def _get_task_json(row: Any) -> str:
    val: Any = row["task_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def _get_contract_json(row: Any) -> str:
    val: Any = row["contract_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def _get_envelope_json(row: Any) -> str:
    val: Any = row["envelope_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def list_tasks(conn: Any, run_id: str) -> tuple[TaskRow, ...]:
    rows: Any = conn.execute(
        "SELECT task_json, contract_json, status FROM tasks WHERE run_id = %s ORDER BY created_at",
        (run_id,),
    ).fetchall()
    result: list[TaskRow] = []
    for row in rows:
        entry = decode_task(_get_task_json(row), _get_contract_json(row))
        result.append(
            TaskRow(task=replace(entry.task, status=row["status"]), contract=entry.contract)
        )
    return tuple(result)


def deliveries(conn: Any) -> dict[str, int]:
    rows: Any = conn.execute(
        "SELECT idempotency_key FROM tasks WHERE idempotency_key IS NOT NULL"
    ).fetchall()
    keys = [row["idempotency_key"] for row in rows]
    rows2: Any = conn.execute("SELECT task_id FROM tasks WHERE idempotency_key IS NULL").fetchall()
    task_ids = [row["task_id"] for row in rows2]
    return {key: 1 for key in [*keys, *task_ids]}


def completed(conn: Any) -> dict[str, TaskCompletion]:
    rows: Any = conn.execute(
        "SELECT task_id, status FROM tasks WHERE status IN ('SUCCEEDED', 'FAILED')"
    ).fetchall()
    return {
        row["task_id"]: TaskCompletion(task_id=row["task_id"], outcome=row["status"])
        for row in rows
    }


def cancelled(conn: Any) -> set[str]:
    rows: Any = conn.execute("SELECT task_id FROM tasks WHERE cancelled = TRUE").fetchall()
    return {row["task_id"] for row in rows}


def due_retries(conn: Any, run_id: str, now: datetime) -> tuple[str, ...]:
    """该 run 里**已经到期**的重排任务 ids（SQLite 侧同一判据，见 sqlite/projections.py）。

    与 claim 候选扫描、`retry_schedule` 同一列同一判据；`now` 由调用方按权威时钟给出
    （生产：`server_now` → DB 时钟；测试：注入时钟），与写 `retry_at` 时同一个源。
    """
    rows: Any = conn.execute(
        "SELECT task_id FROM tasks WHERE run_id = %s AND status = %s"
        " AND (retry_at IS NULL OR retry_at <= %s) ORDER BY task_id",
        (run_id, ResearchTaskState.State.RETRY_SCHEDULED, now),
    ).fetchall()
    return tuple(str(row["task_id"]) for row in rows)


def retry_schedule(conn: Any, run_id: str, now: datetime) -> RetrySchedule:
    """该 run 的重排读面（未到期条数 / 已到期条数 / 最近未到期期限）。

    与 claim 候选扫描、`due_retry_task_ids` 同一列同一判据；`now` 由调用方按权威
    时钟给出（生产：`server_now` → DB 时钟；测试：注入时钟），与写 `retry_at` 时
    同一个源。分类在 SQL 之外做，好让"最近未到期期限"和计数出自同一遍扫描。

    单 run 版就是批量版的一条（`retry_schedules`）——判据只有一处。
    """
    return retry_schedules(conn, (run_id,), now)[run_id]


def retry_schedules(conn: Any, run_ids: tuple[str, ...], now: datetime) -> dict[str, RetrySchedule]:
    """一批 run 的重排读面：一次读回答整批。

    取数走 `_dispatch_facts`（**一条语句**，与租约面同语句）——过滤仍走 `= ANY(%s)`
    （**绑定参数**：psycopg 把 list 适配成数组，SQL 里没有拼进去的值）；每个请求到的
    run_id 都有条目（未知/无重排行 ⇒ 全零 `RetrySchedule`）。分类与单 run 版共用
    `_summarize_retries`，所以两个入口不会各算各的。
    """
    deadlines, _ = _dispatch_facts(conn, run_ids, now)
    return {run_id: _summarize_retries(items, now) for run_id, items in deadlines.items()}


def _summarize_retries(deadlines: list[datetime | None], now: datetime) -> RetrySchedule:
    """重排行分类（计数 + 最近未到期期限）——单 run 与批量共用同一段。"""
    scheduled = 0
    due = 0
    next_retry_at: datetime | None = None
    for value in deadlines:
        if value is None or value <= now:
            due += 1
            continue
        scheduled += 1
        if next_retry_at is None or value < next_retry_at:
            next_retry_at = value
    return RetrySchedule(
        scheduled=scheduled,
        due=due,
        next_retry_at=decode_timestamp_pg(next_retry_at) if next_retry_at is not None else None,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:  # defensive: treat naive DB result as UTC
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def live_lease_holders(
    conn: Any, run_id: str, now: datetime
) -> tuple[tuple[str, str | None, int, datetime | None], ...]:
    """该 run 里**活着**的租约持有者（SQLite 侧同一个判据，见 sqlite/projections.py）。

    "活"= `recover_expired_leases` 回收判据的补集：未过期（`expires_at >= now`）且持有者
    不是 LOST worker。`now` 由调用方按权威时钟给出（生产：`server_now` → DB 时钟；测试：
    注入时钟），与回收方同一个源。`lease_id` 有意不读（作业面凭据不进控制面读面）。

    单 run 版就是批量版的一条（`live_lease_holders_many`）。
    """
    return live_lease_holders_many(conn, (run_id,), now)[run_id]


def live_lease_holders_many(
    conn: Any, run_ids: tuple[str, ...], now: datetime
) -> dict[str, tuple[tuple[str, str | None, int, datetime | None], ...]]:
    """一批 run 的活租约持有者：一次读回答整批。

    判据与单 run 版逐字相同（同一列、同一个 `now`、同一条 LOST 排除子查询）；取数走
    `_dispatch_facts`（**一条语句**，与重排面同语句），过滤走 `= ANY(%s)` 绑定参数；
    每个请求到的 run_id 都有条目（无持有 ⇒ 空元组）。
    """
    _, holders = _dispatch_facts(conn, run_ids, now)
    return holders


def dispatch_ownership(conn: Any, run_id: str, now: datetime) -> DispatchOwnership:
    """统一派发读面的组合（GOAL-004 cycle 6 = EC-05 ②；与 SQLite 侧同形）。

    两件 canonical 事实一次读出并组合：重排读面 + 活租约持有者。`kind` 由
    `DispatchOwnership` 自己算（同一个组合规则，三实现不会各算各的）；`now` 由调用方
    按权威时钟给出（生产：`server_now` → DB 时钟；测试：注入时钟）。

    单 run 版就是批量版的一条（`dispatch_ownership_many`）——装配只有一处。
    """
    return dispatch_ownership_many(conn, (run_id,), now)[run_id]


def dispatch_ownership_many(
    conn: Any, run_ids: tuple[str, ...], now: datetime
) -> dict[str, DispatchOwnership]:
    """一批 run 的统一派发读面：一趟读一条语句、一个快照回答整批。

    两件 canonical 事实（重排 + 活租约）由 `_dispatch_facts` 的**同一条语句**取出：
    PostgreSQL 对单条语句取一个快照，所以组合 `kind` 的两件事实**同刻**——不会出现
    "重排面已前移、租约面仍是旧值"的撕裂读（并发写只会整条语句落在写前或写后）。
    列表路径因此不按 run 数放大查询，且与逐 run 读逐字同判（含"全零 = `DISPATCH_NONE`"
    的未知 run 边界）。
    """
    deadlines, holders_by_run = _dispatch_facts(conn, run_ids, now)
    return {
        run_id: DispatchOwnership(
            retry=_summarize_retries(deadlines[run_id], now),
            leases=tuple(
                LeaseHolder(
                    task_id=task_id,
                    worker_id=worker_id,
                    fence=fence,
                    expires_at=None if expires_at is None else decode_timestamp_pg(expires_at),
                )
                for task_id, worker_id, fence, expires_at in holders_by_run[run_id]
            ),
        )
        for run_id in deadlines
    }


_FACTS_SQL = (
    "SELECT kind, run_id, retry_at, task_id, worker_id, fence, expires_at FROM ("
    " SELECT 'RETRY'::text AS kind, run_id, retry_at,"
    " NULL::text AS task_id, NULL::text AS worker_id, NULL::bigint AS fence,"
    " NULL::timestamptz AS expires_at FROM tasks WHERE run_id = ANY(%s) AND status = %s"
    " UNION ALL"
    " SELECT 'LEASE'::text AS kind, t.run_id, NULL::timestamptz AS retry_at,"
    " l.task_id, l.worker_id, l.fence, l.expires_at"
    " FROM leases AS l JOIN tasks AS t ON t.task_id = l.task_id"
    " WHERE t.run_id = ANY(%s) AND l.expires_at >= %s"
    " AND (l.worker_id IS NULL OR l.worker_id NOT IN"
    " (SELECT worker_id FROM workers WHERE state = 'LOST'))"
    ") AS facts ORDER BY kind, run_id, task_id"
)


def _dispatch_facts(
    conn: Any, run_ids: tuple[str, ...], now: datetime
) -> tuple[
    dict[str, list[datetime | None]],
    dict[str, tuple[tuple[str, str | None, int, datetime | None], ...]],
]:
    """派发读面的两件事实：**一条语句**取出，调用方各取所需的一面。

    存在理由：`dispatch_ownership` 必须把两件事实组合成**一个**答案，两次独立查询之间
    没有快照保证（PG autocommit 下每条语句各取快照）⇒ 可能撕裂。单条语句（`UNION ALL`
    + 判别列 `kind`）把一致性交给语句快照本身，隔离级别与事务边界都不用动。

    代价（有意）：单面调用（`retry_schedules` / `live_lease_holders_many`）也会读到另一
    面的行——换来"判据只有一处"与同一个快照语义；行数由 `run_id` 集合界住。

    每个请求到的 run_id 两面都有条目（无行 ⇒ 空列表）；空入参不读库。
    """
    ordered = tuple(dict.fromkeys(run_ids))
    deadlines: dict[str, list[datetime | None]] = {run_id: [] for run_id in ordered}
    holders: dict[str, list[tuple[str, str | None, int, datetime | None]]] = {
        run_id: [] for run_id in ordered
    }
    if not ordered:
        return deadlines, {run_id: () for run_id in ordered}
    rows: Any = conn.execute(
        _FACTS_SQL,
        (list(ordered), ResearchTaskState.State.RETRY_SCHEDULED, list(ordered), now),
    ).fetchall()
    for row in rows:
        run_id = str(row["run_id"])
        if row["kind"] == "RETRY":
            value = row["retry_at"]
            deadlines[run_id].append(None if value is None else _as_utc(value))
            continue
        holders[run_id].append((
            str(row["task_id"]),
            None if row["worker_id"] is None else str(row["worker_id"]),
            int(row["fence"] or 0),
            None if row["expires_at"] is None else _as_utc(row["expires_at"]),
        ))
    return deadlines, {run_id: tuple(items) for run_id, items in holders.items()}


def pending_outbox(conn: Any) -> tuple[EventEnvelope, ...]:
    rows: Any = conn.execute(
        "SELECT envelope_json FROM outbox_events WHERE published_at IS NULL ORDER BY created_at"
    ).fetchall()
    return tuple(decode_envelope(_get_envelope_json(row)) for row in rows)


def mark_outbox_published(
    conn: Any, event_ids: tuple[str, ...], now: Callable[[], datetime] | None
) -> None:
    if not event_ids:
        return
    from adapters.postgres.db import now_iso

    ts = now_iso(now)
    with conn.transaction():
        for event_id in event_ids:
            conn.execute(
                "UPDATE outbox_events SET published_at = %s WHERE event_id = %s",
                (ts, event_id),
            )
