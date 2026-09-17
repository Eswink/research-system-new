"""过期 lease 的周期回收守护线程（GOAL-004 cycle 7 从 `scheduler.py` 拆出：450 行硬上限）。

与其余守护线程共享 `PeriodicDaemon` 的循环；这里只保留"跑一次回收"的业务动作。
"""

from __future__ import annotations

from typing import Any

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.schedules import ScheduleJob
from services.api.scheduler import PeriodicDaemon


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
