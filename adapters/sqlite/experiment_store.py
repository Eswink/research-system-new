"""SqliteExperimentStore：ExperimentStore Port 的 SQLite 实现（PLAN-040 WP-A）。

与 `adapters/postgres/experiment_store.py` 同一 Port 契约与语义：whole-object
JSON 行（codec 共享 `adapters/contracts/experiment_rows.py`）、save 为 upsert
覆盖、未知 id 抛 InvalidInputError、audit 以 experiment_run_id 为查询键。用途：
SQLite 开发路径消灭 experiments 端点的诚实 503（PG 仍是 canonical state）。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, cast

from adapters.contracts.experiment_rows import (
    decode_audit,
    decode_plan,
    decode_run,
    encode_audit,
    encode_plan,
    encode_run,
)
from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import now_iso
from packages.application.ports.errors import InvalidInputError
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit

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
"""

# 完整字面量 SQL（每个查询形态一条；数据值一律 ? 绑定）。
_SAVE_PLAN_SQL = (
    "INSERT INTO experiment_plans (plan_id, plan_json, created_at) VALUES (?, ?, ?)"
    " ON CONFLICT (plan_id) DO UPDATE SET plan_json = excluded.plan_json,"
    " created_at = excluded.created_at"
)
_GET_PLAN_SQL = "SELECT plan_json FROM experiment_plans WHERE plan_id = ?"
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


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


class SqliteExperimentStore(SqliteAdapterBase):
    """SQLite ExperimentStore；plan/run/audit：id -> JSON 文本行（upsert）。"""

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

    # --- 内部 ---

    def _json_cell(self, method: str, statement: str, column: str, key: str) -> dict[str, Any]:
        self._ensure_open()
        row = self._run(statement, (key,)).fetchone()
        if row is None:
            self._record(method, key, error="InvalidInputError")
            raise InvalidInputError(f"unknown experiment id: {key}")
        self._record(method, key)
        return cast("dict[str, Any]", json.loads(row[column]))
