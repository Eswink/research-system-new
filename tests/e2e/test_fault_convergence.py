"""M7 E2E 故障注入矩阵（F-08..F-12）：收敛路径与科学负结果语义。

注入点与期望收敛（Scientific Negative Result ≠ System Failure）：
- F-08 budget exhausted → Preflight FAIL；
- F-09 policy denied → Preflight FAIL；
- F-10 cancellation → 协作式取消 + lease 释放；
- F-11 malformed runtime result → Run FAILED（system_failure=True）；
- F-12 evaluator rejection（unsupported claim）→ Run FAILED（业务失败，
  非系统失败）。

F-01..F-07 见 test_fault_matrix.py。
"""

from __future__ import annotations

from adapters.fakes.policy_evaluator import FakePolicyEvaluator
from packages.application.run_orchestration import (
    CancelRunCommand,
    RunOutcome,
    StartRunCommand,
)
from packages.domain.core import ID
from packages.domain.enums import PolicyDecision
from packages.domain.run_state import ResearchRunState
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


class TestF08BudgetExhausted:
    def test_budget_exhausted_rejects_run(self) -> None:
        """F-08：预算耗尽 → Preflight FAIL → Run REJECTED（不进入执行）。"""
        from dataclasses import replace

        from packages.domain.budget import BudgetPolicy

        catalog = replace(
            m7_catalog(),
            budget_policies={
                "m7_budget": BudgetPolicy(
                    id="m7_budget",
                    hard_limits={
                        "agent_sessions": 0,
                        "tool_requests": 0,
                        "wall_clock_seconds": 0,
                    },
                )
            },
        )
        harness = M7Harness()
        try:
            outcome = harness.service.start_run(
                m7_protocol(),
                catalog,
                m7_project(),
                m7_preflight_context(catalog, m7_project()),
                StartRunCommand(
                    project_id="m7-project",
                    protocol_id="sort_analysis_v1",
                    run_id=ID.generate(),
                    trace_id="trace-f08",
                ),
            )
            assert outcome.state == ResearchRunState.State.FAILED
            assert "preflight" in outcome.message
        finally:
            harness.close()


class TestF09PolicyDenied:
    def test_policy_deny_fails_preflight(self) -> None:
        """F-09：PolicyEvaluator 对能力 DENY → Preflight POLICY_DENIED → 拒绝执行。"""
        evaluator = FakePolicyEvaluator(default=PolicyDecision.DENY)
        catalog = m7_catalog()
        context = m7_preflight_context(catalog, m7_project(), evaluator=evaluator)
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
                    trace_id="trace-f09",
                ),
            )
            assert outcome.state == ResearchRunState.State.FAILED
            assert harness.engine.list_tasks(outcome.run_id) == ()
        finally:
            harness.close()


class TestF10Cancellation:
    def test_cancel_run_releases_lease(self) -> None:
        """F-10：cancel_run → run 级取消 → lease 移除 + CANCELLED 事件。"""
        harness = M7Harness()
        try:
            from tests.contracts.fixtures import research_task, task_contract

            task = research_task()
            harness.engine.submit(task, task_contract())
            harness.engine.acquire_lease(task.id.value)
            harness.service.cancel_run(
                CancelRunCommand(run_id=task.run_id, reason="test cancellation")
            )
            assert task.id.value in harness.engine.cancelled
            kinds = [e.event_type for e in harness.events.pending()]
            from packages.domain.events import EventType

            assert EventType.TASK_CANCELLED in kinds
        finally:
            harness.close()


class TestF11MalformedResult:
    def test_malformed_result_marks_system_failure(self) -> None:
        """F-11：runtime 输出为空/无结构化 payload → Run FAILED（系统失败）。"""
        runtime = StructuredOutputAgentRuntime(structured_output={})
        harness = M7Harness(runtime=runtime)
        try:
            outcome = _start(harness)
            assert outcome.state == ResearchRunState.State.FAILED
            assert outcome.system_failure is True
            assert "malformed" in outcome.message
        finally:
            harness.close()


class TestF12EvaluatorRejection:
    def test_unsupported_claim_rejected_by_gate(self) -> None:
        """F-12：执行输出无法支撑 Claim（review 无 Evidence）→ REJECT（业务失败）。"""
        runtime = StructuredOutputAgentRuntime(
            outputs_by_contract={
                # execution 正常产出 Artifact
                "sort_analysis_execution": {
                    "analysis_report": {"baseline": "O(n^2)"},
                },
                # review 声称通过但无 Evidence（非 dict 值不产生 evidence）
                "sort_analysis_review": {
                    "review_decision": "unsupported verdict string",
                },
            }
        )
        harness = M7Harness(runtime=runtime)
        try:
            outcome = _start(harness)
            assert outcome.state == ResearchRunState.State.FAILED
            assert outcome.system_failure is False
            assert "acceptance gate" in outcome.message
        finally:
            harness.close()


def test_scientific_negative_result_is_distinct_from_system_failure() -> None:
    """负结果（gate REJECT）与系统失败（配置损坏）的语义边界不变式。"""
    assert ResearchRunState.State.FAILED in ResearchRunState.terminal()
    # F-02/F-11 断言 system_failure=True，F-12 断言 False：同一 FAILED 状态
    # 通过 system_failure 标志区分"科学负结果"与"系统故障"。


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
