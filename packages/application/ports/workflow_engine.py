"""WorkflowEngine Port：run/phase/task 生命周期编排（ADR-0001、WORKFLOW_RELIABILITY.md）。

职责：任务分发（at-least-once + idempotency 键去重）、lease 获取/心跳、
retry 调度、取消传播；不执行 Agent 循环（AgentRuntime 职责）。
非职责：不做持久化（M7 实现 PostgreSQL task queue/outbox）；
不代替 Domain Event 发布（EventPublisher）。

M5 决策 D1：本 Port 与 Fake 在 M5 冻结语义；M7 以 contract suite 验收
PostgreSQL 实现。M5 决策 D2：同步语义；cancellation 为协作式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(frozen=True, slots=True)
class TaskIdentity:
    """canonical 任务的稳定身份投影（重启后续跑按 idempotency key 对齐用）。"""

    idempotency_key: str
    task_id: str
    status: str


@dataclass(frozen=True, slots=True)
class RetrySchedule:
    """该 run 的重排读面（GOAL-004 cycle 2 = EC-02）。

    两件 canonical 事实：任务行的 `status == RETRY_SCHEDULED` 与 `retry_at`。
    `scheduled` 是**还没到**期限的条数，`due` 是**现在就能再交付**的条数
    （`retry_at` 为空 = 立即重排，也算到期），`next_retry_at` 是最近一条未到期的
    期限。分类在 adapter 内用权威时钟完成，所以这里的数字不需要调用方再拿"现在"比。
    """

    scheduled: int = 0
    due: int = 0
    next_retry_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if self.scheduled < 0 or self.due < 0:
            raise ValueError("retry schedule counts must be non-negative")
        if self.scheduled > 0 and self.next_retry_at is None:
            raise ValueError("a scheduled retry must carry its next deadline")
        if self.scheduled == 0 and self.next_retry_at is not None:
            raise ValueError("no scheduled retry may carry a deadline")


# 统一派发读面的 kind 取值（GOAL-004 cycle 6 = EC-05 ②）。四个取值只是两件 canonical
# 事实（重排读面 + 活租约持有者）的组合，不是第二份真相：
# `NONE` = 没有活的派发方（可能仍停在 PAUSED 等人工介入）。
DISPATCH_NONE = "NONE"
DISPATCH_RETRY = "RETRY_DISPATCH"
DISPATCH_WORKER_CLAIM = "WORKER_CLAIM"
DISPATCH_BOTH = "BOTH"


@dataclass(frozen=True, slots=True)
class LeaseHolder:
    """一个 run 里**活着**的租约持有者（读面用，不含 `lease_id`）。

    `worker_id` 为空 = 租约由控制面自己持有（agent session 投递路径），非空 = worker
    plane 的 claim。`lease_id` **不进读面**：那是作业面结果提交的凭据，读面不复制
    能力面（AGENTS.md §9 的最小暴露）。
    """

    task_id: str
    worker_id: str | None = None
    fence: int = 0
    expires_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if self.fence < 0:
            raise ValueError("fence must be non-negative")


@dataclass(frozen=True, slots=True)
class DispatchOwnership:
    """一个 run 的**统一派发读面**：现在谁在派发它（GOAL-004 cycle 6 = EC-05 ②）。

    两个派发方此前各持一半事实、没有一处答得出"这条 run 有没有活的派发方"：retry
    dispatch 守护线程只看 `PAUSED` 的重排到期，worker plane 的租约事实则完全不在读面。
    本读模型把两件 canonical 事实放进**同一次读**：`retry`（任务行的重排）与 `leases`
    （活租约持有者）。

    "活"由 adapter 用**权威时钟**判定（生产：DB 时钟；测试：注入时钟），且是
    `recover_expired_leases` 回收判据的**补集**——回收会动手的那条不算持有，读面不许把
    "马上要被回收"说成"有人在派发"。`kind` 只是这两件事实的组合，调用方不必自己拼。
    """

    retry: RetrySchedule = field(default_factory=RetrySchedule)
    leases: tuple[LeaseHolder, ...] = ()

    @property
    def kind(self) -> str:
        retrying = self.retry.scheduled > 0 or self.retry.due > 0
        claimed = bool(self.leases)
        if retrying and claimed:
            return DISPATCH_BOTH
        if claimed:
            return DISPATCH_WORKER_CLAIM
        if retrying:
            return DISPATCH_RETRY
        return DISPATCH_NONE


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

    def due_retry_task_ids(self, run_id: str) -> tuple[str, ...]:
        """读取该 run 里**已经到期**的重排任务 ids（确定性排序）。

        与 claim 候选扫描同一判据（`RETRY_SCHEDULED` 且 `retry_at` 为空或已过），
        但按 run 问：调度器靠这一句判断"停车中的 run 现在能不能再交付一次"
        （GOAL-003 cycle 19）。任务投影不携带 `retry_at`（期限只在任务行/事件里），
        所以这是读面唯一能回答该问题的入口。

        比较发生在 adapter 内，用的是**权威时钟**（生产：DB 时钟；测试：注入时钟），
        与写 `retry_at` 时同一个源——调用方不自己拿"现在"来比。
        """

    def retry_schedule(self, run_id: str) -> RetrySchedule:
        """该 run 当前的**重排读面**（一个调用、一个时钟）。

        与 `due_retry_task_ids` 同一判据（`RETRY_SCHEDULED` 且 `retry_at` 为空或已过），
        但回答运维读面要问的问题："这条停车会不会自己走、下一个到期是什么时候、现在
        是不是已经到期"。调度器要的是 ids（`due_retry_task_ids`），读面要的是计数与
        最近期限（这一句）——两者由同一个 adapter 时钟分类，不会各算各的。
        """

    def dispatch_ownership(self, run_id: str) -> DispatchOwnership:
        """该 run 的**统一派发读面**：现在谁在派发它（一个调用、一个时钟）。

        两个派发方（retry dispatch 守护线程 / worker plane 的 claim）此前各持一半事实，
        没有一处答得出"这条 run 有没有活的派发方、是哪一个"——这一句就是那一个答案：
        `retry` 给重排读面（与 `retry_schedule` 同一列同一判据、同一个 `now`），
        `leases` 给**活着**的租约持有者（`expires_at >= now` 且持有者不是 LOST worker，
        即 `recover_expired_leases` 回收集合的补集）。

        范围与诚实边界：只回答"有没有"与"是谁"（task/worker/fence/到期），**不回答
        "是不是健康"**（心跳新鲜度、执行进度、卡死与否都不在这里）；读面零写、零缓存，
        也不新增"派发原因"字段——`kind` 由两件 canonical 事实组合，不是第二份真相。
        三实现语义一致；Fake 无租约过期语义（其"活"= 仍在租约表里）由契约用例钉住。
        """

    def task_identities(self, run_id: str) -> tuple[TaskIdentity, ...]:
        """读取该 run 已登记任务的稳定身份（确定性排序）。

        重启后的续跑要重算"还剩哪些工作"（GOAL-003 cycle 20）：`resolve_sessions`
        每次解析都会生成**新的 task id**，而 idempotency key（`run:phase:agent`）才是
        稳定身份。重建路径靠这一句把解析出来的 spec 对齐回 canonical 任务：

        - 已 `SUCCEEDED` 的任务不重跑（重算剩余工作）；
        - 其余任务必须用 canonical task id（引擎按 key 去重，拿新 id 去 acquire
          只会得到"这个任务不存在"）；
        - 未登记的任务（首次交付）按解析出的新 id 走。

        无 key 的任务行（既有/异常数据）不参与回答。
        """

    def recover_expired_leases(self) -> int: ...
