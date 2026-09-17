"""E2E：停车中的 run 由**守护线程**自动续跑（GOAL-003 cycle 19 / PLAN-20260915-082）。

cycle 18 交付了"停车 + 有人按 resume 就能真的跑完"，但没有人自动按：探针实测
`claim_next = None`（worker 只派发 EXECUTION）、`recover_expired_leases = 0`，
停车中的 run 一直停着。本轮把那个派发方补上：`RetryDispatchScheduler` 扫到期的停车
run 并续跑。

本用例跑完整回路（真 SQLite + 真 run store + 注入时钟，全离线）：

    瞬态失败 ⇒ run 停 PAUSED ⇒ 时钟推过 retry_at ⇒ 守护线程一次 pass
    ⇒ 第二次尝试真的执行 ⇒ run SUCCEEDED 且写回 canonical run
"""

from __future__ import annotations

from datetime import timedelta

from adapters.sqlite.run_store import SqliteRunStore
from packages.domain.core import ID, Digest
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.scheduler import RetryDispatchDeps, RetryDispatchScheduler
from tests.e2e.test_retry_park_and_resume import (
    BACKOFF_SECONDS,
    _catalog_with_backoff,
    _harness,
    _start,
)


def _dispatcher(service: object, store: SqliteRunStore, engine: object) -> RetryDispatchScheduler:
    return RetryDispatchScheduler(
        RetryDispatchDeps(runs=service, runs_store=store, workflow=engine)
    )


def test_the_dispatcher_finishes_a_parked_run_without_a_human() -> None:
    service, engine, runtime, clock, artifacts = _harness()
    store = SqliteRunStore(connection=engine._conn)
    try:
        run_id = ID.generate()
        parked = _start(service, _catalog_with_backoff(), run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        assert parked.manifest_digest is not None
        store.save_run(
            ResearchRun(
                id=run_id,
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                state=ResearchRunState.State.PAUSED,
                manifest_digest=Digest.parse(parked.manifest_digest),
            )
        )
        dispatcher = _dispatcher(service, store, engine)

        assert dispatcher._execute_pass() == 0, "还没到期 ⇒ 一次都不派发"
        assert runtime.execution_attempts == 1

        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
        assert dispatcher._execute_pass() == 1, "到期 ⇒ 派发一次"

        assert runtime.execution_attempts == 2, "第二次尝试真的被执行"
        saved = store.get_run(run_id.value)
        assert saved.state == ResearchRunState.State.SUCCEEDED, "canonical run 要跟着续跑更新"
        assert [entry.task.status for entry in engine.list_tasks(run_id.value)] == [
            "SUCCEEDED",
            "SUCCEEDED",
        ]
        assert dispatcher._execute_pass() == 0, "跑完之后没有可派发的了（幂等）"
    finally:
        artifacts.close()
        engine.close()


def test_without_a_local_context_the_dispatcher_refuses_to_fake_a_resume() -> None:
    """进程重启后（本进程没有续跑上下文）⇒ 不派发、不改状态，如实留着等人工。"""
    service, engine, runtime, clock, artifacts = _harness()
    store = SqliteRunStore(connection=engine._conn)
    try:
        run_id = ID.generate()
        parked = _start(service, _catalog_with_backoff(), run_id)
        assert parked.manifest_digest is not None
        store.save_run(
            ResearchRun(
                id=run_id,
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                state=ResearchRunState.State.PAUSED,
                manifest_digest=Digest.parse(parked.manifest_digest),
            )
        )
        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)

        from packages.application.run_orchestration import OrchestrationDependencies
        from packages.application.run_orchestration.service import RunOrchestrationService

        restarted = RunOrchestrationService(
            OrchestrationDependencies(
                runtime=runtime,
                workflow=engine,
                artifacts=artifacts,
                events=service._deps.events,
            )
        )
        assert restarted.has_paused_context(run_id.value) is False

        assert _dispatcher(restarted, store, engine)._execute_pass() == 0
        assert store.get_run(run_id.value).state == ResearchRunState.State.PAUSED
        assert runtime.execution_attempts == 1, "没有上下文就不该偷偷跑第二次尝试"
    finally:
        artifacts.close()
        engine.close()
