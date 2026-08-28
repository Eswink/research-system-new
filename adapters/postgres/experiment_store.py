"""PostgreSQL adapter for ExperimentStore (M14 DS-1 domain state)."""

from __future__ import annotations

import json
from typing import Any, cast

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from adapters.postgres.experiment_rows import (
    decode_audit,
    decode_plan,
    decode_run,
    encode_audit,
    encode_plan,
    encode_run,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit


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


def _json_of(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return cast(dict[str, Any], json.loads(value))
    if isinstance(value, dict):
        return value
    return cast(dict[str, Any], json.loads(json.dumps(value)))
