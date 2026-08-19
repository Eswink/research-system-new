"""Evidence / Claim 域实体定义。

来源：docs/architecture/DATA_LIFECYCLE.md（SourceRecord）、docs/storage/DATABASE_SCHEMA.md。
VERIFIED Claim 必须有 provenance / EvidenceRelation；Writer 不能升级 Claim truth。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel


class ClaimStatus(StrEnum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    RETRACTED = "RETRACTED"


class EvidenceRelationType(StrEnum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    CORROBORATES = "CORROBORATES"


@dataclass(frozen=True, slots=True)
class SourceRecord:
    origin: str
    content_digest: str
    trust_label: TrustLabel = TrustLabel.UNTRUSTED_EXTERNAL
    access_time: Timestamp | None = None
    license_terms: str | None = None
    authors: list[str] = field(default_factory=list)
    parser_version: str | None = None

    def __post_init__(self) -> None:
        if not self.origin:
            raise ValueError("source origin must not be empty")
        if not self.content_digest:
            raise ValueError("source content_digest must not be empty")


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    source_ref: str
    content_digest: str
    extracted_by: str | None = None
    captured_at: Timestamp | None = None
    artifact_id: str | None = None
    run_id: str | None = None
    experiment_run_id: str | None = None
    metric_refs: tuple[str, ...] = ()
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    image_digest: str | None = None
    environment_digest: str | None = None
    tool_refs: tuple[str, ...] = ()
    skill_refs: tuple[str, ...] = ()
    model_refs: tuple[str, ...] = ()
    manifest_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("evidence id must not be empty")
        if not self.source_ref:
            raise ValueError("evidence source_ref must not be empty")
        if not self.content_digest:
            raise ValueError("evidence content_digest must not be empty")
        if self.artifact_id is not None and not self.artifact_id:
            raise ValueError("evidence artifact_id must not be empty when present")


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    statement: str
    status: ClaimStatus = ClaimStatus.DRAFT
    author: str | None = None
    evidence_relations: list[tuple[str, EvidenceRelationType]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("claim id must not be empty")
        if not self.statement:
            raise ValueError("claim statement must not be empty")
        if self.status is ClaimStatus.VERIFIED and not self.evidence_relations:
            raise ValueError("VERIFIED claim must reference at least one evidence relation")


@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    claim_id: str
    evidence_id: str
    relation: EvidenceRelationType
    strength: float = 1.0

    def __post_init__(self) -> None:
        if not self.claim_id:
            raise ValueError("claim_id must not be empty")
        if not self.evidence_id:
            raise ValueError("evidence_id must not be empty")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Decision:
    id: str
    decision: str
    rationale: str = ""
    decided_by: str | None = None
    decided_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("decision id must not be empty")
        if not self.decision:
            raise ValueError("decision text must not be empty")


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    id: str
    review_type: str
    verdict: str
    findings: list[str] = field(default_factory=list)
    reviewed_by: str | None = None
    reviewed_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("finding id must not be empty")
        if not self.verdict:
            raise ValueError("verdict must not be empty")
