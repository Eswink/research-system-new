"""SqliteWorkerRegistry：WorkerRegistry Port 的 SQLite 实现（PLAN-040 WP-A）。

与 `adapters/postgres/worker_registry.py` 同一 Port 契约（contract suite 双实现
验证）：服务端时间权威、心跳 GREATEST 不回拨、世代单调 fail-closed、状态迁移表
唯一来源 `packages.domain.workers.WorkerState`。用途：SQLite 开发路径
`GET /cluster/workers` 与 reaper 生命周期不再依赖 PG（诚实 503 消除）。

时间编码：所有时间戳写入统一 `now_iso` UTC RFC3339（Z 后缀、微秒截断为零），
定长字符串的字典序即时间序，`MAX()/</cutoff` 比较成立。
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect as sqlite_connect
from adapters.sqlite.db import now_iso, parse_iso
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.workers import (
    WorkerGpuObservation,
    WorkerRegistration,
    WorkerState,
)

# 与 adapters/sqlite/db.py SCHEMA_SQL 的 workers 表同形（IF NOT EXISTS 幂等共存）。
_SCHEMA = """
CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    protocol_version TEXT NOT NULL,
    runtime_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    backend_kinds_json TEXT NOT NULL DEFAULT '[]',
    partition_slots_json TEXT NOT NULL DEFAULT '[]',
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    registration_generation INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'REGISTERING',
    last_heartbeat TEXT,
    drain_requested INTEGER NOT NULL DEFAULT 0,
    session_token_sha256 TEXT,
    gpu_observation_json TEXT,
    gpu_observed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# 完整字面量 SQL（每个查询形态一条；数据值一律 ? 绑定）。
_GET_GEN_SQL = "SELECT registration_generation FROM workers WHERE worker_id = ?"
_GET_SQL = (
    "SELECT worker_id, protocol_version, runtime_version, platform, capabilities_json,"
    " backend_kinds_json, partition_slots_json, max_concurrency,"
    " registration_generation, state, last_heartbeat, drain_requested,"
    " session_token_sha256, gpu_observation_json, gpu_observed_at"
    " FROM workers WHERE worker_id = ?"
)
_LIST_SQL = (
    "SELECT worker_id, protocol_version, runtime_version, platform, capabilities_json,"
    " backend_kinds_json, partition_slots_json, max_concurrency,"
    " registration_generation, state, last_heartbeat, drain_requested,"
    " session_token_sha256, gpu_observation_json, gpu_observed_at"
    " FROM workers ORDER BY worker_id"
)
_AUTH_SQL = (
    "SELECT worker_id, protocol_version, runtime_version, platform, capabilities_json,"
    " backend_kinds_json, partition_slots_json, max_concurrency,"
    " registration_generation, state, last_heartbeat, drain_requested,"
    " session_token_sha256, gpu_observation_json, gpu_observed_at"
    " FROM workers WHERE session_token_sha256 = ?"
)
_REQUIRE_STATE_SQL = "SELECT state FROM workers WHERE worker_id = ?"
# 固定四个活跃状态占位符（REGISTERING/READY/BUSY/DRAINING；OFFLINE/LOST 永不回收）。
_STALE_SQL = (
    "SELECT worker_id FROM workers WHERE state IN (?, ?, ?, ?)"
    " AND last_heartbeat IS NOT NULL AND last_heartbeat < ? ORDER BY worker_id"
)
_REGISTER_SQL = (
    "INSERT INTO workers (worker_id, protocol_version, runtime_version, platform,"
    " capabilities_json, backend_kinds_json, partition_slots_json, max_concurrency,"
    " registration_generation, state, last_heartbeat, drain_requested,"
    " gpu_observation_json, gpu_observed_at, created_at, updated_at)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    " ON CONFLICT (worker_id) DO UPDATE SET"
    " protocol_version = excluded.protocol_version,"
    " runtime_version = excluded.runtime_version,"
    " platform = excluded.platform,"
    " capabilities_json = excluded.capabilities_json,"
    " backend_kinds_json = excluded.backend_kinds_json,"
    " partition_slots_json = excluded.partition_slots_json,"
    " max_concurrency = excluded.max_concurrency,"
    " registration_generation = excluded.registration_generation,"
    " state = excluded.state,"
    " last_heartbeat = excluded.last_heartbeat,"
    " drain_requested = 0,"
    " gpu_observation_json = excluded.gpu_observation_json,"
    " gpu_observed_at = excluded.gpu_observed_at,"
    " session_token_sha256 = NULL,"
    " updated_at = excluded.updated_at"
)
_HEARTBEAT_SQL = (
    "UPDATE workers SET last_heartbeat = MAX(COALESCE(last_heartbeat, ?), ?),"
    " updated_at = ? WHERE worker_id = ? AND registration_generation = ?"
)
_SET_STATE_SQL = "UPDATE workers SET state = ?, updated_at = ? WHERE worker_id = ? AND state = ?"
_DRAIN_SQL = (
    "UPDATE workers SET state = ?, drain_requested = 1, updated_at = ?"
    " WHERE worker_id = ? AND state = ?"
)
_LOST_SQL = (
    "UPDATE workers SET state = ?, session_token_sha256 = NULL, updated_at = ?"
    " WHERE worker_id = ? AND state = ?"
)
_TOKEN_SQL = (
    "UPDATE workers SET session_token_sha256 = ?, updated_at = ?"
    " WHERE worker_id = ? AND registration_generation = ?"
)

