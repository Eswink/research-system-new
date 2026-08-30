"""Run orchestration event publishing helper（控制 service.py 文件长度）。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from packages.application.ports.event_publisher import EventPublisher
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.manifest import RunManifest
from packages.domain.run import ResearchRun


class EventSink:
    """Publish target bundle built once from orchestration dependencies."""

    __slots__ = ("_events", "_actor")

    def __init__(self, events: EventPublisher, actor: str) -> None:
        self._events = events
        self._actor = actor


@dataclass(frozen=True, slots=True)
class EventTarget:
    """事件关联目标（run/trace/task）；参数对象规避 max-args。"""

    run_id: str
    trace_id: str
    task_id: str | None = None


def publish_event(
    sink: EventSink,
    event_type: EventType,
    payload: dict[str, object],
    target: EventTarget,
) -> None:
    """Publish a domain event envelope through the injected publisher."""
    envelope = EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        schema_version="1",
        occurred_at=Timestamp.now(),
        actor=sink._actor,
        scope=f"run:{target.run_id}" + (f" task:{target.task_id}" if target.task_id else ""),
        payload=payload,
        payload_digest=digest_of_payload(payload),
        run_id=target.run_id,
        task_id=target.task_id,
        trace_id=target.trace_id,
    )
    sink._events.publish(envelope)


def frozen_payload(run: ResearchRun, manifest: RunManifest) -> dict[str, object]:
    """MANIFEST_FROZEN 事件 payload（含 pricing 冻结引用）。"""
    return {
        "run_id": run.id.value,
        "digest": str(manifest.digest()),
        "pricing_version": manifest.pricing_version,
        "pricing_digest": manifest.pricing_digest,
    }


__all__ = ["EventSink", "EventTarget", "frozen_payload", "publish_event"]
