"""M7 E2E 故障注入矩阵（F-01..F-07）：model 失败、workspace、lease、重复投递。

注入点与期望收敛（Scientific Negative Result ≠ System Failure）：
- F-01 model timeout（retryable）→ 重试成功；
- F-02 model permanent failure → FAILED 不重试；
- F-05 workspace failure → Preflight FAIL；
- F-06 lease 过期 → 重排队；
- F-07 重复投递 → 幂等去重。

F-08..F-12（budget/policy/cancel/malformed/evaluator rejection）见
test_fault_convergence.py。F-03/F-04（ToolProvider failure/timeout）：
编排层链路经 FakeAgentRuntime，不经过 ToolProvider Port；该注入面由
tests/contracts（FakeToolProvider execute 错误注入）与 M6
PolicyWrappedToolExecutor 测试覆盖，此处不伪造不可达的注入点。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from packages.application.ports.errors import (
    PermanentPortError,
    PortTimeoutError,
)
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
)
from packages.application.run_orchestration import (
    RunOutcome,
    StartRunCommand,
)
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import RetryPolicy
from tests.e2e.scenario import (
    M7Harness,
    StructuredOutputAgentRuntime,
    m7_protocol,
)
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)


def _start(harness: M7Harness, trace_id: str = "trace-fault") -> RunOutcome:
    return harness.service.start_run(
        m7_protocol(),
        m7_catalog(),
        m7_project(),
        m7_preflight_context(m7_catalog(), m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=ID.generate(),
            trace_id=trace_id,
        ),
    )


class TestF01ModelTimeoutRetries:
    def _retryable_catalog(self) -> CatalogSnapshot:
        """execution contract 声明 MODEL_TIMEOUT 可重试（max_attempts=2）。"""
        from dataclasses import replace

        catalog = m7_catalog()
        contract = catalog.task_contracts["sort_analysis_execution"]
        return replace(
            catalog,
            task_contracts={
                **dict(catalog.task_contracts),
                "sort_analysis_execution": replace(
                    contract,
                    retry_policy=RetryPolicy(
                        max_attempts=2,
                        retryable_categories=[FailureCategory.MODEL_TIMEOUT],
                    ),
                ),
            },
        )

    def _start_with(self, harness: M7Harness, catalog: CatalogSnapshot) -> RunOutcome:
        return harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-f01",
            ),
        )

    def test_transient_model_failure_retries_then_succeeds(self) -> None:
        """F-01：run 注入一次 transient（MODEL_TIMEOUT）→ 重试成功。"""
        runtime = StructuredOutputAgentRuntime(
            structured_output={
                "analysis_report": {"baseline": "O(n^2)"},
                "review_decision": {"verdict": "PASS"},
            }
        )
        runtime.set_script(
            "run",
            [PortTimeoutError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)],
        )
        harness = M7Harness(runtime=runtime)
        try:
            outcome = self._start_with(harness, self._retryable_catalog())
            assert outcome.state == ResearchRunState.State.SUCCEEDED
            succeeded = [t for t in outcome.tasks if t.outcome == "SUCCEEDED"]
            assert len(succeeded) == 2
        finally:
            harness.close()

    def test_non_retryable_category_does_not_retry(self) -> None:
        """F-01b：TOOL_UNAVAILABLE 不在 retryable_categories → 直接失败。"""
        runtime = StructuredOutputAgentRuntime()
        runtime.set_script(
            "run",
            [PortTimeoutError("tool hung", failure_category=FailureCategory.TOOL_UNAVAILABLE)],
        )
        harness = M7Harness(runtime=runtime)
        try:
            outcome = self._start_with(harness, self._retryable_catalog())
            assert outcome.state == ResearchRunState.State.FAILED
        finally:
            harness.close()


class TestF02PermanentFailureNoRetry:
    def test_permanent_model_failure_marks_run_failed(self) -> None:
        """F-02：permanent 失败不重试（retry boundary）。"""
        runtime = StructuredOutputAgentRuntime()
        runtime.set_script(
            "run",
            [PermanentPortError("config broken", failure_category=FailureCategory.CONFIGURATION)],
        )
        harness = M7Harness(runtime=runtime)
        try:
            outcome = _start(harness)
            assert outcome.state == ResearchRunState.State.FAILED
            assert outcome.system_failure is True
            assert outcome.message.startswith("task")
        finally:
            harness.close()


class TestF05WorkspaceFailure:
    def test_workspace_unavailable_fails_preflight(self) -> None:
        """F-05：workspace 分配不可用 → Preflight FAIL → 不进入执行。"""
        from dataclasses import replace

        catalog = m7_catalog()
        context = replace(
            m7_preflight_context(catalog, m7_project()),
            workspace_available={"sandbox": False},
        )
        harness = M7Harness()
        try:
            outcome = harness.service.start_run(
                m7_protocol(),
                catalog,
                m7_project(),
                context,
                StartRunCommand(
                    project_id="m7-project",
                    protocol_id="sort_analysis_v1",
                    run_id=ID.generate(),
                    trace_id="trace-f05",
                ),
            )
            assert outcome.state == ResearchRunState.State.FAILED
            assert harness.engine.list_tasks(outcome.run_id) == ()
        finally:
            harness.close()


class TestF06LeaseExpiry:
    def test_expired_lease_requeues_task(self) -> None:
        """F-06：lease 过期 → recover → 重排队 → 二次 acquire。"""
        start = datetime(2026, 8, 13, 10, 0, 0, tzinfo=timezone.utc)
        clock = {"now": start}
        harness = M7Harness()
        # 引擎使用注入时钟重建（harness 的 engine 默认时钟）；直接驱动 sqlite 引擎
        harness.close()
        from adapters.sqlite.workflow_engine import SqliteWorkflowEngine

        engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=lambda: clock["now"])
        from tests.contracts.fixtures import research_task, task_contract

        task = research_task()
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
        clock["now"] = start + timedelta(seconds=120)
        assert engine.recover_expired_leases() == 1
        rows = engine.list_tasks(task.run_id.value)
        assert rows[0].task.status == "QUEUED"
        lease = engine.acquire_lease(task.id.value)
        assert lease.task_id == task.id.value
        engine.close()


class TestF07DuplicateDelivery:
    def test_duplicate_submit_is_silent(self) -> None:
        """F-07：同 idempotency_key 重复投递 → 幂等去重，deliveries=1。"""
        harness = M7Harness()
        try:
            engine = harness.engine
            from tests.contracts.fixtures import research_task, task_contract

            task = research_task()
            engine.submit(task, task_contract())
            engine.submit(task, task_contract("hijacked"))
            engine.acquire_lease(task.id.value)
            engine.acquire_lease(task.id.value)
            assert engine.deliveries[task.idempotency_key or ""] == 1
            assert len(engine.list_tasks(task.run_id.value)) == 1
        finally:
            harness.close()
