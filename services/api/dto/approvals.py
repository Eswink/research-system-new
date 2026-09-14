"""Approvals / Interventions DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ApprovalDto(BaseModel):
    id: str
    run_id: str
    action: str
    risk: str
    context: str
    policy_source: str
    status: str
    version: str


class ApprovalDecideDto(BaseModel):
    decision: str = Field(pattern="^(approve|deny)$")


class BudgetAdjustLineDto(BaseModel):
    """budget_adjust 的单条调整：资源类型 + 目标额度（整个 run，非增量）。"""

    resource_type: str
    quantity: int = Field(ge=0)
    unit: str = Field(min_length=1, max_length=64)


class InterventionDto(BaseModel):
    """干预请求（pause/resume 走状态机；budget_adjust 走 BudgetLedger；
    语义变更 replace_agent 保持 501）。"""

    kind: str = Field(pattern="^(pause|resume|budget_adjust|replace_agent)$")
    detail: str | None = None
    adjustments: list[BudgetAdjustLineDto] = Field(default_factory=list)
