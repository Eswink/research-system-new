"""FakeExperimentStore：ExperimentStore Port 的 deterministic 内存实现。

与 Postgres 实现同一语义：whole-object 存取、重复 save 覆盖、未知 id 抛
InvalidInputError（M5 D2 约定）。
"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit


class FakeExperimentStore(FakeBase):
    def __init__(self) -> None:
        super().__init__("experiment_store")
        self._plans: dict[str, ExperimentPlan] = {}
        self._runs: dict[str, ExperimentRun] = {}
        self._audits: dict[str, ReproducibilityAudit] = {}

    def save_plan(self, plan: ExperimentPlan) -> None:
        self._enter("save_plan", plan.id.value)
        self._plans[plan.id.value] = plan

    def get_plan(self, plan_id: str) -> ExperimentPlan:
        self._enter("get_plan", plan_id)
        plan = self._plans.get(plan_id)
        if plan is None:
            raise InvalidInputError(f"unknown plan id: {plan_id}")
        return plan

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

    def close(self) -> None:
        super().close()
