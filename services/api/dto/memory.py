"""Memory 控制面 DTO（PLAN-20260910-037 WP-F）。

诚实语义：提案经完整 §8 门链后直接提交（accepted）或以 stage+reasons
分类拒绝（422）；域内没有持久化 pending 状态，因此不提供两阶段 decide。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryRecordDto(BaseModel):
    id: str
    tier: str
    kind: str
    content: str
    provenance: str
    confidence: float
    valid_from: str | None = None
    review_after: str | None = None
    expires_at: str | None = None
    supersedes: list[str] = Field(default_factory=list)
    active: bool


class MemoryListViewDto(BaseModel):
    records: list[MemoryRecordDto] = Field(default_factory=list)
    scope_note: str


class MemoryProposalDto(BaseModel):
    tier: str = Field(min_length=1, max_length=40)
    kind: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=8000)
    provenance: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    supersedes: list[str] = Field(default_factory=list)
    proposed_by: str | None = Field(default=None, max_length=200)
    curator_approved: bool = False


class MemoryCommittedDto(BaseModel):
    record: MemoryRecordDto
    decision: str
