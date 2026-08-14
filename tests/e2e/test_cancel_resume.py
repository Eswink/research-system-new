"""M7 E2E：Cancel / Pause / Resume。

- Cancel：workflow 层 lease 移除 + CANCELLED 事件（协作式，M5 D2）；
- Pause/Resume：resume 必须使用原 RunManifest frozen semantics；
  manifest digest 与冻结快照不一致 → 拒绝恢复（AGENTS.md §5）。
- M7 恢复边界声明：sync 语义下 resume 在任务边界进行；进程内 run() 阻塞
  期间的恢复属 Temporal 阶段（见 WORKFLOW_RELIABILITY.md 边界）。
"""

from __future__ import annotations

from typing import TypedDict

import pytest

from packages.application.ports.resource_catalog import CatalogSnapshot, PreflightContext
from packages.application.run_orchestration import (
    CancelRunCommand,
    ResumeRunCommand,
    RunContext,
    SessionSpec,
)
from packages.domain.core import ID, Digest
from packages.domain.events import EventType
from packages.domain.manifest import RunManifest
from packages.domain.protocols import CompiledRunPlan, PreflightReport
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)


class DriftParts(TypedDict):
    """漂移 catalog 重新编译后的 plan/report/context 组合。"""

    plan: CompiledRunPlan
    report: PreflightReport
    catalog: CatalogSnapshot
    context: PreflightContext


class TestCancel:
    def test_cancel_after_submit_marks_task_cancelled(self) -> None:
        harness = M7Harness()
        try:
            from tests.contracts.fixtures import research_task, task_contract

            task = research_task()
            harness.engine.submit(task, task_contract())
            lease = harness.engine.acquire_lease(task.id.value)
            assert lease.task_id == task.id.value
            harness.service.cancel_run(CancelRunCommand(run_id=task.id, reason="stop"))
            assert task.id.value in harness.engine.cancelled
            kinds = [e.event_type for e in harness.events.pending()]
            assert EventType.TASK_CANCELLED in kinds
        finally:
            harness.close()

    def test_double_cancel_is_idempotent(self) -> None:
        harness = M7Harness()
        try:
            from tests.contracts.fixtures import research_task, task_contract

            task = research_task()
            harness.engine.submit(task, task_contract())
            command = CancelRunCommand(run_id=task.id, reason="stop")
            harness.service.cancel_run(command)
            harness.service.cancel_run(command)
            assert harness.engine.calls[-1].result_summary == "deduped"
        finally:
            harness.close()


class TestPauseResume:
    RUN_UUID = "11111111-2222-4333-8444-555555555555"

    def _frozen_context(self, harness: M7Harness) -> tuple[RunContext, tuple[SessionSpec, ...]]:
        """执行到 PAUSED 的运行：先跑 happy path 拿 manifest，再手工构造 paused run。"""
        from packages.application import compile_and_preflight
        from packages.application.preflight.preflight import freeze_manifest

        catalog = m7_catalog()
        project = m7_project()
        context = m7_preflight_context(catalog, project)
        plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
        assert plan is not None and report.passed
        manifest = freeze_manifest(self.RUN_UUID, plan, report, context)
        run = _paused_run(self.RUN_UUID, manifest.digest(), manifest.semantic_digest())
        run_context = RunContext(
            protocol=m7_protocol(),
            plan=plan,
            report=report,
            run=run,
            catalog=catalog,
            project=project,
            preflight=context,
            trace_id="trace-resume",
        )
        pending = _pending_sessions(harness, run_context)
        return run_context, pending

    def test_resume_uses_frozen_manifest_semantics(self) -> None:
        runtime = StructuredOutputAgentRuntime(
            structured_output={
                "analysis_report": {"baseline": "O(n^2)"},
                "review_decision": {"verdict": "PASS"},
            }
        )
        harness = M7Harness(runtime=runtime)
        try:
            run_context, pending = self._frozen_context(harness)
            outcome = harness.service.resume_run(
                run_context,
                ResumeRunCommand(
                    run_id=ID(self.RUN_UUID),
                    frozen_manifest_digest=run_context.frozen_manifest_digest,
                    trace_id="trace-resume",
                ),
                pending,
            )
            assert outcome.state == ResearchRunState.State.SUCCEEDED
            assert outcome.manifest_digest == run_context.frozen_manifest_digest
        finally:
            harness.close()

    def test_resume_with_stale_manifest_digest_rejected(self) -> None:
        harness = M7Harness()
        try:
            run_context, pending = self._frozen_context(harness)
            stale = "sha256:" + "0" * 64
            with pytest.raises(ValueError, match="frozen"):
                harness.service.resume_run(
                    run_context,
                    ResumeRunCommand(
                        run_id=ID(self.RUN_UUID),
                        frozen_manifest_digest=stale,
                        trace_id="trace-stale",
                    ),
                    pending,
                )
        finally:
            harness.close()

    def test_resume_from_non_paused_state_rejected(self) -> None:
        harness = M7Harness()
        try:
            from packages.application import compile_and_preflight
            from packages.application.preflight.preflight import freeze_manifest

            catalog = m7_catalog()
            project = m7_project()
            context = m7_preflight_context(catalog, project)
            plan, report = compile_and_preflight(m7_protocol(), catalog, project, context)
            assert plan is not None and report.passed
            manifest = freeze_manifest(self.RUN_UUID, plan, report, context)
            # DRAFT 状态（未 START）不可 resume
            run = _draft_run(self.RUN_UUID, manifest.digest(), manifest.semantic_digest())
            run_context = RunContext(
                protocol=m7_protocol(),
                plan=plan,
                report=report,
                run=run,
                catalog=catalog,
                project=project,
                preflight=context,
                trace_id="trace-draft",
            )
            with pytest.raises(ValueError, match="cannot resume"):
                harness.service.resume_run(
                    run_context,
                    ResumeRunCommand(
                        run_id=ID(self.RUN_UUID),
                        frozen_manifest_digest=str(manifest.digest()),
                        trace_id="trace-draft",
                    ),
                    (),
                )
        finally:
            harness.close()

    def test_resume_with_drifted_semantics_rejected(self) -> None:
        """冻结后 catalog 漂移（如 policy 版本变化）→ resume 必须拒绝而非静默用新语义。"""
        harness = M7Harness()
        try:
            manifest, parts = _drift_parts(self.RUN_UUID)
            run = _paused_run(self.RUN_UUID, manifest.digest(), manifest.semantic_digest())
            run_context = RunContext(
                protocol=m7_protocol(),
                plan=parts["plan"],
                report=parts["report"],
                run=run,
                catalog=parts["catalog"],
                project=m7_project(),
                preflight=parts["context"],
                trace_id="trace-drift",
            )
            with pytest.raises(ValueError, match="drifted from frozen manifest"):
                harness.service.resume_run(
                    run_context,
                    ResumeRunCommand(
                        run_id=ID(self.RUN_UUID),
                        frozen_manifest_digest=str(manifest.digest()),
                        trace_id="trace-drift",
                    ),
                    (),
                )
        finally:
            harness.close()


