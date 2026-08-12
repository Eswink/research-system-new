"""PolicyEvaluator Port：能力授权决策（integration/POLICY_ENGINE.md、ADR-0018）。

职责：evaluate(Actor + Capability + Scope + Resource) →
ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS；
决策必须 deterministic，decision log 不得记录 secret。
非职责：不做策略定义（domain PolicyDefinition）；不做 enforcement
（调用方在 enforcement points 执行决策）。

M5 决策：NativePolicyEvaluator（application/policy/native.py）实现本 Port；
OPA 等生产实现（P2）遵循同一契约。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable

from packages.domain.enums import PolicyDecision


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


@runtime_checkable
class PolicyEvaluator(Protocol):
    """策略决策契约。"""

    def evaluate(self, request: PolicyRequest) -> PolicyEvaluation: ...
