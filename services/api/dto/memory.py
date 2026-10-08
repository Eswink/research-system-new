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
    # GOAL-20261008-039 EC-02：适用范围（AGENTS.md §8「有适用范围」的可判定形态）。
    scope: str = "project"
    valid_from: str | None = None
    review_after: str | None = None
    expires_at: str | None = None
    supersedes: list[str] = Field(default_factory=list)
    active: bool
    # GOAL-20261008-039 EC-04：**给定时点上的时效判定**（`EXPIRED` / `REVIEW_DUE` / None）。
    # 只有显式给 `at` 的路由才填它 —— 不给时点的读面**不猜**（`None` = 未判定）。
    validity: str | None = None


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


class MemoryValidityDto(BaseModel):
    """一条记忆在**给定时点**上的时效（GOAL-20261008-039 EC-04）。

    时点由调用方给（`at`）⇒ 同一份数据同一时点判定必相同（可复现；**不读挂钟**）。
    """

    id: str
    scope: str
    review_after: str | None = None
    expires_at: str | None = None
    validity: str | None = None


class MemoryValidityViewDto(BaseModel):
    """按显式时点的时效读面（逐条给判定 + 原始两时点）。"""

    at: str
    records: list[MemoryValidityDto] = Field(default_factory=list)
    scope_note: str
