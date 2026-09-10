"""通知 DTO（WP-G；事件投影，白名单类型，无 payload 内容——观测隐私）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NotificationDto(BaseModel):
    id: str
    type: str
    run_id: str | None = None
    task_id: str | None = None
    occurred_at: str
    read: bool


class NotificationsViewDto(BaseModel):
    notifications: list[NotificationDto] = Field(default_factory=list)
    note: str
