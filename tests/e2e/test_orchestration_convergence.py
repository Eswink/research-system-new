"""M7 E2E：编排收敛守卫（budget release 幂等、lease 恢复触发、语义守卫）。"""

from __future__ import annotations

import pytest

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.run_orchestration.convergence import (
    assert_semantics_frozen,
    release_reservation,
)
from packages.application.preflight.preflight import ManifestFreezeError
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
    StartRunCommand,
)
from packages.domain.core import Digest, ID
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)


class TestBudgetReleaseConvergence:
    def test_release_reservation_is_idempotent(self) -> None:
        ledger = FakeBudgetLedger()
        ref = ledger.reserve((), m7_catalog().budget_policies["m7_budget"])
        refs = {"run-a": ref}
        release_reservation(refs, ledger, "run-a")
        release_reservation(refs, ledger, "run-a")  # 二次释放必须 no-op
        assert ledger.snapshot().reservations == ()
        assert refs == {}

    def test_release_reservation_safe_without_ledger(self) -> None:
        refs = {"run-a": "budget-reservation:x"}
        release_reservation(refs, None, "run-a")  # 无 ledger 时静默安全
        assert refs == {}


class TestLeaseRecoveryTrigger:
    def test_start_run_triggers_recover_expired_leases(self) -> None:
        """start_run 懒触发 lease 恢复（进程崩溃遗留的过期 lease 先收敛）。"""
        runtime = StructuredOutputAgentRuntime(
            structured_output={
                "analysis_report": {"baseline": "O(n^2)"},
                "review_decision": {"verdict": "PASS"},
            }
        )
        engine = FakeWorkflowEngine()
        harness = M7Harness(runtime=runtime)
        try:
            service = RunOrchestrationService(
                OrchestrationDependencies(
                    runtime=runtime,
                    workflow=engine,
                    artifacts=harness.artifacts,
                    events=harness.events,
                    budget=harness.budget,
                )
            )
            service.start_run(
                m7_protocol(),
                m7_catalog(),
                m7_project(),
                m7_preflight_context(m7_catalog(), m7_project()),
                StartRunCommand(
                    project_id="m7-project",
                    protocol_id="sort_analysis_v1",
                    run_id=ID.generate(),
                    trace_id="trace-recover",
                ),
            )
            assert engine.method_calls("recover_expired_leases") == 1
        finally:
            harness.close()


class TestSemanticGuard:
    def test_missing_semantic_digest_rejected(self) -> None:
        """旧快照（无语义 digest）恢复必须拒绝，不能静默放行。"""
        from packages.application import compile_and_preflight

        catalog = m7_catalog()
        project = m7_project()
        context = m7_preflight_context(catalog, project)
        plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
        assert plan is not None and report.passed
        with pytest.raises(ManifestFreezeError, match="semantic digest"):
            assert_semantics_frozen("run-x", None, plan, report, context)

    def test_non_passing_report_rejected(self) -> None:
        """非 PASS 的 preflight report 不得用于 resume 语义校验。"""
        from dataclasses import replace

        from packages.application import compile_and_preflight
        from packages.domain.protocols import PreflightStatus

        catalog = m7_catalog()
        project = m7_project()
        context = m7_preflight_context(catalog, project)
        plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
        assert plan is not None and report.passed
        digest = Digest.of_bytes(b"frozen")
        with pytest.raises(ManifestFreezeError, match="non-passing"):
            assert_semantics_frozen(
                "run-x",
                digest,
                plan,
                replace(report, status=PreflightStatus.WARN),
                context,
            )