"""MVP NativePolicyEvaluator：纯确定性策略决策（PolicyEvaluator Port 实现）。"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyRequest,
)
from packages.domain.enums import PolicyDecision
from packages.domain.policy import PolicyDefinition, PolicyRule

__all__ = ["NativePolicyEvaluator", "PolicyEvaluation", "PolicyRequest"]


def _matching(rules: tuple[PolicyRule, ...], request: PolicyRequest) -> PolicyRule | None:
    return next(
        (rule for rule in rules if rule.matches(request.capability, request.action, request.scope)),
        None,
    )


@dataclass(frozen=True, slots=True)
class NativePolicyEvaluator:
    """PolicyEvaluator Port 的 MVP 实现（ADR-0018：类型安全 native evaluator）。"""

    policy: PolicyDefinition

    def evaluate(self, request: PolicyRequest) -> PolicyEvaluation:
        deny = _matching(self.policy.deny, request)
        if deny:
            return PolicyEvaluation(PolicyDecision.DENY, reason="matched deny rule")
        approval = _matching(self.policy.require_approval, request)
        if approval:
            return PolicyEvaluation(PolicyDecision.REQUIRE_APPROVAL, reason="matched approval rule")
        constrained = _matching(self.policy.allow_with_constraints, request)
        if constrained:
            return PolicyEvaluation(
                PolicyDecision.ALLOW_WITH_CONSTRAINTS,
                constraints=constrained.constraints,
                reason="matched constrained allow rule",
            )
        allowed = _matching(self.policy.allow, request)
        if allowed:
            return PolicyEvaluation(PolicyDecision.ALLOW, reason="matched allow rule")
        return PolicyEvaluation(self.policy.default_effect, reason="used default policy effect")
