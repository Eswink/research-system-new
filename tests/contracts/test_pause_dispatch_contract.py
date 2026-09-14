"""派发暂停契约（PLAN-20260914-048）：PAUSED run 的任务不再被派发（三实现同语义）。

`claim_next` 读的是 canonical run state（`runs` 行），不是第二个标志位：
暂停后不派发，恢复后重新可认领；**已持租约不被撤销**（协作式，不制造孤儿）。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

import pytest

from adapters.fakes.workflow_engine import FakeWorkflowEngine
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    WorkflowEngine,
)
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])
_RUN_ID = "3d7e1c88-2f0a-4c1b-9a55-6c2d9f0e7b31"
_CREATED_AT = "2026-09-15T00:00:00Z"


def _execution_task(run_id: str = _RUN_ID) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1",
        capabilities=frozenset({"docker"}),
        partitions=frozenset({0}),
    )


def _seed_run_state(engine: WorkflowEngine, state: str) -> None:
    """把 run 的 canonical 状态写成 `state`（控制面正常经由 RunStore 写）。

    Fake 走它自己的状态视图；SQLite/PostgreSQL 直接写共享 `runs` 行——这正是
    派发面读取的那一份真相。
    """
    if isinstance(engine, FakeWorkflowEngine):
        engine.set_run_state(_RUN_ID, state)
        return
    conn = cast(Any, engine)._conn  # noqa: SLF001 - 契约测试经 adapter 连接写 canonical 行
    payload = json.dumps({"state": state, "id": _RUN_ID})
    if isinstance(engine, SqliteWorkflowEngine):
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs (run_id, project_id, run_json, created_at)"
                " VALUES (?, ?, ?, ?)",
                (_RUN_ID, "p", payload, _CREATED_AT),
            )
        return
    conn.execute(
        "INSERT INTO runs (run_id, project_id, run_json, created_at) VALUES (%s, %s, %s, %s)"
        " ON CONFLICT (run_id) DO UPDATE SET run_json = EXCLUDED.run_json",
        (_RUN_ID, "p", payload, _CREATED_AT),
    )
    conn.commit()


def _clear_run(engine: WorkflowEngine) -> None:
    if isinstance(engine, FakeWorkflowEngine):
        return
    conn = cast(Any, engine)._conn  # noqa: SLF001 - 清掉本用例写入的行，避免串味
    if isinstance(engine, SqliteWorkflowEngine):
        conn.execute("DELETE FROM runs WHERE run_id = ?", (_RUN_ID,))
    else:
        conn.execute("DELETE FROM runs WHERE run_id = %s", (_RUN_ID,))
    conn.commit()


@pytest.mark.parametrize("factory", _FACTORIES)
def test_run_state_reads_canonical_row(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    _clear_run(engine)  # 共享 PG 库里的上一轮残留不应影响本用例
    assert engine.run_state(_RUN_ID) is None
    _seed_run_state(engine, ResearchRunState.State.RUNNING)
    try:
        assert engine.run_state(_RUN_ID) == ResearchRunState.State.RUNNING
    finally:
        _clear_run(engine)


@pytest.mark.parametrize("factory", _FACTORIES)
def test_paused_run_is_not_dispatched_and_resumes_after_unpause(
    factory: Callable[[], object],
) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    _clear_run(engine)
    _seed_run_state(engine, ResearchRunState.State.PAUSED)
    task = _execution_task()
    engine.submit(task, task_contract())
    try:
        assert engine.claim_next(_request()) is None

        _seed_run_state(engine, ResearchRunState.State.RUNNING)
        lease = engine.claim_next(_request())
        assert lease is not None
        assert lease.task_id == task.id.value
    finally:
        _clear_run(engine)


@pytest.mark.parametrize("factory", _FACTORIES)
def test_pause_does_not_revoke_a_lease_already_held(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    _clear_run(engine)
    _seed_run_state(engine, ResearchRunState.State.RUNNING)
    granted = _execution_task()
    queued = _execution_task()
    engine.submit(granted, task_contract())
    engine.submit(queued, task_contract())
    try:
        lease = engine.claim_next(_request())
        assert lease is not None
        assert lease.task_id == granted.id.value

        _seed_run_state(engine, ResearchRunState.State.PAUSED)
        assert engine.claim_next(_request()) is None
        # 已持租约仍在（heartbeat 成功 = 未被撤销、未被回收）
        renewed = engine.heartbeat(lease)
        assert renewed.task_id == granted.id.value
    finally:
        _clear_run(engine)
