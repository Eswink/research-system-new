"""冲突证据检测 use case：新 Evidence 与已有 Claim 冲突时转 DISPUTED。

规则（AGENTS.md §8、M10 Scope contradiction handling）：
- REFUTES 命中 VERIFIED/PROPOSED Claim → Claim 状态转 DISPUTED；
- 旧 Evidence / relation 全部保留（不覆盖、不删除，矛盾可回查）；
- 状态转换产生 CLAIM_DISPUTED 事件（审计信息）；
- 不修改 Evidence 本身，不反向影响 source。

本模块只组合 EvidenceLedger Port 与 Domain 类型；事件发布经
EventPublisher Port（可选注入，测试/只读场景可省略）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)


@dataclass(frozen=True, slots=True)
class ContradictionOutcome:
    """一次注册的结果：是否触发争议及 Claim 当前状态。"""

    disputed: bool
    claim: Claim
    evidence_id: str
    relation: EvidenceRelationType


def register_evidence_with_contradiction_check(
    ledger: EvidenceLedger,
    evidence: Evidence,
    relation: EvidenceRelation,
    publisher: EventPublisher | None = None,
    actor: str = "system:evidence",
) -> ContradictionOutcome:
    """登记 Evidence + relation；REFUTES 命中活跃 Claim 时转 DISPUTED。

    claim 必须已在 ledger 登记（relation 引用完整性由 attach_relation
    强制）；evidence 由本函数登记（同内容重复登记幂等）。
    旧 Evidence/relation 保留。

    provenance 前置：REFUTES 关系会改变 Claim 的 epistemic 状态，
    因此该 evidence 的 source 必须已在 ledger 登记；未登记来源的
    evidence 不得争议（dispute）任何 Claim。
    """
    ledger.register_evidence(evidence)
    if relation.relation is EvidenceRelationType.REFUTES and not ledger.has_source(
        evidence.source_ref
    ):
        raise InvalidInputError(
            f"evidence {evidence.id} source {evidence.source_ref!r} is not registered "
            "and cannot refute a claim"
        )
    ledger.attach_relation(relation)
    claim = ledger.get_claim(relation.claim_id)
    disputed = False
    if relation.relation is EvidenceRelationType.REFUTES and claim.status in (
        ClaimStatus.VERIFIED,
        ClaimStatus.PROPOSED,
    ):
        disputed_claim = replace(claim, status=ClaimStatus.DISPUTED)
        ledger.update_claim(disputed_claim)
        claim = disputed_claim
        disputed = True
        if publisher is not None:
            _publish_dispute(publisher, disputed_claim, evidence, relation, actor)
    return ContradictionOutcome(
        disputed=disputed,
        claim=claim,
        evidence_id=evidence.id,
        relation=relation.relation,
    )


def _publish_dispute(
    publisher: EventPublisher,
    claim: Claim,
    evidence: Evidence,
    relation: EvidenceRelation,
    actor: str,
) -> None:
    payload: dict[str, object] = {
        "claim_id": claim.id,
        "evidence_id": evidence.id,
        "relation": relation.relation.value,
    }
    publisher.publish(
        EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CLAIM_DISPUTED,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor=actor,
            scope=f"claim:{claim.id}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
        )
    )
