"""Memory / Context 域实体定义。

来源：docs/architecture/CONTEXT_ENGINE.md。
Memory 写入必须经过 MemoryWriteProposal → schema → provenance → policy → gate
（AGENTS.md §8）。向量索引是 derived，不是 canonical。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: str
    tier: MemoryTier
    kind: MemoryType
    content: str
    provenance: str
    confidence: float
    valid_from: Timestamp | None = None
    review_after: Timestamp | None = None
    expires_at: Timestamp | None = None
    supersedes: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("memory id must not be empty")
        if not self.content:
            raise ValueError("memory content must not be empty")
        if not self.provenance:
            raise ValueError("memory provenance must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class MemoryWriteProposal:
    id: str
    tier: MemoryTier
    kind: MemoryType
    content: str
    provenance: str
    confidence: float
    scope: str = "project"
    proposed_by: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("proposal id must not be empty")
        if not self.content:
            raise ValueError("proposal content must not be empty")
        if not self.provenance:
            raise ValueError("proposal provenance must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    selected_refs: list[str] = field(default_factory=list)
    template_hash: str | None = None
    retrieval_digest: str | None = None
    token_allocation: int = 0
    trust_labels: list[str] = field(default_factory=list)
    created_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if self.token_allocation < 0:
            raise ValueError("token_allocation must be non-negative")
