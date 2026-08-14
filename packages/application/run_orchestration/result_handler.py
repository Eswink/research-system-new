"""AgentSessionResult → Artifact / Evidence / Claim 结果处理。

职责（单一）：把一次 Agent 会话的归一化结果转为可验证的领域产物：
- 大 payload 写 ArtifactStore（内容寻址），Domain 只保留引用；
- Evidence 引用 Artifact source；
- Claim 只能由 EvidenceRelation 支撑（VERIFIED 必须有合法证据，
  不因 Agent 自述"完成"而验证——AGENTS.md §8、DATA_LIFECYCLE.md）。

副作用边界：本模块是 application 层，经 ArtifactStore Port 落盘；
Evidence/Claim 为纯领域对象，由调用方（orchestration）提交。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)
from packages.domain.serialization import digest_of
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class ResultRegistration:
    """一次会话结果注册的产物引用集合。"""

    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    claims: tuple[Claim, ...] = field(default_factory=tuple)

    @property
    def evidence_source_count(self) -> int:
        return len(self.evidence)

    def artifact_refs(self) -> tuple[str, ...]:
        return tuple(artifact.id for artifact in self.artifacts)

    def evidence_refs(self) -> tuple[str, ...]:
        return tuple(evidence.id for evidence in self.evidence)

    def claim_refs(self) -> tuple[str, ...]:
        return tuple(claim.id for claim in self.claims)


def _artifact_for_output(
    task: ResearchTask,
    name: str,
    payload: Mapping[str, Any],
    agent_id: str | None,
) -> tuple[Artifact, bytes]:
    """结构化输出 → 内容寻址 Artifact（大 payload 不进入 Domain JSON）。"""
    content = json.dumps(
        dict(payload), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    artifact = Artifact(
        id=f"{task.id.value}:{name}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        storage_uri=None,
        created_by=agent_id or task.id.value,
        source_refs=[f"task:{task.id.value}"],
        classification="execution_result",
    )
    return artifact, content


def _evidence_from_artifact(
    task: ResearchTask,
    artifact: Artifact,
    claim_statement: str,
    claim_id: str,
    agent_id: str | None,
) -> tuple[Evidence, Claim, EvidenceRelation]:
    """Artifact → Evidence → Claim（VERIFIED 必须携带 EvidenceRelation）。"""
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=artifact.storage_uri or artifact.id,
        content_digest=str(artifact.digest),
        extracted_by=agent_id or task.id.value,
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
    )
    claim = Claim(
        id=claim_id,
        statement=claim_statement,
        status=ClaimStatus.PROPOSED,
        author=agent_id or task.id.value,
        evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
    )
    relation = EvidenceRelation(
        claim_id=claim.id,
        evidence_id=evidence.id,
        relation=EvidenceRelationType.SUPPORTS,
    )
    return evidence, claim, relation


def register_session_result(
    store: ArtifactStore,
    task: ResearchTask,
    contract: TaskContract,
    structured_output: Mapping[str, Any],
    *,
    agent_id: str | None,
) -> ResultRegistration:
    """把会话结构化输出注册为 Artifact + Evidence + PROPOSED Claim。

    调用方（evaluation_gate）负责将 PROPOSED 升级为 VERIFIED，升级前
    必须完成 AcceptanceCriteria 评估——本函数不自行认证成功。
    """
    if not structured_output:
        raise InvalidInputError(
            f"session result for task {task.id.value} carries no structured output"
        )
    artifacts: list[Artifact] = []
    evidences: list[Evidence] = []
    claims: list[Claim] = []
    claim_id = f"claim:{task.id.value}:result"
    for name, payload in structured_output.items():
        if not isinstance(payload, dict):
            continue
        artifact, content = _artifact_for_output(task, name, payload, agent_id)
        store.put(artifact, content)
        artifacts.append(artifact)
        evidence, claim, _relation = _evidence_from_artifact(
            task, artifact, f"Task {task.id.value} produced {name}", claim_id, agent_id
        )
        evidences.append(evidence)
        claims.append(claim)
    return ResultRegistration(
        artifacts=tuple(artifacts),
        evidence=tuple(evidences),
        claims=tuple(claims),
    )


def evidence_digest(evidence: Evidence) -> Digest:
    """Evidence 的确定性 digest（供 lineage 校验）。"""
    return digest_of(evidence)
