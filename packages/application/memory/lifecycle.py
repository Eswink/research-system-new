"""Memory 生命周期 use case：supersede / deactivate（tombstone）/ delete。

区分（M10 Scope memory lifecycle/delete）：
- deactivate：canonical tombstone（active=False 保留记录，审计可回查）；
- delete：物理移除 canonical 记录 + derived index 同步移除 + 审计事件；
- supersede：新记录 commit（supersedes=[old]）后旧记录 deactivate。

事件：delete 发布 MEMORY_DELETED（含 memory id 与删除者，审计信息）。
索引协调：delete/deactivate 同步 index.remove，禁止 ghost retrieval。

supersede 门禁：必须走与 commit_memory 相同的正式 gate 阶段链
（schema → provenance → contradiction → policy → curator），不得以
"生命周期操作"名义绕过 MemoryWriteProposal gate；无直写回退路径。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace

from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.memory_store import MemoryStore
from packages.application.ports.retrieval_index import RetrievalIndex
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.memory import MemoryRecord, MemoryWriteProposal


@dataclass(frozen=True, slots=True)
class MemoryLifecycleDeps:
    """lifecycle use case 的 Port 组合（由 composition root 注入）。"""

    store: MemoryStore
    index: RetrievalIndex | None = None
    publisher: EventPublisher | None = None
    actor: str = "system:memory"


def deactivate_memory(deps: MemoryLifecycleDeps, memory_id: str) -> MemoryRecord:
    """canonical tombstone：active=False；索引同步移除。"""
    record = deps.store.deactivate(memory_id)
    if deps.index is not None:
        deps.index.remove(memory_id)
    return record


def delete_memory(deps: MemoryLifecycleDeps, memory_id: str) -> None:
    """物理删除 canonical 记录；索引移除；发布 MEMORY_DELETED 审计事件。"""
    deps.store.delete(memory_id)
    if deps.index is not None:
        deps.index.remove(memory_id)
    if deps.publisher is not None:
        payload: dict[str, object] = {"memory_id": memory_id}
        deps.publisher.publish(
            EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MEMORY_DELETED,
                schema_version="1",
                occurred_at=Timestamp.now(),
                actor=deps.actor,
                scope=f"memory:{memory_id}",
                payload=payload,
                payload_digest=digest_of_payload(payload),
            )
        )


def supersede_memory(
    deps: MemoryLifecycleDeps,
    old_id: str,
    proposal: MemoryWriteProposal,
    *,
    gate_deps: MemoryGateDeps,
    curator_approved: bool | None = None,
) -> MemoryRecord:
    """新记录 commit 并记录 supersedes=[old_id]；旧记录 deactivate。

    - 目标必须存在且 active（inactive 记录不可被 supersede）；
    - 必须经正式 MemoryWriteProposal gate 提交（拒绝 = InvalidInputError
      携带阶段原因，绝不绕过 pipeline）；
    - 提交成功（含 MEMORY_PROPOSED/COMMITTED 事件）后旧记录 deactivate。
    """
    existing = deps.store.get(old_id)
    if not existing.active:
        raise InvalidInputError(f"cannot supersede inactive memory {old_id}")
    replaced = replace(proposal, supersedes=[old_id])
    result = commit_memory(replaced, gate_deps, curator_approved=curator_approved)
    if not result.accepted:
        raise InvalidInputError(
            f"supersede proposal rejected at {result.stage}: "
            f"{result.reasons[0] if result.reasons else 'unknown reason'}"
        )
    assert result.record is not None
    deactivate_memory(deps, old_id)
    return result.record
