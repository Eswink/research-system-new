"""RunStore Port：ResearchRun 状态存储（M13-R1 引入）。

职责：run 生命周期状态的持久化（M13-R1 WP-M1：API 重启后 run 状态
可恢复，Timeline 事件端点不再被内存注册表 gate 挡住）。
非职责：不做任务/事件存储（WorkflowEngine/Outbox 负责）；不决定
状态机语义（domain ResearchRunState 唯一权威）。
M14 PostgreSQL canonical state 落地后走同一 Port。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.run import ResearchRun


@runtime_checkable
class RunStore(Protocol):
    """ResearchRun 存储；CRUD 语义由实现保证。"""

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]: ...

    def get_run(self, run_id: str) -> ResearchRun: ...

    def save_run(self, run: ResearchRun) -> None: ...
