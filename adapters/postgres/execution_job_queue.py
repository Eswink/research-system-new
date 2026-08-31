"""PostgreSQL ExecutionJobQueue: EXECUTION jobs on the single canonical queue.

`enqueue` writes a `tasks` row (kind='EXECUTION', status QUEUED) plus an
`execution_jobs` payload projection — the one queue, no second table of
record. `record_result` is the Control-Plane write path the worker gateway
calls after it has authenticated the worker; it re-validates the
`(task_id, lease_id, fence)` triple against the active lease inside the same
transaction, so a stale worker's result can never be persisted.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from psycopg.rows import dict_row

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from packages.application.ports.execution_job_queue import (
    ExecutionJobOutcome,
    ExecutionJobRequest,
    ExecutionJobResult,
)
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, TaskKind
from packages.domain.serialization import canonical_json_bytes
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

_SYNTHETIC_CONTRACT = TaskContract(
    id="remote-execution",
    version="1",
    purpose="remote execution job",
    acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
    budget={},
)

_INSERT_TASK = (
    "INSERT INTO tasks (task_id, run_id, idempotency_key, attempt, status,"
    " assigned_agent_id, task_json, contract_json, cancelled, created_at,"
    " kind, partition, required_capability)"
    " VALUES (%s, %s, %s, 1, %s, NULL, %s::jsonb, %s::jsonb, FALSE, %s, %s, %s, %s)"
)
_INSERT_JOB = (
    "INSERT INTO execution_jobs (task_id, spec_json, input_bundle_ref,"
    " input_bundle_digest, required_capability, partition, created_at)"
    " VALUES (%s, %s::jsonb, %s, %s, %s, %s, %s)"
)


def _synthetic_task(
    task_id: str, run_id: str, capability: str, partition: int | None
) -> ResearchTask:
    return ResearchTask(
        id=ID(task_id),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability=capability,
        partition=partition,
    )


class PostgresExecutionJobQueue(PostgresAdapterBase):
    """ExecutionJobQueue on PostgreSQL; `now` injectable for deterministic tests."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connection: Any | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("execution_job_queue")
        self._now = now
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresExecutionJobQueue requires dsn or connection")
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

    def enqueue(self, request: ExecutionJobRequest) -> str:
        self._ensure_open()
        task_id = ID.generate().value
        spec = request.spec
        task = _synthetic_task(task_id, request.run_id, request.capability, request.partition)
        task_json = canonical_json_bytes(task).decode("utf-8")
        contract_json = canonical_json_bytes(_SYNTHETIC_CONTRACT).decode("utf-8")
        spec_json = canonical_json_bytes(spec).decode("utf-8")
        with self._conn.transaction():
            existing: Any = self._conn.execute(
                "SELECT task_id FROM tasks WHERE idempotency_key = %s",
                (request.idempotency_key,),
            ).fetchone()
            if existing is not None:
                self._record("enqueue", request.idempotency_key, result="deduped")
                return str(existing["task_id"])
            self._conn.execute(
                _INSERT_TASK,
                (
                    task_id,
                    request.run_id,
                    request.idempotency_key,
                    ResearchTaskState.State.QUEUED,
                    task_json,
                    contract_json,
                    now_iso(self._now),
                    TaskKind.EXECUTION.value,
                    request.partition,
                    request.capability,
                ),
            )
            self._conn.execute(
                _INSERT_JOB,
                (
                    task_id,
                    spec_json,
                    request.input_bundle_ref,
                    request.input_bundle_digest,
                    request.capability,
                    request.partition,
                    now_iso(self._now),
                ),
            )
        self._record("enqueue", request.idempotency_key, result=task_id)
        return task_id

    def poll(self, task_id: str) -> ExecutionJobOutcome | None:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT t.status, t.fence_seq, j.worker_id, j.exit_code, j.stdout_digest,"
            " j.stderr_digest, j.output_bundle_ref, j.output_bundle_digest,"
            " j.failure_category FROM tasks t LEFT JOIN execution_jobs j"
            " ON j.task_id = t.task_id WHERE t.task_id = %s",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        if row["status"] not in (
            ResearchTaskState.State.SUCCEEDED,
            ResearchTaskState.State.FAILED,
            ResearchTaskState.State.CANCELLED,
        ):
            return None
        return ExecutionJobOutcome(
            task_id=task_id,
            status=str(row["status"]),
            fence=int(row["fence_seq"] or 0),
            worker_id=str(row["worker_id"]) if row["worker_id"] else None,
            exit_code=int(row["exit_code"]) if row["exit_code"] is not None else None,
            stdout_digest=str(row["stdout_digest"]) if row["stdout_digest"] else None,
            stderr_digest=str(row["stderr_digest"]) if row["stderr_digest"] else None,
            output_bundle_ref=str(row["output_bundle_ref"]) if row["output_bundle_ref"] else None,
            output_bundle_digest=(
                str(row["output_bundle_digest"]) if row["output_bundle_digest"] else None
            ),
            failure_category=str(row["failure_category"]) if row["failure_category"] else None,
        )

    def record_result(self, result: ExecutionJobResult) -> None:
        """Persist a settled result. Fencing is enforced by the caller (the
        worker gateway validates `(task_id, lease_id, fence)` against the
        active lease before invoking this), so this write is unconditional."""
        self._ensure_open()
        task_id = result.task_id
        with self._conn.transaction():
            self._conn.execute(
                "UPDATE execution_jobs SET worker_id = (SELECT worker_id FROM leases"
                " WHERE task_id = %s), exit_code = %s, stdout_digest = %s, stderr_digest = %s,"
                " output_bundle_ref = %s, output_bundle_digest = %s, failure_category = %s"
                " WHERE task_id = %s",
                (
                    task_id,
                    result.exit_code,
                    result.stdout_digest,
                    result.stderr_digest,
                    result.output_bundle_ref,
                    result.output_bundle_digest,
                    result.failure_category,
                    task_id,
                ),
            )
            self._conn.execute(
                "UPDATE tasks SET status = %s WHERE task_id = %s", (result.status, task_id)
            )
            self._conn.execute("DELETE FROM leases WHERE task_id = %s", (task_id,))
        self._record("record_result", task_id, result=result.status)

    def request_cancel(self, task_id: str) -> None:
        self._ensure_open()
        self._conn.execute(
            "UPDATE execution_jobs SET cancel_requested = TRUE WHERE task_id = %s", (task_id,)
        )
        self._record("request_cancel", task_id)

    def cancel_requested(self, task_id: str) -> bool:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT cancel_requested FROM execution_jobs WHERE task_id = %s", (task_id,)
        ).fetchone()
        return bool(row and row["cancel_requested"])
