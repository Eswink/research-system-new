"""E2E：声明了退避的重排，在 run 级**真的**会发生（PLAN-20260915-081）。

收口前：任务失败 ⇒ run FAILED（终态），durable 侧那条 `RETRY_SCHEDULED` 再没有派发方
会来取——声明了退避的重排变成孤儿（RECHECK-20260915-080 W-1）。实测同一场景：
`phase runner 返回 = FAILED` / `on_pause 拿到的 specs = 0` / `RESUME = InvalidTransitionError`。

收口后：run 停在 PAUSED（失败的任务与后续 specs 一起交回 service 暂存），
deadline 之前 resume 只是**重新停车**（不破坏 run），到期后 resume 续跑会真的执行
第二次尝试，run 跑完。

全离线：SQLite `:memory:` + 替身 runtime，不依赖真实 LLM/网络/凭据（AGENTS.md §11）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.application.ports.errors import TransientPortError
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
    StartRunCommand,
)
from packages.domain.core import ID, Digest
from packages.domain.enums import FailureCategory
from packages.domain.events import EventType
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import RetryPolicy
from tests.e2e.scenario import StructuredOutputAgentRuntime, m7_protocol, seed_run_inputs
from tests.e2e.scenario_catalog import m7_catalog, m7_preflight_context, m7_project

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)
BACKOFF_SECONDS = 3600
OUTPUTS: dict[str, dict[str, object]] = {
    "sort_analysis_execution": {"analysis_report": {"baseline": "O(n^2)"}},
    "sort_analysis_review": {"review_decision": {"verdict": "PASS"}},
}


@dataclass(slots=True)
class _Clock:
    value: datetime = START

    def __call__(self) -> datetime:
        return self.value


class _FlakyOnce(StructuredOutputAgentRuntime):
    """第一次 run 抛瞬态失败（模型超时），之后按父类正常产出结构化输出。

    只数**执行契约**的尝试次数：同一个 runtime 还驱动 review 任务（那边一次就过），
    数全部 run 会把"另一个任务正常跑了一次"也算成重试。
    """

    EXECUTION_CONTRACT = "sort_analysis_execution"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.execution_attempts = 0
        self._failed = False

    def run(self, session_id: str) -> AgentSessionResult:
        spec = self._specs.get(session_id)
        if spec is not None and spec.task_contract.id == self.EXECUTION_CONTRACT:
            self.execution_attempts += 1
        if not self._failed:
            self._failed = True
            raise TransientPortError(
                "model timed out", failure_category=FailureCategory.MODEL_TIMEOUT
            )
        return super().run(session_id)


def _harness() -> tuple[
    RunOrchestrationService, SqliteWorkflowEngine, _FlakyOnce, _Clock, SqliteArtifactStore
]:
    clock = _Clock()
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=60, now=clock)
    artifacts = SqliteArtifactStore(connection=connection)
    seed_run_inputs(artifacts)  # GOAL-010 EC-02：协议声明的输入须在库（同生产组合根）
    events = SqliteOutboxEventPublisher(connection=connection)
    runtime = _FlakyOnce(outputs_by_contract=OUTPUTS)
    service = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=runtime,
            workflow=engine,
            artifacts=artifacts,
            events=events,
            budget=FakeBudgetLedger(),
        )
    )
    return service, engine, runtime, clock, artifacts


def _catalog_with_retry(*, backoff: int | None) -> Any:
    """m7 目录 + 给执行契约声明重试策略（其余字段不动）。"""
    catalog = m7_catalog()
    execution = catalog.task_contracts["sort_analysis_execution"]
    retrying = replace(
        execution,
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )
    return replace(catalog, task_contracts={**catalog.task_contracts, execution.id: retrying})


def _catalog_with_backoff() -> Any:
    return _catalog_with_retry(backoff=BACKOFF_SECONDS)


def _canonical(run_id: ID, digest: str) -> ResearchRun:
    """控制面持久化后的那个 run（PAUSED + 冻结 manifest 引用，与 API 面一致）。"""
    return ResearchRun(
        id=run_id,
        project_id="m7-project",
        protocol_id="sort_analysis_v1",
        state=ResearchRunState.State.PAUSED,
        manifest_digest=Digest.parse(digest),
    )


def _start(service: RunOrchestrationService, catalog: Any, run_id: ID) -> Any:
    return service.start_run(
        m7_protocol(),
        catalog,
        m7_project(),
        m7_preflight_context(catalog, m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=run_id,
            trace_id="trace-retry",
        ),
    )


def test_a_declared_backoff_parks_the_run_instead_of_failing_it() -> None:
    """瞬态失败 + 声明退避：run 停 PAUSED（不是 FAILED），任务落 RETRY_SCHEDULED。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        outcome = _start(service, _catalog_with_backoff(), run_id)

        assert outcome.state == ResearchRunState.State.PAUSED, "run 不该在重排未到期时判失败"
        assert runtime.execution_attempts == 1
        task = engine.list_tasks(run_id.value)[0].task
        assert (task.status, task.attempt) == ("RETRY_SCHEDULED", 1)
        kinds = [envelope.event_type for envelope in engine.pending_outbox()]
        assert EventType.TASK_RETRY_SCHEDULED in kinds, "重排必须留下事件（带 deadline）"
        assert EventType.RUN_FAILED not in kinds, "停车不是 run 失败"
        assert service.has_paused_context(run_id.value) is True
    finally:
        artifacts.close()
        engine.close()


