"""PostgreSQL WorkerRegistry: worker lifecycle + server-time heartbeat authority.

Production uses PostgreSQL `now()` as the sole clock (worker self-reported
timestamps never participate). An optional injectable `now` exists only for
deterministic contract tests, mirroring `PostgresWorkflowEngine`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from psycopg.rows import dict_row

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from adapters.postgres.serialization import decode_timestamp_pg
from packages.application.ports.errors import InvalidInputError
from packages.domain.state_base import InvalidTransitionError
from packages.domain.workers import WorkerGpuObservation, WorkerRegistration, WorkerState

_COLUMNS = (
    "worker_id, protocol_version, runtime_version, platform, capabilities_json, "
    "backend_kinds_json, partition_slots_json, max_concurrency, registration_generation, "
    "state, last_heartbeat, drain_requested, gpu_observation_json, gpu_observed_at"
)

# Static upsert SQL (values bound as parameters; {time_sql} is the only
# interpolation — server-time expression or a bound test-clock placeholder).
# M17 freshness layer 1: registration is the truth — the GPU observation is
# replaced wholesale on every (re)register.
_REGISTER_SQL = (
    "INSERT INTO workers (" + _COLUMNS + ", created_at, updated_at) "
    "VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, "
    "{time_sql}, %s, %s::jsonb, CASE WHEN %s THEN {time_sql} ELSE NULL END, "
    "{time_sql}, {time_sql}) "
    "ON CONFLICT (worker_id) DO UPDATE SET "
    "protocol_version = EXCLUDED.protocol_version, "
    "runtime_version = EXCLUDED.runtime_version, "
    "platform = EXCLUDED.platform, "
    "capabilities_json = EXCLUDED.capabilities_json, "
    "backend_kinds_json = EXCLUDED.backend_kinds_json, "
    "partition_slots_json = EXCLUDED.partition_slots_json, "
    "max_concurrency = EXCLUDED.max_concurrency, "
    "registration_generation = EXCLUDED.registration_generation, "
    "state = EXCLUDED.state, "
    "last_heartbeat = EXCLUDED.last_heartbeat, "
    "drain_requested = FALSE, "
    "gpu_observation_json = EXCLUDED.gpu_observation_json, "
    "gpu_observed_at = EXCLUDED.gpu_observed_at, "
    "session_token_sha256 = NULL, "
    "updated_at = {time_sql}"
)


def _as_list(value: Any) -> list[Any]:
    """JSONB arrives pre-decoded as a list via psycopg; tolerate raw text too."""
    if isinstance(value, str):
        return list(json.loads(value))
    return list(value)


def _decode_observation(value: Any) -> WorkerGpuObservation | None:
    """fail-closed 解码：畸形观测行拒绝读取（InvalidInputError）。"""
    if value is None:
        return None
    data = json.loads(value) if isinstance(value, str) else value
    try:
        return WorkerGpuObservation.from_json_dict(data)
    except ValueError as exc:
        raise InvalidInputError(f"corrupted gpu observation row: {exc}") from exc


def _row_to_registration(row: dict[str, Any]) -> WorkerRegistration:
    heartbeat = row["last_heartbeat"]
    observed_at = row.get("gpu_observed_at")
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
        last_heartbeat=decode_timestamp_pg(heartbeat) if heartbeat is not None else None,
        drain_requested=bool(row["drain_requested"]),
        gpu_observation=_decode_observation(row.get("gpu_observation_json")),
        gpu_observed_at=decode_timestamp_pg(observed_at) if observed_at is not None else None,
    )


class PostgresWorkerRegistry(PostgresAdapterBase):
    """WorkerRegistry on PostgreSQL; `now` injectable for deterministic tests."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connection: Any | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("worker_registry")
        self._now = now
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresWorkerRegistry requires dsn or connection")
            self._conn = pg_connect(resolved)
        try:
            self._conn.row_factory = dict_row
        except Exception:
            pass

    def close(self) -> None:
        if getattr(self, "_owns_connection", False):
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def _time_expr(self) -> tuple[str, list[Any]]:
        """Server-time SQL expression, or bound param when a test clock is set."""
        if self._now is None:
            return "now()", []
        return "%s", [self._now()]

    def register(self, registration: WorkerRegistration) -> WorkerRegistration:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        observation = registration.gpu_observation
        obs_json = json.dumps(observation.to_json_dict()) if observation is not None else None
        with self._conn.transaction():
            existing: Any = self._conn.execute(
                "SELECT registration_generation FROM workers WHERE worker_id = %s FOR UPDATE",
                (registration.worker_id,),
            ).fetchone()
            next_gen = (int(existing["registration_generation"]) if existing else 0) + 1
            self._conn.execute(
                _REGISTER_SQL.format(time_sql=time_sql),
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
                    *time_params,
                    False,
                    obs_json,
                    obs_json is not None,
                    *time_params,
                    *time_params,
                    *time_params,
                ),
            )
        self._record("register", registration.worker_id, result=f"gen={next_gen}")
        stored = self.get(registration.worker_id)
        assert stored is not None
        return stored

    def heartbeat(self, worker_id: str, generation: int) -> bool:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        cur: Any = self._conn.execute(
            f"UPDATE workers SET last_heartbeat = GREATEST(last_heartbeat, {time_sql}), "
            f"updated_at = {time_sql} "
            "WHERE worker_id = %s AND registration_generation = %s",
            (*time_params, *time_params, worker_id, generation),
        )
        accepted = int(cur.rowcount) > 0
        self._record("heartbeat", worker_id, result="ok" if accepted else "rejected")
        return accepted

    def _require_row(self, worker_id: str) -> dict[str, Any]:
        row: Any = self._conn.execute(
            f"SELECT {_COLUMNS} FROM workers WHERE worker_id = %s", (worker_id,)
        ).fetchone()
        if row is None:
            raise InvalidInputError(f"unknown worker: {worker_id}")
        return dict(row)

    def transition(self, worker_id: str, event: str) -> WorkerRegistration:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        illegal: InvalidTransitionError | None = None
        with self._conn.transaction():
            row = self._require_row(worker_id)
            current = _row_to_registration(row)
            try:
                new_state = WorkerState.transition(current.state, event)
            except InvalidTransitionError as exc:
                illegal = exc
                new_state = current.state
            if illegal is None:
                cur: Any = self._conn.execute(
                    f"UPDATE workers SET state = %s, updated_at = {time_sql} "
                    "WHERE worker_id = %s AND state = %s",
                    (*time_params, new_state, worker_id, current.state),
                )
                if int(cur.rowcount) == 0:
                    raise InvalidInputError(f"worker {worker_id} state changed concurrently")
        if illegal is not None:
            # Raise outside the transaction context: a frozen-dataclass exception
            # cannot propagate through psycopg's transaction __exit__.
            self._record("transition", f"{worker_id}:{event}", error="InvalidTransitionError")
            raise illegal
        self._record("transition", f"{worker_id}:{event}", result=new_state)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def drain(self, worker_id: str) -> WorkerRegistration:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        illegal: InvalidTransitionError | None = None
        with self._conn.transaction():
            row = self._require_row(worker_id)
            current = _row_to_registration(row)
            try:
                new_state = WorkerState.transition(
                    current.state, WorkerState.Transition.DRAIN_REQUESTED
                )
            except InvalidTransitionError as exc:
                illegal = exc
                new_state = current.state
            if illegal is None:
                self._conn.execute(
                    f"UPDATE workers SET state = %s, drain_requested = TRUE, "
                    f"updated_at = {time_sql} WHERE worker_id = %s",
                    (*time_params, new_state, worker_id),
                )
        if illegal is not None:
            raise illegal
        self._record("drain", worker_id, result=new_state)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def mark_lost(self, worker_id: str) -> WorkerRegistration:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        illegal: InvalidTransitionError | None = None
        with self._conn.transaction():
            row = self._require_row(worker_id)
            current = _row_to_registration(row)
            try:
                new_state = WorkerState.transition(
                    current.state, WorkerState.Transition.HEARTBEAT_EXPIRED
                )
            except InvalidTransitionError as exc:
                illegal = exc
                new_state = current.state
            if illegal is None:
                self._conn.execute(
                    f"UPDATE workers SET state = %s, session_token_sha256 = NULL, "
                    f"updated_at = {time_sql} WHERE worker_id = %s",
                    (*time_params, new_state, worker_id),
                )
        if illegal is not None:
            raise illegal
        self._record("mark_lost", worker_id, result=new_state)
        stored = self.get(worker_id)
        assert stored is not None
        return stored

    def set_session_token(self, worker_id: str, generation: int, token_sha256: str) -> bool:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        cur: Any = self._conn.execute(
            f"UPDATE workers SET session_token_sha256 = %s, updated_at = {time_sql} "
            "WHERE worker_id = %s AND registration_generation = %s",
            (token_sha256, *time_params, worker_id, generation),
        )
        bound = int(cur.rowcount) > 0
        self._record("set_session_token", worker_id, result="ok" if bound else "rejected")
        return bound

    def authenticate(self, token_sha256: str) -> WorkerRegistration | None:
        self._ensure_open()
        row: Any = self._conn.execute(
            f"SELECT {_COLUMNS} FROM workers WHERE session_token_sha256 = %s", (token_sha256,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_registration(dict(row))

    def list_stale(self, stale_seconds: float) -> tuple[str, ...]:
        self._ensure_open()
        time_sql, time_params = self._time_expr()
        # Schedulable-but-not-reaped states only: OFFLINE is terminal (never
        # reaped) and LOST is already reaped (no per-pass no-op re-listing).
        active_states = (
            WorkerState.State.REGISTERING,
            WorkerState.State.READY,
            WorkerState.State.BUSY,
            WorkerState.State.DRAINING,
        )
        rows: Any = self._conn.execute(
            f"SELECT worker_id FROM workers "
            f"WHERE state = ANY(%s) AND last_heartbeat < {time_sql} - make_interval(secs => %s) "
            "ORDER BY worker_id",
            (list(active_states), *time_params, stale_seconds),
        ).fetchall()
        ids = tuple(str(r["worker_id"]) for r in rows)
        self._record("list_stale", f"{stale_seconds}", result=str(len(ids)))
        return ids

    def get(self, worker_id: str) -> WorkerRegistration | None:
        self._ensure_open()
        row: Any = self._conn.execute(
            f"SELECT {_COLUMNS} FROM workers WHERE worker_id = %s", (worker_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_registration(dict(row))

    def list_workers(self) -> tuple[WorkerRegistration, ...]:
        self._ensure_open()
        rows: Any = self._conn.execute(
            f"SELECT {_COLUMNS} FROM workers ORDER BY worker_id"
        ).fetchall()
        return tuple(_row_to_registration(dict(r)) for r in rows)
