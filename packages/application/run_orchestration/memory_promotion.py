"""Claim/Evidence -> Governed Memory promotion (IG-1 seam).

M10's MemoryWriteProposal gate is the only long-term memory write path.  This
module connects verified Claims to that gate.  It never writes directly to
MemoryStore.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.run_orchestration.result_handler import ResultRegistration
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.evidence import Claim, ClaimStatus, Evidence
from packages.domain.memory import MemoryRecord, MemoryWriteProposal


@dataclass(frozen=True, slots=True)
class MemoryPromotionContext:
    """Context for promoting verified claims into governed memory."""

    memory_gate: MemoryGateDeps
    tier: MemoryTier = MemoryTier.RUN
    kind: MemoryType = MemoryType.FACT
    confidence: float = 0.8
    content_builder: Callable[[Claim, tuple[Evidence, ...]], str] | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


def promote_memory_from_registration(
    ctx: MemoryPromotionContext,
    registration: ResultRegistration,
) -> tuple[MemoryRecord, ...]:
    """Commit one MemoryWriteProposal per verified claim in registration."""
    ledger = ctx.memory_gate.ledger
    if ledger is None:
        return ()
    records: list[MemoryRecord] = []
    for claim in registration.claims:
        current = ledger.get_claim(claim.id)
        if current.status is not ClaimStatus.VERIFIED:
            continue
        evidence = _evidence_for_claim(ledger, current)
        if not evidence:
            continue
        content = (
            ctx.content_builder(current, evidence)
            if ctx.content_builder is not None
            else f"Claim {current.id}: {current.statement}"
        )
        proposal = MemoryWriteProposal(
            id=f"memory:{current.id}",
            tier=ctx.tier,
            kind=ctx.kind,
            content=content,
            provenance=evidence[0].source_ref,
            confidence=ctx.confidence,
            scope=ctx.tier.value.lower(),
            proposed_by=ctx.memory_gate.actor,
        )
        result = commit_memory(proposal, ctx.memory_gate)
        if result.accepted and result.record is not None:
            records.append(result.record)
    return tuple(records)


def _evidence_for_claim(ledger: object, claim: Claim) -> tuple[Evidence, ...]:
    from packages.application.ports.evidence_ledger import EvidenceLedger

    assert isinstance(ledger, EvidenceLedger)
    evidence: list[Evidence] = []
    for evidence_id, _relation in claim.evidence_relations:
        evidence.append(ledger.get_evidence(evidence_id))
    return tuple(evidence)
