"""Policy 可见性路由（PLAN-20260914-049 WP-C）。

`GET /policy/capabilities` 呈现在 `examples/config/policy.yaml` 里**声明**的
规则，以及门链能力（`_GATE_CAPABILITY_SCOPES`，如 memory.write 的四个 tier）
的逐 scope **有效判决**——判决由控制面运行期实际使用的同一 PolicyEvaluator
计算（同一代码路径，不做第二套判定）。

诚实边界：
- policy.yaml 缺失/不可解析 → 503（不伪造默认策略，也不回退成"全放开"的假绿）；
- 只读快照：不提供规则 CRUD（策略变更是运维面对 policy.yaml 的版本化改动）；
- actor 不参与规则匹配（NativePolicyEvaluator 仅按 capability/action/scope 匹配），
  故逐 scope 判决对任何 actor 都成立；响应在 note 里显式说明。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.policy.native import PolicyRequest
from packages.application.preflight.policy_check import gate_capability_scopes
from packages.domain.policy import PolicyDefinition
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.policy import (
    GateCapabilityViewDto,
    PolicyCapabilitiesDto,
    PolicyRuleViewDto,
)
from services.api.errors import ApiError

router = APIRouter(prefix="/policy", tags=["policy"])

SOURCE = "examples/config/policy.yaml"

NOTE = (
    "只读快照：规则来自 examples/config/policy.yaml；gate_capabilities 的逐 scope "
    "判决由控制面运行期同一 PolicyEvaluator 计算（actor 不参与匹配，故对任何 "
    "actor 成立）。修改策略需改 policy.yaml 并重启控制面，无规则 CRUD API。"
)


def _rule_views(policy: PolicyDefinition) -> list[PolicyRuleViewDto]:
    groups = (
        ("ALLOW", policy.allow),
        ("ALLOW_WITH_CONSTRAINTS", policy.allow_with_constraints),
        ("REQUIRE_APPROVAL", policy.require_approval),
        ("DENY", policy.deny),
    )
    return [
        PolicyRuleViewDto(
            effect=effect,
            capability=rule.capability,
            action=rule.action,
            scope=rule.scope,
            constraints=dict(rule.constraints),
        )
        for effect, rules in groups
        for rule in rules
    ]


def _gate_views(deps: ApiDeps) -> list[GateCapabilityViewDto]:
    evaluator = deps.policy_evaluator
    views: list[GateCapabilityViewDto] = []
    for capability, scopes in sorted(gate_capability_scopes().items()):
        ordered = sorted(scopes)
        if evaluator is None:
            views.append(GateCapabilityViewDto(capability=capability, scopes=ordered, effects={}))
            continue
        effects: dict[str, str] = {}
        reasons: dict[str, str] = {}
        for scope in ordered:
            result = evaluator.evaluate(
                PolicyRequest(
                    actor="system:policy-view",
                    capability=capability,
                    action="commit",
                    scope=scope,
                )
            )
            effects[scope] = result.decision.value
            reasons[scope] = result.reason
        views.append(
            GateCapabilityViewDto(
                capability=capability,
                scopes=ordered,
                effects=effects,
                reasons=reasons,
            )
        )
    return views


@router.get("/capabilities", response_model=PolicyCapabilitiesDto)
async def policy_capabilities(request: Request) -> PolicyCapabilitiesDto:
    """策略面只读快照（声明的规则 + 门链能力的逐 scope 有效判决）。"""
    deps: ApiDeps = get_deps(request)
    policy = deps.policy
    if policy is None:
        raise ApiError(
            503,
            "Policy Unavailable",
            f"policy definition not loaded from {SOURCE}",
        )
    return PolicyCapabilitiesDto(
        policy_id=policy.id,
        version=policy.version.text,
        default_effect=policy.default_effect.value,
        source=SOURCE,
        rules=_rule_views(policy),
        gate_capabilities=_gate_views(deps),
        note=NOTE,
    )
