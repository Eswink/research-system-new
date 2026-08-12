"""FakePolicyEvaluator：可配置确定性策略决策。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyRequest,
)
from packages.domain.enums import PolicyDecision


class FakePolicyEvaluator(FakeBase):
    """按 capability 返回预置决策；未配置时返回默认决策。"""

    def __init__(
        self,
        *,
        default: PolicyDecision = PolicyDecision.ALLOW,
    ) -> None:
        super().__init__("policy_evaluator")
        self._default = default
        self._by_capability: dict[str, PolicyDecision] = {}
        self._constraints: dict[str, tuple[str, ...]] = {}

    def set_decision(self, capability: str, decision: PolicyDecision) -> None:
        self._by_capability[capability] = decision

    def set_constraints(self, capability: str, constraints: tuple[str, ...]) -> None:
        self._constraints[capability] = constraints

    def evaluate(self, request: PolicyRequest) -> PolicyEvaluation:
        self._enter("evaluate", f"{request.actor}/{request.capability}")
        decision = self._by_capability.get(request.capability, self._default)
        result = PolicyEvaluation(
            decision=decision,
            constraints={"allowed": self._constraints.get(request.capability, ())}
            if decision is PolicyDecision.ALLOW_WITH_CONSTRAINTS
            else {},
        )
        self._record("evaluate", f"{request.actor}/{request.capability}", result=decision.value)
        return result
