"""G14 实验队列派发器（控制面进程内的调度消费者）。

队列条目只有被真正派发才有意义，因此这里是与 `POST /runs` **同一装配链**的
消费者（`services.api.run_execution`），不是第二套执行器：

- 认领：`ExperimentStore.claim_due_entry` 原子把条目 QUEUED → DISPATCHING，
  同一时刻只有一个派发者拿到它（PG `FOR UPDATE SKIP LOCKED` / SQLite 条件更新）。
- 派发：按条目冻结的协议来源启动 run，成功写回 `run_id`（DISPATCHED），
  失败写回原因（FAILED）。派发前检查计划是否已归档——归档计划不再启动。
- 恢复：认领超过 `claim_ttl_seconds` 的条目（进程崩溃/停机中被中断）回到
  QUEUED 并重新派发。这是 **at-least-once**：不假装 exactly-once，重派发会在
  控制面产生第二次启动尝试，条目上的 `run_id` 始终是最近一次派发的结果。
- 串行：进程内 run 是同步执行的（HTTP 面亦然），因此一次 pass 默认只派发一条；
  多实例并发由原子认领保证不重复认领，吞吐不上行（本轮不引入执行面扩容）。

守护线程形态与 `services/api/scheduler.py` 的既有 scheduler 一致：stdlib 线程、
telemetry fail-open、stop 有界。停机时不打断在途 run；被中断的认领留给 TTL 恢复。
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.experiment_store import ExperimentStore
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.core import ID, Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.state_base import InvalidTransitionError
from services.api.composition import ApiDeps
from services.api.run_access import save_run
from services.api.run_execution import ExecutionRequest, start_run_from_source

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DispatchOutcome:
    """一次派发尝试的结果（供测试与运维观测；不落库的部分不复用）。"""

    entry_id: str
    dispatched: bool
    run_id: str | None = None
    reason: str | None = None


class ExperimentQueueDispatcher:
    """按排期认领并派发实验队列条目的后台守护线程。"""

    def __init__(
        self,
        deps: ApiDeps,
        *,
        interval_seconds: float = 15.0,
        claim_ttl_seconds: float = 300.0,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if claim_ttl_seconds <= 0:
            raise ValueError("claim_ttl_seconds must be > 0")
        self._deps = deps
        self._interval = interval_seconds
        self._claim_ttl = claim_ttl_seconds
        self._telemetry = telemetry if telemetry is not None else deps.telemetry
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def store(self) -> ExperimentStore | None:
        """Port 句柄：装配面允许缺席（未配置 experiment store 时派发整体禁用）。"""
        store: ExperimentStore | None = self._deps.experiment_store
        return store

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="experiment-queue", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            self.run_once()

    def run_once(self, *, now: Timestamp | None = None) -> list[DispatchOutcome]:
        """One pass: claim at most one due entry and dispatch it (M14 scheduler shape)."""
        store = self.store
        if store is None:
            return []
        with operation(
            self._telemetry,
            scope=OperationScope.EXPERIMENT_QUEUE,
            name="experiment_queue.dispatch_pass",
        ) as op:
            tried = now or Timestamp.now()
            try:
                entry = store.claim_due_entry(now=tried, claim_ttl_seconds=self._claim_ttl)
            except Exception:
                op.set_outcome(OperationOutcome.FAILED, "claim_failed")
                _log.warning("experiment queue claim failed", exc_info=True)
                return []
            if entry is None:
                return []
            outcome = self._dispatch(entry)
            if not outcome.dispatched:
                op.set_outcome(OperationOutcome.FAILED, "dispatch_failed")
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.EXPERIMENT_QUEUE_DISPATCH_TOTAL,
                    kind=MetricKind.COUNTER,
                    value=1,
                ),
            )
            return [outcome]

    def _dispatch(self, entry: ExperimentQueueEntry) -> DispatchOutcome:
        """派发一条已认领条目；失败原因写回条目（不静默重试）。"""
        store = self.store
        assert store is not None
        reason = self._blocking_reason(entry)
        if reason is not None:
            return self._fail(entry, reason)
        draft_ref = entry.source.draft_ref
        try:
            run = start_run_from_source(
                ExecutionRequest(
                    self._deps,
                    entry.source.protocol_path,
                    ID.generate(),
                    f"queue-{entry.id.value}",
                    draft_ref,
                    entry.project_id,
                )
            )
        except Exception as exc:  # noqa: BLE001 - 任何启动失败都是条目的失败原因
            return self._fail(entry, _short_reason(exc))
        save_run(self._deps, run)
        store.save_queue_entry(entry.mark_dispatched(run.id.value))
        _log.info("experiment queue entry %s dispatched as run %s", entry.id.value, run.id.value)
        return DispatchOutcome(entry_id=entry.id.value, dispatched=True, run_id=run.id.value)

    def _blocking_reason(self, entry: ExperimentQueueEntry) -> str | None:
        """派发前的事实检查：计划必须仍可启动（归档计划不再启动）。"""
        store = self.store
        assert store is not None
        try:
            plan = store.get_plan(entry.plan_id.value)
        except InvalidInputError:
            return f"experiment plan {entry.plan_id.value} no longer exists"
        if plan.state == ExperimentPlanState.State.ARCHIVED:
            return f"experiment plan {entry.plan_id.value} is ARCHIVED; not dispatching"
        return None

    def _fail(self, entry: ExperimentQueueEntry, reason: str) -> DispatchOutcome:
        store = self.store
        assert store is not None
        try:
            store.save_queue_entry(entry.mark_failed(reason))
        except InvalidTransitionError:  # pragma: no cover - 认领后状态由本进程持有
            _log.warning("queue entry %s vanished before failure was recorded", entry.id.value)
        _log.warning("experiment queue entry %s not dispatched: %s", entry.id.value, reason)
        return DispatchOutcome(entry_id=entry.id.value, dispatched=False, reason=reason)


def _short_reason(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return text if len(text) <= 500 else f"{text[:497]}..."


__all__ = ["DispatchOutcome", "ExperimentQueueDispatcher"]
