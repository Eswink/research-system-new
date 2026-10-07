"""E2E（EC-03）：**研究连续性的覆盖度矩阵** —— `rebuild_and_resume` 处理什么、不处理什么。

GOAL-20261007-032 建档勘察把覆盖度逐条量成事实（见该 GOAL「事实层结论」第 3 条）。
本文件把那些**事实**变成判据（每条都能被按压判红），并补上一条既有判据没有的形态：

| 情形 | 判定 | 本文件怎么判 |
| --- | --- | --- |
| run 级重建（有冻结正文 ⇒ 自包含） | **处理** | ① 见既有判据（`test_restart_rebuild_resume.py`） |
| 无冻结正文 ⇒ 依赖来源仍可解析 | **处理** | ① 同上 |
| preflight 不过 / 语义漂移 ⇒ 拒绝 | **处理（点名拒绝）** | ① 同上 |
| 重启后未完成（重排到期 ⇒ 自动派发） | **处理** | ② 守护线程 pass 真跑到终态 |
| 租约过期 | **处理**（任务级，非本入口） | ③ `recover_expired_leases` ⇒ `QUEUED` |
| **死信任务** | **不处理**（点名拒绝） | ④ 续跑路径上 `acquire_lease` 拒绝它 |
| 已成功任务 | **不重跑**（幂等） | ⑤ 重建前后 attempt 与契约交付数不变 |

**为什么单独写**：既有的 `test_restart_rebuild_resume.py` 判的是「重建这条路走得通」；
本文件判的是「**覆盖度的边界在哪**」—— 把「不处理」的形态（死信）与「不重跑」的形态
（幂等计数）**都变成实测读数**，而不是留在散文里。二者互补，不是重复。
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from services.api.scheduler import RetryDispatchDeps, RetryDispatchScheduler
from tests.e2e.test_restart_rebuild_resume import (
    _frozen_digests,
    _parked_run,
    _rebuilt_context,
    _restarted,
    _resume_command,
)
from tests.e2e.test_retry_park_and_resume import (
    BACKOFF_SECONDS,
    _catalog_with_backoff,
    _harness,
    _start,
)


def _run_store(engine: SqliteWorkflowEngine) -> SqliteRunStore:
    return SqliteRunStore(connection=engine._conn)


def _statuses(engine: SqliteWorkflowEngine, run_id: ID) -> list[str]:
    return [str(row.task.status) for row in engine.list_tasks(run_id.value)]


def test_a_parked_run_is_actually_finished_by_the_retry_dispatch_pass() -> None:
    """**覆盖 ②（重启后重排到期的自动派发）**：守护线程的一轮 pass **真的续跑到终态**。

    与既有判据（`test_restart_rebuild_resume.py` 直接调 `resume_rebuilt`）的差别：
    本用例走**守护线程的入口**（`RetryDispatchScheduler`）—— 判的是**调度侧**的
    「到期判定 → 派发 → 结果写回 canonical」这条产品路径成立。

    **接线边界（如实写明）**：本文件用「durable 行重建上下文 → `resume_rebuilt`」两步
    接守护线程的 `rebuild` 面（与 `services/api/app.py` 的 `_rebuild` 同形）；`run_resume`
    的**来源解析层**（冻结正文 / 路径 / 草稿）需要完整 `ApiDeps`，由
    `tests/api/test_run_source_and_rebuild_api.py` 覆盖（本文件不重复）。
    """
    service, engine, runtime, clock, artifacts = _harness()
    try:
        store, run_id = _run_store(engine), ID.generate()
        catalog = _catalog_with_backoff()
        parked = _start(service, catalog, run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        # run 行必须记下装配来源（守护线程的 _can_rebuild 读的就是它）
        store.save_run(
            _parked_run(
                run_id,
                _frozen_digests(run_id, catalog),
                source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
            )
        )

        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
        restarted = _restarted(service, artifacts)

        from services.api.run_resume import ResumeAttempt

        def _rebuild(run: Any) -> Any:
            """守护线程的 rebuild 面：durable 行重建上下文 → `resume_rebuilt`（两步同序）。"""
            context = _rebuilt_context(run, catalog)
            return ResumeAttempt(outcome=restarted.resume_rebuilt(context, _resume_command(run)))

        scheduler = RetryDispatchScheduler(
            RetryDispatchDeps(runs=restarted, runs_store=store, workflow=engine, rebuild=_rebuild),
            interval_seconds=15.0,
        )
        dispatched = scheduler.run_once()

        assert dispatched == 1, f"到期的停车 run 必须被派发一次（实测 {dispatched}）"
        assert _statuses(engine, run_id) == ["SUCCEEDED", "SUCCEEDED"], "跑到终态"
        assert runtime.execution_attempts == 2, "第一次失败 + 第二次成功"
        assert store.get_run(run_id.value).state == ResearchRunState.State.SUCCEEDED
    finally:
        artifacts.close()
        engine.close()


def test_an_expired_lease_is_recovered_to_queued_and_redeliverable() -> None:
    """**覆盖 ③（租约过期）**：任务级恢复 ⇒ `QUEUED` ⇒ 可再交付（不属 `rebuild_and_resume`）。"""
    service, engine, runtime, clock, artifacts = _harness()
    try:
        run_id = ID.generate()
        task_id = _start_lease(engine, run_id)
        before = dict(engine.deliveries)

        clock.value = clock.value + timedelta(seconds=10_000)  # 越过 lease TTL（60s）
        recovered = engine.recover_expired_leases()

        assert recovered == 1, f"过期租约必须被回收（实测 {recovered}）"
        assert _statuses(engine, run_id) == [ResearchTaskState.State.QUEUED]
        again = engine.acquire_lease(task_id)
        assert again.task_id == task_id, "回收后必须能再次交付"
        assert sum(engine.deliveries.values()) >= sum(before.values()), "往返不消耗事实"
    finally:
        artifacts.close()
        engine.close()


def _start_lease(engine: SqliteWorkflowEngine, run_id: ID) -> str:
    """造一条已租约的 EXECUTION 任务（不经编排：本用例只判租约面）。"""
    from packages.application.ports.workflow_engine import ClaimRequest
    from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
    from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

    task = ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )
    contract = TaskContract(
        id="continuity-contract",
        version="1.0",
        purpose="lease recovery coverage",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=2, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )
    engine.submit(task, contract)
    engine.acquire_lease(task.id.value)
    assert (
        ClaimRequest(worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0}))
        is not None
    )
    return task.id.value


def test_a_dead_letter_is_not_recovered_by_the_resume_path() -> None:
    """**不覆盖 ④（死信）**：续跑路径上的自动交付入口对死信任务**点名拒绝**。

    这是 EC-03 与 EC-01 的交界：死信的出路是**人工恢复**（ADR-0033），
    **不是** run 级续跑自己会捞它。判据打的是续跑最终必经的那一关（`acquire_lease`）。
    """
    service, engine, runtime, clock, artifacts = _harness()
    try:
        from tests.e2e.test_dead_letter_recovery_full_loop import (
            _catalog_dead_letter_on_first_failure,
        )

        run_id = ID.generate()
        first = _start(service, _catalog_dead_letter_on_first_failure(), run_id)
        assert first.state == ResearchRunState.State.FAILED
        dead = next(
            row.task
            for row in engine.list_tasks(run_id.value)
            if row.task.status == ResearchTaskState.State.DEAD_LETTER
        )

        with pytest.raises(InvalidInputError) as refused:
            engine.acquire_lease(dead.id.value)
        assert "terminal" in str(refused.value), "续跑路径不捞死信（必须点名拒绝）"
        # 人工恢复之后才可交付（EC-01 的路径）
        assert engine.requeue(dead.id.value) == "restored"
        assert engine.acquire_lease(dead.id.value).task_id == dead.id.value
    finally:
        artifacts.close()
        engine.close()


def test_a_rebuild_does_not_deliver_already_finished_work() -> None:
    """**不重跑 ⑤（幂等）**：重建续跑前后，**已成功任务**的交付次数**不变**。

    与既有 `test_already_finished_work_is_not_delivered_again_after_a_rebuild` 的差别：
    本用例把「不重跑」量成 **deliveries 计数**（不是只看最终状态）—— 计数不增才是
    「零第二次副作用」的直接读数。
    """
    from tests.e2e.test_restart_rebuild_resume import _catalog_with_review_retry, _two_task_harness

    service, engine, runtime, artifacts, clock = _two_task_harness()
    try:
        store, run_id = _run_store(engine), ID.generate()
        catalog = _catalog_with_review_retry()
        parked = _start(service, catalog, run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        # 第一个任务已成功、第二个在重排 ⇒ 断点在第二个
        tasks_before = engine.list_tasks(run_id.value)
        succeeded_before = [
            r.task.id.value
            for r in tasks_before
            if (r.task.status == ResearchTaskState.State.SUCCEEDED)
        ]
        assert len(succeeded_before) == 1, "前置：恰好一条已完成"

        store.save_run(_parked_run(run_id, _frozen_digests(run_id, catalog), source=None))
        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
        restarted = _restarted(service, artifacts)
        resumed = store.get_run(run_id.value).transition(ResearchRunState.Transition.RESUME)
        store.save_run(resumed)
        outcome = restarted.resume_rebuilt(
            _rebuilt_context(resumed, catalog), _resume_command(resumed)
        )

        assert outcome.state == ResearchRunState.State.SUCCEEDED
        # 已成功的那个任务**没有被再交付**：它的完成记录仍在、attempt 未前进
        after = {r.task.id.value: r.task for r in engine.list_tasks(run_id.value)}
        for task_id in succeeded_before:
            assert after[task_id].status == ResearchTaskState.State.SUCCEEDED
            assert after[task_id].attempt == 1, "已完成任务不得被再交付（attempt 不动）"
        assert runtime.contract_of.count("sort_analysis_execution") == 1, "第一个契约只交付一次"
    finally:
        artifacts.close()
        engine.close()
