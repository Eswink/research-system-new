"""PostgresWorkflowEngine — WorkflowEngine Port on PostgreSQL."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, cast

import psycopg
import psycopg.errors
from psycopg.rows import dict_row

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from adapters.postgres.leases import lease_from_row
from adapters.postgres.outbox import PgOutboxWriter
from adapters.postgres.projections import (
    cancelled as proj_cancelled,
)
from adapters.postgres.projections import (
    completed as proj_completed,
)
from adapters.postgres.projections import (
    deliveries as proj_deliveries,
)
from adapters.postgres.projections import (
    list_tasks as proj_list_tasks,
)
from adapters.postgres.projections import (
    mark_outbox_published as proj_mark_published,
)
from adapters.postgres.projections import (
    pending_outbox as proj_pending_outbox,
)
from adapters.postgres.serialization import TaskRow, encode_task
from adapters.postgres.workflow_acquire import AcquirePayload, acquire_lease_impl
from adapters.postgres.workflow_ops import complete_impl, heartbeat_impl, recover_impl
from adapters.postgres.workflow_submit import SubmitPayload, submit_task
from packages.application.ports.errors import (
    InvalidInputError,
    TransientPortError,
)
from packages.application.ports.workflow_engine import TaskCompletion, TaskLease
from packages.domain.enums import FailureCategory
from packages.domain.events import EventEnvelope
from packages.domain.tasks import ResearchTask, TaskContract


def _redacted(dsn: str) -> str:
    text = re.sub(r"(password\s*=\s*)\S+", r"\1***REDACTED***", dsn, flags=re.IGNORECASE)
    text = re.sub(r"://[^@]*@", "://***REDACTED***@", text)
    return text


class PostgresWorkflowEngine(PostgresAdapterBase):
    """PostgreSQL WorkflowEngine; `now` injectable for deterministic tests."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connection: Any | None = None,
        lease_ttl_seconds: int = 300,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("workflow_engine")
        self._lease_ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        if connection is not None:
            self._conn: Any = connection
            self._owns_connection = False
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresWorkflowEngine requires dsn or connection")
            self._conn = pg_connect(resolved)
            self._owns_connection = True
        try:
            self._conn.row_factory = dict_row
        except Exception:
            pass
        self._outbox = PgOutboxWriter(self._conn, self._now)

    def close(self) -> None:
        if getattr(self, "_owns_connection", False):
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def _wrap_operational(self, exc: Exception) -> TransientPortError:
        return TransientPortError(
            f"postgres transient failure: {exc!r}",
            failure_category=FailureCategory.SYSTEM_BUG,
        )

    def submit(self, task: ResearchTask, contract: TaskContract) -> None:
        self._ensure_open()
        task_json, contract_json = encode_task(task, contract)
        try:
            result = submit_task(
                self._conn,
                self._record,
                SubmitPayload(task, contract, task_json, contract_json),
                self._now,
            )
            if result == "deduped":
                return
        except psycopg.errors.UniqueViolation:
            self._record("submit", task.id.value, result="deduped")
            return
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def acquire_lease(self, task_id: str) -> TaskLease:
        self._ensure_open()
        try:
            return acquire_lease_impl(
                self._conn,
                self._record,
                self._outbox,
                AcquirePayload(task_id, self._lease_ttl),
                self._now,
            )
        except InvalidInputError:
            raise
        except psycopg.errors.UniqueViolation:
            row2: Any = self._conn.execute(
                "SELECT * FROM leases WHERE task_id = %s", (task_id,)
            ).fetchone()
            if row2 is not None:
                self._record("acquire_lease", task_id, result="deduped")
                return lease_from_row(cast(dict[str, object], row2))
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def heartbeat(self, lease: TaskLease) -> TaskLease:
        self._ensure_open()
        try:
            return heartbeat_impl(self._conn, self._record, lease, self._lease_ttl, self._now)
        except InvalidInputError:
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._ensure_open()
        try:
            complete_impl(self._conn, self._record, self._outbox, lease, completion)
        except InvalidInputError:
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def cancel(self, task_id: str) -> None:
        self._ensure_open()
        try:
            from adapters.postgres.cancel_run import cancel_task

            outcome = cancel_task(self._conn, self._outbox, task_id)
            self._record("cancel", task_id, result=outcome)
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def cancel_run(self, run_id: str) -> int:
        self._ensure_open()
        try:
            from adapters.postgres.cancel_run import cancel_run_tasks

            count = cancel_run_tasks(self._conn, self._outbox, run_id)
            self._record("cancel_run", run_id, result=f"{count} cancelled")
            return count
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def recover_expired_leases(self) -> int:
        self._ensure_open()
        try:
            return recover_impl(self._conn, self._record, self._outbox, self._now)
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def list_tasks(self, run_id: str) -> tuple[TaskRow, ...]:
        return proj_list_tasks(self._conn, run_id)

    @property
    def deliveries(self) -> dict[str, int]:
        return proj_deliveries(self._conn)

    @property
    def completed(self) -> dict[str, TaskCompletion]:
        return proj_completed(self._conn)

    @property
    def cancelled(self) -> set[str]:
        return proj_cancelled(self._conn)

    def pending_outbox(self) -> tuple[EventEnvelope, ...]:
        return proj_pending_outbox(self._conn)

    def mark_outbox_published(self, event_ids: tuple[str, ...]) -> None:
        proj_mark_published(self._conn, event_ids, self._now)
