"""Periodic self-healing for expired leases (M14 Production).

WP2 requirement: `recover_expired_leases` must run periodically, not only
lazily in `RunOrchestrationService.start_run`.

This module provides lightweight background-thread schedulers that start
in the composition root's lifespan. No APScheduler dependency — stdlib only.

Idempotent, `FOR UPDATE SKIP LOCKED` in engine, concurrent-safe.

M15 观测:per-pass `operation()` span(LEASE_RECOVERY / OUTBOX_RELAY),
异常不再静默吞掉——outcome=FAILED 可见(ADR-0026)。
"""

from __future__ import annotations

import threading
from typing import Any

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import (
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.worker_registry import WorkerRegistry


class LeaseRecoveryScheduler:
    """Background daemon that calls `workflow.recover_expired_leases()` on interval.

    No new Port — it operates on the existing WorkflowEngine port.
    """

    def __init__(
        self,
        workflow: Any,
        *,
        interval_seconds: float = 30.0,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._workflow = workflow
        self._interval = interval_seconds
        self._telemetry = telemetry
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="lease-recovery", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        """守护线程主循环:任何 telemetry 故障都不得杀掉这个线程。

        M15 复审:此处的 `record_metric` 原先裸调用,抛错会穿出 `_run` 并让
        lease-recovery 守护线程在进程余生内消失——正是 M14 引入该 scheduler
        要防的失败模式。现在经 `record_metric_safely`(构造 + 投递都受保护)。
        """
        while not self._stop.wait(self._interval):
            with operation(
                self._telemetry,
                scope=OperationScope.LEASE_RECOVERY,
                name="lease_recovery.pass",
            ) as op:
                try:
                    recovered = self._workflow.recover_expired_leases()
                except Exception:
                    op.set_outcome(OperationOutcome.FAILED, "lease_recovery_failed")
                    continue
                if recovered:
                    record_metric_safely(
                        self._telemetry,
                        lambda: MetricSample(
                            name=MetricName.WORKFLOW_LEASE_EXPIRED,
                            kind=MetricKind.COUNTER,
                            value=recovered,
                        ),
                    )


class OutboxRelayScheduler:
    """Background daemon that drains PG outbox via PgOutboxRelay (WP-E).

    Periodically calls `PgOutboxRelay.run_once()` to forward PG workflow
    events to the control-plane publisher. At-least-once semantics: partial
    passes are safe, consumer deduplicates by event_id.
    """

    def __init__(
        self,
        engine: Any,
        sink: Any,
        *,
        interval_seconds: float = 5.0,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._engine = engine
        self._sink = sink
        self._interval = interval_seconds
        self._telemetry = telemetry
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="outbox-relay", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        from adapters.postgres.outbox_relay import PgOutboxRelay

        relay = PgOutboxRelay(self._engine, self._sink, telemetry=self._telemetry)
        while not self._stop.wait(self._interval):
            with operation(
                self._telemetry,
                scope=OperationScope.OUTBOX_RELAY,
                name="outbox.relay_pass",
            ) as op:
                try:
                    relay.run_once()
                except Exception:
                    op.set_outcome(OperationOutcome.FAILED, "outbox_relay_failed")
                    continue


class RetentionScheduler:
    """Background daemon that applies artifact retention on interval (M14 DS-2).

    Calls `apply_retention(store)` periodically. No new Port — it operates on
    the existing ArtifactStore port. Single-artifact failures are already
    skipped inside apply_retention (InvalidInputError → skipped), so a pass
    never aborts mid-scan.
    """

    def __init__(
        self,
        store: Any,
        *,
        interval_seconds: float = 3600.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._store = store
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.last_report: Any = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="retention", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def run_once(self) -> Any:
        from packages.application.artifacts.retention import apply_retention

        report = apply_retention(self._store)
        self.last_report = report
        return report

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                self.run_once()
            except Exception:
                continue


class WorkerReaperScheduler:
    """Background daemon that marks heartbeat-expired workers LOST (M16 WP1).

    Server time is the sole authority: `registry.list_stale()` compares each
    worker's `last_heartbeat` against the database clock. The reaper only
    flips worker state to LOST; releasing the lost worker's leases stays the
    job of `recover_expired_leases` (single lease authority, M16 §5).

    Shape mirrors `LeaseRecoveryScheduler`: stdlib daemon thread, telemetry
    fail-open (a metric error must never kill the reaper loop).
    """

    def __init__(
        self,
        registry: WorkerRegistry,
        *,
        stale_threshold_seconds: float = 30.0,
        interval_seconds: float = 15.0,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if stale_threshold_seconds <= 0:
            raise ValueError("stale_threshold_seconds must be > 0")
        self._registry = registry
        self._stale = stale_threshold_seconds
        self._interval = interval_seconds
        self._telemetry = telemetry
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="worker-reaper", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def run_once(self) -> int:
        """One reap pass: mark every stale worker LOST; return the count."""
        lost = self._registry.list_stale(self._stale)
        for worker_id in lost:
            try:
                self._registry.mark_lost(worker_id)
            except Exception:
                # A concurrent transition (e.g. worker re-registered) is not a
                # reaper failure; the next pass re-evaluates from server time.
                continue
        return len(lost)

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            with operation(
                self._telemetry,
                scope=OperationScope.WORKER_SESSION,
                name="worker.reaper_pass",
            ) as op:
                try:
                    self.run_once()
                except Exception:
                    op.set_outcome(OperationOutcome.FAILED, "worker_reap_failed")
                    continue
