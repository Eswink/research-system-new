"""E2E：重启后的续跑（GOAL-003 cycle 20 / PLAN-20260915-083）。

cycle 18/19 的续跑上下文只活在进程内存里：探针
`scratch/goal3-cycle20-probe1-restart-loses-the-plan.py` 量出重启后
`has_paused_context=False`、`resume_paused` 抛 `InvalidInputError`、守护线程派发 0
——已到期的重排没有任何交付入口。

本轮把入口补上：run 行记下装配来源，重启后按来源重建上下文、按 idempotency key
重算剩余工作，再由 `resume_rebuilt` 真的交付。本文件用真实 SQLite + 替身 runtime
（全离线）跑完整回路，并钉住两件事：

1. **剩余工作重算正确**：已成功完成的任务不重跑，断点（重排中的任务）与它后面的
   工作才执行；
2. **重建不是放宽**：冻结 digest 不符 / 语义漂移一律拒绝。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

from adapters.sqlite.run_store import SqliteRunStore
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.application.ports.errors import TransientPortError
from packages.application.preflight.preflight import ManifestFreezeError
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.application.run_orchestration.commands import ResumeRunCommand
from packages.application.run_orchestration.context import RunContext
from packages.domain.core import ID, Digest
from packages.domain.enums import FailureCategory
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import RetryPolicy
from services.api.catalog import read_protocol_text
from services.api.protocol_source import parse_frozen_protocol
from tests.e2e.scenario import (
    PROTOCOL_PATH,
    StructuredOutputAgentRuntime,
    m7_protocol,
    seed_run_inputs,
)
from tests.e2e.scenario_catalog import m7_catalog, m7_preflight_context, m7_project
from tests.e2e.test_retry_park_and_resume import (
    BACKOFF_SECONDS,
    _catalog_with_backoff,
    _Clock,
    _harness,
    _start,
)

REVIEW_CONTRACT = "sort_analysis_review"
# 受控模板在 `examples/protocols/` 下的文件名（`read_protocol_text` 的入参口径）。
_PROTOCOL_FILE = PROTOCOL_PATH.removeprefix("examples/protocols/")


class _ReviewFlakyOnce(StructuredOutputAgentRuntime):
    """第一个任务正常完成；**第二个**任务第一次抛瞬态失败（模型超时）。

    用来验证"已成功的工作不重跑"：重建后只有第二个任务（attempt=2）该被执行。
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.contract_of: list[str] = []
        self.review_attempts = 0
        self._failed = False

    def run(self, session_id: str) -> AgentSessionResult:
        spec = self._specs.get(session_id)
        contract_id = spec.task_contract.id if spec is not None else ""
        self.contract_of.append(contract_id)
        if contract_id == REVIEW_CONTRACT:
            self.review_attempts += 1
            if not self._failed:
                self._failed = True
                raise TransientPortError(
                    "model timed out", failure_category=FailureCategory.MODEL_TIMEOUT
                )
        return super().run(session_id)


def _parked_run(
    run_id: ID,
    digests: tuple[str, str],
    *,
    source: ProtocolSource | None,
    body: ProtocolBody | None = None,
) -> ResearchRun:
    """控制面持久化后的那个 run：PAUSED + 冻结引用（digest + 语义 digest）+ 装配事实。

    GOAL-004 cycle 1：`body` 是被解析的那份协议正文（自足续跑的输入）。
    """
    digest, semantic = digests
    return ResearchRun(
        id=run_id,
        project_id="m7-project",
        protocol_id="sort_analysis_v1",
        state=ResearchRunState.State.PAUSED,
        manifest_digest=Digest.parse(digest),
        manifest_semantic_digest=Digest.parse(semantic),
        protocol_source=source,
        protocol_body=body,
    )


def _frozen_digests(run_id: ID, catalog: Any) -> tuple[str, str]:
    """按同一装配链算出冻结 digest 对（控制面在启动时持久化的就是这两个事实）。"""
    from packages.application.preflight.preflight import compile_and_preflight, freeze_manifest

    project = m7_project()
    preflight = m7_preflight_context(catalog, project)
    plan, report = compile_and_preflight(m7_protocol(), catalog, project, preflight)
    assert plan is not None and report.passed
    manifest = freeze_manifest(run_id.value, plan, report, preflight)
    return str(manifest.digest()), str(manifest.semantic_digest())


def _catalog_with_review_retry(*, backoff: int | None = BACKOFF_SECONDS) -> Any:
    """m7 目录 + 给**复核**契约声明重试策略（让断点落在第二个任务上）。"""
    catalog = m7_catalog()
    review = catalog.task_contracts[REVIEW_CONTRACT]
    retrying = replace(
        review,
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )
    return replace(catalog, task_contracts={**catalog.task_contracts, review.id: retrying})


def _restarted(
    service: RunOrchestrationService,
    artifacts: Any,
) -> RunOrchestrationService:
    """新进程：同一个 durable 世界，全新的编排服务（进程内暂存为空）。"""
    return RunOrchestrationService(
        OrchestrationDependencies(
            runtime=service._deps.runtime,
            workflow=service._deps.workflow,
            artifacts=artifacts,
            events=service._deps.events,
            budget=service._deps.budget,
        )
    )