_ACTIVE_STATES = (
    WorkerState.State.REGISTERING,
    WorkerState.State.READY,
    WorkerState.State.BUSY,
    WorkerState.State.DRAINING,
)


def _decode_observation(value: Any) -> WorkerGpuObservation | None:
    """fail-closed 解码：畸形观测行拒绝读取（InvalidInputError）。"""
    if value is None:
        return None
    data = json.loads(value) if isinstance(value, str) else value
    try:
        return WorkerGpuObservation.from_json_dict(data)
    except ValueError as exc:
        raise InvalidInputError(f"corrupted gpu observation row: {exc}") from exc


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        return list(json.loads(value))
    return list(value)


def _opt_ts(text: Any) -> Timestamp | None:
    return Timestamp(parse_iso(text)) if text else None


def _row_to_registration(row: sqlite3.Row) -> WorkerRegistration:
    return WorkerRegistration(
        worker_id=str(row["worker_id"]),
        protocol_version=str(row["protocol_version"]),
        runtime_version=str(row["runtime_version"]),
        capabilities=frozenset(str(c) for c in _as_list(row["capabilities_json"])),
        backend_kinds=frozenset(str(b) for b in _as_list(row["backend_kinds_json"])),
        platform=str(row["platform"]),
        partition_slots=frozenset(int(s) for s in _as_list(row["partition_slots_json"])),
        max_concurrency=int(row["max_concurrency"]),
        registration_generation=int(row["registration_generation"]),
        state=str(row["state"]),
        last_heartbeat=_opt_ts(row["last_heartbeat"]),
        drain_requested=bool(row["drain_requested"]),
        gpu_observation=_decode_observation(row["gpu_observation_json"]),
        gpu_observed_at=_opt_ts(row["gpu_observed_at"]),
    )


