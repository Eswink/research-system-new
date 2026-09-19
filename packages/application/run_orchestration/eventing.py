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
    """MANIFEST_FROZEN 事件 payload（含 pricing 冻结引用与语义 digest）。

    `digest` 覆盖 `frozen_at`（这份快照的字节级标识），`semantic_digest` 排除冻结时刻
    （resume 漂移校验的输入）。两者都要进 payload：失败收敛路径没有 `RunOutcome` 可读，
    只能从事件链把 run 行的冻结引用补回来（GOAL-004 cycle 4 / RECHECK-083 W-1+W-2）。
    """
    return {
        "run_id": run.id.value,
        "digest": str(manifest.digest()),
        "semantic_digest": str(manifest.semantic_digest()),
        "pricing_version": manifest.pricing_version,
        "pricing_digest": manifest.pricing_digest,
        # PLAN-20260919-107（EC-01）：执行基质随冻结快照进读面。EC-01 时读面只走
        # `GET /runs/{id}/events`；EC-04 起同一事实另有 `GET /runs/{id}` 的 `execution`
        # 读面——**回读的仍是本 payload**，不另存一份（少一处可漂移的副本）。
        # None = 冻结时未声明（M7 不伪填充口径），不得读作某一个具体执行体。
        "execution_backend": manifest.execution_backend,
        # PLAN-20260919-110（EC-04）：指纹槽位的**诚实状态**（AGENTS.md §4）随冻结快照
        # 进读面。空 dict = 冻结时未声明该面，与 `execution_backend` 的 None 同口径；
        # 有值时是 `{substrate, status, reason}` 的**状态**记录，不是指纹值本身。
        "runtime_fingerprint": dict(manifest.model_runtime_fingerprints),
    }


__all__ = ["EventSink", "EventTarget", "frozen_payload", "publish_event"]
