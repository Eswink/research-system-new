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
from packages.domain.enums import FailureCategory
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class TaskLease:
    lease_id: str
    task_id: str
    agent_id: str | None = None
    expires_at: Timestamp | None = None
    heartbeat_at: Timestamp | None = None
    # M16: worker identity + auditable fencing generation. Defaults keep the
    # frozen M5/M14 construction sites and contract suites intact.
    worker_id: str | None = None
    fence: int = 0

    def __post_init__(self) -> None:
        if not self.lease_id:
            raise ValueError("lease_id must not be empty")
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if self.fence < 0:
            raise ValueError("fence must be non-negative")


@dataclass(frozen=True, slots=True)
class ClaimRequest:
    """A worker's claim filter (M16 §7).

    `capabilities`/`partitions` are claim *filters*, not ownership: the sole
    ownership authority remains the `leases` row (task_id PK + lease_id +
    fence). `relax_partitions` is the starvation fallback — when a partition
    has no worker coverage past a threshold, the scheduler may claim by
    capability only.
    """

    worker_id: str
    capabilities: frozenset[str]
    partitions: frozenset[int]
    lease_ttl_seconds: int = 300
    relax_partitions: bool = False

    def __post_init__(self) -> None:
        if not self.worker_id:
            raise ValueError("worker_id must not be empty")
        if self.lease_ttl_seconds < 1:
            raise ValueError("lease_ttl_seconds must be >= 1")


@dataclass(frozen=True, slots=True)
class TaskCompletion:
    task_id: str
    outcome: str
    message: str = ""
    # 失败分类（PLAN-20260915-078）：重试策略要按**类别**判断可否重试，而类别只有
    # 完成方（执行侧）知道。缺省 None = 未分类 ⇒ 不重试（见 TaskContract.decide_failure）。
    failure_category: FailureCategory | None = None

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

    def claim_next(self, request: ClaimRequest) -> TaskLease | None:
        """Pull the next QUEUED EXECUTION task matching the worker's capability
        /partition filter, atomically leasing it to that worker (M16 §7).

        Returns None when nothing claimable matches. Increments the task's
        `fence_seq` and records it on the lease so a stale worker's late
        result is rejected by `(task_id, lease_id, fence)`. Implementations
        must serialize concurrent claims (PostgreSQL `FOR UPDATE SKIP LOCKED`);
        the SQLite/Fake implementations are single-process and say so.

        Cooperative pause (PLAN-20260914-048): a task whose run is canonically
        `PAUSED` is not claimable. Dispatch stops; leases already held are NOT
        revoked (no orphan, no fake "stopped" claim).
        """
        ...

    def run_state(self, run_id: str) -> str | None:
        """Read the run's canonical state (`None` = unknown run).

        The dispatch plane needs exactly this one read-only fact to honor a
        pause: it is the same truth the control plane persists, not a second
        flag that could drift.
        """
        ...

    def heartbeat(self, lease: TaskLease) -> TaskLease: ...

    def renew_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        """Extend an active lease's expiry WITHOUT rotating lease_id or fence.

        Used by a worker to keep a long-running EXECUTION job alive during
        execution (M16 re-audit F-7). Unlike `heartbeat` (which rotates the
        lease id for agent sessions), this preserves the exact fencing triple
        the worker holds, so its later result still validates. Raises
        InvalidInputError if the triple/identity no longer matches an active
        lease (superseded, expired, or reclaimed).
        """
        ...

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None: ...

    def cancel(self, task_id: str) -> None: ...

    def cancel_run(self, run_id: str) -> int:
        """取消 run 下所有未终止任务；返回实际取消数量（协作式，幂等）。"""

    def cancelled_task_ids(self, run_id: str) -> tuple[str, ...]:
        """读取该 run 当前处于 CANCELLED 的 canonical task ids（确定性排序）。"""

    def recover_expired_leases(self) -> int: ...
