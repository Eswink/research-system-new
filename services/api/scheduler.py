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
from dataclasses import dataclass, replace
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
from packages.domain.run_state import ResearchRunState
from packages.domain.schedules import ScheduleJob
from services.api.run_resume import RebuildRefused, continue_from_rebuild


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


@dataclass(frozen=True, slots=True)
class RetryDispatchDeps:
    """派发所需的三个只读面（参数对象，避免参数爆发）。

    `rebuild` 是本进程**没有**续跑上下文时的第二入口（GOAL-003 cycle 20）：按 run 记下的
    装配来源重建上下文并续跑（composition root 注入 `run_resume.rebuild_and_resume`）。
    None ⇒ 重启后的停车 run 只能等人工——诚实降级，不假装有派发方。
    """

    runs: Any
    runs_store: Any
    workflow: Any
    rebuild: Any = None


class RetryDispatchScheduler(PeriodicDaemon):
    """把**重排已到期**的停车 run 自动续跑（GOAL-003 cycle 19）。

    cycle 18 之后，"退避 > 0"的任务失败会把 run 停在 `PAUSED`（而不是终态 FAILED），
    失败任务与后续 specs 交回 service 暂存——但**没有人自动来按 resume**：worker 的
    `claim_next` 只派发 EXECUTION 任务，lease 恢复面也不管这件事（探针实测）。

    本守护线程就是那个派发方：扫到期的停车 run 并续跑一次。判定"到期"只问
    `WorkflowEngine.due_retry_task_ids(run_id)`（adapter 内用权威时钟比较，与写
    `retry_at` 同源），本类不自己拿墙钟去比。

    诚实边界（写进读面事实，不假装成功）：

    - 只有**本进程**持有续跑上下文（`has_paused_context`）时才动手——进程重启后
      上下文的缺席是诚实的，跳过并计数，等人工/控制面处理；
    - 用户手动暂停的 run 没有到期的重排 ⇒ 本守护线程不会碰它（区分靠任务面，
      不靠猜测）；
    - 单个 run 的失败不影响整轮（下一个 pass 重新评估）。
    """

    job = ScheduleJob.RETRY_DISPATCH
    thread_name = "retry-dispatch"

    def __init__(
        self,
        deps: RetryDispatchDeps,
        *,
        interval_seconds: float = 15.0,
        telemetry: TelemetrySink | None = None,
        control: Any = None,
    ) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._runs = deps.runs
        self._runs_store = deps.runs_store
        self._workflow = deps.workflow
        self._rebuild = deps.rebuild
        self._telemetry = telemetry

    def _execute_pass(self) -> int:
        """One dispatch pass: resume every parked run whose retry is due.

        `dispatched` 是本轮真的被续跑的 run 数——读面据此区分"跑过但没有可派发的"
        与"跑过并推进了工作"。
        """
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="retry.dispatch_pass",
        ) as op:
            try:
                dispatched = self._dispatch_due()
            except Exception:
                op.set_outcome(OperationOutcome.FAILED, "retry_dispatch_failed")
                raise
            return dispatched

    def _dispatch_due(self) -> int:
        dispatched = 0
        for run in self._runs_store.list_runs():
            if run.state != ResearchRunState.State.PAUSED:
                continue
            run_id = run.id.value
            local = self._runs.has_paused_context(run_id)
            if not local and not self._can_rebuild(run):
                continue  # 没有续跑能力（既有：上下文不在本进程；cycle 20 起：也无可重建来源）
            try:
                if not self._workflow.due_retry_task_ids(run_id):
                    continue  # 没有到期的重排（含用户手动暂停）：不是本守护线程的事
            except Exception:
                continue  # 读面失败：下一个 pass 重新评估，不因为一个 run 中断整轮
            dispatched += self._resume(run_id, run, local=local)
        return dispatched

    def _can_rebuild(self, run: Any) -> bool:
        """重建入口可用性：本进程装了重建函数 **且** run 记下了装配来源。

        来源缺失（早于来源登记的旧 run）时不翻转 canonical 状态——不把"没有入口"
        伪装成"派发过一次"。
        """
        return self._rebuild is not None and getattr(run, "protocol_source", None) is not None

    def _resume(self, run_id: str, run: Any, *, local: bool) -> int:
        """续跑一个到期的停车 run：先迁 canonical 状态，再续跑，最后写回结果。

        顺序不是随意的：协作式暂停谓词读的就是 canonical run 状态（`pause_requested`），
        所以"还停在 PAUSED"就是"继续暂停"——必须先按状态机迁到 RUNNING 并落库，续跑才
        真的会执行任务（与 `POST /runs/{id}/resume` 同序）。续跑又停回 PAUSED（例如
        durable 侧其实还没到期）时如实写回 PAUSED。

        两种续跑来源（GOAL-003 cycle 20）：本进程持有上下文 ⇒ `resume_paused`；否则按
        run 记下的装配来源重建。**重建被诚实拒绝**时把 canonical 放回停车状态（本进程
        一个任务都没执行，留 RUNNING 就不是事实）；上下文竞态等其他失败仍返回 0 并留
        RUNNING（派发已释放、没有 continuation）——与 API 面"解除暂停但不伪装续跑"同义。
        """
        try:
            resumed = run.transition(ResearchRunState.Transition.RESUME)
        except Exception:
            return 0  # 状态机不允许（并发迁移）——不是本守护线程该处理的
        try:
            self._runs_store.save_run(resumed)
            outcome = (
                self._runs.resume_paused(run_id, resumed)
                if local
                else continue_from_rebuild(self._rebuild, resumed)
            )
        except RebuildRefused:
            try:
                self._runs_store.save_run(resumed.transition(ResearchRunState.Transition.PAUSE))
            except Exception:
                pass
            return 0
        except Exception:
            return 0
        try:
            self._runs_store.save_run(replace(resumed, state=outcome.state))
        except Exception:
            return 0
        return 1
