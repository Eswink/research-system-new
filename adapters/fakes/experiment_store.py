"""FakeExperimentStore：ExperimentStore Port 的 deterministic 内存实现。

与 Postgres 实现同一语义：whole-object 存取、重复 save 覆盖、未知 id 抛
InvalidInputError（M5 D2 约定）。G14 队列：到期顺序 = COALESCE(not_before,
created_at) 升序，认领是条件更新（QUEUED→DISPATCHING），认领过期先归位再参与
认领（at-least-once）。
"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry
from packages.domain.experiment_state import ExperimentQueueState
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.state_base import InvalidTransitionError


class FakeExperimentStore(FakeBase):
    def __init__(self) -> None:
        super().__init__("experiment_store")
        self._plans: dict[str, ExperimentPlan] = {}
        self._runs: dict[str, ExperimentRun] = {}
        self._audits: dict[str, ReproducibilityAudit] = {}
        self._queue: dict[str, ExperimentQueueEntry] = {}

    def save_plan(self, plan: ExperimentPlan) -> None:
        self._enter("save_plan", plan.id.value)
        self._plans[plan.id.value] = plan

    def get_plan(self, plan_id: str) -> ExperimentPlan:
        self._enter("get_plan", plan_id)
        plan = self._plans.get(plan_id)
        if plan is None:
            raise InvalidInputError(f"unknown plan id: {plan_id}")
        return plan

    def list_plans(self, *, state: str | None = None) -> list[ExperimentPlan]:
        self._enter("list_plans", state or "-")
        plans = [plan for plan in self._plans.values() if state is None or plan.state == state]
        return sorted(plans, key=lambda plan: plan.created_at.value, reverse=True)

    def save_run(self, run: ExperimentRun) -> None:
        self._enter("save_run", run.id.value)
        self._runs[run.id.value] = run

    def get_run(self, run_id: str) -> ExperimentRun:
        self._enter("get_run", run_id)
        run = self._runs.get(run_id)
        if run is None:
            raise InvalidInputError(f"unknown run id: {run_id}")
        return run

    def save_audit(self, audit: ReproducibilityAudit) -> None:
        self._enter("save_audit", audit.experiment_run_id.value)
        self._audits[audit.experiment_run_id.value] = audit

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit:
        self._enter("get_audit", experiment_run_id)
        audit = self._audits.get(experiment_run_id)
        if audit is None:
            raise InvalidInputError(f"unknown audit for run: {experiment_run_id}")
        return audit

    # --- G14 队列 ---

    def save_queue_entry(self, entry: ExperimentQueueEntry) -> None:
        self._enter("save_queue_entry", entry.id.value)
        self._queue[entry.id.value] = entry

    def get_queue_entry(self, entry_id: str) -> ExperimentQueueEntry:
        self._enter("get_queue_entry", entry_id)
        return self._known_entry(entry_id)

    def _known_entry(self, entry_id: str) -> ExperimentQueueEntry:
        entry = self._queue.get(entry_id)
        if entry is None:
            raise InvalidInputError(f"unknown queue entry id: {entry_id}")
        return entry

    def list_queue_entries(self, project_id: str) -> list[ExperimentQueueEntry]:
        self._enter("list_queue_entries", project_id)
        entries = [entry for entry in self._queue.values() if entry.project_id == project_id]
        return sorted(entries, key=lambda entry: entry.created_at.value)

    def claim_due_entry(
        self, *, now: Timestamp, claim_ttl_seconds: float
    ) -> ExperimentQueueEntry | None:
        self._enter("claim_due_entry", now.value.isoformat())
        self._requeue_expired(now, claim_ttl_seconds)
        candidates = [entry for entry in self._queue.values() if entry.is_due(now)]
        if not candidates:
            return None
        entry = min(candidates, key=_due_order)
        claimed = entry.claim(now)
        self._queue[claimed.id.value] = claimed
        return claimed

    def cancel_queue_entry(self, entry_id: str, *, now: Timestamp) -> ExperimentQueueEntry:
        self._enter("cancel_queue_entry", entry_id)
        entry = self._known_entry(entry_id)
        try:
            cancelled = entry.cancel(now)
        except InvalidTransitionError as exc:
            raise InvalidInputError(self._conflict_message(entry_id)) from exc
        self._queue[entry_id] = cancelled
        return cancelled

    def reschedule_queue_entry(
        self,
        entry_id: str,
        *,
        not_before: Timestamp | None,
        now: Timestamp,
    ) -> ExperimentQueueEntry:
        self._enter("reschedule_queue_entry", entry_id)
        entry = self._known_entry(entry_id)
        try:
            rescheduled = entry.reschedule(not_before, now)
        except InvalidTransitionError as exc:
            raise InvalidInputError(self._conflict_message(entry_id)) from exc
        self._queue[entry_id] = rescheduled
        return rescheduled

    @staticmethod
    def _conflict_message(entry_id: str) -> str:
        return f"queue entry {entry_id} is not QUEUED; the operation applies to QUEUED only"

    def _requeue_expired(self, now: Timestamp, claim_ttl_seconds: float) -> None:
        """认领者已死（要求：超过 ttl）的 DISPATCHING 归位 QUEUED。"""
        for entry in list(self._queue.values()):
            if entry.state != ExperimentQueueState.State.DISPATCHING:
                continue
            if entry.claimed_at is None:
                expired = True
            else:
                expired = (now.value - entry.claimed_at.value).total_seconds() >= claim_ttl_seconds
            if expired:
                self._queue[entry.id.value] = entry.requeue(now)

    def close(self) -> None:
        super().close()


def _due_order(entry: ExperimentQueueEntry) -> tuple[object, object]:
    """到期顺序：未排期条目按创建时间参与排序（COALESCE(not_before, created_at)）。"""
    effective = entry.not_before.value if entry.not_before is not None else entry.created_at.value
    return (effective, entry.created_at.value)
