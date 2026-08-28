"""ExperimentStore Port：ExperimentPlan/Run/ReproducibilityAudit 持久化（M14 DS-1）。

职责：实验域三实体的生命周期状态持久化（whole-object 存储）：
- ExperimentPlan：预注册实验计划（状态机由 domain ExperimentPlanState 权威）；
- ExperimentRun：一次实验执行（spec/result 拆分；状态机由 ExperimentRunState 权威）；
- ReproducibilityAudit：可复现性绑定记录（audit_digest 复核语义在 domain）。

非职责：不执行实验（packages.application.experiments.execute）；不做状态
迁移判断；audit 的 findings/status 推导在 domain（packages.domain.reproducibility）。

M5 决策 D2：同步语义；未知 id 查询抛出 InvalidInputError（与 evidence_ledger
Port 同一约定）。audit 以 experiment_run_id 为查询键（一次 run 一份审计，
重复 save 为覆盖更新）。持久化落点：M14 PostgreSQL canonical state
（packages.domain.reproducibility 模块边界注记）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit


@runtime_checkable
class ExperimentStore(Protocol):
    """实验域三实体存储；CRUD 语义由实现保证。"""

    def save_plan(self, plan: ExperimentPlan) -> None: ...

    def get_plan(self, plan_id: str) -> ExperimentPlan: ...

    def save_run(self, run: ExperimentRun) -> None: ...

    def get_run(self, run_id: str) -> ExperimentRun: ...

    def save_audit(self, audit: ReproducibilityAudit) -> None: ...

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit: ...

    def close(self) -> None: ...
