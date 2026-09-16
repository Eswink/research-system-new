"""ScheduleStore Port：调度定义的配置存储（GOAL-003 EC-03）。

职责：`ScheduleDefinition` 的持久化（创建/启停/改 interval）；与 OpsStore/ProjectStore
同族（配置面，SQLite 共享连接由 composition root 注入）。
非职责：不调度、不执行、不记录运行事实——执行体是 `services/api/scheduler.py` 的
守护线程，运行事实由 `ScheduleRegistry` 在本进程内观测。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.schedules import ScheduleDefinition


@runtime_checkable
class ScheduleStore(Protocol):
    """调度定义 CRUD；未找到一律抛 `KeyError`（控制面映射 404）。"""

    def list_definitions(self) -> list[ScheduleDefinition]: ...

    def get_definition(self, name: str) -> ScheduleDefinition | None: ...

    def save_definition(self, definition: ScheduleDefinition) -> None: ...

    def delete_definition(self, name: str) -> None: ...