def _draft_run(run_id: str, manifest_digest: Digest, semantic_digest: Digest) -> ResearchRun:
    return ResearchRun(
        id=ID(run_id),
        project_id="m7-project",
        protocol_id="sort_analysis_v1",
        manifest_digest=manifest_digest,
        manifest_semantic_digest=semantic_digest,
    )


def _paused_run(run_id: str, manifest_digest: Digest, semantic_digest: Digest) -> ResearchRun:
    run = ResearchRun(
        id=ID(run_id),
        project_id="m7-project",
        protocol_id="sort_analysis_v1",
        manifest_digest=manifest_digest,
        manifest_semantic_digest=semantic_digest,
    )
    run = run.transition(ResearchRunState.Transition.START_COMPILE)
    run = run.transition(ResearchRunState.Transition.COMPILE_OK)
    run = run.transition(ResearchRunState.Transition.PREFLIGHT_OK)
    run = run.transition(ResearchRunState.Transition.START)
    return run.transition(ResearchRunState.Transition.PAUSE)


def _pending_sessions(harness: M7Harness, run_context: RunContext) -> tuple[SessionSpec, ...]:
    """从 RunContext 解析待执行任务（复用 service 的 team resolution）。"""
    return harness.service._resolve_sessions(run_context)  # noqa: SLF001


def _drift_parts(run_id: str) -> tuple[RunManifest, DriftParts]:
    """冻结原始 manifest 后构造漂移 catalog（policy 版本 0.5.0）的 plan/report/context。"""
    from dataclasses import replace

    from packages.application import compile_and_preflight
    from packages.application.preflight.preflight import freeze_manifest
    from packages.domain.core import Version
    from packages.domain.enums import PolicyDecision
    from packages.domain.policy import PolicyDefinition

    original_catalog = m7_catalog()
    project = m7_project()
    original_context = m7_preflight_context(original_catalog, project)
    plan, report = compile_and_preflight(m7_protocol(), original_catalog, project, original_context)
    assert plan is not None and report.passed
    manifest = freeze_manifest(run_id, plan, report, original_context)

    drifted_catalog = replace(
        original_catalog,
        policy=PolicyDefinition(
            id="project-policy",
            version=Version("0.5.0"),
            default_effect=PolicyDecision.DENY,
        ),
    )
    drifted_context = m7_preflight_context(drifted_catalog, project)
    drifted_plan, drifted_report = compile_and_preflight(
        m7_protocol(), drifted_catalog, project, drifted_context
    )
    assert drifted_plan is not None and drifted_report.passed
    parts: DriftParts = {
        "plan": drifted_plan,
        "report": drifted_report,
        "catalog": drifted_catalog,
        "context": drifted_context,
    }
    return manifest, parts
