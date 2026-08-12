"""FakeWorkflowEngine：at-least-once 分发（幂等去重）+ lease/heartbeat/cancel。"""

from __future__ import annotations

from uuid import uuid4

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    TaskLease,
)
from packages.domain.core import Timestamp
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
        )
        self._leases[lease.task_id] = renewed
        self._record("heartbeat", lease.task_id)
        return renewed

    def complete(self, lease: TaskLease, completion: TaskCompletion) -> None:
        self._enter("complete", lease.task_id)
        if lease.task_id not in self._leases:
            self._record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no lease for task: {lease.task_id}")
        self._completed[lease.task_id] = completion
        self._leases.pop(lease.task_id, None)
        self._record("complete", lease.task_id, result=completion.outcome)

    def cancel(self, task_id: str) -> None:
        self._enter("cancel", task_id)
        self._cancelled.add(task_id)
        self._leases.pop(task_id, None)
        self._record("cancel", task_id)

    @property
    def deliveries(self) -> dict[str, int]:
        return dict(self._deliveries)

    @property
    def completed(self) -> dict[str, TaskCompletion]:
        return dict(self._completed)

    @property
    def cancelled(self) -> set[str]:
        return set(self._cancelled)
