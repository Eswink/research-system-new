"""RunOrchestrationService 的依赖聚合（composition root 注入面）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.cost.pricing import PricingTable
from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.approval_store import ApprovalStore
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.pricing_snapshot_store import PricingSnapshotStore
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.output_schema_check import output_schema_check_for


@dataclass(frozen=True, slots=True)
class OrchestrationDependencies:
    """composition root：全部 Port 显式注入，不直接实例化 adapter。"""

    runtime: AgentRuntime
    workflow: WorkflowEngine
    artifacts: ArtifactStore
    events: EventPublisher
    budget: BudgetLedger | None = None
    ledger: EvidenceLedger | None = None
    telemetry: TelemetrySink | None = None
    # M15 定价冻结(BLOCKER-6):成对注入;缺省 = 冻结的 manifest 不携带
    # 定价引用(遗留行为,投影侧显式表达"pricing 未冻结")。
    pricing: PricingTable | None = None
    pricing_store: PricingSnapshotStore | None = None
    # WP-H：human gate 审批注册面（与 ApiDeps.approvals 同一实例，由 composition
    # root 保证；None 时 human gate 不注入执行循环 → 不会静默暂停）。
    approvals: ApprovalStore | None = None
    # GOAL-011 EC-01：运行链能力步装配面（`phase_capabilities.CapabilityDeps`）。
    # None（缺省）= 该步不启用；注入 = 本装配声明"这些 run-chain 能力由运行链执行"，
    # 而 phase 是否属于运行链执行仍由协议侧 `capability_execution` 决定。
    # 注解取 Any：本模块不因此导入 phase_capabilities（依赖方向单向）。
    capabilities: Any | None = None
    # GOAL-011 EC-03：**沙箱实验**阶段的执行缝（与 `PhaseRunnerDeps.experiment_task` 同型）。
    # None（缺省）= 没接。此时契约里**声明了** `experiment` 的任务以**点名拒绝**收敛
    # （fail-closed，不静默回退到会话——否则"声明了实验"与"真的跑了实验"会分叉）。
    experiment_task: Any | None = None
    # GOAL-014 EC-02（A/a）：`SCHEMA_VALID` 的**产品路径**校验回调工厂
    # （`output_schema` 名 → `SchemaCheck`）。缺省就是产品实现（按合约声明的 schema 名从
    # 仓内 `schemas/` 取；见 `output_schema_check`）——装配方可以换，但**不接**不等于
    # 「这项算过」：取不到回调时该判据仍是既有的 `schema validator unavailable`（fail-closed）。
    output_schema_validator: Any | None = output_schema_check_for
    default_actor: str = "system:orchestration"


__all__ = ["OrchestrationDependencies"]
