"""FakeWorkerRegistry：WorkerRegistry Port 的确定性 test-double。

服务端时间由可注入 `now` 驱动（默认 UTC now）；心跳/迁移/stale 判定全部
以该时钟为准，与 PG 实现共享同一 contract suite 语义。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.state_base import InvalidTransitionError
from packages.domain.workers import WorkerRegistration, WorkerState


def _server_now(now: Callable[[], datetime] | None) -> datetime:
    value = datetime.now(timezone.utc) if now is None else now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    return value.astimezone(timezone.utc)


class FakeWorkerRegistry(FakeBase):
    """内存 worker 注册表；generation 单调 +1，心跳幂等不回拨。"""

    def __init__(self, now: Callable[[], datetime] | None = None) -> None:
        super().__init__("worker_registry")
        self._workers: dict[str, WorkerRegistration] = {}
        self._generations: dict[str, int] = {}
        self._tokens: dict[str, str] = {}  # worker_id -> session token sha256
        self._now = now

    def _stamp(self) -> Timestamp:
        return Timestamp(_server_now(self._now))

    def register(self, registration: WorkerRegistration) -> WorkerRegistration:
        self._enter("register", registration.worker_id)
        next_gen = self._generations.get(registration.worker_id, 0) + 1
        self._generations[registration.worker_id] = next_gen
        stored = WorkerRegistration(
            worker_id=registration.worker_id,
            protocol_version=registration.protocol_version,
            runtime_version=registration.runtime_version,
            capabilities=registration.capabilities,
            backend_kinds=registration.backend_kinds,
            platform=registration.platform,
            partition_slots=registration.partition_slots,
            max_concurrency=registration.max_concurrency,
            registration_generation=next_gen,
            state=WorkerState.State.REGISTERING,
            last_heartbeat=self._stamp(),
            drain_requested=False,
        )
        self._workers[registration.worker_id] = stored
        self._tokens.pop(registration.worker_id, None)  # re-register voids old token
        self._record("register", registration.worker_id, result=f"gen={next_gen}")
        return stored

    def heartbeat(self, worker_id: str, generation: int) -> bool:
        self._enter("heartbeat", worker_id)
        stored = self._workers.get(worker_id)
        if stored is None or stored.registration_generation != generation:
            self._record("heartbeat", worker_id, result="rejected")
            return False
        stamp = self._stamp()
        current = stored.last_heartbeat
        newest = stamp if current is None or stamp.value >= current.value else current
        self._workers[worker_id] = replace(stored, last_heartbeat=newest)
        self._record("heartbeat", worker_id, result="ok")
        return True

    def _require(self, worker_id: str) -> WorkerRegistration:
        stored = self._workers.get(worker_id)
        if stored is None:
            raise InvalidInputError(f"unknown worker: {worker_id}")
        return stored

    def transition(self, worker_id: str, event: str) -> WorkerRegistration:
        self._enter("transition", f"{worker_id}:{event}")
        stored = self._require(worker_id)
        try:
            new_state = WorkerState.transition(stored.state, event)
        except InvalidTransitionError:
            self._record("transition", f"{worker_id}:{event}", error="InvalidTransitionError")
            raise
        updated = stored.with_state(new_state)
        self._workers[worker_id] = updated
        self._record("transition", f"{worker_id}:{event}", result=new_state)
        return updated

    def drain(self, worker_id: str) -> WorkerRegistration:
        self._enter("drain", worker_id)
        stored = self._require(worker_id)
        new_state = WorkerState.transition(stored.state, WorkerState.Transition.DRAIN_REQUESTED)
        updated = stored.with_state(new_state, drain_requested=True)
        self._workers[worker_id] = updated
        self._record("drain", worker_id, result=new_state)
        return updated

    def mark_lost(self, worker_id: str) -> WorkerRegistration:
        self._enter("mark_lost", worker_id)
        stored = self._require(worker_id)
        new_state = WorkerState.transition(stored.state, WorkerState.Transition.HEARTBEAT_EXPIRED)
        updated = stored.with_state(new_state)
        self._workers[worker_id] = updated
        self._record("mark_lost", worker_id, result=new_state)
        return updated

    def set_session_token(self, worker_id: str, generation: int, token_sha256: str) -> bool:
        self._enter("set_session_token", worker_id)
        stored = self._workers.get(worker_id)
        if stored is None or stored.registration_generation != generation:
            self._record("set_session_token", worker_id, result="rejected")
            return False
        self._tokens[worker_id] = token_sha256
        self._record("set_session_token", worker_id, result="ok")
        return True

    def authenticate(self, token_sha256: str) -> WorkerRegistration | None:
        self._enter("authenticate", "<sha256>")
        for worker_id, bound in self._tokens.items():
            if bound == token_sha256:
                return self._workers.get(worker_id)
        return None

    def list_stale(self, stale_seconds: float) -> tuple[str, ...]:
        self._enter("list_stale", f"{stale_seconds}")
        cutoff = _server_now(self._now) - timedelta(seconds=stale_seconds)
        # Match the PG filter: terminal (OFFLINE) and already-reaped (LOST)
        # workers are never re-listed.
        reapable = (
            WorkerState.State.REGISTERING,
            WorkerState.State.READY,
            WorkerState.State.BUSY,
            WorkerState.State.DRAINING,
        )
        stale = tuple(
            sorted(
                worker_id
                for worker_id, reg in self._workers.items()
                if reg.state in reapable
                and reg.last_heartbeat is not None
                and reg.last_heartbeat.value < cutoff
            )
        )
        self._record("list_stale", f"{stale_seconds}", result=str(len(stale)))
        return stale

    def get(self, worker_id: str) -> WorkerRegistration | None:
        self._enter("get", worker_id)
        return self._workers.get(worker_id)

    def list_workers(self) -> tuple[WorkerRegistration, ...]:
        self._enter("list_workers", "")
        return tuple(self._workers[k] for k in sorted(self._workers))
