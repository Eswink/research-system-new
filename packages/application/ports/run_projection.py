"""RunProjection Port：控制面只读投影（M13 引入）。

职责：Run Timeline/Task 的只读查询（canonical state 与 outbox 事件投影）。
非职责：不修改状态（只读）；不替代 WorkflowEngine（调度/lease/cancel）。
M14 PostgreSQL canonical state 落地时本 Port 是查询接缝（接口不变）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.events import EventEnvelope
from packages.domain.tasks import ResearchTask, TaskContract


@runtime_checkable
class RunProjection(Protocol):
    """Run 只读投影：tasks（canonical state）与 events（outbox）。"""

    def list_tasks(self, run_id: str) -> tuple[tuple[ResearchTask, TaskContract], ...]: ...

    def events(self, run_id: str) -> tuple[EventEnvelope, ...]: ...
