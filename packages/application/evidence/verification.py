"""Claim 升级 use case：只有 evidence-backed 的 PROPOSED Claim 才能 VERIFIED。

VERIFIED 前置（AGENTS.md §8、ADR-0003）：
- Claim 状态为 PROPOSED（DISPUTED/RETRACTED 走 contradiction 流程）；
- 至少一条 EvidenceRelation，且 Evidence 能在 ledger 解析；
- Evidence 的 source 已在 ledger 登记（provenance 可追溯）；
- 由独立验证依据授权（acceptance gate PASS verdict），
  不能由 Agent 自述 / ToolResult / 聊天摘要升级。

本模块不发布事件；事件发布由编排层（phase_runner）负责。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.evidence import Claim, ClaimStatus


@dataclass(frozen=True, slots=True)
class VerificationBasis:
    """独立验证依据：acceptance gate 的 verdict 与评审者身份。"""

    verdict: str
    reviewer: str

    def __post_init__(self) -> None:
        if not self.verdict:
            raise ValueError("verification verdict must not be empty")
        if not self.reviewer:
            raise ValueError("verification reviewer must not be empty")


def promote_claim_to_verified(
    ledger: EvidenceLedger,
    claim: Claim,
    *,
    basis: VerificationBasis,
) -> Claim:
    """PROPOSED → VERIFIED；任一前置不满足抛 InvalidInputError。"""
    if claim.status is not ClaimStatus.PROPOSED:
        raise InvalidInputError(f"claim {claim.id} cannot be verified from {claim.status.value}")
    if basis.verdict != "PASS":
        raise InvalidInputError("claim verification requires a passing gate verdict")
    if not claim.evidence_relations:
        raise InvalidInputError(f"claim {claim.id} has no evidence relations")
    for evidence_id, _relation in claim.evidence_relations:
        evidence = ledger.get_evidence(evidence_id)
        if not ledger.has_source(evidence.source_ref):
            raise InvalidInputError(
                f"evidence {evidence_id} source {evidence.source_ref!r} "
                "is not registered in the ledger"
            )
    verified = Claim(
        id=claim.id,
        statement=claim.statement,
        status=ClaimStatus.VERIFIED,
        author=claim.author,
        evidence_relations=claim.evidence_relations,
    )
    ledger.update_claim(verified)
    return verified
