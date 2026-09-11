"""通知控制面路由（WP-G）：outbox 事件投影 + 已读标记。

诚实语义：通知是 derived 投影（事件流是真相）；白名单限用户相关事件
类型（task.* 等高频执行噪音不呈现）；不含 payload 内容（观测隐私，
AGENTS §10）；无事件时为空列表（不虚构）；已读状态持久化于控制面。
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from packages.domain.events import EventEnvelope, EventType
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.notifications import NotificationDto, NotificationsViewDto
from services.api.errors import ApiError

router = APIRouter(tags=["notifications"])

_USER_RELEVANT = frozenset({
    EventType.MANIFEST_FROZEN,
    EventType.RUN_COMPLETED,
    EventType.RUN_FAILED,
    EventType.RUN_CANCELLED,
    EventType.APPROVAL_REQUESTED,
    EventType.APPROVAL_DECIDED,
    EventType.CLAIM_VERIFIED,
    EventType.CLAIM_DISPUTED,
    EventType.MEMORY_COMMITTED,
    EventType.MEMORY_DELETED,
})

NOTE = (
    "通知来自 outbox 事件投影（事件流是真相；已读是 view-state）。"
    "白名单外的高频执行事件（task.* 等）不呈现；不含 payload 内容。"
)

SCAN_CAP = 500


def _projection(deps: ApiDeps) -> object:
    if deps.projection is None or deps.notification_reads is None:
        raise ApiError(503, "Notifications Unavailable", "projection/read store not configured")
    return deps.projection


def _dto(envelope: EventEnvelope, read_ids: frozenset[str]) -> NotificationDto:
    return NotificationDto(
        id=envelope.event_id,
        type=envelope.event_type.value,
        run_id=envelope.run_id,
        task_id=envelope.task_id,
        occurred_at=envelope.occurred_at.value.isoformat(),
        read=envelope.event_id in read_ids,
    )


@router.get("/notifications", response_model=NotificationsViewDto)
async def list_notifications(
    request: Request, limit: int = Query(default=50, ge=1, le=200)
) -> NotificationsViewDto:
    deps: ApiDeps = get_deps(request)
    projection = _projection(deps)
    read_ids = deps.notification_reads.read_event_ids()  # type: ignore[union-attr]
    events = projection.recent_events(min(limit * 10, SCAN_CAP))  # type: ignore[attr-defined]
    items = [
        _dto(envelope, read_ids) for envelope in events if envelope.event_type in _USER_RELEVANT
    ]
    return NotificationsViewDto(notifications=items[:limit], note=NOTE)


@router.post("/notifications/{event_id}/read", status_code=204)
async def mark_read(event_id: str, request: Request) -> None:
    deps: ApiDeps = get_deps(request)
    _projection(deps)
    if len(event_id) > 160:
        raise ApiError(422, "Invalid Notification Id", "event id too long")
    deps.notification_reads.mark_read(event_id)  # type: ignore[union-attr]
