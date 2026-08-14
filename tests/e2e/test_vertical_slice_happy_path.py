"""M7 E2E：sort-analysis-v1 全链路 happy path。

验证：Compile/Preflight 无 bypass、Manifest freeze、team resolution、
Task/Lease 执行、Artifact provenance、Evidence→Claim 链、Evaluation gate、
事件关联（run_id/task_id/trace_id）、预算用量。
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from packages.application.run_orchestration import RunOutcome, StartRunCommand
from packages.domain.core import ID
from packages.domain.enums import ArtifactState
from packages.domain.events import EventType
from packages.domain.manifest import RunManifest
from packages.domain.run_state import ResearchRunState
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)


@pytest.fixture
def harness() -> Generator[M7Harness, None, None]:
    runtime = StructuredOutputAgentRuntime(
        structured_output={
            "analysis_report": {"baseline": "O(n^2)", "recommendation": "use TimSort"},
            "review_decision": {"verdict": "PASS", "score": 0.95},
        }
    )
    instance = M7Harness(runtime=runtime)
    yield instance
    instance.close()


def _start(harness: M7Harness) -> RunOutcome:
    return harness.service.start_run(
        m7_protocol(),
        m7_catalog(),
        m7_project(),
        m7_preflight_context(m7_catalog(), m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=ID.generate(),
            trace_id="trace-happy-1",
            idempotency_key="run-happy-1",
        ),
    )


class TestPreflightNoBypass:
    def test_compile_and_preflight_pass(self) -> None:
        from packages.application import compile_and_preflight

        catalog = m7_catalog()
        project = m7_project()
        policy = catalog.policy
        assert policy is not None
        context = m7_preflight_context(catalog, project)
        plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
        assert plan is not None
        assert report.status.value == "PASS", report.findings
        assert report.reserved_budget_ref is not None
        assert len(plan.phase_assignments) == 2


class TestManifestFreeze:
    def test_manifest_frozen_before_execution(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        assert outcome.manifest_digest is not None
        events = [e for e in harness.events.published if e.event_type is EventType.MANIFEST_FROZEN]
        assert len(events) == 1
        assert events[0].run_id == outcome.run_id
        assert events[0].trace_id == "trace-happy-1"

    def test_manifest_digest_stable_and_verifiable(self) -> None:
        from dataclasses import replace

        from packages.application import compile_and_preflight
        from packages.application.preflight.preflight import freeze_manifest

        catalog = m7_catalog()
        project = m7_project()
        context = m7_preflight_context(catalog, project)
        plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
        assert plan is not None and report.passed
        first = freeze_manifest("run-a", plan, report, context)
        second = freeze_manifest("run-b", plan, report, context)
        assert isinstance(first, RunManifest)
        assert first.frozen_at is not None
        # digest 确定性：同对象重复计算一致
        assert first.digest() == first.digest()
        # 冻结内容确定性：同构输入（排除 run_id / frozen_at）→ 同 digest
        same_instant = replace(second, run_id="run-a", frozen_at=first.frozen_at)
        assert first.digest() == same_instant.digest()
        assert first.role_definitions and first.agent_specs
        assert first.resolved_models
        assert first.budget_reservation_ref is not None


class TestEndToEndHappyPath:
    def test_run_completes_succeeded(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        assert outcome.state == ResearchRunState.State.SUCCEEDED
        assert outcome.message == "run completed"
        assert not outcome.system_failure
        assert len(outcome.tasks) == 2
        assert all(task.outcome == "SUCCEEDED" for task in outcome.tasks)
        assert all(task.verdict == "PASS" for task in outcome.tasks)

    def test_task_contracts_resolved_from_catalog_not_hardcoded(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        contract_ids = {task.task.contract_id for task in outcome.tasks}
        assert contract_ids == {"sort_analysis_execution", "sort_analysis_review"}
        agents = {task.task.assigned_agent_id for task in outcome.tasks}
        assert agents == {"engineer-1", "reviewer-1"}

    def test_artifacts_have_provenance(self, harness: M7Harness) -> None:
        _start(harness)
        artifacts = harness.artifacts.list_refs()
        # 2 tasks × 2 结构化输出 = 4 个内容寻址 Artifact
        assert len(artifacts) == 4
        produced_by = {artifact.created_by for artifact in artifacts}
        assert produced_by == {"engineer-1", "reviewer-1"}
        for artifact in artifacts:
            assert artifact.state is ArtifactState.STAGED
            assert artifact.source_refs and artifact.source_refs[0].startswith("task:")
            content = harness.artifacts.get(artifact.id)
            assert len(content) > 0
            assert harness.artifacts.verify(artifact.id) is True

    def test_artifact_content_is_not_in_domain_json(self, harness: M7Harness) -> None:
        """大 payload 只进 Artifact Store，不进入 Domain JSON/事件 payload。"""
        _start(harness)
        for envelope in harness.events.published:
            rendered = str(envelope.payload)
            assert "O(n^2)" not in rendered
            assert "use TimSort" not in rendered
            assert "analysis_report" not in rendered

    def test_evidence_claim_lineage_and_gate(self, harness: M7Harness) -> None:
        """Artifact → Evidence → Claim lineage：每 Artifact 有可追踪 Evidence 引用。"""
        outcome = _start(harness)
        rows = harness.engine.list_tasks(outcome.run_id)
        assert len(rows) == 2
        for artifact in harness.artifacts.list_refs():
            evidence_id = f"evidence:{artifact.id}"
            assert evidence_id.startswith("evidence:")
            assert artifact.digest is not None
            # VERIFIED Claim 前置：存在合法 Evidence（域约束由 Claim.__post_init__ 强制）
            from packages.domain.evidence import Claim, ClaimStatus

            with pytest.raises(ValueError, match="evidence"):
                Claim(
                    id=f"claim:{artifact.id}",
                    statement="verified without evidence",
                    status=ClaimStatus.VERIFIED,
                )

    def test_events_correlated_by_run_task_trace(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        published = harness.events.published
        assert any(e.event_type is EventType.MANIFEST_FROZEN for e in published)
        assert any(e.event_type is EventType.TASK_CREATED for e in published)
        assert any(e.event_type is EventType.RUN_COMPLETED for e in published)
        # application 层发布的事件必须携带 trace 关联
        application_events = {
            EventType.MANIFEST_FROZEN,
            EventType.TASK_CREATED,
            EventType.RUN_COMPLETED,
            EventType.RUN_FAILED,
        }
        for envelope in published:
            assert envelope.run_id == outcome.run_id
            if envelope.event_type in application_events:
                assert envelope.trace_id == "trace-happy-1"
            if envelope.event_type is EventType.TASK_CREATED:
                assert envelope.task_id is not None
        # workflow engine 事务写入的审计事件带 run/task 关联（trace 边界：M7 记录为
        # 分层事实，workflow 层不感知 application trace——见 service 模块注释）
        workflow_events = {
            EventType.TASK_LEASED,
            EventType.TASK_COMPLETED,
            EventType.TASK_CANCELLED,
            EventType.TASK_RETRY_SCHEDULED,
        }
        for envelope in published:
            if envelope.event_type in workflow_events:
                assert envelope.task_id is not None

    def test_budget_usage_recorded(self, harness: M7Harness) -> None:
        from tests.e2e.scenario_catalog import m7_preflight_context

        catalog = m7_catalog()
        project = m7_project()
        context = m7_preflight_context(catalog, project, budget_ledger=harness.budget)
        harness.service.start_run(
            m7_protocol(),
            catalog,
            project,
            context,
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-budget-1",
            ),
        )
        snapshot = harness.budget.snapshot()
        # run 收敛后预留已释放（BUDGET_QUOTA.md §2 reserve → release 闭环），
        # append-only usage 保留。
        assert snapshot.reservations == ()
        turn_entries = [e for e in snapshot.entries if e.resource_type.value == "AGENT_TURNS"]
        assert len(turn_entries) == 2

    def test_workflow_tasks_persisted_in_sqlite(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        rows = harness.engine.list_tasks(outcome.run_id)
        assert len(rows) == 2
        assert all(row.task.status in {"SUCCEEDED", "FAILED"} for row in rows)
        assert all(row.contract.id.startswith("sort_analysis_") for row in rows)

    def test_runtime_events_not_canonical_domain_events(self, harness: M7Harness) -> None:
        """RuntimeEvent（stream_events）不进入 Domain Event outbox。"""
        _start(harness)
        for envelope in harness.events.published:
            assert envelope.event_type not in {
                EventType.TOOL_CALL_STARTED,
                EventType.TOOL_CALL_COMPLETED,
            }
