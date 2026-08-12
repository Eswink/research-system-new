"""Policy 规则的纯 Domain 表达。

Policy evaluator 属于 application；本模块只保存版本化规则和不可变输入。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Version
from packages.domain.enums import PolicyDecision


@dataclass(frozen=True, slots=True)
class PolicyRule:
    capability: str | None = None
    action: str | None = None
    scope: str | None = None
    constraints: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capability and not self.action:
            raise ValueError("policy rule must declare capability or action")
        if self.capability is not None and not self.capability:
            raise ValueError("policy capability must not be empty")
        if self.action is not None and not self.action:
            raise ValueError("policy action must not be empty")

    def matches(self, capability: str, action: str | None, scope: str | None) -> bool:
        capability_matches = self.capability is None or self.capability == capability
        action_matches = self.action is None or self.action == action
        scope_matches = self.scope is None or self.scope == scope
        return capability_matches and action_matches and scope_matches


@dataclass(frozen=True, slots=True)
class PolicyDefinition:
    id: str
    version: Version
    default_effect: PolicyDecision
    allow: tuple[PolicyRule, ...] = ()
    allow_with_constraints: tuple[PolicyRule, ...] = ()
    require_approval: tuple[PolicyRule, ...] = ()
    deny: tuple[PolicyRule, ...] = ()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("policy id must not be empty")
