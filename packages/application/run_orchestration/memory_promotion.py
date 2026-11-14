"""Claim/Evidence -> Governed Memory promotion (IG-1 seam).

M10's MemoryWriteProposal gate is the only long-term memory write path.  This
module connects verified Claims to that gate.  It never writes directly to
MemoryStore.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.run_orchestration.result_handler import ResultRegistration
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.evidence import Claim, ClaimStatus, Evidence
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from packages.domain.tasks import MemoryExportSpec


@dataclass(frozen=True, slots=True)
class MemoryPromotionContext:
    """Context for promoting verified claims into governed memory.

    `curator_approved`（GOAL-20261114-113 EC-03）原样转交 `commit_memory`：PROJECT /
    ORGANIZATION 档的 curator 门**不放宽**（`gate.py` 逐字未动）；装配方以声明为授权
    提交时**必须点名授权来源**（本仓的判据按此按压）。
    """

    memory_gate: MemoryGateDeps
    tier: MemoryTier = MemoryTier.RUN
    kind: MemoryType = MemoryType.FACT
    confidence: float = 0.8
    content_builder: Callable[[Claim, tuple[Evidence, ...]], str] | None = None
    curator_approved: bool | None = None

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
        result = commit_memory(proposal, ctx.memory_gate, curator_approved=ctx.curator_approved)
        if result.accepted and result.record is not None:
            records.append(result.record)
    return tuple(records)


def promote_memory(
    deps: Any,
    registration: ResultRegistration,
    *,
    kind: MemoryType = MemoryType.FACT,
    memory_export: MemoryExportSpec | None = None,
) -> None:
    """任务收尾的**记忆晋升**入口（自 `task_phase_helpers` 迁入，GOAL-20261114-113 EC-03）。

    **授权面**：晋升只发生在**两个前提同时成立**时 —— 装配把 gate 接上（`deps.memory_gate`
    非 None）**且**本任务合约显式声明 `memory_export`。缺声明 ⇒ **不晋升**（不是拒绝：
    「没声明就没这条通道」）；有声明 ⇒ 档位 / 类型 / 置信度取自声明，并以
    `curator_approved=True` **代表合约**提交 —— 授权来源就是合约声明本身
    （`gate.py` 的 curator 判定逐字未动）。

    **类型归并**：编排层观察到的 `NEGATIVE_RESULT` 是 run 级事实，优先于声明的缺省
    `FACT`（否则一条「实验失败了」的记忆会被标成 FACT）。
    """
    if deps.memory_gate is None or memory_export is None:
        return
    promoted_kind = kind if kind is not MemoryType.FACT else memory_export.kind
    promote_memory_from_registration(
        MemoryPromotionContext(
            memory_gate=deps.memory_gate,
            tier=memory_export.tier,
            kind=promoted_kind,
            # 声明里的 confidence 是 Decimal（canonical 序列化拒绝 float）；
            # 门链提案面（MemoryWriteProposal）是 float —— 边界处显式换算。
            confidence=float(memory_export.confidence),
            curator_approved=True,
        ),
        registration,
    )


def _evidence_for_claim(ledger: object, claim: Claim) -> tuple[Evidence, ...]:
    from packages.application.ports.evidence_ledger import EvidenceLedger

    assert isinstance(ledger, EvidenceLedger)
    evidence: list[Evidence] = []
    for evidence_id, _relation in claim.evidence_relations:
        evidence.append(ledger.get_evidence(evidence_id))
    return tuple(evidence)
