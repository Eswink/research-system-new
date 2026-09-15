"""PostgreSQL adapter for ExperimentStore (M14 DS-1 domain state + G14 queue)."""

from __future__ import annotations

import json
from typing import Any, cast

from adapters.contracts.experiment_rows import (
    decode_audit,
    decode_plan,
    decode_queue_entry,
    decode_run,
    encode_audit,
    encode_plan,
    encode_queue_entry,
    encode_run,
)
from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry
from packages.domain.experiment_state import ExperimentQueueState
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.state_base import InvalidTransitionError

# G14 claim SQL: the QUEUED candidate is picked in COALESCE(not_before, created_at)
# order and locked with SKIP LOCKED, so two dispatchers never claim the same entry.
# Due-ness itself is decided by the domain (`ExperimentQueueEntry.is_due`): if the
# earliest-ranked candidate is not due yet, no later-ranked entry can be due.
_SELECT_QUEUED_CANDIDATE = (
    "SELECT entry_json FROM experiment_queue WHERE state = %s"
    " ORDER BY COALESCE(not_before, created_at) ASC, created_at ASC"
    " FOR UPDATE SKIP LOCKED LIMIT 1"
)
_SELECT_DISPATCHING = (
    "SELECT entry_json FROM experiment_queue WHERE state = %s"
    " ORDER BY claimed_at ASC FOR UPDATE SKIP LOCKED"
)
_LIST_QUEUE_SQL = (
    "SELECT entry_json FROM experiment_queue WHERE project_id = %s ORDER BY created_at ASC"
)
_LIST_PLANS_SQL = "SELECT plan_json FROM experiment_plans ORDER BY created_at DESC"
_LIST_PLANS_BY_STATE_SQL = (
    "SELECT plan_json FROM experiment_plans WHERE plan_json ->> 'state' = %s"
    " ORDER BY created_at DESC"
)
_GET_QUEUE_SQL = "SELECT entry_json FROM experiment_queue WHERE entry_id = %s"
_UPSERT_QUEUE_SQL = (
    "INSERT INTO experiment_queue (entry_id, project_id, plan_id, state, not_before,"
    " claimed_at, entry_json, created_at, updated_at)"
    " VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)"
    " ON CONFLICT (entry_id) DO UPDATE SET project_id=EXCLUDED.project_id,"
    " plan_id=EXCLUDED.plan_id, state=EXCLUDED.state, not_before=EXCLUDED.not_before,"
    " claimed_at=EXCLUDED.claimed_at, entry_json=EXCLUDED.entry_json,"
    " updated_at=EXCLUDED.updated_at"
)
_CONDITIONAL_QUEUE_SQL = (
    "UPDATE experiment_queue SET state = %s, claimed_at = %s, entry_json = %s::jsonb,"
    " updated_at = %s WHERE entry_id = %s AND state = %s"
)


