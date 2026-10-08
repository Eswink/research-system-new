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

    def for_program(self, program_id: str) -> tuple[ResearchRun, ...]: ...

    """某研究程序的全部 run，按 `program_index` **升序**（GOAL-20261008-037 EC-01）。

    它是「程序推进到第几轮」的唯一 canonical 查询面：驱动据此判序号与去重，
    不依赖任何侧表（关联就在 run 自身的 `program_id` / `program_index` 上）。
    """
