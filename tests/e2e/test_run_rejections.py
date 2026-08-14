"""M7 E2E：Run 拒绝路径（Preflight FAIL / compile 阻断 / 内容寻址拒绝）。"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration import StartRunCommand
from packages.domain.core import ID
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
            "analysis_report": {"baseline": "O(n^2)"},
            "review_decision": {"verdict": "PASS"},
        }
    )
    instance = M7Harness(runtime=runtime)
    yield instance
    instance.close()


class TestPreflightRejections:
    def test_budget_exhausted_rejects_run(self, harness: M7Harness) -> None:
        """预算耗尽 → Preflight FAIL → Run FAILED，不进入执行。"""
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
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-reject-1",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert "preflight" in outcome.message
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_missing_contract_fails_compile_and_run(self, harness: M7Harness) -> None:
        """协议引用的 contract 缺失 → compile 阻断 → Run FAILED（不进入执行）。"""
        from dataclasses import replace

        catalog = replace(
            m7_catalog(),
            task_contracts={
                key: value
                for key, value in m7_catalog().task_contracts.items()
                if key != "sort_analysis_execution"
            },
        )
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-missing-contract",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_missing_role_rejects_run(self, harness: M7Harness) -> None:
        """role 未注册 → compile 阻断 → Run FAILED（不进入执行）。"""
        from dataclasses import replace

        catalog = replace(
            m7_catalog(),
            roles={
                key: value
                for key, value in m7_catalog().roles.items()
                if key != "scientific_reviewer"
            },
        )
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-missing-role",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_model_ineligible_rejects_run(self, harness: M7Harness) -> None:
        """模型缺少 Role 硬能力 → MODEL_ELIGIBILITY → Run FAILED。"""
        from dataclasses import replace

        from packages.domain.enums import CapabilitySource, CapabilityStatus
        from packages.domain.models import CapabilityAssertion, ModelDefinition

        catalog = m7_catalog()
        ineligible = ModelDefinition(
            id="model-engineer",
            endpoint_id="relay-main",
            model_name="model-engineer",
            capabilities={
                "chat": CapabilityAssertion(
                    status=CapabilityStatus.SUPPORTED,
                    confidence=1.0,
                    source=CapabilitySource.PROBED,
                    probe_version="m7-fixture-v1",
                ),
            },
        )
        catalog = replace(catalog, models={**catalog.models, "model-engineer": ineligible})
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-model-ineligible",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_tool_unavailable_rejects_run(self, harness: M7Harness) -> None:
        """capability 无可用 provider → TOOL_UNAVAILABLE → Run FAILED。"""
        from dataclasses import replace

        catalog = replace(m7_catalog(), tool_providers={})
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            m7_preflight_context(catalog, m7_project()),
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-tool-unavailable",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_credential_missing_rejects_run(self, harness: M7Harness) -> None:
        """endpoint 凭据无法解析 → CREDENTIAL_MISSING → Run FAILED。"""
        from adapters.fakes.credential_resolver import FakeCredentialResolver

        catalog = m7_catalog()
        context = m7_preflight_context(
            catalog, m7_project(), budget_ledger=harness.budget
        )
        from dataclasses import replace

        context = replace(context, credentials=FakeCredentialResolver({}))
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            context,
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-credential-missing",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()

    def test_policy_denied_rejects_run(self, harness: M7Harness) -> None:
        """policy 默认 DENY → POLICY_DENIED → Run FAILED。"""
        from adapters.fakes.policy_evaluator import FakePolicyEvaluator
        from packages.domain.enums import PolicyDecision

        catalog = m7_catalog()
        context = m7_preflight_context(
            catalog,
            m7_project(),
            evaluator=FakePolicyEvaluator(default=PolicyDecision.DENY),
        )
        outcome = harness.service.start_run(
            m7_protocol(),
            catalog,
            m7_project(),
            context,
            StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-policy-denied",
            ),
        )
        assert outcome.state == ResearchRunState.State.FAILED
        assert harness.engine.list_tasks(outcome.run_id) == ()


def test_artifact_store_rejects_tampered_content(harness: M7Harness) -> None:
    """内容寻址：与声明 digest 不一致的内容必须被拒绝（不覆盖/不写入）。"""
    from packages.domain.artifacts import Artifact
    from packages.domain.core import Digest

    content = b"report"
    artifact = Artifact(
        id="tampered",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
    )
    with pytest.raises(InvalidInputError, match="digest mismatch"):
        harness.artifacts.put(artifact, b"other")