class PostgresExperimentStore(PostgresAdapterBase):
    """PostgreSQL ExperimentStore; plan/run/audit port: id -> JSONB row."""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("experiment_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresExperimentStore requires dsn or connection")
            self._conn = pg_connect(resolved)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    # --- ExperimentPlan ---

    def save_plan(self, plan: ExperimentPlan) -> None:
        self._ensure_open()
        payload = encode_plan(plan)
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO experiment_plans (plan_id, plan_json, created_at)"
                " VALUES (%s, %s::jsonb, %s)"
                " ON CONFLICT (plan_id) DO UPDATE SET plan_json=EXCLUDED.plan_json,"
                " created_at=EXCLUDED.created_at",
                (
                    plan.id.value,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_plan", plan.id.value)

    def get_plan(self, plan_id: str) -> ExperimentPlan:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT plan_json FROM experiment_plans WHERE plan_id = %s", (plan_id,)
        ).fetchone()
        if row is None:
            self._record("get_plan", plan_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown experiment plan id: {plan_id}")
        self._record("get_plan", plan_id)
        return decode_plan(_json_of(row["plan_json"]))

    # --- ExperimentRun ---

    def save_run(self, run: ExperimentRun) -> None:
        self._ensure_open()
        payload = encode_run(run)
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO experiment_runs (run_id, plan_id, run_json, created_at)"
                " VALUES (%s, %s, %s::jsonb, %s)"
                " ON CONFLICT (run_id) DO UPDATE SET plan_id=EXCLUDED.plan_id,"
                " run_json=EXCLUDED.run_json, created_at=EXCLUDED.created_at",
                (
                    run.id.value,
                    run.plan_id.value,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_run", run.id.value)

    def get_run(self, run_id: str) -> ExperimentRun:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT run_json FROM experiment_runs WHERE run_id = %s", (run_id,)
        ).fetchone()
        if row is None:
            self._record("get_run", run_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown experiment run id: {run_id}")
        self._record("get_run", run_id)
        return decode_run(_json_of(row["run_json"]))

    # --- ReproducibilityAudit ---

    def save_audit(self, audit: ReproducibilityAudit) -> None:
        self._ensure_open()
        payload = encode_audit(audit)
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO reproducibility_audits (experiment_run_id, audit_id,"
                " audit_json, created_at) VALUES (%s, %s, %s::jsonb, %s)"
                " ON CONFLICT (experiment_run_id) DO UPDATE SET audit_id=EXCLUDED.audit_id,"
                " audit_json=EXCLUDED.audit_json, created_at=EXCLUDED.created_at",
                (
                    audit.experiment_run_id.value,
                    audit.audit_id.value,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_audit", audit.audit_id.value)

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT audit_json FROM reproducibility_audits WHERE experiment_run_id = %s",
            (experiment_run_id,),
        ).fetchone()
        if row is None:
            self._record("get_audit", experiment_run_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown experiment run id: {experiment_run_id}")
        self._record("get_audit", experiment_run_id)
        return decode_audit(_json_of(row["audit_json"]))

    # --- ExperimentPlan list（G14 队列需要计划列表：队列条目引用计划）---

    def list_plans(self, *, state: str | None = None) -> list[ExperimentPlan]:
        self._ensure_open()
        if state is None:
            rows: Any = self._sql(_LIST_PLANS_SQL).fetchall()
        else:
            rows = self._sql(_LIST_PLANS_BY_STATE_SQL, (state,)).fetchall()
        self._record("list_plans", state or "-")
        return [decode_plan(_json_of(row["plan_json"])) for row in rows]

    # --- G14 实验队列 ---

    def save_queue_entry(self, entry: ExperimentQueueEntry) -> None:
        self._ensure_open()
        with self._conn.transaction():
            self._sql(_UPSERT_QUEUE_SQL, _queue_values(entry))
        self._record("save_queue_entry", entry.id.value)

    def get_queue_entry(self, entry_id: str) -> ExperimentQueueEntry:
        self._ensure_open()
        row: Any = self._sql(_GET_QUEUE_SQL, (entry_id,)).fetchone()
        if row is None:
            self._record("get_queue_entry", entry_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown queue entry id: {entry_id}")
        self._record("get_queue_entry", entry_id)
        return decode_queue_entry(_json_of(row["entry_json"]))

    def list_queue_entries(self, project_id: str) -> list[ExperimentQueueEntry]:
        self._ensure_open()
        rows: Any = self._sql(_LIST_QUEUE_SQL, (project_id,)).fetchall()
        self._record("list_queue_entries", project_id)
        return [decode_queue_entry(_json_of(row["entry_json"])) for row in rows]

    def claim_due_entry(
        self, *, now: Timestamp, claim_ttl_seconds: float
    ) -> ExperimentQueueEntry | None:
        self._ensure_open()
        with self._conn.transaction():
            self._requeue_expired(now, claim_ttl_seconds)
            row: Any = self._sql(
                _SELECT_QUEUED_CANDIDATE, (ExperimentQueueState.State.QUEUED,)
            ).fetchone()
            entry = decode_queue_entry(_json_of(row["entry_json"])) if row is not None else None
            if entry is None or not entry.is_due(now):
                self._record("claim_due_entry", now.value.isoformat(), result="none")
                return None
            claimed = entry.claim(now)
            if not self._conditional_write(claimed, from_state=entry.state):
                self._record("claim_due_entry", entry.id.value, result="lost")
                return None
        self._record("claim_due_entry", claimed.id.value, result="claimed")
        return claimed

    def cancel_queue_entry(self, entry_id: str, *, now: Timestamp) -> ExperimentQueueEntry:
        self._ensure_open()
        with self._conn.transaction():
            entry = self._known_queue_entry(entry_id)
            try:
                cancelled = entry.cancel(now)
            except InvalidTransitionError as exc:
                raise InvalidInputError(_conflict_message(entry_id)) from exc
            applied = self._conditional_write(cancelled, from_state=entry.state)
        if not applied:
            raise InvalidInputError(_conflict_message(entry_id))
        self._record("cancel_queue_entry", entry_id)
        return cancelled

    def reschedule_queue_entry(
        self,
        entry_id: str,
        *,
        not_before: Timestamp | None,
        now: Timestamp,
    ) -> ExperimentQueueEntry:
        self._ensure_open()
        with self._conn.transaction():
            entry = self._known_queue_entry(entry_id)
            try:
                rescheduled = entry.reschedule(not_before, now)
            except InvalidTransitionError as exc:
                raise InvalidInputError(_conflict_message(entry_id)) from exc
            applied = self._conditional_write(rescheduled, from_state=entry.state)
        if not applied:
            raise InvalidInputError(_conflict_message(entry_id))
        self._record("reschedule_queue_entry", entry_id)
        return rescheduled

    # --- queue/plan 内部 ---

    def _sql(self, statement: str, params: tuple[Any, ...] = ()) -> Any:
        """单一绑定出口：语句是模块内完整字面量常量，数据一律占位符绑定。"""
        runner = getattr(self._conn, "execute")
        return runner(statement, params)

    def _known_queue_entry(self, entry_id: str) -> ExperimentQueueEntry:
        row: Any = self._sql(_GET_QUEUE_SQL, (entry_id,)).fetchone()
        if row is None:
            raise InvalidInputError(f"unknown queue entry id: {entry_id}")
        return decode_queue_entry(_json_of(row["entry_json"]))

    def _conditional_write(self, entry: ExperimentQueueEntry, *, from_state: str) -> bool:
        """条件更新（状态比较并写入 domain 计算结果）；返回是否命中该行。"""
        cursor: Any = self._sql(
            _CONDITIONAL_QUEUE_SQL,
            (
                entry.state,
                entry.claimed_at.value if entry.claimed_at else None,
                json.dumps(encode_queue_entry(entry), ensure_ascii=False, sort_keys=True),
                entry.updated_at.value,
                entry.id.value,
                from_state,
            ),
        )
        return bool(cursor.rowcount == 1)

    def _requeue_expired(self, now: Timestamp, claim_ttl_seconds: float) -> None:
        """认领者已死（DISPATCHING 超过 ttl）⇒ 归位 QUEUED，下轮可再派发。"""
        rows: Any = self._sql(
            _SELECT_DISPATCHING, (ExperimentQueueState.State.DISPATCHING,)
        ).fetchall()
        for row in rows:
            entry = decode_queue_entry(_json_of(row["entry_json"]))
            if entry.claimed_at is None:
                expired = True
            else:
                expired = (now.value - entry.claimed_at.value).total_seconds() >= claim_ttl_seconds
            if expired:
                self._conditional_write(entry.requeue(now), from_state=entry.state)


def _queue_values(entry: ExperimentQueueEntry) -> tuple[Any, ...]:
    """队列行的事实列（从 domain 实例派生，与 JSON 列同源）。"""
    return (
        entry.id.value,
        entry.project_id,
        entry.plan_id.value,
        entry.state,
        entry.not_before.value if entry.not_before else None,
        entry.claimed_at.value if entry.claimed_at else None,
        json.dumps(encode_queue_entry(entry), ensure_ascii=False, sort_keys=True),
        entry.created_at.value,
        entry.updated_at.value,
    )


def _conflict_message(entry_id: str) -> str:
    return f"queue entry {entry_id} is not QUEUED; the operation applies to QUEUED only"


def _json_of(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return cast(dict[str, Any], json.loads(value))
    if isinstance(value, dict):
        return value
    return cast(dict[str, Any], json.loads(json.dumps(value)))
