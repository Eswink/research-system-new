"""AgentSessionResult → Artifact / Evidence / Claim 结果处理。

职责（单一）：把一次 Agent 会话的归一化结果转为可验证的领域产物：
- 大 payload 写 ArtifactStore（内容寻址），Domain 只保留引用；
- Evidence 引用 Artifact source；
- Claim 只能由 EvidenceRelation 支撑（VERIFIED 必须有合法证据，
  不因 Agent 自述"完成"而验证——AGENTS.md §8、DATA_LIFECYCLE.md）。

副作用边界：本模块是 application 层，经 ArtifactStore Port 落盘；
Evidence/Claim 为纯领域对象，由调用方（orchestration）提交。

GOAL-010 EC-02（证据链真实性）——**来源分两类，计数只认第二类**：
- **自身来源**：会话结构化输出 → `{task_id}:{name}` artifact → Evidence。它的
  `origin` 就是交付物自己，所以它是**模型自述**，`EVIDENCE_COVERAGE` **不**认它；
- **非自身来源**：本 phase **声明的输入制品**（`declared_inputs`）。对象由组合根
  种入 ArtifactStore、内容寻址、digest **可独立重算**，且与模型叙述**可分离核验**
  ⇒ 只有它计入覆盖。
判别是**集合判定**（`artifact_id` 是否在本任务自产 artifact 的集合里），**不是**
id 前缀启发式——前缀会随生产者变化而失效。缺省（未声明输入）时计数为 0，覆盖
判据**如实判拒**：这正是本 EC 要的语义，不得用「计数 ≥ 1」把它糊过去。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.serialization import digest_of
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class ResultRegistration:
    """一次会话结果注册的产物引用集合。

    `self_artifact_ids` 是**本任务自产**的 artifact id 集合；`evidence_source_count`
    只数**不在**该集合里的 evidence（GOAL-010 EC-02 的判别性质）。
    """

    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    claims: tuple[Claim, ...] = field(default_factory=tuple)
    self_artifact_ids: frozenset[str] = frozenset()

    @property
    def evidence_source_count(self) -> int:
        """计入覆盖的来源数 = **非自身**来源数（模型自述不算）。

        缺省 `self_artifact_ids` 为空集时，全部 evidence 都算——但生产路径**总是**
        传入真实的自产 id 集（`register_session_result` 填），所以「漏传 ⇒ 判过」
        这条退路在生产上不通；测试若直接构造本对象，需自行声明自产集合。
        """
        return sum(1 for item in self.evidence if item.artifact_id not in self.self_artifact_ids)

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
    """Artifact → Evidence → Claim（VERIFIED 必须携带 EvidenceRelation）。

    Evidence 携带 task.run_id（溯源类型化，SA-1 N003 清偿）：Inspection
    的 run 级 evidence 视图依赖该字段做 run 隔离。
    """
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=artifact.storage_uri or artifact.id,
        content_digest=str(artifact.digest),
        extracted_by=agent_id or task.id.value,
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
        run_id=str(task.run_id.value),
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


@dataclass(frozen=True, slots=True)
class _LedgerBatch:
    """一次会话结果要写进 ledger 的全量引用（参数对象，避免参数爆发）。"""

    artifacts: list[Artifact]
    evidences: list[Evidence]
    claims: list[Claim]
    claim_id: str
    #: **声明输入**的 evidence id（非模型自述那一类），一并进 claim relations。
    extra_evidence_ids: tuple[str, ...] = ()


def _register_into_ledger(ledger: EvidenceLedger, batch: _LedgerBatch) -> None:
    """登记 SourceRecord（GENERATED，显式非可信）+ Evidence + 合并 Claim。

    同 task 的多条 evidence 合并注册为单一 Claim（relations 全量），
    避免同 id 冲突登记；每条 evidence 的 source 单独登记。
    """
    for artifact, evidence in zip(batch.artifacts, batch.evidences):
        ledger.register_source(
            SourceRecord(
                origin=evidence.source_ref,
                content_digest=str(artifact.digest),
                trust_label=TrustLabel.GENERATED,
                access_time=Timestamp.now(),
            )
        )
        ledger.register_evidence(evidence)
    # 声明输入的 evidence 一并进 claim 的 relations（GOAL-010 EC-02）：`GET
    # /runs/{id}/evidence` 的投影只经 claim relations 走，不挂上就读不到来源。
    # 合并进**同一** Claim 也让「claim.evidence_relations == 已挂 relations」这条
    # 不变量继续成立（否则读面与 claim 记录会各说一套）。
    all_ids = [evidence.id for evidence in batch.evidences] + list(batch.extra_evidence_ids)
    merged = Claim(
        id=batch.claim_id,
        statement=batch.claims[0].statement,
        status=ClaimStatus.PROPOSED,
        author=batch.claims[0].author,
        evidence_relations=[
            (evidence_id, EvidenceRelationType.SUPPORTS) for evidence_id in all_ids
        ],
    )
    ledger.register_claim(merged)
    for evidence_id in all_ids:
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=merged.id,
                evidence_id=evidence_id,
                relation=EvidenceRelationType.SUPPORTS,
            )
        )


@dataclass(frozen=True, slots=True)
class RegistrationDeps:
    """register_session_result 的 Port 组合（参数对象）。"""

    store: ArtifactStore
    agent_id: str | None
    ledger: EvidenceLedger | None = None
    # GOAL-010 EC-02：本 phase 声明的输入制品 id（`ProtocolPhase.inputs`）。
    # 空 = 未声明 ⇒ 不产生非自身来源 ⇒ 覆盖判据如实判拒。
    declared_inputs: tuple[str, ...] = ()


def _input_evidence(
    deps: RegistrationDeps,
    task: ResearchTask,
    artifact_id: str,
    claim_id: str,
) -> tuple[SourceRecord, Evidence]:
    """**声明输入制品** → SourceRecord + Evidence（GOAL-010 EC-02 的非自身来源）。

    与 `_evidence_from_artifact` 的**根本区别**：这里的对象**不是**会话产出，而是
    组合根种进 ArtifactStore 的输入。校验沿用工具证据那条既有的严格口径：
    对象必须在库里、内容必须能**重算出** `meta.digest`（内容寻址，防篡改）。
    取不到 ⇒ 抛错（fail closed）：声明了输入却没有对象，**不得**静默降级成
    「没有来源但照样通过」——那正是本 EC 要消灭的旧行为。
    """
    meta = deps.store.meta(artifact_id)
    if meta is None:
        raise InvalidInputError(
            f"declared input artifact {artifact_id} is not in the artifact store"
        )
    if not deps.store.verify(artifact_id):
        raise InvalidInputError(
            f"declared input artifact {artifact_id} failed content verification"
        )
    source = SourceRecord(
        origin=artifact_id,
        content_digest=str(meta.digest),
        trust_label=TrustLabel.USER_PROVIDED,
        access_time=Timestamp.now(),
        parser_version="ec02-declared-input-v1",
    )
    evidence = Evidence(
        id=f"evidence:input:{artifact_id}:{task.id.value}",
        source_ref=artifact_id,
        content_digest=str(meta.digest),
        extracted_by="system:run-input",
        captured_at=Timestamp.now(),
        artifact_id=artifact_id,
        run_id=str(task.run_id.value),
    )
    return source, evidence


def _produced_outputs(
    deps: RegistrationDeps,
    task: ResearchTask,
    structured_output: Mapping[str, Any],
    claim_id: str,
) -> tuple[list[Artifact], list[Evidence], list[Claim]]:
    """结构化输出 → 落盘 + 自述 Evidence（模型自述那一类）。"""
    artifacts: list[Artifact] = []
    evidences: list[Evidence] = []
    claims: list[Claim] = []
    for name, payload in structured_output.items():
        if not isinstance(payload, dict):
            continue
        artifact, content = _artifact_for_output(task, name, payload, deps.agent_id)
        deps.store.put(artifact, content)
        deps.store.mark(artifact.id, ArtifactState.VERIFIED)
        artifacts.append(artifact)
        evidence, claim, _relation = _evidence_from_artifact(
            task, artifact, f"Task {task.id.value} produced {name}", claim_id, deps.agent_id
        )
        evidences.append(evidence)
        claims.append(claim)
    return artifacts, evidences, claims


def register_declared_input_sources(
    deps: RegistrationDeps,
    task: ResearchTask,
    *,
    claim_id: str,
) -> tuple[Evidence, ...]:
    """把**本 phase 声明的输入制品**登记为 SourceRecord + Evidence。

    会话结果路径与 experiment 结果路径共用这一处：两条路径的「非自身来源」是同一个
    定义（对象不是该任务自己产出的 artifact），不该各写一遍。返回登记出的 evidence
    （调用方把它并进 registration，计数只认这一类）。

    **与 claim 的关系**（GOAL-010 EC-02 实测补）：`GET /runs/{id}/evidence` 的投影
    （`services/api/run_evidence.evidence_of_run`）是**经过 claim relations** 走的，
    所以只登记 evidence 而不挂 relation 的来源**读不到**——判据要求「来源记录可读」，
    那就得真的挂上（会话路径在 `_register_into_ledger` 里合并挂；experiment 路径
    由 `registration_from_experiment` 挂）。`SUPPORTS` 在这里的确切含义是
    **该任务的交付物以其声明输入为据**（grounding），不是「输入证明了交付物的结论」。
    """
    pairs = [
        _input_evidence(deps, task, artifact_id, claim_id) for artifact_id in deps.declared_inputs
    ]
    if deps.ledger is not None:
        for source, evidence in pairs:
            deps.ledger.register_source(source)
            deps.ledger.register_evidence(evidence)
    return tuple(evidence for _source, evidence in pairs)


def register_session_result(
    deps: RegistrationDeps,
    task: ResearchTask,
    contract: TaskContract,
    structured_output: Mapping[str, Any],
) -> ResultRegistration:
    """把会话结构化输出注册为 Artifact + Evidence + PROPOSED Claim。

    调用方（evaluation_gate）负责将 PROPOSED 升级为 VERIFIED，升级前
    必须完成 AcceptanceCriteria 评估——本函数不自行认证成功。
    deps.ledger 提供时同步登记 SourceRecord/Evidence/Claim/Relation。

    **声明输入**（`deps.declared_inputs`）与结构化输出无关地**总是**登记：它是
    本任务的 grounding 对象，无论模型说了什么都在场；正因为它独立于模型产出，
    才能被当作「非模型自述」的来源（GOAL-010 EC-02）。
    """
    if not structured_output:
        raise InvalidInputError(
            f"session result for task {task.id.value} carries no structured output"
        )
    claim_id = f"claim:{task.id.value}:result"
    artifacts, evidences, claims = _produced_outputs(deps, task, structured_output, claim_id)
    inputs = register_declared_input_sources(deps, task, claim_id=claim_id)
    if deps.ledger is not None and claims:
        _register_into_ledger(
            deps.ledger,
            _LedgerBatch(
                artifacts=artifacts,
                evidences=evidences,
                claims=claims,
                claim_id=claim_id,
                extra_evidence_ids=tuple(evidence.id for evidence in inputs),
            ),
        )
    return ResultRegistration(
        artifacts=tuple(artifacts),
        evidence=tuple(evidences) + inputs,
        claims=tuple(claims),
        self_artifact_ids=frozenset(artifact.id for artifact in artifacts),
    )


def evidence_digest(evidence: Evidence) -> Digest:
    """Evidence 的确定性 digest（供 lineage 校验）。"""
    return digest_of(evidence)
