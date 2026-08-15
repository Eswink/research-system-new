"""编排内 Claim 升级（gate PASS → VERIFIED + CLAIM_VERIFIED 事件）。

与 phase_runner 分离：升级逻辑独立可测，phase_runner 只负责调用。
ledger 未装配或证据前置不满足时安全跳过（绝不无证据升级）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from packages.application.evidence.verification import (
    VerificationBasis,
    promote_claim_to_verified,
)
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.evaluation_gate import (
    GateOutcome,
    verify_claim_with_evidence,
)
from packages.application.run_orchestration.result_handler import ResultRegistration
from packages.domain.events import EventType


@dataclass(frozen=True, slots=True)
class ClaimPromotionContext:
    """升级所需的依赖与标识（参数对象，避免参数爆发）。"""

    ledger: EvidenceLedger
    reviewer: str
    run_id: str
    trace_id: str
    task_id: str
    emit: Callable[[EventType, dict[str, object], str, str, str | None], None]


def promote_registered_claims(
    ctx: ClaimPromotionContext,
    registration: ResultRegistration,
    gate: GateOutcome,
) -> None:
    """gate PASS 后把 ledger 中已登记（合并 relations）的 Claim 升级。"""
    if not verify_claim_with_evidence(gate.evaluations, registration.evidence_source_count):
        return
    seen: set[str] = set()
    for claim in registration.claims:
        if claim.id in seen:
            continue
        seen.add(claim.id)
        registered = ctx.ledger.get_claim(claim.id)
        verified = promote_claim_to_verified(
            ctx.ledger,
            registered,
            basis=VerificationBasis(verdict="PASS", reviewer=ctx.reviewer),
        )
        ctx.emit(
            EventType.CLAIM_VERIFIED,
            {
                "claim_id": verified.id,
                "reviewer": ctx.reviewer,
                "task_id": ctx.task_id,
            },
            ctx.run_id,
            ctx.trace_id,
            ctx.task_id,
        )
