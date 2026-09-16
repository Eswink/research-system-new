"""Periodic self-healing for expired leases (M14 Production).

WP2 requirement: `recover_expired_leases` must run periodically, not only
lazily in `RunOrchestrationService.start_run`.

This module provides lightweight background-thread schedulers that start
in the composition root's lifespan. No APScheduler dependency — stdlib only.

Idempotent, `FOR UPDATE SKIP LOCKED` in engine, concurrent-safe.

M15 观测:per-pass `operation()` span(LEASE_RECOVERY / OUTBOX_RELAY),
异常不再静默吞掉——outcome=FAILED 可见(ADR-0026)。

GOAL-003 EC-03: every daemon now extends `PeriodicDaemon`, so the same daemon
loop is both the **only** executor and the thing `POST /ops/schedules/{name}/trigger`
calls (via `ScheduleRegistry.trigger`) — enable/disable and interval come from the
writable schedule definitions, and each pass is reported back as runtime facts.
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
from packages.application.ops.schedule_registry import OUTCOME_FAILED, OUTCOME_OK
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.worker_registry import WorkerRegistry
from packages.domain.schedules import ScheduleJob


class PeriodicDaemon:
    """守护线程公共循环：每轮向 `ScheduleRegistry` 要该作业到点的定义并执行。

    - **执行体仍是这里**：注册的 pass 函数与定时执行的 pass 是同一个（EC-03 口径）；
    - 无 `control`（未装配调度写面）时退化为原行为：固定 interval 一直跑；
    - 每个 pass 的结果写回 registry（run_count / last_run_at / last_outcome）。
    """

    #: 子类覆盖：本守护线程执行的作业类型（None = 不接入调度写面）。
    job: ScheduleJob | None = None
    thread_name = "periodic-daemon"

    def __init__(
        self,
        *,
        interval_seconds: float,
        control: Any = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._interval = interval_seconds
        self._control = control
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ── 生命周期 ──

    def start(self) -> None:
        if self._thread is not None:
            return
        self._register_executor()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=self.thread_name, daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _register_executor(self) -> None:
        """把**同一条** pass 注册进调度写面（trigger 走它，不另开执行路径）。"""
        if self._control is not None and self.job is not None:
            self._control.register_executor(self.job, self._execute_pass)

    # ── 循环 ──

    def _run(self) -> None:
        while not self._stop.wait(self._next_wait()):
            for name in self._due_names():
                outcome, error = OUTCOME_OK, None
                try:
                    self._execute_pass()
                except Exception as exc:  # noqa: BLE001 — 失败要留痕，不能让守护线程消失
                    outcome, error = OUTCOME_FAILED, str(exc)
                self._record(name, outcome, error)

    def _record(self, name: str | None, outcome: str, error: str | None) -> None:
        """回写运行事实。

        记账失败（读面/存储抖动、定义刚被删）**不得**让守护线程消失：这条自愈线程
        比它写的事实更重要，事实滞后会在读面如实可见（`last_outcome` 停在旧值）。
        """
        if name is None or self._control is None:
            return
        try:
            self._control.record(name, outcome=outcome, error=error)
        except Exception:  # noqa: BLE001
            return

    def _due_names(self) -> list[str | None]:
        """到点的定义名；无调度写面时返回 `[None]`（原固定 interval 行为）。"""
        if self._control is None or self.job is None:
            return [None]
        try:
            return [definition.name for definition in self._control.due(self.job)]
        except Exception:  # noqa: BLE001 — 读面故障时本轮不跑，下一轮重试（不退出）
            return []

    def _next_wait(self) -> float:
        if self._control is None or self.job is None:
            return self._interval
        try:
            return float(self._control.next_wait_seconds(self.job, self._interval))
        except Exception:  # noqa: BLE001 — 同上：退化为自身 interval
            return self._interval

    # ── 子类实现 ──

    def _execute_pass(self) -> object:
        raise NotImplementedError

    # 兼容既有调用面（某些测试/装配直接用 run_once）
    def run_once(self) -> object:
        return self._execute_pass()


class LeaseRecoveryScheduler(PeriodicDaemon):
    """Background daemon that calls `workflow.recover_expired_leases()` on interval.

    No new Port — it operates on the existing WorkflowEngine port.
    """

    job = ScheduleJob.LEASE_RECOVERY
    thread_name = "lease-recovery"

    def __init__(
        self,
        workflow: Any,
        *,
        interval_seconds: float = 30.0,
        telemetry: TelemetrySink | None = None,
        control: Any = None,
    ) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._workflow = workflow
        self._telemetry = telemetry

    def _execute_pass(self) -> int:
        """One lease-recovery pass.

        M15 复审:此处的 `record_metric` 原先裸调用,抛错会穿出 `_run` 并让
        lease-recovery 守护线程在进程余生内消失——正是 M14 引入该 scheduler
        要防的失败模式。现在经 `record_metric_safely`(构造 + 投递都受保护)。
        """
        with operation(
            self._telemetry,
            scope=OperationScope.LEASE_RECOVERY,
            name="lease_recovery.pass",
        ) as op:
            try:
                recovered = self._workflow.recover_expired_leases()
            except Exception:
                op.set_outcome(OperationOutcome.FAILED, "lease_recovery_failed")
                raise
            if recovered:
                record_metric_safely(
                    self._telemetry,
                    lambda: MetricSample(
                        name=MetricName.WORKFLOW_LEASE_EXPIRED,
                        kind=MetricKind.COUNTER,
                        value=recovered,
                    ),
                )
            return int(recovered)


class OutboxRelayScheduler(PeriodicDaemon):
    """Background daemon that drains PG outbox via PgOutboxRelay (WP-E).

    Periodically calls `PgOutboxRelay.run_once()` to forward PG workflow
    events to the control-plane publisher. At-least-once semantics: partial
    passes are safe, consumer deduplicates by event_id.
    """

    job = ScheduleJob.OUTBOX_RELAY
    thread_name = "outbox-relay"

    def __init__(
        self,
        engine: Any,
        sink: Any,
        *,
        interval_seconds: float = 5.0,
        telemetry: TelemetrySink | None = None,
        control: Any = None,
    ) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._engine = engine
        self._sink = sink
        self._telemetry = telemetry
        self._relay: Any = None

    def _relay_instance(self) -> Any:
        if self._relay is None:
            from adapters.postgres.outbox_relay import PgOutboxRelay

            self._relay = PgOutboxRelay(self._engine, self._sink, telemetry=self._telemetry)
        return self._relay

    def _execute_pass(self) -> None:
        with operation(
            self._telemetry,
            scope=OperationScope.OUTBOX_RELAY,
            name="outbox.relay_pass",
        ) as op:
            try:
                self._relay_instance().run_once()
            except Exception:
                op.set_outcome(OperationOutcome.FAILED, "outbox_relay_failed")
                raise


class RetentionScheduler(PeriodicDaemon):
    """Background daemon that applies artifact retention on interval (M14 DS-2).

    Calls `apply_retention(store)` periodically. No new Port — it operates on
    the existing ArtifactStore port. Single-artifact failures are already
    skipped inside apply_retention (InvalidInputError → skipped), so a pass
    never aborts mid-scan.
    """

    job = ScheduleJob.RETENTION
    thread_name = "retention"

    def __init__(
        self,
        store: Any,
        *,
        interval_seconds: float = 3600.0,
        control: Any = None,
    ) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._store = store
        self.last_report: Any = None

    def _execute_pass(self) -> Any:
        from packages.application.artifacts.retention import apply_retention

        report = apply_retention(self._store)
        self.last_report = report
        return report


class WorkerReaperScheduler(PeriodicDaemon):
    """Background daemon that marks heartbeat-expired workers LOST (M16 WP1).

    Server time is the sole authority: `registry.list_stale()` compares each
    worker's `last_heartbeat` against the database clock. The reaper only
    flips worker state to LOST; releasing the lost worker's leases stays the
    job of `recover_expired_leases` (single lease authority, M16 §5).

    Shape mirrors `LeaseRecoveryScheduler`: stdlib daemon thread, telemetry
    fail-open (a metric error must never kill the reaper loop).
    """

    job = ScheduleJob.WORKER_REAPER
    thread_name = "worker-reaper"

    def __init__(
        self,
        registry: WorkerRegistry,
        *,
        stale_threshold_seconds: float = 30.0,
        interval_seconds: float = 15.0,
        telemetry: TelemetrySink | None = None,
        control: Any = None,
    ) -> None:
        if stale_threshold_seconds <= 0:
            raise ValueError("stale_threshold_seconds must be > 0")
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._registry = registry
        self._stale = stale_threshold_seconds
        self._telemetry = telemetry

    def _execute_pass(self) -> int:
        """One reap pass: mark every stale worker LOST; return the count."""
        with operation(
            self._telemetry,
            scope=OperationScope.WORKER_SESSION,
            name="worker.reaper_pass",
        ) as op:
            try:
                lost = self._registry.list_stale(self._stale)
            except Exception:
                op.set_outcome(OperationOutcome.FAILED, "worker_reap_failed")
                raise
            for worker_id in lost:
                try:
                    self._registry.mark_lost(worker_id)
                except Exception:
                    # A concurrent transition (e.g. worker re-registered) is not a
                    # reaper failure; the next pass re-evaluates from server time.
                    continue
            return len(lost)