class SqliteWorkerRegistry(SqliteAdapterBase):
    """WorkerRegistry on SQLite；`now` 仅供确定性测试注入（同 PG 语义）。"""

    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("worker_registry")
        self._now = now
        if connection is None:
            self._owns_connection = True
            self._conn = sqlite_connect(":memory:")
        else:
            self._owns_connection = False
            self._conn = connection
        self._conn.row_factory = sqlite3.Row
        bootstrapper = getattr(self._conn, "executescript")
        bootstrapper(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def _run(self, statement: str, params: tuple[Any, ...] = ()) -> Any:
        runner = getattr(self._conn, "execute")
        return runner(statement, params)

    # --- 时钟（服务端权威，定长 UTC Z 格式）---

    def _server_now(self) -> datetime:
        value = datetime.now(timezone.utc) if self._now is None else self._now()
        return value.astimezone(timezone.utc).replace(microsecond=0)

    def _server_time(self) -> str:
        return now_iso(self._server_now)

    # --- 写路径 ---

    def register(self, registration: WorkerRegistration) -> WorkerRegistration:
        self._ensure_open()
        ts = self._server_time()
        obs = registration.gpu_observation
        obs_json = json.dumps(obs.to_json_dict()) if obs is not None else None
        observed_at = ts if obs_json is not None else None
        existing = self._run(_GET_GEN_SQL, (registration.worker_id,)).fetchone()
        next_gen = (int(existing["registration_generation"]) if existing else 0) + 1
        with self._conn:
            self._run(
                _REGISTER_SQL,
                (
                    registration.worker_id,
                    registration.protocol_version,
                    registration.runtime_version,
                    registration.platform,
                    json.dumps(sorted(registration.capabilities)),
                    json.dumps(sorted(registration.backend_kinds)),
                    json.dumps(sorted(registration.partition_slots)),
                    registration.max_concurrency,
                    next_gen,
                    WorkerState.State.REGISTERING,
                    ts,
                    0,
                    obs_json,
                    observed_at,
                    ts,
                    ts,
                ),
            )
        self._record("register", registration.worker_id, result=f"gen={next_gen}")
        stored = self.get(registration.worker_id)
        assert stored is not None
        return stored

    def heartbeat(self, worker_id: str, generation: int) -> bool:
        self._ensure_open()
        ts = self._server_time()
        with self._conn:
            cur = self._run(_HEARTBEAT_SQL, (ts, ts, ts, worker_id, generation))
        accepted = int(cur.rowcount) > 0
        self._record("heartbeat", worker_id, result="ok" if accepted else "rejected")
        return accepted

    def transition(self, worker_id: str, event: str) -> WorkerRegistration:
        self._ensure_open()
        current = self._require_row(worker_id)
        expected = str(current["state"])
        new_state = WorkerState.transition(expected, event)
        self._apply_state(worker_id, expected, new_state, event)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def drain(self, worker_id: str) -> WorkerRegistration:
        self._ensure_open()
        current = self._require_row(worker_id)
        expected = str(current["state"])
        new_state = WorkerState.transition(expected, WorkerState.Transition.DRAIN_REQUESTED)
        ts = self._server_time()
        with self._conn:
            self._run(_DRAIN_SQL, (new_state, ts, worker_id, expected))
        self._record("drain", worker_id, result=new_state)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def mark_lost(self, worker_id: str) -> WorkerRegistration:
        self._ensure_open()
        current = self._require_row(worker_id)
        expected = str(current["state"])
        new_state = WorkerState.transition(expected, WorkerState.Transition.HEARTBEAT_EXPIRED)
        ts = self._server_time()
        with self._conn:
            self._run(_LOST_SQL, (new_state, ts, worker_id, expected))
        self._record("mark_lost", worker_id, result=new_state)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def set_session_token(self, worker_id: str, generation: int, token_sha256: str) -> bool:
        self._ensure_open()
        ts = self._server_time()
        with self._conn:
            cur = self._run(_TOKEN_SQL, (token_sha256, ts, worker_id, generation))
        bound = int(cur.rowcount) > 0
        self._record("set_session_token", worker_id, result="ok" if bound else "rejected")
        return bound

    # --- 读路径 ---

    def authenticate(self, token_sha256: str) -> WorkerRegistration | None:
        self._ensure_open()
        row = self._run(_AUTH_SQL, (token_sha256,)).fetchone()
        return _row_to_registration(row) if row is not None else None

    def list_stale(self, stale_seconds: float) -> tuple[str, ...]:
        self._ensure_open()
        cutoff = now_iso(lambda: self._server_now() - timedelta(seconds=stale_seconds))
        rows = self._run(_STALE_SQL, (*_ACTIVE_STATES, cutoff)).fetchall()
        ids = tuple(str(row["worker_id"]) for row in rows)
        self._record("list_stale", f"{stale_seconds}", result=str(len(ids)))
        return ids

    def get(self, worker_id: str) -> WorkerRegistration | None:
        self._ensure_open()
        row = self._run(_GET_SQL, (worker_id,)).fetchone()
        return _row_to_registration(row) if row is not None else None

    def list_workers(self) -> tuple[WorkerRegistration, ...]:
        self._ensure_open()
        rows = self._run(_LIST_SQL).fetchall()
        return tuple(_row_to_registration(row) for row in rows)

    # --- 内部 ---

    def _require_row(self, worker_id: str) -> sqlite3.Row:
        row = self._run(_REQUIRE_STATE_SQL, (worker_id,)).fetchone()
        if row is None:
            raise InvalidInputError(f"unknown worker: {worker_id}")
        assert isinstance(row, sqlite3.Row)
        return row

    def _apply_state(self, worker_id: str, expected: str, new_state: str, event: str) -> None:
        ts = self._server_time()
        with self._conn:
            self._run(_SET_STATE_SQL, (new_state, ts, worker_id, expected))
        self._record("transition", f"{worker_id}:{event}", result=new_state)
