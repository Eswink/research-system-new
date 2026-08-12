"""MVP NativePolicyEvaluator：纯确定性策略决策。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from packages.domain.enums import PolicyDecision
from packages.domain.policy import PolicyDefinition, PolicyRule


@dataclass(frozen=True, slots=True)
class PolicyRequest:
    actor: str
    capability: str
    action: str | None = None
    scope: str | None = None
    resource: str | None = None
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.actor:
            raise ValueError("policy actor must not be empty")
        if not self.capability:
            raise ValueError("policy capability must not be empty")


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    decision: PolicyDecision
    constraints: Mapping[str, object] = field(default_factory=dict)
    reason: str = ""


def _matching(rules: tuple[PolicyRule, ...], request: PolicyRequest) -> PolicyRule | None:
    return next(
        (rule for rule in rules if rule.matches(request.capability, request.action, request.scope)),
        None,
    )


@dataclass(frozen=True, slots=True)
class NativePolicyEvaluator:
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
