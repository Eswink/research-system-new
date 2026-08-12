"""EventPublisher Port：发布 Domain Event（docs/architecture/EVENT_MODEL.md）。

职责：publish(EventEnvelope)，按 event_id 幂等（重复发布返回首次结果，
Consumer 必须按 event_id 去重）。Domain Event 是产品审计信号；runtime
event（AgentRuntime.stream_events）与 telemetry 都不是 Domain Event，
不得经本 Port 替代（OBSERVABILITY.md §2）。
非职责：不做 Outbox 持久化（M7 transactional outbox）；不做敏感内容
记录（payload 中禁止 secret/raw CoT，EVENT_MODEL.md §4）。

M5 决策 D2：同步语义。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.events import EventEnvelope


@runtime_checkable
class EventPublisher(Protocol):
    """Domain Event 发布；event_id 幂等。"""

    def publish(self, envelope: EventEnvelope) -> None: ...
