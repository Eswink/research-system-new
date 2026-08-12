"""Protocol Compiler、Preflight 与 Manifest freeze 的离线契约测试。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from packages.application.preflight import (
    ManifestFreezeError,
    dry_run_projection,
    freeze_manifest,
    run_preflight,
)
from packages.application.protocol_compile import compile_protocol
from packages.domain.budget import BudgetPolicy
from packages.domain.enums import (
    CapabilitySource,
    CapabilityStatus,
    ModelCapability,
)
from packages.domain.models import CapabilityAssertion
from tests.application import protocol_fixtures as fixtures


def test_compile_is_complete_and_deterministic() -> None:
    plan, _ = fixtures.compiled()
    second = compile_protocol(
        fixtures.protocol(),
        fixtures.catalog(),
        fixtures.context().project,
    ).plan
    assert second is not None
    assert plan.digest() == second.digest()
    assert plan.phase_dag == {"collect": []}
    assert plan.resolved_models == {"agent-1": "model-1"}
    assert plan.tool_requirements[0].provider_ids == ("fixture-tools",)


def test_preflight_passes_and_freezes_manifest() -> None:
    plan, context = fixtures.compiled()
    report = run_preflight(plan, context)
    assert report.passed
    manifest = freeze_manifest("run-1", plan, report, context)
    assert manifest.protocol_digest == plan.protocol_digest
    assert manifest.compiled_plan_digest == plan.digest()
    assert manifest.digest() == manifest.digest()


def test_dry_run_projection_exposes_resources() -> None:
    plan, context = fixtures.compiled()
    projection = dry_run_projection(plan, context)
    payload = projection.to_payload()
    assert payload["role_counts"] == {"researcher": 1}
    assert payload["agent_models"] == {"agent-1": "model-1"}
    assert payload["workspaces"] == {"collect": "workspace"}
    assert payload["budget_reservations"]


def test_missing_credentials_block_preflight_and_freeze() -> None:
    plan, context = fixtures.compiled()
    report = run_preflight(plan, replace(context, credentials=None))
    assert report.status.value == "FAIL"
    assert "CREDENTIAL_MISSING" in {finding.code for finding in report.findings}
    with pytest.raises(ManifestFreezeError):
        freeze_manifest("run-1", plan, report, context)


def test_ineligible_model_blocks_preflight() -> None:
    plan, context = fixtures.compiled()
    model = context.catalog.models["model-1"]
    unsupported = replace(
        model,
        capabilities={
            ModelCapability.CHAT: CapabilityAssertion(
                status=CapabilityStatus.UNSUPPORTED,
                confidence=1.0,
                source=CapabilitySource.PROBED,
            )
        },
    )
    catalog = replace(context.catalog, models={"model-1": unsupported})
    report = run_preflight(plan, replace(context, catalog=catalog))
    assert "MODEL_ELIGIBILITY" in {finding.code for finding in report.findings}


def test_tool_unavailable_and_policy_denied_are_structured() -> None:
    plan, context = fixtures.compiled()
    empty_tools = replace(context.catalog, tool_providers={})
    tool_report = run_preflight(plan, replace(context, catalog=empty_tools))
    assert "TOOL_UNAVAILABLE" in {finding.code for finding in tool_report.findings}
    assert context.catalog.policy is not None
    denied = replace(
        context.catalog,
        policy=replace(context.catalog.policy, allow=()),
    )
    policy_report = run_preflight(plan, replace(context, catalog=denied))
    assert "POLICY_DENIED" in {finding.code for finding in policy_report.findings}


def test_workspace_and_budget_failures_block() -> None:
    plan, context = fixtures.compiled()
    workspace_report = run_preflight(
        plan,
        replace(context, workspace_available={"workspace": False}),
    )
    assert "WORKSPACE_UNAVAILABLE" in {finding.code for finding in workspace_report.findings}
    low_budget = replace(
        context.catalog,
        budget_policies={"budget": BudgetPolicy(id="budget", hard_limits={"tool_requests": 0})},
    )
    budget_report = run_preflight(plan, replace(context, catalog=low_budget))
    assert "BUDGET_EXHAUSTED" in {finding.code for finding in budget_report.findings}