def _rebuilt_context(run: ResearchRun, catalog: Any) -> RunContext:
    """按 durable 事实重建上下文（与 API 面 `rebuild_and_resume` 同一条装配链）。"""
    from packages.application.preflight.preflight import compile_and_preflight

    project = m7_project()
    preflight = m7_preflight_context(catalog, project)
    plan, report = compile_and_preflight(m7_protocol(), catalog, project, preflight)
    assert plan is not None and report.passed
    return RunContext(
        protocol=m7_protocol(),
        plan=plan,
        report=report,
        run=run,
        catalog=catalog,
        project=project,
        preflight=preflight,
        trace_id=f"api-resume-{run.id.value}",
    )


def _rebuilt_context_from_body(run: ResearchRun, catalog: Any, body: ProtocolBody) -> RunContext:
    """按 **run 行里的冻结正文**重建上下文（GOAL-004 cycle 1：不碰任何外部来源）。"""
    from packages.application.preflight.preflight import compile_and_preflight

    protocol = parse_frozen_protocol(body)
    project = m7_project()
    preflight = m7_preflight_context(catalog, project)
    plan, report = compile_and_preflight(protocol, catalog, project, preflight)
    assert plan is not None and report.passed
    return RunContext(
        protocol=protocol,
        plan=plan,
        report=report,
        run=run,
        catalog=catalog,
        project=project,
        preflight=preflight,
        trace_id=f"api-resume-{run.id.value}",
    )


def _resume_command(run: ResearchRun, *, digest: str | None = None) -> ResumeRunCommand:
    return ResumeRunCommand(
        run_id=run.id,
        frozen_manifest_digest=digest if digest is not None else str(run.manifest_digest),
        trace_id=f"api-resume-{run.id.value}",
    )


def test_a_rebuild_from_the_frozen_body_finishes_the_remaining_work() -> None:
    """冻结正文是重建的**充分输入**（GOAL-004 cycle 1）。

    与 cycle 20 的差别只有一处：上下文不是从进程内的 `m7_protocol()` 装配，而是从
    **canonical run 行里那份正文**（先写库、再从库里读回来）装配——外部协议来源在
    这里完全缺席（`source=None`），跑完与否只取决于 run 自己记得的字节。
    断点语义不变：已成功的任务不重跑，重排的任务走第二次尝试。
    """
    service, engine, runtime, artifacts, clock = _two_task_harness()
    catalog = _catalog_with_review_retry()
    store = SqliteRunStore(connection=engine._conn)
    try:
        run_id = ID.generate()
        parked = _start(service, catalog, run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        body = ProtocolBody.of(read_protocol_text(_PROTOCOL_FILE))
        assert parse_frozen_protocol(body) == m7_protocol(), "正文解出的定义与装配链同源"

        canonical = _parked_run(run_id, _frozen_digests(run_id, catalog), source=None, body=body)
        store.save_run(canonical)
        reloaded = store.get_run(run_id.value)
        assert reloaded.protocol_body == body, "重建的输入只能来自 canonical 行"

        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)
        restarted = _restarted(service, artifacts)
        resumed_run = reloaded.transition(ResearchRunState.Transition.RESUME)
        store.save_run(resumed_run)

        outcome = restarted.resume_rebuilt(
            _rebuilt_context_from_body(resumed_run, catalog, reloaded.protocol_body),
            _resume_command(resumed_run),
        )

        assert outcome.state == ResearchRunState.State.SUCCEEDED
        assert runtime.contract_of.count("sort_analysis_execution") == 1, "第一个任务不重跑"
        assert runtime.review_attempts == 2, "断点任务走第二次尝试"
    finally:
        artifacts.close()
        engine.close()


def test_a_restarted_process_finishes_a_parked_run_from_its_recorded_source() -> None:
    """停车 ⇒ 重启（新服务）⇒ 按来源重建 ⇒ 真跑完（不是"只解除暂停"）。"""
    service, engine, runtime, clock, artifacts = _harness()
    store = SqliteRunStore(connection=engine._conn)
    try:
        run_id = ID.generate()
        catalog = _catalog_with_backoff()
        parked = _start(service, catalog, run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        canonical = _parked_run(
            run_id,
            _frozen_digests(run_id, catalog),
            source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
        )
        store.save_run(canonical)

        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)

        restarted = _restarted(service, artifacts)
        assert restarted.has_paused_context(run_id.value) is False, "重启后没有进程内上下文"

        resumed_run = canonical.transition(ResearchRunState.Transition.RESUME)
        store.save_run(resumed_run)
        outcome = restarted.resume_rebuilt(
            _rebuilt_context(resumed_run, catalog),
            _resume_command(resumed_run),
        )

        assert outcome.state == ResearchRunState.State.SUCCEEDED
        assert runtime.execution_attempts == 2, "断点任务被再交付一次（attempt=2）"
        tasks = engine.list_tasks(run_id.value)
        assert [row.task.status for row in tasks] == ["SUCCEEDED", "SUCCEEDED"]
        assert tasks[0].task.attempt == 2, "重排的那次尝试真的被执行"

        # 控制面职责：续跑结果写回 canonical run（API 路由与守护线程各自都写，
        # 服务本身不持有 run store——本用例手写这一步以钉住"结局要落库"）。
        store.save_run(replace(resumed_run, state=outcome.state))
        assert store.get_run(run_id.value).state == ResearchRunState.State.SUCCEEDED
    finally:
        artifacts.close()
        engine.close()


