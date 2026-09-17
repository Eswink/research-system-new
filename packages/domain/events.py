"""Domain Event 类型（docs/architecture/EVENT_MODEL.md）。

Domain Event 是产品审计信号，不等于 telemetry/runtime event
（docs/architecture/OBSERVABILITY.md）；AgentRuntime.stream_events 的
runtime event 不替代 Domain Event。

EventEnvelope 的 payload_digest 在构造时校验，保证 envelope 内容不可伪造。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from packages.domain.core import Digest, Timestamp
from packages.domain.serialization import canonical_json_bytes, digest_of


class EventType(StrEnum):
    PROTOCOL_COMPILED = "protocol.compiled"
    PREFLIGHT_COMPLETED = "preflight.completed"
    MANIFEST_FROZEN = "manifest.frozen"
    TEAM_RESOLVED = "team.resolved"
    ROLE_ACTIVATED = "role.activated"
    MODEL_PROBED = "model.probed"
    MODEL_RESOLVED = "model.resolved"
    MODEL_DRIFT_DETECTED = "model.drift_detected"
    BUDGET_RESERVED = "budget.reserved"
    TASK_CREATED = "task.created"
    TASK_LEASED = "task.leased"
    TASK_HEARTBEAT = "task.heartbeat"
    TASK_RETRY_SCHEDULED = "task.retry_scheduled"
    TASK_COMPLETED = "task.completed"
    # GOAL-004 cycle 3：任务终局失败且契约声明容忍（`on_task_failure: CONTINUE`）
    # ⇒ 记一条 task.failed（payload 带 failure_policy），run 继续跑剩余工作。
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    HANDOFF_CREATED = "handoff.created"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"
    MEMORY_PROPOSED = "memory.proposed"
    MEMORY_COMMITTED = "memory.committed"
    TOOL_PACK_INSTALLED = "tool_pack.installed"
    TOOL_PACK_UPDATED = "tool_pack.updated"
    TOOL_PACK_REVOKED = "tool_pack.revoked"
    TOOL_CALL_STARTED = "tool_call.started"
    TOOL_CALL_COMPLETED = "tool_call.completed"
    WORKSPACE_SNAPSHOT_CREATED = "workspace.snapshot.created"
    ARTIFACT_VERIFIED = "artifact.verified"
    CLAIM_VERIFIED = "claim.verified"
    CLAIM_DISPUTED = "claim.disputed"
    MEMORY_DELETED = "memory.deleted"
    RUN_FORKED = "run.forked"
    RUN_COMPLETED = "run.completed"
    RUN_CANCELLED = "run.cancelled"
    RUN_FAILED = "run.failed"
    # GOAL-004 cycle 3：契约声明 `on_task_failure: CONTINUE` 的 run 跑完全部剩余工作、
    # 但有任务终局失败 ⇒ 收敛 DEGRADED（非终态）并如实点名哪几条失败 + 哪条策略允许的。
    RUN_DEGRADED = "run.degraded"
    # GOAL-004 cycle 7：一次续跑尝试失败并被补偿回停车（canonical 放回 PAUSED）。
    # 事件链是这次失败原因的 canonical 记录——读面不新增"停车原因"字段。
    RUN_RESUME_FAILED = "run.resume_failed"


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """EVENT_MODEL.md §2 Envelope；payload 与 payload_digest 必须一致。"""

    event_id: str
    event_type: EventType
    schema_version: str
    occurred_at: Timestamp
    actor: str
    scope: str
    payload: Mapping[str, object]
    payload_digest: Digest
    project_id: str | None = None
    run_id: str | None = None
    phase_run_id: str | None = None
    task_id: str | None = None
    agent_session_id: str | None = None
    trace_id: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")
        if not self.schema_version:
            raise ValueError("schema_version must not be empty")
        if not self.actor:
            raise ValueError("actor must not be empty")
        if not self.scope:
            raise ValueError("scope must not be empty")
        actual = digest_of(self.payload)
        if actual != self.payload_digest:
            raise ValueError("payload_digest does not match payload content")


def digest_of_payload(payload: Mapping[str, object]) -> Digest:
    """计算 payload 的确定性 digest（构造 EventEnvelope 前使用）。"""
    return digest_of(payload)


def event_payload_digest_roundtrip(payload: Mapping[str, object]) -> bytes:
    """payload 的 canonical JSON 字节（测试用确定性基线）。"""
    return canonical_json_bytes(payload)
