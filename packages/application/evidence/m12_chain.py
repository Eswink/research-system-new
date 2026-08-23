"""M12 Research Evidence Chain：实验产物 → Source → Evidence → Claim → Memory。

组合 M10 既有生产 use case（不新建第二套证据模型）：
1. 实验输出 artifact（experiment_result.json）内容 digest 登记为 SourceRecord；
2. 依据 artifact 构造 Evidence（绑定 artifact_id / run_id / experiment_run_id /
   image_digest / workspace snapshots / metrics），写入 EvidenceLedger；
3. 构造 PROPOSED Claim + EvidenceRelation（SUPPORTS / REFUTES / CORROBORATES），
   经 promote_claim_to_verified（VerificationBasis 独立 gate verdict）升级；
4. 经 MemoryGateDeps 5 阶段 gate 将 NEGATIVE_RESULT / FACT 记忆入账（PROJECT
   tier 需 curator approval；sanitize before commit）。

ToolResult / 实验输出不直接成为可信 Evidence：source trust_label 为
GENERATED（非可信），Claim 升级必须满足 provenance + gate 前置
（verification.py 唯一升级入口）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from packages.application.evidence.contradiction import (
    register_evidence_with_contradiction_check,
)
from packages.application.evidence.verification import (
    VerificationBasis,
    promote_claim_to_verified,
)
from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.memory import MemoryWriteProposal
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class ExperimentEvidenceInput:
    """一次实验产物到证据链的输入；plan/run 标识用于 provenance 绑定。"""

    source_origin: str
    artifact_id: str
    run_id: str
    experiment_run_id: str
    image_digest: str | None = None
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    metrics: dict[str, object] = field(default_factory=dict)
    manifest_digest: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceChainOutcome:
    """一次链式登记的结果：source/evidence/claim 标识与最终状态。"""

    source_origin: str
    evidence_id: str
    claim_id: str
    claim_status: ClaimStatus
    memory_ids: tuple[str, ...] = ()


def register_experiment_evidence(
    ledger: EvidenceLedger,
    artifacts: ArtifactStore,
    *,
    input: ExperimentEvidenceInput,
    claim_statement: str,
    relation: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
) -> tuple[SourceRecord, Evidence, Claim]:
    """实验产物 → Source → Evidence → PROPOSED Claim 全链登记。

    - 读取 artifact 内容并校验内容寻址 digest（artifact 与声明一致）；
    - SourceRecord：origin=source_origin，content_digest=artifact digest，
      trust_label=GENERATED（实验产物是生成来源，非外部可信源）；
    - Evidence：绑定 artifact_id/run_id/experiment_run_id/image_digest/
      workspace snapshots/metrics（N003 类型化溯源缺口在 M12 链上闭合）；
    - Claim：PROPOSED + EvidenceRelation（SUPPORTS/REFUTES/CORROBORATES）。
    """
    content = artifacts.get(input.artifact_id)
    artifact_digest = Digest.of_bytes(content)
    payload = json.loads(content.decode("utf-8"))
    if not isinstance(payload, dict):
        raise InvalidInputError("experiment artifact must be a JSON object")
    if payload.get("experiment_run_id") != input.experiment_run_id:
        raise InvalidInputError(
            "experiment artifact experiment_run_id mismatch with evidence input"
        )
    source = SourceRecord(
        origin=input.source_origin,
        content_digest=str(artifact_digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="m12-evidence-v1",
    )
    ledger.register_source(source)
    evidence = Evidence(
        id=f"evidence:{input.run_id}:{input.experiment_run_id}",
        source_ref=source.origin,
        content_digest=str(artifact_digest),
        extracted_by="system:m12-evidence-chain",
        captured_at=Timestamp.now(),
        artifact_id=input.artifact_id,
        run_id=input.run_id,
        experiment_run_id=input.experiment_run_id,
        metric_refs=tuple(sorted(str(key) for key in input.metrics)),
        workspace_snapshot_before=input.workspace_snapshot_before,
        workspace_snapshot_after=input.workspace_snapshot_after,
        image_digest=input.image_digest,
        manifest_digest=input.manifest_digest,
    )
    ledger.register_evidence(evidence)
    claim = Claim(
        id=f"claim:{input.run_id}",
        statement=claim_statement,
        status=ClaimStatus.PROPOSED,
        author="system:m12-experiment",
        evidence_relations=[(evidence.id, relation)],
    )
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relation=relation,
            strength=0.95,
        )
    )
    return source, evidence, claim


def verify_claim(
    ledger: EvidenceLedger,
    claim: Claim,
    *,
    reviewer: str,
    verdict: str = "PASS",
) -> Claim:
    """经 VerificationBasis 独立 gate 升级 PROPOSED → VERIFIED（唯一升级入口）。

    Research Integrity（M12）：拒绝 agent 自证——reviewer 标识必须以独立
    gate/panel 命名空间（如 `gate:` / `panel:` / `human:`）出现；`agent:` /
    `writer:` / `system:orchestration` 不是独立验证主体，禁止升级。
    """
    if reviewer.startswith(("agent:", "writer:", "system:")):
        raise InvalidInputError(
            f"reviewer {reviewer!r} is not an independent verification body"
        )
    return promote_claim_to_verified(
        ledger,
        claim,
        basis=VerificationBasis(verdict=verdict, reviewer=reviewer),
    )


@dataclass(frozen=True, slots=True)
class ContradictionInput:
    """REFUTES 新证据登记输入（参数对象，避免函数参数超限）。"""

    source_origin: str
    evidence_id: str
    claim: Claim
    content_digest: str
    run_id: str
    experiment_run_id: str


def register_contradicting_evidence(
    ledger: EvidenceLedger,
    *,
    input: ContradictionInput,
    publisher: EventPublisher | None = None,
) -> Claim:
    """REFUTES 新证据：provenance 前置 + 命中活跃 Claim → DISPUTED（旧证据保留）。"""
    if not ledger.has_source(input.source_origin):
        ledger.register_source(
            SourceRecord(
                origin=input.source_origin,
                content_digest=input.content_digest,
                trust_label=TrustLabel.GENERATED,
                access_time=Timestamp.now(),
            )
        )
    evidence = Evidence(
        id=input.evidence_id,
        source_ref=input.source_origin,
        content_digest=input.content_digest,
        extracted_by="system:m12-contradiction",
        captured_at=Timestamp.now(),
        run_id=input.run_id,
        experiment_run_id=input.experiment_run_id,
    )
    outcome = register_evidence_with_contradiction_check(
        ledger,
        evidence,
        EvidenceRelation(
            claim_id=input.claim.id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.REFUTES,
            strength=0.9,
        ),
        publisher=publisher,
    )
    return outcome.claim


@dataclass(frozen=True, slots=True)
class MemoryProposalInput:
    """Governed Memory 提案输入（参数对象）。"""

    memory_id: str
    content: str
    provenance: str
    kind: MemoryType = MemoryType.FACT
    tier: MemoryTier = MemoryTier.PROJECT
    confidence: float = 0.95
    curator_approved: bool | None = None


def propose_and_commit_memory(
    deps: MemoryGateDeps,
    *,
    input: MemoryProposalInput,
) -> str | None:
    """经 5 阶段 gate 提交长期记忆；返回 memory_id 或 None（拒绝）。"""
    proposal = MemoryWriteProposal(
        id=input.memory_id,
        tier=input.tier,
        kind=input.kind,
        content=input.content,
        provenance=input.provenance,
        confidence=input.confidence,
        scope="project",
        proposed_by="system:m12-evidence-chain",
    )
    result = commit_memory(proposal, deps, curator_approved=input.curator_approved)
    if not result.accepted:
        return None
    assert result.record is not None
    return result.record.id


def summarize_evidence_chain(ledger: EvidenceLedger, run_id: str) -> dict[str, object]:
    """证据链只读摘要（供评测 scorer 与 deliverable 引用）。"""
    claim = ledger.get_claim(f"claim:{run_id}")
    relations = ledger.relations_for_claim(claim.id)
    evidence_ids = tuple(relation.evidence_id for relation in relations)
    return {
        "claim_id": claim.id,
        "claim_status": claim.status.value,
        "evidence_ids": evidence_ids,
        "relation_types": tuple(relation.relation.value for relation in relations),
        "claim_digest": str(digest_of({"claim": claim.statement})),
    }