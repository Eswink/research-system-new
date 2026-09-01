"""PostgresWorkflowEngine — WorkflowEngine Port on PostgreSQL."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import psycopg
import psycopg.errors
from psycopg.rows import dict_row

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
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
from adapters.postgres.telemetry_notes import note_queue_lag, note_task_duration
from adapters.postgres.workflow_acquire import AcquirePayload, acquire_lease_impl
from adapters.postgres.workflow_claim import ClaimPayload, claim_next_impl
from adapters.postgres.workflow_ops import (
    complete_impl,
    heartbeat_impl,
    recover_impl,
    renew_lease_impl,
)
from adapters.postgres.workflow_submit import SubmitPayload, submit_task
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import (
    CorrelationRef,
    OperationScope,
)
from packages.application.ports.errors import (
    InvalidInputError,
    TransientPortError,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion, TaskLease
from packages.domain.enums import FailureCategory
from packages.domain.events import EventEnvelope
from packages.domain.tasks import ResearchTask, TaskContract


def _resolve_connection(dsn: str | None, connection: Any | None) -> tuple[Any, bool]:
    """Return (connection, owns_connection) with dict_row factory applied."""
    if connection is not None:
        conn = connection
        owns = False
    else:
        resolved = dsn or dsn_from_env()
        if not resolved:
            raise ValueError("PostgresWorkflowEngine requires dsn or connection")
        conn, owns = pg_connect(resolved), True
    try:
        conn.row_factory = dict_row
    except Exception:
        pass
    return conn, owns


class PostgresWorkflowEngine(PostgresAdapterBase):
    """PostgreSQL WorkflowEngine; `now` injectable for deterministic tests."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connection: Any | None = None,
        lease_ttl_seconds: int = 300,
        now: Callable[[], datetime] | None = None,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        super().__init__("workflow_engine")
        self._lease_ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        self._telemetry = telemetry
        self._owned_lease_ids: set[str] = set()
        self._conn, self._owns_connection = _resolve_connection(dsn, connection)
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
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.submit",
            correlation=CorrelationRef(task_id=task.id.value, run_id=task.run_id.value),
        ):
            self._submit_impl(task, contract)

    def _submit_impl(self, task: ResearchTask, contract: TaskContract) -> None:
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
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.acquire_lease",
            correlation=CorrelationRef(task_id=task_id),
        ):
            return self._acquire_impl(task_id)

    def _acquire_impl(self, task_id: str) -> TaskLease:
        self._ensure_open()
        try:
            lease = acquire_lease_impl(
                self._conn,
                self._record,
                self._outbox,
                AcquirePayload(task_id, self._lease_ttl, frozenset(self._owned_lease_ids)),
                self._now,
            )
            self._owned_lease_ids.add(lease.lease_id)
            note_queue_lag(self._telemetry, self._conn, task_id)
            return lease
        except InvalidInputError:
            raise
        except psycopg.errors.UniqueViolation:
            # Note: with autocommit=True + explicit transactions, UniqueViolation
            # should not reach here — the Impl now handles reclaim atomically and
            # the rest is covered by the top-level transaction rollback. Keep as
            # a safety fallback; the failing transaction has already rolled back.
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def claim_next(self, request: ClaimRequest) -> TaskLease | None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKER_DISPATCH,
            name="workflow.claim_next",
            correlation=CorrelationRef(),
        ):
            return self._claim_next_impl(request)

    def _claim_next_impl(self, request: ClaimRequest) -> TaskLease | None:
        self._ensure_open()
        try:
            return claim_next_impl(
                self._conn,
                self._record,
                self._outbox,
                ClaimPayload(request, self._lease_ttl),
                self._now,
            )
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def heartbeat(self, lease: TaskLease) -> TaskLease:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.heartbeat",
            correlation=CorrelationRef(task_id=lease.task_id),
        ):
            return self._heartbeat_impl(lease)

    def _heartbeat_impl(self, lease: TaskLease) -> TaskLease:
        self._ensure_open()
        try:
            renewed = heartbeat_impl(self._conn, self._record, lease, self._lease_ttl, self._now)
            self._owned_lease_ids.add(renewed.lease_id)
            return renewed
        except InvalidInputError:
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def renew_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.renew_lease",
            correlation=CorrelationRef(task_id=task_id),
        ):
            self._ensure_open()
            try:
                renew_lease_impl(
                    self._conn,
                    self._record,
                    task_id,
                    lease_id,
                    fence,
                    worker_id,
                    self._lease_ttl,
                    self._now,
                )
            except InvalidInputError:
                raise
            except psycopg.OperationalError as exc:
                raise self._wrap_operational(exc) from exc

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.complete",
            correlation=CorrelationRef(task_id=lease.task_id),
        ):
            return self._complete_impl(lease, completion)

    def _complete_impl(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._ensure_open()
        try:
            from adapters.postgres.workflow_ops import CompletePayload

            complete_impl(
                self._conn,
                self._record,
                self._outbox,
                CompletePayload(lease, completion, self._now),
            )
            note_task_duration(self._telemetry, self._conn, lease.task_id)
        except InvalidInputError:
            raise
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def cancel(self, task_id: str) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.cancel",
            correlation=CorrelationRef(task_id=task_id),
        ):
            self._cancel_impl(task_id)

    def _cancel_impl(self, task_id: str) -> None:
        self._ensure_open()
        try:
            from adapters.postgres.cancel_run import cancel_task

            outcome = cancel_task(self._conn, self._outbox, task_id)
            self._record("cancel", task_id, result=outcome)
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def cancel_run(self, run_id: str) -> int:
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.cancel_run",
            correlation=CorrelationRef(run_id=run_id),
        ):
            return self._cancel_run_impl(run_id)

    def _cancel_run_impl(self, run_id: str) -> int:
        self._ensure_open()
        try:
            from adapters.postgres.cancel_run import cancel_run_tasks

            count = cancel_run_tasks(self._conn, self._outbox, run_id)
            self._record("cancel_run", run_id, result=f"{count} cancelled")
            return count
        except psycopg.OperationalError as exc:
            raise self._wrap_operational(exc) from exc

    def cancelled_task_ids(self, run_id: str) -> tuple[str, ...]:
        """该 run 的取消任务 id（canonical task projection，只读）。"""
        self._ensure_open()
        cancelled_ids = self.cancelled
        ids = tuple(
            row.task.id.value
            for row in self.list_tasks(run_id)
            if row.task.id.value in cancelled_ids
        )
        self._record("cancelled_task_ids", run_id, result=str(len(ids)))
        return ids

    def recover_expired_leases(self) -> int:
        with operation(
            self._telemetry,
            scope=OperationScope.LEASE_RECOVERY,
            name="lease_recovery.recover",
        ):
            return self._recover_impl()

    def _recover_impl(self) -> int:
        self._ensure_open()
        try:
            recovered = recover_impl(self._conn, self._record, self._outbox, self._now)
            if recovered:
                record_metric_safely(
                    self._telemetry,
                    lambda: MetricSample(
                        name=MetricName.WORKFLOW_LEASE_EXPIRED,
                        kind=MetricKind.COUNTER,
                        value=recovered,
                    ),
                )
            return recovered
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
