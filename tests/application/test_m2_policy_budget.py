"""M2 policy、预算、供应链与 WARN 语义测试。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from packages.application.policy.native import NativePolicyEvaluator, PolicyRequest
from packages.application.ports import LedgerSnapshot
from packages.application.preflight import (
    ManifestFreezeError,
    dry_run_projection,
    freeze_manifest,
    run_preflight,
)
from packages.application.preflight.budget import check_budget, reserve_budget
from packages.application.protocol_compile import compile_protocol
from packages.domain.budget import BudgetPolicy, BudgetReservation, ResourceType, UsageLedgerEntry
from packages.domain.core import Version
from packages.domain.enums import (
    EffectClass,
    GateType,
    PolicyDecision,
    ProviderType,
    TrustLevel,
)
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.tools import ToolProviderSpec
from tests.application import protocol_fixtures as fixtures


def test_native_policy_priority_and_default_deny() -> None:
    request = PolicyRequest(
        actor="project:project-1",
        capability="package.install",
        scope="approved_tool_providers",
    )
    policy = PolicyDefinition(
        id="policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.DENY,
        allow=(PolicyRule(capability="package.install", scope="approved_tool_providers"),),
        allow_with_constraints=(
            PolicyRule(
                capability="package.install",
                scope="approved_tool_providers",
                constraints={"sandbox_required": True},
            ),
        ),
        require_approval=(
            PolicyRule(capability="package.install", scope="approved_tool_providers"),
        ),
        deny=(PolicyRule(capability="package.install", scope="approved_tool_providers"),),
    )
    evaluator = NativePolicyEvaluator(policy)
    assert evaluator.evaluate(request).decision is PolicyDecision.DENY
    approval = evaluator.__class__(replace(policy, deny=())).evaluate(request)
    assert approval.decision is PolicyDecision.REQUIRE_APPROVAL
    constrained = evaluator.__class__(replace(policy, deny=(), require_approval=())).evaluate(
        request
    )
    assert constrained.decision is PolicyDecision.ALLOW_WITH_CONSTRAINTS
    allowed = evaluator.__class__(
        replace(policy, deny=(), require_approval=(), allow_with_constraints=())
    ).evaluate(request)
    assert allowed.decision is PolicyDecision.ALLOW
    unknown = evaluator.evaluate(replace(request, capability="not.declared"))
    assert unknown.decision is PolicyDecision.DENY


def _reservations() -> tuple[BudgetReservation, ...]:
    return (
        BudgetReservation("p1", "phase:p1", ResourceType.PARALLELISM, 2, "agents"),
        BudgetReservation("p2", "phase:p2", ResourceType.PARALLELISM, 3, "agents"),
        BudgetReservation("t1", "phase:p1", ResourceType.TOOL_REQUESTS, 4, "requests"),
        BudgetReservation("t2", "phase:p2", ResourceType.TOOL_REQUESTS, 5, "requests"),
        BudgetReservation("w1", "phase:p1", ResourceType.WALL_CLOCK, 6, "seconds"),
    )


def test_budget_aggregates_totals_and_parallel_peak() -> None:
    check = check_budget(
        _reservations(),
        BudgetPolicy(
            id="budget",
            hard_limits={
                "agent_sessions": 3,
                "tool_requests": 8,
                "wall_clock_seconds": 6,
            },
        ),
    )
    assert check.totals == {
        "agent_sessions": 3,
        "tool_requests": 9,
        "wall_clock_seconds": 6,
    }
    assert check.exceeded == {"tool_requests": (9, 8)}


def test_budget_unknown_limits_are_explicit_and_reservation_uses_port() -> None:
    class Reserver:
        def __init__(self) -> None:
            self.calls = 0

        def reserve(
            self,
            reservations: tuple[BudgetReservation, ...],
            policy: BudgetPolicy,
        ) -> str:
            self.calls += 1
            return "reservation:1"

        def release(self, reservation_ref: str) -> None:
            return None

        def record_usage(self, entry: UsageLedgerEntry) -> None:
            return None

        def snapshot(self) -> LedgerSnapshot:
            return LedgerSnapshot()

    reserver = Reserver()
    result = reserve_budget(
        _reservations(),
        BudgetPolicy(id="budget", hard_limits={"tool_requests": 9}),
        reserver,
    )
    assert result.check.unknown_limits == ("agent_sessions", "wall_clock_seconds")
    assert result.reservation_ref == "reservation:1"
    assert reserver.calls == 1


def test_budget_unmapped_resource_type_is_not_silently_dropped() -> None:
    """未映射 ResourceType 必须显式暴露，不能静默放行。"""
    from dataclasses import replace

    from packages.domain.budget import BudgetReservation, ResourceType

    plan, context = fixtures.compiled()
    plan = replace(
        plan,
        budget_reservations=[
            *plan.budget_reservations,
            BudgetReservation(
                "model-tokens", "phase:collect", ResourceType.MODEL_TOKENS, 1000, "tokens"
            ),
        ],
    )
    report = run_preflight(plan, context)
    assert report.status.value == "WARN"
    assert "BUDGET_RESOURCE_UNMAPPED" in {item.code for item in report.findings}
    assert any("MODEL_TOKENS" in item.message for item in report.findings)
    with pytest.raises(ManifestFreezeError):
        freeze_manifest("run-1", plan, report, context)


def test_budget_mapped_types_produce_no_unmapped_finding() -> None:
    """编译器生成的 3 类 reservation 不产生 unmapped 告警。"""
    plan, context = fixtures.compiled()
    report = run_preflight(plan, context)
    assert "BUDGET_RESOURCE_UNMAPPED" not in {item.code for item in report.findings}
    assert report.status.value == "PASS"


def test_preflight_warn_requires_new_run_attempt() -> None:
    plan, context = fixtures.compiled()
    assert context.catalog.policy is not None
    policy = replace(
        context.catalog.policy,
        allow=(),
        require_approval=(
            PolicyRule(
                capability="literature.search",
                scope="approved_tool_providers",
            ),
        ),
    )
    warned = run_preflight(
        plan,
        replace(
            context,
            catalog=replace(context.catalog, policy=policy),
            policy_evaluator=NativePolicyEvaluator(policy),
        ),
    )
    assert warned.status.value == "WARN"
    assert "POLICY_APPROVAL_REQUIRED" in {item.code for item in warned.findings}
    with pytest.raises(ManifestFreezeError):
        freeze_manifest(
            "run-1",
            plan,
            warned,
            replace(
                context,
                catalog=replace(context.catalog, policy=policy),
                policy_evaluator=NativePolicyEvaluator(policy),
            ),
        )


def test_unknown_budget_limits_warn_and_do_not_reserve() -> None:
    plan, context = fixtures.compiled()
    budget = BudgetPolicy(id="budget", hard_limits={"tool_requests": 1})
    report = run_preflight(
        plan,
        replace(context, catalog=replace(context.catalog, budget_policies={"budget": budget})),
    )
    assert report.status.value == "WARN"
    assert "BUDGET_LIMIT_UNKNOWN" in {item.code for item in report.findings}
    assert report.reserved_budget_ref is None


def test_external_tool_provider_requires_pinned_digest() -> None:
    provider = ToolProviderSpec(
        id="mcp-tools",
        kind=ProviderType.MCP,
        trust_level=TrustLevel.USER_APPROVED,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
    )
    catalog = replace(
        fixtures.catalog(),
        tool_providers={"mcp-tools": provider},
        tool_pack_digests={},
    )
    context = fixtures.context(catalog)
    result = compile_protocol(fixtures.protocol(), catalog, context.project)
    assert result.plan is not None
    report = run_preflight(result.plan, context)
    assert "SUPPLY_CHAIN_UNPINNED" in {item.code for item in report.findings}

    pinned_catalog = replace(catalog, tool_pack_digests={"mcp-tools": "sha256:" + "0" * 64})
    pinned_context = replace(context, catalog=pinned_catalog)
    pinned_result = compile_protocol(fixtures.protocol(), pinned_catalog, context.project)
    assert pinned_result.plan is not None
    assert run_preflight(pinned_result.plan, pinned_context).passed


def test_human_gate_is_warn_and_requires_approval() -> None:
    base = fixtures.protocol()
    gated = replace(
        base,
        phases=[replace(base.phases[0], gate=GateType.HUMAN_GATE)],
    )
    context = fixtures.context()
    result = compile_protocol(gated, context.catalog, context.project)
    assert result.plan is not None
    report = run_preflight(result.plan, context)
    assert report.status.value == "WARN"
    assert "HUMAN_GATE_REQUIRED" in {item.code for item in report.findings}
    projection = dry_run_projection(result.plan, context, report)
    assert projection.approval_actions
