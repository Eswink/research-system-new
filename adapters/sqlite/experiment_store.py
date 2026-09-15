"""SqliteExperimentStore：ExperimentStore Port 的 SQLite 实现（PLAN-040 WP-A）。

与 `adapters/postgres/experiment_store.py` 同一 Port 契约与语义：whole-object
JSON 行（codec 共享 `adapters/contracts/experiment_rows.py`）、save 为 upsert
覆盖、未知 id 抛 InvalidInputError、audit 以 experiment_run_id 为查询键。用途：
SQLite 开发路径消灭 experiments 端点的诚实 503（PG 仍是 canonical state）。

G14 队列：状态/排期/认领时间落列（判定仍在 domain），认领是条件更新
（`WHERE state = 'QUEUED'` + rowcount 仲裁），并发认领只有一个赢家；认领过期的
DISPATCHING 先按 domain 归位 QUEUED 再参与本轮认领（at-least-once）。
"""

from __future__ import annotations

import json
import sqlite3
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
from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import now_iso
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry
from packages.domain.experiment_state import ExperimentQueueState
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.state_base import InvalidTransitionError

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiment_plans (
    plan_id TEXT PRIMARY KEY,
    plan_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    run_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reproducibility_audits (
    experiment_run_id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    audit_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_queue (
    entry_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    state TEXT NOT NULL,
    not_before TEXT,
    claimed_at TEXT,
    entry_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiment_queue_project ON experiment_queue(project_id);
CREATE INDEX IF NOT EXISTS idx_experiment_queue_state ON experiment_queue(state);
"""

# 完整字面量 SQL（每个查询形态一条；数据值一律 ? 绑定）。
_SAVE_PLAN_SQL = (
    "INSERT INTO experiment_plans (plan_id, plan_json, created_at) VALUES (?, ?, ?)"
    " ON CONFLICT (plan_id) DO UPDATE SET plan_json = excluded.plan_json,"
    " created_at = excluded.created_at"
)
_GET_PLAN_SQL = "SELECT plan_json FROM experiment_plans WHERE plan_id = ?"
_LIST_PLANS_SQL = "SELECT plan_json FROM experiment_plans ORDER BY created_at DESC"
_LIST_PLANS_BY_STATE_SQL = (
    "SELECT plan_json FROM experiment_plans WHERE json_extract(plan_json, '$.state') = ?"
    " ORDER BY created_at DESC"
)
_SAVE_RUN_SQL = (
    "INSERT INTO experiment_runs (run_id, plan_id, run_json, created_at) VALUES (?, ?, ?, ?)"
    " ON CONFLICT (run_id) DO UPDATE SET plan_id = excluded.plan_id,"
    " run_json = excluded.run_json, created_at = excluded.created_at"
)
_GET_RUN_SQL = "SELECT run_json FROM experiment_runs WHERE run_id = ?"
_SAVE_AUDIT_SQL = (
    "INSERT INTO reproducibility_audits (experiment_run_id, audit_id, audit_json, created_at)"
    " VALUES (?, ?, ?, ?)"
    " ON CONFLICT (experiment_run_id) DO UPDATE SET audit_id = excluded.audit_id,"
    " audit_json = excluded.audit_json, created_at = excluded.created_at"
)
_GET_AUDIT_SQL = "SELECT audit_json FROM reproducibility_audits WHERE experiment_run_id = ?"
_UPSERT_QUEUE_SQL = (
    "INSERT INTO experiment_queue (entry_id, project_id, plan_id, state, not_before,"
    " claimed_at, entry_json, created_at, updated_at)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    " ON CONFLICT (entry_id) DO UPDATE SET project_id = excluded.project_id,"
    " plan_id = excluded.plan_id, state = excluded.state, not_before = excluded.not_before,"
    " claimed_at = excluded.claimed_at, entry_json = excluded.entry_json,"
    " updated_at = excluded.updated_at"
)
_GET_QUEUE_SQL = "SELECT entry_json FROM experiment_queue WHERE entry_id = ?"
_LIST_QUEUE_SQL = (
    "SELECT entry_json FROM experiment_queue WHERE project_id = ? ORDER BY created_at ASC"
)
_STATES_QUEUE_SQL = "SELECT entry_json FROM experiment_queue WHERE state = ?"
_CLAIM_QUEUE_SQL = (
    "UPDATE experiment_queue SET state = ?, claimed_at = ?, entry_json = ?, updated_at = ?"
    " WHERE entry_id = ? AND state = ?"
)


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _queue_columns(entry: ExperimentQueueEntry) -> tuple[Any, ...]:
    """队列行的事实列（从 domain 实例派生，与 JSON 文本同源）。"""
    return (
        entry.id.value,
        entry.project_id,
        entry.plan_id.value,
        entry.state,
        entry.not_before.value.isoformat() if entry.not_before else None,
        entry.claimed_at.value.isoformat() if entry.claimed_at else None,
        _dumps(encode_queue_entry(entry)),
        entry.created_at.value.isoformat(),
        entry.updated_at.value.isoformat(),
    )


class SqliteExperimentStore(SqliteAdapterBase):
    """SQLite ExperimentStore；plan/run/audit/queue：id -> JSON 文本行（upsert）。"""

    def __init__(self, connection: sqlite3.Connection | str = ":memory:") -> None:
        super().__init__("experiment_store")
        if isinstance(connection, str):
            self._owns_connection = True
            self._conn = sqlite3.connect(connection)
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

    # --- ExperimentPlan ---

    def save_plan(self, plan: ExperimentPlan) -> None:
        self._ensure_open()
        with self._conn:
            self._run(_SAVE_PLAN_SQL, (plan.id.value, _dumps(encode_plan(plan)), now_iso(None)))
        self._record("save_plan", plan.id.value)

    def get_plan(self, plan_id: str) -> ExperimentPlan:
        return decode_plan(self._json_cell("get_plan", _GET_PLAN_SQL, "plan_json", plan_id))

    def list_plans(self, *, state: str | None = None) -> list[ExperimentPlan]:
        self._ensure_open()
        if state is None:
            rows = self._run(_LIST_PLANS_SQL).fetchall()
        else:
            rows = self._run(_LIST_PLANS_BY_STATE_SQL, (state,)).fetchall()
        self._record("list_plans", state or "-")
        return [decode_plan(json.loads(row["plan_json"])) for row in rows]

    # --- ExperimentRun ---

    def save_run(self, run: ExperimentRun) -> None:
        self._ensure_open()
        with self._conn:
            self._run(
                _SAVE_RUN_SQL,
                (run.id.value, run.plan_id.value, _dumps(encode_run(run)), now_iso(None)),
            )
        self._record("save_run", run.id.value)

    def get_run(self, run_id: str) -> ExperimentRun:
        return decode_run(self._json_cell("get_run", _GET_RUN_SQL, "run_json", run_id))

    # --- ReproducibilityAudit ---

    def save_audit(self, audit: ReproducibilityAudit) -> None:
        self._ensure_open()
        with self._conn:
            self._run(
                _SAVE_AUDIT_SQL,
                (
                    audit.experiment_run_id.value,
                    audit.audit_id.value,
                    _dumps(encode_audit(audit)),
                    now_iso(None),
                ),
            )
        self._record("save_audit", audit.audit_id.value)

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit:
        return decode_audit(
            self._json_cell("get_audit", _GET_AUDIT_SQL, "audit_json", experiment_run_id)
        )

    # --- G14 队列 ---

    def save_queue_entry(self, entry: ExperimentQueueEntry) -> None:
        self._ensure_open()
        with self._conn:
            self._run(_UPSERT_QUEUE_SQL, _queue_columns(entry))
        self._record("save_queue_entry", entry.id.value)

    def get_queue_entry(self, entry_id: str) -> ExperimentQueueEntry:
        return decode_queue_entry(
            self._json_cell("get_queue_entry", _GET_QUEUE_SQL, "entry_json", entry_id)
        )

    def list_queue_entries(self, project_id: str) -> list[ExperimentQueueEntry]:
        self._ensure_open()
        rows = self._run(_LIST_QUEUE_SQL, (project_id,)).fetchall()
        self._record("list_queue_entries", project_id)
        return [decode_queue_entry(json.loads(row["entry_json"])) for row in rows]

    def claim_due_entry(
        self, *, now: Timestamp, claim_ttl_seconds: float
    ) -> ExperimentQueueEntry | None:
        self._ensure_open()
        with self._conn:
            self._requeue_expired(now, claim_ttl_seconds)
            entry = self._next_due(now)
            if entry is None:
                self._record("claim_due_entry", now.value.isoformat(), result="none")
                return None
            claimed = entry.claim(now)
            applied = self._conditional_write(claimed, from_state=entry.state)
        self._record("claim_due_entry", claimed.id.value, result=str(applied))
        return claimed if applied else None

    def cancel_queue_entry(self, entry_id: str, *, now: Timestamp) -> ExperimentQueueEntry:
        self._ensure_open()
        with self._conn:
            entry = self._known_queue_entry(entry_id)
            try:
                cancelled = entry.cancel(now)
            except InvalidTransitionError as exc:
                raise InvalidInputError(self._conflict_message(entry_id)) from exc
            applied = self._conditional_write(cancelled, from_state=entry.state)
        if not applied:
            raise InvalidInputError(self._conflict_message(entry_id))
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
        with self._conn:
            entry = self._known_queue_entry(entry_id)
            try:
                rescheduled = entry.reschedule(not_before, now)
            except InvalidTransitionError as exc:
                raise InvalidInputError(self._conflict_message(entry_id)) from exc
            applied = self._conditional_write(rescheduled, from_state=entry.state)
        if not applied:
            raise InvalidInputError(self._conflict_message(entry_id))
        self._record("reschedule_queue_entry", entry_id)
        return rescheduled

    # --- 内部 ---

    def _known_queue_entry(self, entry_id: str) -> ExperimentQueueEntry:
        row = self._run(_GET_QUEUE_SQL, (entry_id,)).fetchone()
        if row is None:
            raise InvalidInputError(f"unknown queue entry id: {entry_id}")
        return decode_queue_entry(json.loads(row["entry_json"]))

    @staticmethod
    def _conflict_message(entry_id: str) -> str:
        return f"queue entry {entry_id} is not QUEUED; the operation applies to QUEUED only"

    def _conditional_write(self, entry: ExperimentQueueEntry, *, from_state: str) -> bool:
        """条件更新：只有仍处于 `from_state` 的行才被改写（并发仲裁点）。"""
        cursor = self._run(
            _CLAIM_QUEUE_SQL,
            (
                entry.state,
                entry.claimed_at.value.isoformat() if entry.claimed_at else None,
                _dumps(encode_queue_entry(entry)),
                entry.updated_at.value.isoformat(),
                entry.id.value,
                from_state,
            ),
        )
        return bool(cursor.rowcount == 1)

    def _requeue_expired(self, now: Timestamp, claim_ttl_seconds: float) -> None:
        rows = self._run(_STATES_QUEUE_SQL, (ExperimentQueueState.State.DISPATCHING,)).fetchall()
        for row in rows:
            entry = decode_queue_entry(json.loads(row["entry_json"]))
            if entry.claimed_at is None:
                expired = True
            else:
                expired = (now.value - entry.claimed_at.value).total_seconds() >= claim_ttl_seconds
            if expired:
                self._conditional_write(entry.requeue(now), from_state=entry.state)

    def _next_due(self, now: Timestamp) -> ExperimentQueueEntry | None:
        rows = self._run(_STATES_QUEUE_SQL, (ExperimentQueueState.State.QUEUED,)).fetchall()
        entries = [decode_queue_entry(json.loads(row["entry_json"])) for row in rows]
        due = [entry for entry in entries if entry.is_due(now)]
        if not due:
            return None
        return min(due, key=_due_order)

    def _json_cell(self, method: str, statement: str, column: str, key: str) -> dict[str, Any]:
        self._ensure_open()
        row = self._run(statement, (key,)).fetchone()
        if row is None:
            self._record(method, key, error="InvalidInputError")
            raise InvalidInputError(f"unknown experiment id: {key}")
        self._record(method, key)
        return cast("dict[str, Any]", json.loads(row[column]))


def _due_order(entry: ExperimentQueueEntry) -> tuple[object, object]:
    """到期顺序：未排期条目按创建时间参与排序（COALESCE(not_before, created_at)）。"""
    effective = entry.not_before.value if entry.not_before is not None else entry.created_at.value
    return (effective, entry.created_at.value)
