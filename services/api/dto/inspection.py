"""Evidence / Claim / Budget / Audit DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceDto(BaseModel):
    id: str
    source_ref: str
    content_digest: str
    run_id: str | None = None
    experiment_run_id: str | None = None
    artifact_id: str | None = None
    image_digest: str | None = None
    environment_digest: str | None = None
    model_refs: list[str] = Field(default_factory=list)
    manifest_digest: str | None = None


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


class UsageEntryDto(BaseModel):
    entry_id: str
    resource_type: str
    quantity: int
    unit: str
    cost_status: str
    estimated_cost_minor: int | None = None
    actual_cost_minor: int | None = None
    model_id: str | None = None
    task_id: str | None = None


class BudgetViewDto(BaseModel):
    entries: list[UsageEntryDto] = Field(default_factory=list)
    total_estimated_cost_minor: int
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
