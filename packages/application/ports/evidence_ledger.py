"""EvidenceLedger Port：SourceRecord / Evidence / Claim 的 canonical 事实源。

依据 ADR-0003（Evidence-native）与 AGENTS.md §8：VERIFIED Claim 必须由
合法 Evidence relation 支撑；MemoryStore 不拥有 Claim/Evidence truth。

职责：登记与查询 SourceRecord（按 origin）、Evidence（按 id）、
Claim（按 id）与 EvidenceRelation；供 claim 升级、contradiction 检测与
memory provenance check 使用。

非职责：不做 Claim 状态转换决策（application evidence use case 负责）；
不做 derived retrieval index（RetrievalIndex Port 负责）。

M5 决策 D2：同步语义；未知 id 查询抛出 InvalidInputError。
M10 复审强化（实现必须一致遵守，contract suite 强制）：register_claim
与 update_claim 必须拒绝 VERIFIED 状态且任一 evidence relation 的
evidence 未登记或 source 未登记的 Claim——VERIFIED 的 provenance
不变量在 canonical 登记面强制，防止绕过 promote_claim_to_verified 的
直写路径。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.evidence import (
    Claim,
    Evidence,
    EvidenceRelation,
    SourceRecord,
)


@runtime_checkable
class EvidenceLedger(Protocol):
    """Evidence/Claim 登记与查询契约。"""

    def register_source(self, source: SourceRecord) -> None: ...

    def register_evidence(self, evidence: Evidence) -> None: ...

    def register_claim(self, claim: Claim) -> None: ...

    def update_claim(self, claim: Claim) -> None: ...

    def attach_relation(self, relation: EvidenceRelation) -> None: ...

    def get_source(self, origin: str) -> SourceRecord: ...

    def get_evidence(self, evidence_id: str) -> Evidence: ...

    def get_claim(self, claim_id: str) -> Claim: ...

    def relations_for_claim(self, claim_id: str) -> tuple[EvidenceRelation, ...]: ...

    def has_source(self, origin: str) -> bool: ...

    def claims(self) -> tuple[Claim, ...]: ...

    def close(self) -> None: ...
