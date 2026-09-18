"""M16 WP2 concurrent claim + partition ownership (PostgreSQL).

Proves the scheduling invariants that make a distributed plane safe on a
single queue: multiple schedulers claiming concurrently never split-brain
(FOR UPDATE SKIP LOCKED yields disjoint work), and overlapping partition
slots still produce a single owner per task — because partition is only a
filter and the `leases` row is the sole ownership authority.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskLease
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract

pytestmark = pytest.mark.postgres

START = datetime(2026, 8, 31, 9, 0, 0, tzinfo=timezone.utc)

#: 相位等待上限：barrier 不靠"等得够久"，但也不能把死锁无限挂住（超时即红）。
_PHASE_TIMEOUT_SECONDS = 30
_DRAIN_TIMEOUT_SECONDS = 60


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


@pytest.fixture(autouse=True, scope="function")
def _clean_postgres() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, workers CASCADE")
    conn.commit()
    conn.close()


def _submit_execution_tasks(count: int, *, partition: int | None = 0) -> list[str]:
    engine = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START)
    ids: list[str] = []
    try:
        for _ in range(count):
            task = ResearchTask(
                id=ID.generate(),
                run_id=ID.generate(),
                status=ResearchTaskState.State.QUEUED,
                kind=TaskKind.EXECUTION,
                required_capability="docker",
                partition=partition,
            )
            engine.submit(task, task_contract())
            ids.append(task.id.value)
    finally:
        engine.close()
    return ids


class _ClaimProbe:
    """领任务调用的**相位记录器**（测试侧，不改产品代码）。

    GOAL-006 cycle 4 = EC-04：这条用例原来用"至少两个 worker 领到了活"
    （`sum(...) >= 2`）来证明"并发是真的"——那读的是**调度产物**（谁先拿到 CPU，谁就
    可以合法地把 24 条任务全排空；单个 worker 全排空**不是缺陷**）。改为可复核的事实：

    - `attempts`：该 worker **进过几次领循环**（含最后一次空返回）——尝试计数是"测试真的
      在并发领任务"的相位事实，不读谁赢；
    - `arrival_index`：首次领任务调用在 `overlap` barrier 上的到达序号。**同一个** barrier
      的 N 个到达者拿到互不相同的 0…N-1 ⇒ 断言 `{index} == {0…N-1}` 同时证明三件事：
      所有 worker 都到达、它们由同一个 barrier 释放、重叠是构造而不是运气（把 barrier
      退化成每 worker 一个 `Barrier(1)` 会得到全 0 的序号 ⇒ 判据可识破）。
    """

    def __init__(self, engine: PostgresWorkflowEngine, overlap: threading.Barrier) -> None:
        self._engine = engine
        self._overlap = overlap
        self.attempts = 0
        self.arrival_index: int | None = None
        self._first = True

    def call(self, request: ClaimRequest) -> TaskLease | None:
        if self._first:
            self._first = False
            self.arrival_index = self._overlap.wait(timeout=_PHASE_TIMEOUT_SECONDS)
        self.attempts += 1
        return self._engine.claim_next(request)


def _drain(probe: _ClaimProbe, worker_id: str) -> list[str]:
    claimed: list[str] = []
    while True:
        lease = probe.call(
            ClaimRequest(
                worker_id=worker_id,
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0, 1, 2, 3}),
            )
        )
        if lease is None:
            return claimed
        claimed.append(lease.task_id)


def _concurrent_drain(
    worker_ids: list[str],
) -> tuple[dict[str, list[str]], dict[str, _ClaimProbe], dict[str, str]]:
    """F-6: genuinely concurrent claim drain — one engine (own connection) per
    worker thread.

    相位（EC-04）：`start` barrier 让所有线程**同时开始**；`overlap` barrier 在
    `_ClaimProbe` 的首次调用里让所有 worker 的**第一次领任务同时进入**——前提由构造
    保证，断言因此不依赖调度。返回值 = 各自的领取结果 + 相位记录 + 线程异常
    （线程里炸掉不再静默）。
    """
    clock = lambda: START + timedelta(seconds=1)  # noqa: E731
    engines = {w: PostgresWorkflowEngine(dsn=_dsn(), now=clock) for w in worker_ids}
    start = threading.Barrier(len(worker_ids))
    overlap = threading.Barrier(len(worker_ids))
    assert overlap.parties == len(worker_ids), "overlap barrier 必须覆盖所有 worker"
    probes = {w: _ClaimProbe(engines[w], overlap) for w in worker_ids}
    results: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    lock = threading.Lock()

    def _run(worker_id: str) -> None:
        try:
            start.wait(timeout=_PHASE_TIMEOUT_SECONDS)
            claimed = _drain(probes[worker_id], worker_id)
        except Exception as exc:  # noqa: BLE001 - 相位事实：线程异常必须可见
            with lock:
                failures[worker_id] = f"{type(exc).__name__}: {exc}"
            overlap.abort()
            return
        with lock:
            results[worker_id] = claimed

    threads = [threading.Thread(target=_run, args=(w,)) for w in worker_ids]
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=_DRAIN_TIMEOUT_SECONDS)
    finally:
        for engine in engines.values():
            engine.close()
    return results, probes, failures


def test_concurrent_schedulers_claim_disjoint_work() -> None:
    """N engines claiming SIMULTANEOUSLY never split-brain (SKIP LOCKED disjoint).

    "并发是真的"这条前提的判据是**相位/计数事实**（EC-04）：每个 worker 都进过领循环，
    且所有 worker 的**首次**领任务由构造重叠。不再用"至少两个 worker 领到了活"当代理
    ——单个 worker 合法地把 24 条全排空不是缺陷，把"谁赢"当判据才会 flake。
    """
    total = 24
    _submit_execution_tasks(total)
    workers = [f"w-{i}" for i in range(4)]
    results, probes, failures = _concurrent_drain(workers)
    all_claimed = [t for claimed in results.values() for t in claimed]
    assert len(all_claimed) == len(set(all_claimed))  # no task claimed twice
    assert len(all_claimed) == total  # every task claimed exactly once
    assert failures == {}, failures  # 线程异常不静默
    assert all(probes[w].attempts >= 1 for w in workers), {w: probes[w].attempts for w in workers}
    # 同一 barrier 的到达序号互不相同 ⇒ 所有 worker 的首次领任务由构造重叠
    assert {probes[w].arrival_index for w in workers} == set(range(len(workers))), {
        w: probes[w].arrival_index for w in workers
    }


def test_overlapping_partitions_single_owner() -> None:
    """All workers claim the SAME partition concurrently; each task still has one owner."""
    total = 12
    _submit_execution_tasks(total, partition=0)
    workers = [f"w-{i}" for i in range(3)]
    results, _, failures = _concurrent_drain(workers)
    assert failures == {}, failures
    all_claimed = [t for claimed in results.values() for t in claimed]
    assert len(all_claimed) == len(set(all_claimed)) == total


def test_fence_advances_on_reclaim_after_recovery() -> None:
    """A reclaimed lease carries a strictly higher fence than the first claim."""
    (task_id,) = _submit_execution_tasks(1)
    engine = PostgresWorkflowEngine(dsn=_dsn(), now=lambda: START, lease_ttl_seconds=1)
    try:
        first = engine.claim_next(
            ClaimRequest(
                worker_id="w1",
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0}),
            )
        )
        assert first is not None and first.fence == 1
        # expire the lease (advance clock past ttl) and recover
        later = START + timedelta(seconds=10)
        engine._now = lambda: later  # deterministic test clock
        recovered = engine.recover_expired_leases()
        assert recovered == 1
        second = engine.claim_next(
            ClaimRequest(
                worker_id="w2",
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0}),
            )
        )
        assert second is not None
        assert second.fence == 2
        assert second.worker_id == "w2"
    finally:
        engine.close()
