"""E2E（EC-01 (f)）：**从真实失败路径进死信 → 人工恢复 → 跑到终态**（ADR-0033）。

与 `tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py` 的差别是射程：
那条打的是引擎面（SQLite 单元）；本文件走**真编排**（`RunOrchestrationService` + 真
phase runner + 真 SQLite 任务面 + 注入时钟），证明恢复在**产品路径**上成立：

1. 执行契约声明 `max_attempts=1`（打满即死信）⇒ run 收敛 `FAILED`、任务落 `DEAD_LETTER`；
2. **恢复前**：**自动交付入口**点名拒绝它（终态守卫）——这就是「run 级重建续跑也捞不回
   它」的机制（续跑最终仍要过这一关）；
3. **人工恢复**（`engine.requeue`）⇒ 任务回 `QUEUED`；
4. **恢复后**：重建续跑真的把它跑到终态（第二次尝试成功）⇒ `SUCCEEDED`。

全离线：SQLite `:memory:` + 替身 runtime（AGENTS.md §11）。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import RetryPolicy
from tests.e2e.test_restart_rebuild_resume import (
    _frozen_digests,
    _parked_run,
    _rebuilt_context,
    _restarted,
    _resume_command,
)
from tests.e2e.test_retry_park_and_resume import OUTPUTS, _FlakyOnce, _harness, _start

BACKOFF_SECONDS = 3600


def _catalog_dead_letter_on_first_failure() -> Any:
    """执行契约 `max_attempts=1` ⇒ 第一次可重试失败就**打满** ⇒ 立刻死信。"""
    from tests.e2e.scenario_catalog import m7_catalog

    catalog = m7_catalog()
    execution = catalog.task_contracts["sort_analysis_execution"]
    dying = replace(
        execution,
        retry_policy=RetryPolicy(
            max_attempts=1,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=BACKOFF_SECONDS,
        ),
    )
    return replace(catalog, task_contracts={**catalog.task_contracts, execution.id: dying})


def _statuses(engine: SqliteWorkflowEngine, run_id: str) -> list[str]:
    return [str(row.task.status) for row in engine.list_tasks(run_id)]


def _task_row(engine: SqliteWorkflowEngine, run_id: str, task_id: str) -> Any:
    return next(row.task for row in engine.list_tasks(run_id) if row.task.id.value == task_id)


def _flaky_runtime() -> _FlakyOnce:
    return _FlakyOnce(outputs_by_contract=OUTPUTS)


def _drive_to_a_real_dead_letter(
    service: Any, engine: SqliteWorkflowEngine, run_id: ID
) -> tuple[str, int, list[str]]:
    """① 真实失败路径 —— 返回 (死信任务 id, 死亡时的 attempt, 当时的全量状态)。"""
    catalog = _catalog_dead_letter_on_first_failure()
    first = _start(service, catalog, run_id)
    assert first.state == ResearchRunState.State.FAILED, "打满预算 ⇒ run 判失败"
    statuses = _statuses(engine, run_id.value)
    assert ResearchTaskState.State.DEAD_LETTER in statuses, (
        f"真实失败路径必须产出死信（实测 {statuses}）"
    )
    dead = next(
        row.task
        for row in engine.list_tasks(run_id.value)
        if (row.task.status == ResearchTaskState.State.DEAD_LETTER)
    )
    assert dead.attempt == 1, "max_attempts=1 ⇒ 第一次尝试就耗尽"
    return dead.id.value, dead.attempt, statuses


def _assert_auto_path_refuses_before_recovery(
    engine: SqliteWorkflowEngine, run_id: ID, task_id: str, expected_statuses: list[str]
) -> None:
    """② 恢复**前**：自动交付入口点名拒绝（不吞异常、不把散文当判据）。"""
    with pytest.raises(InvalidInputError) as refused:
        engine.acquire_lease(task_id)
    assert "terminal" in str(refused.value), "恢复前：自动路径必须点名拒绝"
    assert task_id in str(refused.value), "拒绝消息必须点名任务 id"
    assert _statuses(engine, run_id.value) == expected_statuses, "恢复前：状态一字不动"


def _assert_recovery_lands(engine: SqliteWorkflowEngine, run_id: ID, task_id: str) -> None:
    """③ 人工恢复：状态回 `QUEUED`。"""
    assert engine.requeue(task_id) == "restored"
    assert _task_row(engine, run_id.value, task_id).status == ResearchTaskState.State.QUEUED


def _finish_with_a_rebuilt_resume(
    service: Any,
    clock: Any,
    run_id: ID,
    store: Any,
    artifacts: Any,
) -> None:
    """④ 恢复**后**：重建续跑真的把它跑到终态（含两组机械读数）。"""
    catalog = _catalog_dead_letter_on_first_failure()
    clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
    parked = _parked_run(run_id, _frozen_digests(run_id, catalog), source=None)
    resumed = parked.transition(ResearchRunState.Transition.RESUME)
    store.save_run(resumed)
    done = _restarted(service, artifacts).resume_rebuilt(
        _rebuilt_context(resumed, catalog), _resume_command(resumed)
    )
    assert done.state == ResearchRunState.State.SUCCEEDED, "恢复后必须能跑到终态"


def test_a_dead_letter_from_a_real_failure_is_recovered_and_finishes_the_run() -> None:
    """**主实跑**：真实失败 → 死信 → 人工恢复 → 重建续跑 → 终态（全程留档在断言里）。"""
    from adapters.sqlite.run_store import SqliteRunStore

    service, engine, runtime, clock, artifacts = _harness()
    try:
        store = SqliteRunStore(connection=engine._conn)
        run_id = ID.generate()

        task_id, attempts_at_death, statuses = _drive_to_a_real_dead_letter(service, engine, run_id)
        _assert_auto_path_refuses_before_recovery(engine, run_id, task_id, statuses)
        _assert_recovery_lands(engine, run_id, task_id)
        _finish_with_a_rebuilt_resume(service, clock, run_id, store, artifacts)

        final = _statuses(engine, run_id.value)
        assert ResearchTaskState.State.DEAD_LETTER not in final
        assert final.count(ResearchTaskState.State.SUCCEEDED) == len(final), final
        retried = _task_row(engine, run_id.value, task_id)
        assert retried.attempt > attempts_at_death, "恢复后的交付推进了尝试代次"
        kinds = [envelope.event_type for envelope in engine.pending_outbox()]
        assert EventType.TASK_RETRY_SCHEDULED in kinds
        assert runtime.execution_attempts == 2, "第一次失败 + 恢复后的第二次成功"
    finally:
        artifacts.close()
        engine.close()
