"""Evidence / Claim / Budget / Audit DTO。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from services.api.dto.enums import (
    LedgerCostStatusValue,
    LedgerQuantityStatusValue,
    ResourceTypeValue,
)


class EvidenceDto(BaseModel):
    id: str
    source_ref: str
    content_digest: str
    run_id: str | None = None
    experiment_run_id: str | None = None
    artifact_id: str | None = None
    image_digest: str | None = None
    environment_digest: str | None = None
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    model_refs: list[str] = Field(default_factory=list)
    manifest_digest: str | None = None
    # GOAL-010 EC-02：来源记录的**可读面**。`EVIDENCE_COVERAGE` 的判据要求
    # 「其 `origin` / `trust_label` 可取」，而在加这两个字段之前 `SourceRecord`
    # **没有任何读面**（`services/` 里对 `SourceRecord` 零命中）⇒ 判据只能靠读库
    # 或读代码间接凑。取不到来源时保持 None（不伪填充）。
    source_origin: str | None = None
    source_trust_label: str | None = None
    source_access_time: str | None = None
    # GOAL-011 EC-01：**工具观测**的可读面之一。`Evidence.tool_refs` 一直有持久化，
    # 但直到这里才有读面 ⇒ 判据此前**没法**从读面区分「这条证据是一次工具调用产生的」
    # 与「它是模型自述」。空列表 = 不是工具来源（**不**伪填充一个工具名）。
    tool_refs: list[str] = Field(default_factory=list)


class RelationDto(BaseModel):
    claim_id: str
    evidence_id: str
    relation: str
    strength: float = 1.0


class ClaimDto(BaseModel):
    id: str
    statement: str
    status: str
    author: str | None = None
    relations: list[RelationDto] = Field(default_factory=list)


class ClaimMapDto(BaseModel):
    claims: list[ClaimDto] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    contradictory_claims: list[str] = Field(default_factory=list)
    degraded: bool = False


class UsageEntryDto(BaseModel):
    entry_id: str
    resource_type: ResourceTypeValue
    # PA-1 W3: duration resources (seconds) may be fractional Decimals.
    quantity: int | Decimal
    unit: str
    cost_status: LedgerCostStatusValue
    estimated_cost_minor: int | None = None
    actual_cost_minor: int | None = None
    currency: str
    quantity_status: LedgerQuantityStatusValue
    unavailable_reason: str | None = None
    attempt: int
    run_id: str | None = None
    model_id: str | None = None
    task_id: str | None = None


class BudgetViewDto(BaseModel):
    entries: list[UsageEntryDto] = Field(default_factory=list)
    # None 表示总额不完整（UNKNOWN / 未定价），绝不以 0 补齐。
    total_estimated_cost_minor: int | None = None
    total_currency: str | None = None
    known_cost_subtotal_minor: int | None = 0
    unknown_cost_entries: int
    reservations: list[dict[str, object]] = Field(default_factory=list)


class ExportBundleDto(BaseModel):
    run_id: str
    run_state: str
    manifest_digest: str | None = None
    evidence: list[EvidenceDto] = Field(default_factory=list)
    claims: list[ClaimDto] = Field(default_factory=list)
    usage: BudgetViewDto
    exported_from: str


class DeliverableDto(BaseModel):
    """Run 的 persisted research deliverable（M12 build_deliverable 产物）。

    available=false 时 deliverable 恒空 dict，reason 说明为何不可用（不伪装
    生成空报告）。artifact_id/digest 指向 artifact store 中的 `deliverable.json`。
    """

    run_id: str
    available: bool
    reason: str | None = None
    artifact_id: str | None = None
    artifact_digest: str | None = None
    deliverable: dict[str, object] = Field(default_factory=dict)


class LineageNodeDto(BaseModel):
    id: str
    kind: str
    label: str
    run_id: str | None = None


class LineageEdgeDto(BaseModel):
    source: str
    target: str
    relation: str


class LineageDto(BaseModel):
    """Run 级来源血缘投影（nodes/edges 确定性排序）。

    只由 API 明确返回的 evidence/claim/artifact 引用构造边；缺失引用显示为
    断开（不补节点）。全局跨 run 血缘仍不可用（G9）。
    """

    run_id: str
    nodes: list[LineageNodeDto] = Field(default_factory=list)
    edges: list[LineageEdgeDto] = Field(default_factory=list)
    global_lineage_available: bool = False
    global_lineage_reason: str | None = None
    degraded: bool = False


class ProjectLineageNodeDto(BaseModel):
    """项目级血缘节点：run-scope 同规则，另带贡献该节点的 run 列表。

    `shared=true` 表示有多个 run 贡献同一节点 id（跨 run 的公共来源/制品/模型）
    —— 跨 run 关系由**共享节点**表达，不由猜测的连边表达。
    """

    id: str
    kind: str
    label: str
    run_ids: list[str] = Field(default_factory=list)
    shared: bool = False


class ProjectLineageResourceDto(BaseModel):
    """项目库资源条目（数据集/提示词/笔记本）的未连边清单项。"""

    id: str
    kind: str
    name: str
    status: str


class ProjectLineageDto(BaseModel):
    """项目级来源血缘投影（G9 / GOAL-20260915-002 EC-01）。

    `reference_recording` 如实说明：run 与库资源（数据集/提示词）的引用关系当前
    **没有记录面**，因此 `library_resources` 只是未连边清单，不画资源边。
    """

    project_id: str
    run_count: int
    nodes: list[ProjectLineageNodeDto] = Field(default_factory=list)
    edges: list[LineageEdgeDto] = Field(default_factory=list)
    library_resources: list[ProjectLineageResourceDto] = Field(default_factory=list)
    reference_recording: str = "NOT_RECORDED"
    reference_recording_reason: str | None = None
    degraded: bool = False
    degraded_reason: str | None = None


class ExperimentRunDto(BaseModel):
    """单个 experiment run 的只读视图（persisted truth）。"""

    experiment_run_id: str
    artifact_ids: list[str] = Field(default_factory=list)
    image_digest: str | None = None
    environment_digest: str | None = None
    metrics: dict[str, object] = Field(default_factory=dict)
    reproduction_available: bool = False


class ExperimentViewDto(BaseModel):
    """run 的 experiment 聚合视图；reproduction 诚实标注 unavailable。"""

    experiments: list[ExperimentRunDto] = Field(default_factory=list)
    reproduction_note: str = ""
