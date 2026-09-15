"""memory.write 能力策略接线测试（PLAN-20260914-049 WP-B）。

用**真实的** NativePolicyEvaluator + examples/config/policy.yaml 覆盖门链 policy
阶段（不是替身）：默认四 tier 放行不改变既有行为；运维收紧为 deny /
require_approval 时提案在 policy 阶段被拒，且 reason 可读。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from adapters.contracts import load_policy
from adapters.fakes import FakeEvidenceLedger, FakeMemoryStore
from packages.application.memory.gate import MemoryGateDeps, evaluate_memory_proposal
from packages.application.policy.native import NativePolicyEvaluator
from packages.domain.enums import MemoryTier, PolicyDecision
from packages.domain.memory import MemoryWriteProposal
from packages.domain.policy import PolicyDefinition, PolicyRule
from tests.contracts.fixtures import memory_proposal

SOURCE = "source:article-1"


def _policy_with(
    *, deny: tuple[PolicyRule, ...] = (), approval: tuple[PolicyRule, ...] = ()
) -> PolicyDefinition:
    base = load_policy("examples/config/policy.yaml")
    return PolicyDefinition(
        id=base.id,
        version=base.version,
        default_effect=base.default_effect,
        allow=base.allow,
        allow_with_constraints=base.allow_with_constraints,
        require_approval=base.require_approval + approval,
        deny=base.deny + deny,
    )


def _deps(policy: PolicyDefinition) -> MemoryGateDeps:
    store = FakeMemoryStore(allowed_sources=(SOURCE,))
    return MemoryGateDeps(
        store=store,
        policy=NativePolicyEvaluator(policy),
        ledger=FakeEvidenceLedger(),
        allowed_sources=frozenset({SOURCE}),
    )


def _proposal(tier: MemoryTier = MemoryTier.SESSION) -> MemoryWriteProposal:
    base = memory_proposal("mem-policy-1")
    return replace(
        base,
        tier=tier,
        content="policy wiring probe",
        provenance=SOURCE,
        confidence=0.8,
    )


@pytest.mark.parametrize("tier", [MemoryTier.SESSION, MemoryTier.RUN])
def test_default_policy_allows_low_tiers(tier: MemoryTier) -> None:
    """policy.yaml 的四个 allow 规则放行低 tier，行为与接线前一致（回归）。"""
    result = evaluate_memory_proposal(
        _proposal(tier), _deps(load_policy("examples/config/policy.yaml"))
    )
    assert result.accepted is True, result.reasons


@pytest.mark.parametrize("tier", [MemoryTier.PROJECT, MemoryTier.ORGANIZATION])
def test_default_policy_keeps_curator_gate_for_high_tiers(tier: MemoryTier) -> None:
    """高 tier 的审批仍由 curator 门承担（policy 放行不越权）。"""
    result = evaluate_memory_proposal(
        _proposal(tier), _deps(load_policy("examples/config/policy.yaml"))
    )
    assert result.stage == "curator"


def test_deny_rule_rejects_at_policy_stage_with_reason() -> None:
    policy = _policy_with(deny=(PolicyRule(capability="memory.write", scope="SESSION"),))
    result = evaluate_memory_proposal(_proposal(), _deps(policy))
    assert result.accepted is False
    assert result.stage == "policy"
    assert result.decision is PolicyDecision.DENY
    assert result.reasons == ("policy deny: matched deny rule",)


def test_deny_rule_is_scope_specific() -> None:
    """deny 只作用于声明的 tier：RUN tier 仍走 allow 规则。"""
    policy = _policy_with(deny=(PolicyRule(capability="memory.write", scope="SESSION"),))
    result = evaluate_memory_proposal(_proposal(MemoryTier.RUN), _deps(policy))
    assert result.accepted is True, result.reasons


def test_require_approval_rule_needs_curator_input() -> None:
    policy = _policy_with(approval=(PolicyRule(capability="memory.write", scope="SESSION"),))
    rejected = evaluate_memory_proposal(_proposal(), _deps(policy))
    assert rejected.stage == "policy"
    assert rejected.decision is PolicyDecision.REQUIRE_APPROVAL
    assert rejected.reasons == ("policy requires approval: matched approval rule",)
    accepted = evaluate_memory_proposal(_proposal(), _deps(policy), curator_approved=True)
    assert accepted.accepted is True, accepted.reasons


def test_mirror_declares_every_memory_tier() -> None:
    """镜像契约：policy.yaml 的 memory.write 规则覆盖全部 MemoryTier（无 tier 落 default）。"""
    policy = load_policy("examples/config/policy.yaml")
    declared = {rule.scope for rule in policy.allow if rule.capability == "memory.write"}
    assert declared == {tier.value for tier in MemoryTier}
