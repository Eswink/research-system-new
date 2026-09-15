"""ExperimentStore Port：ExperimentPlan/Run/ReproducibilityAudit/QueueEntry 持久化。

职责：实验域实体的生命周期状态持久化（whole-object 存储）：
- ExperimentPlan：预注册实验计划（状态机由 domain ExperimentPlanState 权威）；
- ExperimentRun：一次实验执行（spec/result 拆分；状态机由 ExperimentRunState 权威）；
- ReproducibilityAudit：可复现性绑定记录（audit_digest 复核语义在 domain）；
- ExperimentQueueEntry（G14）：排队待派发的启动请求（状态机由 domain
  ExperimentQueueState 权威）。

非职责：不执行实验（packages.application.experiments.execute）；不做状态
迁移判断；audit 的 findings/status 推导在 domain（packages.domain.reproducibility）。

M5 决策 D2：同步语义；未知 id 查询抛出 InvalidInputError（与 evidence_ledger
Port 同一约定）。audit 以 experiment_run_id 为查询键（一次 run 一份审计，
重复 save 为覆盖更新）。持久化落点：M14 PostgreSQL canonical state
（packages.domain.reproducibility 模块边界注记）。

G14 队列语义（存储层只做**条件更新**，判定仍在 domain）：
- `claim_due_entry` 是原子 compare-and-set（QUEUED → DISPATCHING），同一时刻
  只有一个派发者能拿到某条目；过期的 DISPATCHING（认领者已死）先归位 QUEUED
  再参与认领 —— 这就是 at-least-once 的落点，不假装 exactly-once。
- `cancel_queue_entry` / `reschedule_queue_entry` 只作用于 QUEUED；条件不满足时
  抛 InvalidInputError（调用方映射 409），未知 id 同样抛 InvalidInputError。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.core import Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit


@runtime_checkable
class ExperimentStore(Protocol):
    """实验域实体存储；CRUD 语义由实现保证。"""

    def save_plan(self, plan: ExperimentPlan) -> None: ...

    def get_plan(self, plan_id: str) -> ExperimentPlan: ...

    def list_plans(self, *, state: str | None = None) -> list[ExperimentPlan]: ...

    def save_run(self, run: ExperimentRun) -> None: ...

    def get_run(self, run_id: str) -> ExperimentRun: ...

    def save_audit(self, audit: ReproducibilityAudit) -> None: ...

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit: ...

    # --- G14 实验队列 ---

    def save_queue_entry(self, entry: ExperimentQueueEntry) -> None: ...

    def get_queue_entry(self, entry_id: str) -> ExperimentQueueEntry: ...

    def list_queue_entries(self, project_id: str) -> list[ExperimentQueueEntry]: ...

    def claim_due_entry(
        self, *, now: Timestamp, claim_ttl_seconds: float
    ) -> ExperimentQueueEntry | None: ...

    def cancel_queue_entry(self, entry_id: str, *, now: Timestamp) -> ExperimentQueueEntry: ...

    def reschedule_queue_entry(
        self,
        entry_id: str,
        *,
        not_before: Timestamp | None,
        now: Timestamp,
    ) -> ExperimentQueueEntry: ...

    def close(self) -> None: ...
