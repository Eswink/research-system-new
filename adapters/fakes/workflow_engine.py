"""FakeWorkflowEngine：at-least-once 分发（幂等去重）+ lease/heartbeat/cancel。"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    DispatchOwnership,
    LeaseHolder,
    RetrySchedule,
    TaskCompletion,
    TaskIdentity,
    TaskLease,
)
from packages.domain.core import Timestamp
from packages.domain.enums import TaskKind
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask, TaskContract


class FakeWorkflowEngine(FakeBase):
    """submit 按 idempotency_key 去重；acquire_lease 为投递副作用。

    重复投递（同 idempotency_key 再次 submit + acquire）不产生新的
    副作用记录：deliveries 仅统计首次。
    """

    def __init__(self) -> None:
        super().__init__("workflow_engine")
        self._tasks: dict[str, ResearchTask] = {}
        self._contracts: dict[str, TaskContract] = {}
        self._idem_keys: dict[str, str] = {}
        self._leases: dict[str, TaskLease] = {}
        self._completed: dict[str, TaskCompletion] = {}
        self._cancelled: set[str] = set()
        self._deliveries: dict[str, int] = {}
        self._fences: dict[str, int] = {}
        # 协作式暂停（PLAN-048）：run 状态视图由控制面注入（与 SQLite/PG 侧
        # 读共享 runs 行等价），Fake 不自己造第二份真相。
        self._run_states: dict[str, str] = {}

    def set_run_state(self, run_id: str, state: str) -> None:
        """测试装配：登记 run 的 canonical 状态（暂停协调的唯一输入）。"""
        self._run_states[run_id] = state

    def run_state(self, run_id: str) -> str | None:
        self._enter("run_state", run_id)
        state = self._run_states.get(run_id)
        self._record("run_state", run_id, result=str(state))
        return state

    def submit(self, task: ResearchTask, contract: TaskContract) -> None:
        self._enter("submit", task.id.value)
        # at-least-once：重复提交（同 task.id 或同 idempotency_key）静默幂等，
        # 不抛错、不覆盖首次契约（PORTS.md §1 幂等语义）。
        if task.id.value in self._tasks or (
            task.idempotency_key is not None and task.idempotency_key in self._idem_keys
        ):
            self._record("submit", task.id.value, result="deduped")
            return
        self._tasks[task.id.value] = task
        self._contracts[task.id.value] = contract
        if task.idempotency_key is not None:
            self._idem_keys[task.idempotency_key] = task.id.value
        self._record("submit", task.id.value)

    def acquire_lease(self, task_id: str) -> TaskLease:
        self._enter("acquire_lease", task_id)
        if task_id not in self._tasks:
            self._record("acquire_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown task: {task_id}")
        # 与 SqliteWorkflowEngine 对齐：取消/完成后的任务不可重新租约（终止态无出边）。
        if task_id in self._cancelled or task_id in self._completed:
            self._record("acquire_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(f"task {task_id} is terminal; cannot acquire lease")
        existing = self._leases.get(task_id)
        if existing is not None:
            # at-least-once：重复投递不产生新副作用（幂等去重）
            self._record("acquire_lease", task_id, result="deduped")
            return existing
        task = self._tasks[task_id]
        key = task.idempotency_key or task.id.value
        lease = TaskLease(
            lease_id=str(uuid4()),
            task_id=task_id,
            agent_id=task.assigned_agent_id,
            expires_at=Timestamp.now(),
            heartbeat_at=Timestamp.now(),
        )
        self._leases[task_id] = lease
        self._deliveries[key] = self._deliveries.get(key, 0) + 1
        self._record("acquire_lease", task_id)
        return lease

    def claim_next(self, request: ClaimRequest) -> TaskLease | None:
        """Single-process claim_next (Fake): first QUEUED EXECUTION task whose
        capability/partition match the claim; advances the fence.

        Fake has no cross-process serialization (that is the PostgreSQL
        adapter's guarantee); it models the same claim/fence semantics for
        contract tests. Tasks of a canonically PAUSED run are not claimable
        (cooperative pause, PLAN-048) — held leases are untouched.
        """
        self._enter("claim_next", request.worker_id)
        for task_id, task in self._tasks.items():
            if task.kind != TaskKind.EXECUTION:
                continue
            if task.status != ResearchTaskState.State.QUEUED:
                continue
            if self._run_states.get(task.run_id.value) == ResearchRunState.State.PAUSED:
                continue
            if task_id in self._leases or task_id in self._completed or task_id in self._cancelled:
                continue
            if (
                task.required_capability is not None
                and task.required_capability not in request.capabilities
            ):
                continue
            if not request.relax_partitions and task.partition is not None:
                if task.partition not in request.partitions:
                    continue
            fence = self._fences.get(task_id, 0) + 1
            self._fences[task_id] = fence
            lease = TaskLease(
                lease_id=str(uuid4()),
                task_id=task_id,
                agent_id=task.assigned_agent_id,
                expires_at=Timestamp.now(),
                heartbeat_at=Timestamp.now(),
                worker_id=request.worker_id,
                fence=fence,
            )
            self._leases[task_id] = lease
            self._record("claim_next", request.worker_id, result=f"{task_id}@fence={fence}")
            return lease
        self._record("claim_next", request.worker_id, result="none")
        return None

    def heartbeat(self, lease: TaskLease) -> TaskLease:
        self._enter("heartbeat", lease.task_id)
        if lease.task_id not in self._leases:
            self._record("heartbeat", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no lease for task: {lease.task_id}")
        renewed = TaskLease(
            lease_id=lease.lease_id,
            task_id=lease.task_id,
            agent_id=lease.agent_id,
            expires_at=Timestamp.now(),
            heartbeat_at=Timestamp.now(),
            worker_id=lease.worker_id,
            fence=lease.fence,
        )
        self._leases[lease.task_id] = renewed
        self._record("heartbeat", lease.task_id)
        return renewed

    def renew_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        """Extend an active EXECUTION lease in place (M16 re-audit F-7); Fake mirror."""
        self._enter("renew_lease", task_id)
        current = self._leases.get(task_id)
        if (
            current is None
            or current.lease_id != lease_id
            or current.fence != fence
            or current.worker_id != worker_id
        ):
            self._record("renew_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(f"no active lease to renew for task: {task_id}")
        self._leases[task_id] = replace(
            current, expires_at=Timestamp.now(), heartbeat_at=Timestamp.now()
        )
        self._record("renew_lease", task_id, result="extended")

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._enter("complete", lease.task_id)
        stored = self._leases.get(lease.task_id)
        if stored is None:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no lease for task: {lease.task_id}")
        # fencing: only the current lease generation may write completion (M16 §8)
        if stored.lease_id != lease.lease_id or stored.fence != lease.fence:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"stale lease/fence for task: {lease.task_id}")
        self._completed[lease.task_id] = completion
        self._leases.pop(lease.task_id, None)
        self._record("complete", lease.task_id, result=completion.outcome)

    def cancel(self, task_id: str) -> None:
        self._enter("cancel", task_id)
        self._cancelled.add(task_id)
        self._leases.pop(task_id, None)
        self._record("cancel", task_id)

    def cancel_run(self, run_id: str) -> int:
        """取消 run 下所有未终止任务（协作式）；返回实际取消数量。"""
        self._enter("cancel_run", run_id)
        cancelled_count = 0
        for task_id, task in self._tasks.items():
            if task.run_id.value != run_id:
                continue
            if task_id in self._cancelled or task_id in self._completed:
                continue
            self._cancelled.add(task_id)
            self._leases.pop(task_id, None)
            cancelled_count += 1
        self._record("cancel_run", run_id, result=f"{cancelled_count} cancelled")
        return cancelled_count

    def cancelled_task_ids(self, run_id: str) -> tuple[str, ...]:
        self._enter("cancelled_task_ids", run_id)
        ids = tuple(
            sorted(
                task_id
                for task_id, task in self._tasks.items()
                if task.run_id.value == run_id and task_id in self._cancelled
            )
        )
        self._record("cancelled_task_ids", run_id, result=str(len(ids)))
        return ids

    def due_retry_task_ids(self, run_id: str) -> tuple[str, ...]:
        """Fake 无退避时延语义（重排即刻可交付）⇒ 该 run 所有可重排任务都"已到期"。

        与 `cancelled_task_ids` 同形：只按 canonical 任务投影回答，不读墙钟——
        Fake 没有写入 deadline 的路径（真实 deadline 判定由两个持久化 adapter 提供，
        tests/adapters/sqlite/test_workflow_due_retries.py 与 PG parity 覆盖）。
        """
        self._enter("due_retry_task_ids", run_id)
        ids = tuple(
            sorted(
                task_id
                for task_id, task in self._tasks.items()
                if task.run_id.value == run_id
                and task.status == ResearchTaskState.State.RETRY_SCHEDULED
            )
        )
        self._record("due_retry_task_ids", run_id, result=str(len(ids)))
        return ids

    def retry_schedule(self, run_id: str) -> RetrySchedule:
        """Fake 无退避时延语义 ⇒ 该 run 所有重排任务都算"已到期"、无下一个期限。

        与 `due_retry_task_ids` 同判据（只按 canonical 任务投影回答，不读墙钟）：
        Fake 没有写入 deadline 的路径，真实 deadline 分类由两个持久化 adapter 提供
        （SQLite 单测与 PG parity 覆盖）。
        """
        self._enter("retry_schedule", run_id)
        schedule = self._retry_schedule_of(run_id)
        self._record("retry_schedule", run_id, result=f"scheduled=0 due={schedule.due}")
        return schedule

    def _retry_schedule_of(self, run_id: str) -> RetrySchedule:
        """不记账的装配（单 run 与批量共用；见 `dispatch_ownership_many`）。"""
        due = sum(
            1
            for task in self._tasks.values()
            if task.run_id.value == run_id
            and task.status == ResearchTaskState.State.RETRY_SCHEDULED
        )
        return RetrySchedule(due=due)

    def dispatch_ownership(self, run_id: str) -> DispatchOwnership:
        """Fake 的统一派发读面：持有 = 租约还在表里（Fake 没有过期语义）。

        Fake 的租约不携带时钟（`expires_at` 只是构造时刻的戳，没有回收路径），所以
        "活"在这里只能是"仍被持有"——**这不是与持久化实现同强度的判据**，过期与
        LOST worker 两种情形由 SQLite 注入时钟单测与 PG parity 覆盖，本类不假装实现。
        `retry` 沿用 `retry_schedule`（Fake 无写 `RETRY_SCHEDULED` 路径 ⇒ 恒为零）。

        单 run 版就是批量版的**一条**（`_ownership_of`）——两个入口共用同一段装配。
        """
        self._enter("dispatch_ownership", run_id)
        ownership = self._ownership_of(run_id)
        self._record("dispatch_ownership", run_id, result=ownership.kind)
        return ownership

    def dispatch_ownership_many(self, run_ids: tuple[str, ...]) -> dict[str, DispatchOwnership]:
        """一批 run 的统一派发读面（GOAL-005 cycle 5 = EC-05 ①）。

        与单 run 版同一段装配（`_ownership_of`）⇒ 两个入口不会各算各的；每个请求到的
        run_id 都有条目（未知 run 与"没有持有"同判 = `DISPATCH_NONE`）。记账只记一次
        （列表路径的入口），不把内部的单 run 装配记成 N 次调用。
        """
        self._enter("dispatch_ownership_many", f"n={len(run_ids)}")
        ownerships = {run_id: self._ownership_of(run_id) for run_id in dict.fromkeys(run_ids)}
        kinds = ",".join(sorted({ownership.kind for ownership in ownerships.values()}))
        self._record(
            "dispatch_ownership_many",
            f"n={len(ownerships)}",
            result=kinds or "-",
        )
        return ownerships

    def _ownership_of(self, run_id: str) -> DispatchOwnership:
        """单 run 装配（不记账）：单 run 与批量共用的唯一一段判据。"""
        holders = tuple(
            LeaseHolder(
                task_id=task_id,
                worker_id=lease.worker_id,
                fence=lease.fence,
                expires_at=lease.expires_at,
            )
            for task_id, lease in sorted(self._leases.items())
            if task_id in self._tasks and self._tasks[task_id].run_id.value == run_id
        )
        return DispatchOwnership(retry=self._retry_schedule_of(run_id), leases=holders)

    def task_identities(self, run_id: str) -> tuple[TaskIdentity, ...]:
        """Fake 与两个持久化 adapter 同判据：按 canonical 任务回答稳定身份。

        `resolve_sessions` 每次生成新的 task id，所以重算剩余工作只能按
        idempotency key 对齐；无 key 的任务行不参与回答（与 SQL 侧 `IS NOT NULL` 同义）。
        """
        self._enter("task_identities", run_id)
        identities: list[TaskIdentity] = []
        for task in sorted(
            (
                item
                for item in self._tasks.values()
                if item.run_id.value == run_id and item.idempotency_key is not None
            ),
            key=lambda item: item.idempotency_key or "",
        ):
            key = task.idempotency_key
            if key is None:  # pragma: no cover - 上面的过滤已排除（mypy 需要显式收窄）
                continue
            identities.append(
                TaskIdentity(idempotency_key=key, task_id=task.id.value, status=task.status)
            )
        self._record("task_identities", run_id, result=str(len(identities)))
        return tuple(identities)

    def recover_expired_leases(self) -> int:
        """Fake 无 lease TTL 语义（lease 随 acquire/heartbeat 刷新），恒无过期 lease。

        Port 契约要求本方法存在；真实过期恢复语义由 SqliteWorkflowEngine 提供
        （tests/e2e/test_restart_recovery.py 覆盖）。
        """
        self._enter("recover_expired_leases", "")
        self._record("recover_expired_leases", "", result="0 recovered")
        return 0

    @property
    def deliveries(self) -> dict[str, int]:
        return dict(self._deliveries)

    @property
    def completed(self) -> dict[str, TaskCompletion]:
        return dict(self._completed)

    @property
    def cancelled(self) -> set[str]:
        return set(self._cancelled)