def _two_task_harness() -> tuple[RunOrchestrationService, Any, _ReviewFlakyOnce, Any, _Clock]:
    """两个任务的 harness：第一个成功、第二个第一次失败并重排（用于"剩余工作重算"）。"""
    from adapters.sqlite.artifact_store import SqliteArtifactStore
    from adapters.sqlite.db import connect
    from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
    from adapters.sqlite.workflow_engine import SqliteWorkflowEngine

    clock = _Clock()
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=60, now=clock)
    artifacts = SqliteArtifactStore(connection=connection)
    seed_run_inputs(artifacts)  # GOAL-010 EC-02：协议声明的输入须在库（同生产组合根）
    runtime = _ReviewFlakyOnce(
        outputs_by_contract={
            "sort_analysis_execution": {"analysis_report": {"baseline": "O(n^2)"}},
            REVIEW_CONTRACT: {"review_decision": {"verdict": "PASS"}},
        }
    )
    service = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=runtime,
            workflow=engine,
            artifacts=artifacts,
            events=SqliteOutboxEventPublisher(connection=connection),
        )
    )
    return service, engine, runtime, artifacts, clock


def test_already_finished_work_is_not_delivered_again_after_a_rebuild() -> None:
    """剩余工作按 idempotency key 重算：已成功完成的任务不重跑。"""
    service, engine, runtime, artifacts, clock = _two_task_harness()
    catalog = _catalog_with_review_retry()
    try:
        run_id = ID.generate()
        parked = _start(service, catalog, run_id)
        assert parked.state == ResearchRunState.State.PAUSED
        assert runtime.review_attempts == 1, "第二个任务第一次失败并重排"
        canonical = _parked_run(
            run_id,
            _frozen_digests(run_id, catalog),
            source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
        )
        clock.value = clock.value + timedelta(seconds=BACKOFF_SECONDS)

        restarted = _restarted(service, artifacts)
        resumed_run = canonical.transition(ResearchRunState.Transition.RESUME)
        outcome = restarted.resume_rebuilt(
            _rebuilt_context(resumed_run, catalog), _resume_command(resumed_run)
        )

        assert outcome.state == ResearchRunState.State.SUCCEEDED
        assert runtime.contract_of.count("sort_analysis_execution") == 1, "第一个任务不重跑"
        assert runtime.review_attempts == 2, "第二个任务走第二次尝试"
        assert engine.task_identities(run_id.value) != ()
    finally:
        artifacts.close()
        engine.close()


def test_a_rebuild_rejects_a_frozen_digest_that_does_not_match() -> None:
    """重建不放宽：冻结 digest 不符 ⇒ 拒绝（不改状态、不执行）。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        catalog = _catalog_with_backoff()
        parked = _start(service, catalog, run_id)
        canonical = _parked_run(
            run_id,
            _frozen_digests(run_id, catalog),
            source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
        )
        restarted = _restarted(service, artifacts)

        try:
            restarted.resume_rebuilt(
                _rebuilt_context(canonical, catalog),
                _resume_command(canonical, digest="sha256:" + "0" * 64),
            )
            raise AssertionError("digest 不符必须拒绝")
        except ManifestFreezeError as exc:
            assert "manifest digest" in str(exc)
        assert runtime.execution_attempts == 1
        assert parked.state == ResearchRunState.State.PAUSED
    finally:
        artifacts.close()
        engine.close()


def test_a_drifted_catalog_is_rejected_by_the_semantic_check() -> None:
    """重建不放宽：目录漂移（语义 digest 变化）⇒ 拒绝。"""
    service, engine, runtime, _, artifacts = _harness()
    try:
        run_id = ID.generate()
        catalog = _catalog_with_backoff()
        _start(service, catalog, run_id)
        canonical = _parked_run(
            run_id,
            _frozen_digests(run_id, catalog),
            source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
        )
        drifted = replace(
            catalog,
            task_contracts={
                **catalog.task_contracts,
                "sort_analysis_review": replace(
                    catalog.task_contracts["sort_analysis_review"],
                    purpose="漂移后的用途描述",
                ),
            },
        )
        restarted = _restarted(service, artifacts)

        try:
            restarted.resume_rebuilt(
                _rebuilt_context(canonical, drifted), _resume_command(canonical)
            )
            raise AssertionError("语义漂移必须拒绝")
        except ManifestFreezeError as exc:
            assert "drifted" in str(exc) or "semantic" in str(exc)
        assert runtime.execution_attempts == 1, "拒绝之后一次都不执行"
    finally:
        artifacts.close()
        engine.close()
