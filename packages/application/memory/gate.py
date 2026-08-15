"""MemoryWriteProposal gate pipeline（M10 Key Deliverable）。

阶段链（CONTEXT_ENGINE.md §6、AGENTS.md §8）：
schema → provenance → contradiction → policy → curator/automatic gate
→ commit

- schema：content 非空白（domain 不变量兜底之外的业务校验）；
- provenance：来源必须在 allowed_sources 或 EvidenceLedger 已登记，
  无合法 provenance 默认拒绝；
- contradiction：supersedes 引用完整性（引用未知 id 拒绝）；
- policy：复用 PolicyEvaluator Port（capability="memory.write"），
  不重建第二套 permission model（ADR-0018 / AGENTS.md §8）；
- curator：SESSION/RUN 自动；PROJECT/ORGANIZATION 需显式 curator
  approval；REQUIRE_APPROVAL 决策强制 curator 输入；
- sanitize：commit 前用 domain.redaction 脱敏 secret 样式内容
  （sanitize before commit，非 commit 后清理）；
- commit：评估通过后 MEMORY_PROPOSED → MemoryStore.commit →
  MEMORY_COMMITTED。

Agent / Writer / Reviewer / Runtime / ToolResult / chat summary 不得
绕过本 pipeline 直接调用 MemoryStore 将内容升级为长期 Memory
（FakeMemoryStore 内嵌 provenance 白名单为防御纵深）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.memory_store import MemoryStore
from packages.application.ports.policy_evaluator import PolicyEvaluator, PolicyRequest
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, PolicyDecision
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from packages.domain.redaction import redact_text

_CURATOR_TIERS = (MemoryTier.PROJECT, MemoryTier.ORGANIZATION)


@dataclass(frozen=True, slots=True)
class GateResult:
    """一次提案评估/提交的可分类结果。"""

    accepted: bool
    stage: str
    decision: PolicyDecision
    reasons: tuple[str, ...] = ()
    record: MemoryRecord | None = None


@dataclass(frozen=True, slots=True)
class MemoryGateDeps:
    """gate pipeline 的 Port 组合（由 composition root 注入）。"""

    store: MemoryStore
    policy: PolicyEvaluator | None = None
    ledger: EvidenceLedger | None = None
    publisher: EventPublisher | None = None
    allowed_sources: frozenset[str] = frozenset()
    actor: str = "system:memory"


def _schema_check(proposal: MemoryWriteProposal, deps: MemoryGateDeps) -> str | None:
    if not proposal.content.strip():
        return "memory content must not be blank"
    return None


def _provenance_check(proposal: MemoryWriteProposal, deps: MemoryGateDeps) -> str | None:
    if proposal.provenance in deps.allowed_sources:
        return None
    if deps.ledger is not None and deps.ledger.has_source(proposal.provenance):
        return None
    return f"provenance {proposal.provenance!r} is not registered"


def _contradiction_check(proposal: MemoryWriteProposal, deps: MemoryGateDeps) -> str | None:
    for old_id in proposal.supersedes:
        try:
            deps.store.get(old_id)
        except InvalidInputError:
            return f"supersedes target {old_id!r} does not exist"
    return None


def evaluate_memory_proposal(
    proposal: MemoryWriteProposal,
    deps: MemoryGateDeps,
    *,
    curator_approved: bool | None = None,
) -> GateResult:
    """按阶段链评估提案；返回可分类 GateResult（不产生写入）。"""
    for check in (_schema_check, _provenance_check, _contradiction_check):
        reason = check(proposal, deps)
        if reason is not None:
            stage = {
                _schema_check: "schema",
                _provenance_check: "provenance",
                _contradiction_check: "contradiction",
            }[check]
            return GateResult(
                accepted=False, stage=stage, decision=PolicyDecision.DENY, reasons=(reason,)
            )
    decision = _evaluate_policy(proposal, deps)
    if decision is PolicyDecision.DENY:
        return GateResult(
            accepted=False, stage="policy", decision=decision, reasons=("policy deny",)
        )
    if decision is PolicyDecision.REQUIRE_APPROVAL and curator_approved is not True:
        return GateResult(
            accepted=False,
            stage="policy",
            decision=decision,
            reasons=("policy requires approval",),
        )
    if proposal.tier in _CURATOR_TIERS and curator_approved is not True:
        return GateResult(
            accepted=False,
            stage="curator",
            decision=decision,
            reasons=(f"tier {proposal.tier.value} requires curator approval",),
        )
    return GateResult(accepted=True, stage="evaluated", decision=decision)


def _evaluate_policy(proposal: MemoryWriteProposal, deps: MemoryGateDeps) -> PolicyDecision:
    if deps.policy is None:
        return PolicyDecision.ALLOW
    evaluation = deps.policy.evaluate(
        PolicyRequest(
            actor=proposal.proposed_by or deps.actor,
            capability="memory.write",
            action="commit",
            scope=proposal.tier.value,
        )
    )
    return evaluation.decision


def commit_memory(
    proposal: MemoryWriteProposal,
    deps: MemoryGateDeps,
    *,
    curator_approved: bool | None = None,
) -> GateResult:
    """评估通过后提交：脱敏 → 评估 → MEMORY_PROPOSED → commit → 一致性校验 → MEMORY_COMMITTED。

    secret 样式内容（Bearer/API key/URL 凭据）在 commit 前脱敏，
    绝不先入账后清理；完整 data governance 属 M19，本处只复用
    domain.redaction 原语，不是第二套 permission/secret 框架。
    """
    proposal = _sanitize_proposal(proposal)
    result = evaluate_memory_proposal(proposal, deps, curator_approved=curator_approved)
    if not result.accepted:
        return result
    _publish(deps, EventType.MEMORY_PROPOSED, proposal.id, {"memory_id": proposal.id})
    record = deps.store.commit(proposal)
    _verify_committed_record(proposal, record)
    _publish(deps, EventType.MEMORY_COMMITTED, proposal.id, {"memory_id": proposal.id})
    return GateResult(
        accepted=True,
        stage="committed",
        decision=result.decision,
        record=record,
    )


def _sanitize_proposal(proposal: MemoryWriteProposal) -> MemoryWriteProposal:
    """commit 前脱敏（sanitize before commit）：secret 不进 canonical Memory。"""
    sanitized = redact_text(proposal.content)
    if sanitized == proposal.content:
        return proposal
    return replace(proposal, content=sanitized)


def _verify_committed_record(
    proposal: MemoryWriteProposal,
    record: MemoryRecord,
) -> None:
    """adapter 返回记录必须与提案一致；不一致是 Port 实现缺陷，绝不静默入账。"""
    if (
        record.id != proposal.id
        or record.content != proposal.content
        or record.provenance != proposal.provenance
    ):
        raise InvalidInputError(
            f"memory store returned record inconsistent with proposal {proposal.id}"
        )


def _publish(
    deps: MemoryGateDeps,
    event_type: EventType,
    memory_id: str,
    payload: dict[str, object],
) -> None:
    if deps.publisher is None:
        return
    deps.publisher.publish(
        EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor=deps.actor,
            scope=f"memory:{memory_id}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
        )
    )