def test_resuming_before_the_deadline_parks_again_without_executing() -> None:
    """没到期就 resume：重新停车，一次都不执行（不破坏 run，也不提前重试）。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        parked = _start(service, _catalog_with_backoff(), run_id)
        assert parked.manifest_digest is not None

        again = service.resume_paused(run_id.value, _canonical(run_id, parked.manifest_digest))

        assert again.state == ResearchRunState.State.PAUSED
        assert runtime.execution_attempts == 1, "deadline 之前不得交付（durable 的 acquire 守卫）"
        assert service.has_paused_context(run_id.value) is True, "还能再次 resume"
    finally:
        artifacts.close()
        engine.close()


def test_resume_after_the_deadline_really_retries_and_the_run_completes() -> None:
    """到期后 resume：第二次尝试真的执行，后续 phase 一起跑完，run SUCCEEDED。"""
    service, engine, runtime, clock, artifacts = _harness()
    try:
        run_id = ID.generate()
        parked = _start(service, _catalog_with_backoff(), run_id)
        assert parked.manifest_digest is not None

        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
        # 不调用 recover_expired_leases：失败完成时租约已被释放，重派不该依赖那次清扫。
        done = service.resume_paused(run_id.value, _canonical(run_id, parked.manifest_digest))

        assert done.state == ResearchRunState.State.SUCCEEDED
        assert runtime.execution_attempts == 2, "第一次失败 + 第二次成功"
        tasks = engine.list_tasks(run_id.value)
        assert [entry.task.status for entry in tasks] == ["SUCCEEDED", "SUCCEEDED"]
        assert tasks[0].task.attempt == 2, "第二次尝试用的是交付代次（attempt=2）"
    finally:
        artifacts.close()
        engine.close()


def test_without_a_retry_policy_a_transient_failure_still_fails_the_run() -> None:
    """对照组：没有重试策略 ⇒ 任务 FAILED、run FAILED（既有语义不变）。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        outcome = _start(service, m7_catalog(), run_id)

        assert outcome.state == ResearchRunState.State.FAILED
        assert runtime.execution_attempts == 1
        assert engine.list_tasks(run_id.value)[0].task.status == "FAILED"
        assert service.has_paused_context(run_id.value) is False
    finally:
        artifacts.close()
        engine.close()


def test_without_a_backoff_the_retry_still_happens_inside_the_same_call() -> None:
    """对照组：声明了重试但**没有**退避 ⇒ 同一次调用里继续第二次尝试（cycle 17 语义）。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        outcome = _start(service, _catalog_with_retry(backoff=None), run_id)

        assert outcome.state == ResearchRunState.State.SUCCEEDED
        assert runtime.execution_attempts == 2, "失败后立刻在同一次调用里重试，不需要派发方"
        assert engine.list_tasks(run_id.value)[0].task.attempt == 2
    finally:
        artifacts.close()
        engine.close()
