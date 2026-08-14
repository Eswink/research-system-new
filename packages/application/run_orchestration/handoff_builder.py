"""HandoffBundle 构建：多角色间结构化交接，不依赖聊天历史。"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.serialization import digest_of
from packages.domain.tasks import HandoffBundle, ResearchTask


@dataclass(frozen=True, slots=True)
class HandoffPayload:
    """一次交接的输入面（由 orchestration 层组装）。"""

    task: ResearchTask
    producer: str
    summary: str
    artifact_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    claim_refs: tuple[str, ...] = field(default_factory=tuple)
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    open_questions: tuple[str, ...] = field(default_factory=tuple)
    known_failures: tuple[str, ...] = field(default_factory=tuple)
    structured_output: dict[str, object] = field(default_factory=dict)


def build_handoff(payload: HandoffPayload) -> HandoffBundle:
    """构建结构化 HandoffBundle；digest 覆盖全部声明字段。"""
    content: dict[str, object] = {
        "task_id": payload.task.id.value,
        "producer": payload.producer,
        "summary": payload.summary,
        "artifact_refs": payload.artifact_refs,
        "evidence_refs": payload.evidence_refs,
        "claim_refs": payload.claim_refs,
        "decision_refs": payload.decision_refs,
    }
    return HandoffBundle(
        task_id=payload.task.id,
        producer=payload.producer,
        summary=payload.summary,
        digest=digest_of(content),
        producer_agent_id=payload.task.assigned_agent_id,
        producer_role_id=payload.task.contract_id,
        structured_output=dict(payload.structured_output),
        artifact_refs=list(payload.artifact_refs),
        claim_refs=list(payload.claim_refs),
        evidence_refs=list(payload.evidence_refs),
        decision_refs=list(payload.decision_refs),
        open_questions=list(payload.open_questions),
        known_failures=list(payload.known_failures),
        recommended_next_actions=[],
    )


def handoff_digest(bundle: HandoffBundle) -> str:
    """HandoffBundle 的确定性 digest 文本。"""
    return str(digest_of(bundle))
