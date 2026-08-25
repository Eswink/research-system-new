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


class InterventionDto(BaseModel):
    """干预请求（M13：pause/resume 走状态机；语义变更 501）。"""

    kind: str = Field(pattern="^(pause|resume|budget_adjust|replace_agent)$")
    detail: str | None = None
