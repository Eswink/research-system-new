"""FakeEvidenceLedger：Evidence/Claim 事实源的 deterministic 内存实现。

按 id/origin 登记；同键重登内容不一致即失败（防静默漂移）；
未知 id 查询抛 InvalidInputError；attach_relation 强制引用完整性。
"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    SourceRecord,
)


class FakeEvidenceLedger(FakeBase):
    """内存登记表；commit 语义与真实 adapter 相同（contract suite 强制）。

    冲突判定只比较业务字段：access_time / captured_at 是观测元数据，
    幂等重登（时间漂移）不误报冲突（M12-R1 WP2 真实链修复）。
    """

    def __init__(self) -> None:
        super().__init__("evidence_ledger")
        self._sources: dict[str, SourceRecord] = {}
        self._evidence: dict[str, Evidence] = {}
        self._claims: dict[str, Claim] = {}
        self._relations: dict[str, list[EvidenceRelation]] = {}

    def register_source(self, source: SourceRecord) -> None:
        self._enter("register_source", source.origin)
        existing = self._sources.get(source.origin)
        if existing is not None and not self._same_source(existing, source):
            self._record("register_source", source.origin, error="InvalidInputError")
            raise InvalidInputError(f"conflicting source registration: {source.origin}")
        self._sources[source.origin] = source
        self._record("register_source", source.origin, result="registered")

    def register_evidence(self, evidence: Evidence) -> None:
        self._enter("register_evidence", evidence.id)
        existing = self._evidence.get(evidence.id)
        if existing is not None and not self._same_evidence(existing, evidence):
            self._record("register_evidence", evidence.id, error="InvalidInputError")
            raise InvalidInputError(f"conflicting evidence registration: {evidence.id}")
        self._evidence[evidence.id] = evidence
        self._record("register_evidence", evidence.id, result="registered")

    def register_claim(self, claim: Claim) -> None:
        self._enter("register_claim", claim.id)
        self._require_verifiable(claim)
        existing = self._claims.get(claim.id)
        if existing is not None and existing != claim:
            self._record("register_claim", claim.id, error="InvalidInputError")
            raise InvalidInputError(f"conflicting claim registration: {claim.id}")
        self._claims[claim.id] = claim
        self._record("register_claim", claim.id, result="registered")

    def update_claim(self, claim: Claim) -> None:
        """替换已登记 Claim（状态迁移）；未知 id 即失败。"""
        self._enter("update_claim", claim.id)
        self._require_verifiable(claim)
        if claim.id not in self._claims:
            self._record("update_claim", claim.id, error="InvalidInputError")
            raise InvalidInputError(f"unknown claim id: {claim.id}")
        self._claims[claim.id] = claim
        self._record("update_claim", claim.id, result="updated")

    def _require_verifiable(self, claim: Claim) -> None:
        """VERIFIED Claim 的 provenance 不变量（canonical 登记面强制）。

        VERIFIED 状态的 Claim 每条 evidence relation 必须：
        - evidence 已在 ledger 登记；
        - evidence 的 source 已在 ledger 登记。
        否则拒绝登记/更新——防止绕过 promote_claim_to_verified 的
        直写路径把无 provenance 的 Claim 升级为 VERIFIED。
        """
        if claim.status is not ClaimStatus.VERIFIED:
            return
        for evidence_id, _relation in claim.evidence_relations:
            evidence = self._evidence.get(evidence_id)
            if evidence is None:
                self._record("update_claim", claim.id, error="InvalidInputError")
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} references unknown evidence {evidence_id!r}"
                )
            if evidence.source_ref not in self._sources:
                self._record("update_claim", claim.id, error="InvalidInputError")
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} evidence {evidence_id!r} "
                    f"source {evidence.source_ref!r} is not registered"
                )

    def attach_relation(self, relation: EvidenceRelation) -> None:
        self._enter("attach_relation", f"{relation.claim_id}->{relation.evidence_id}")
        if relation.claim_id not in self._claims:
            self._record("attach_relation", relation.claim_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown claim id: {relation.claim_id}")
        if relation.evidence_id not in self._evidence:
            self._record("attach_relation", relation.evidence_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown evidence id: {relation.evidence_id}")
        relations = self._relations.setdefault(relation.claim_id, [])
        if relation not in relations:
            relations.append(relation)
        self._record("attach_relation", relation.claim_id, result="attached")

    def get_source(self, origin: str) -> SourceRecord:
        self._enter("get_source", origin)
        if origin not in self._sources:
            self._record("get_source", origin, error="InvalidInputError")
            raise InvalidInputError(f"unknown source origin: {origin}")
        self._record("get_source", origin, result="found")
        return self._sources[origin]

    def get_evidence(self, evidence_id: str) -> Evidence:
        self._enter("get_evidence", evidence_id)
        if evidence_id not in self._evidence:
            self._record("get_evidence", evidence_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown evidence id: {evidence_id}")
        self._record("get_evidence", evidence_id, result="found")
        return self._evidence[evidence_id]

    def get_claim(self, claim_id: str) -> Claim:
        self._enter("get_claim", claim_id)
        if claim_id not in self._claims:
            self._record("get_claim", claim_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown claim id: {claim_id}")
        self._record("get_claim", claim_id, result="found")
        return self._claims[claim_id]

    def relations_for_claim(self, claim_id: str) -> tuple[EvidenceRelation, ...]:
        self._enter("relations_for_claim", claim_id)
        if claim_id not in self._claims:
            self._record("relations_for_claim", claim_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown claim id: {claim_id}")
        relations = tuple(self._relations.get(claim_id, ()))
        self._record("relations_for_claim", claim_id, result=str(len(relations)))
        return relations

    def has_source(self, origin: str) -> bool:
        self._enter("has_source", origin)
        found = origin in self._sources
        self._record("has_source", origin, result=str(found))
        return found

    @staticmethod
    def _same_source(existing: SourceRecord, source: SourceRecord) -> bool:
        """业务字段一致判定；access_time 是观测元数据，不参与冲突比较。"""
        return (
            existing.content_digest == source.content_digest
            and existing.trust_label == source.trust_label
            and existing.license_terms == source.license_terms
            and existing.authors == source.authors
            and existing.parser_version == source.parser_version
        )

    @staticmethod
    def _same_evidence(existing: Evidence, evidence: Evidence) -> bool:
        """业务字段一致判定；captured_at 是观测元数据，不参与冲突比较。"""
        return (
            existing.source_ref == evidence.source_ref
            and existing.content_digest == evidence.content_digest
            and existing.extracted_by == evidence.extracted_by
            and existing.artifact_id == evidence.artifact_id
            and existing.run_id == evidence.run_id
            and existing.experiment_run_id == evidence.experiment_run_id
            and existing.metric_refs == evidence.metric_refs
            and existing.workspace_snapshot_before == evidence.workspace_snapshot_before
            and existing.workspace_snapshot_after == evidence.workspace_snapshot_after
            and existing.image_digest == evidence.image_digest
            and existing.environment_digest == evidence.environment_digest
            and existing.tool_refs == evidence.tool_refs
            and existing.skill_refs == evidence.skill_refs
            and existing.model_refs == evidence.model_refs
            and existing.manifest_digest == evidence.manifest_digest
        )

    def claims(self) -> tuple[Claim, ...]:
        self._enter("claims", "*")
        result = tuple(self._claims.values())
        self._record("claims", "*", result=str(len(result)))
        return result
