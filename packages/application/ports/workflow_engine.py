"""WorkflowEngine Port：run/phase/task 生命周期编排（ADR-0001、WORKFLOW_RELIABILITY.md）。

职责：任务分发（at-least-once + idempotency 键去重）、lease 获取/心跳、
retry 调度、取消传播；不执行 Agent 循环（AgentRuntime 职责）。
非职责：不做持久化（M7 实现 PostgreSQL task queue/outbox）；
不代替 Domain Event 发布（EventPublisher）。

M5 决策 D1：本 Port 与 Fake 在 M5 冻结语义；M7 以 contract suite 验收
PostgreSQL 实现。M5 决策 D2：同步语义；cancellation 为协作式。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from packages.domain.core import Timestamp
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class TaskLease:
    lease_id: str
    task_id: str
    agent_id: str | None = None
    expires_at: Timestamp | None = None
    heartbeat_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.lease_id:
            raise ValueError("lease_id must not be empty")
        if not self.task_id:
            raise ValueError("task_id must not be empty")


@dataclass(frozen=True, slots=True)
class TaskCompletion:
    task_id: str
    outcome: str
    message: str = ""

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if not self.outcome:
            raise ValueError("outcome must not be empty")


@runtime_checkable
class WorkflowEngine(Protocol):
    """at-least-once 任务分发契约；实现必须保证幂等去重。"""

    def submit(self, task: ResearchTask, contract: TaskContract) -> None: ...

    def acquire_lease(self, task_id: str) -> TaskLease: ...

    def heartbeat(self, lease: TaskLease) -> TaskLease: ...

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None: ...

    def cancel(self, task_id: str) -> None: ...

    def recover_expired_leases(self) -> int: ...
