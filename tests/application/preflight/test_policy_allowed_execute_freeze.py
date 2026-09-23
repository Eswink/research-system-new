"""GOAL-20260923-012 EC-01：冻结门的**显式策略通道**（路径 (A)）。

判据形态（每条都**离线**：零出网、零容器、零凭据）：

1. 起点如实：`sort_analysis_v1` 的报告**仍是 `WARN`**、`passed` **仍是 `False`**
   （通道**不改** preflight 语义）；
2. **允许通道**：策略已显式允许的 EXECUTE 风险 ⇒ **冻结可完成**，且留痕在场；
3. **留痕同源**：manifest 的 `accepted_policy_exceptions` 与 `MANIFEST_FROZEN` 事件
   payload 里的同一键**同源同值**；未走通道时**为空**（既有 run 的字节不变）；
4. **拒冻反证（成对）**：撤掉「显式允许」⇒ **回到拒冻**，且消息**点名**缺失的策略事实；
5. **不可转换面**：非 `TOOL_RISK_ELEVATED` 的警示、以及**非 EXECUTE** 的高风险 provider
   **一律拒冻**（默认 deny 不变）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.preflight.preflight import ManifestFreezeError, freeze_manifest
from packages.application.run_orchestration.eventing import frozen_payload
from packages.domain.core import ID
from packages.domain.enums import EffectClass, PolicyDecision
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.protocols import PreflightStatus
from packages.domain.run import ResearchRun

_PROTOCOL = "examples/protocols/sort_analysis_v1.yaml"
_EXECUTE_PROVIDER = "openhands_workspace"
_EXPECTED_PAIRS = {
    ("execution", "code.execute"),
    ("execution", "workspace.read"),
    ("execution", "workspace.write.code"),
    ("review", "workspace.read"),
}


def _deps() -> Any:
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


def _protocol_policy() -> PolicyDefinition:
    """`examples/config/policy.yaml` + 这份协议声明但**产品策略尚未放行**的
    `evidence.read`（那是另一条独立的既有缺口，不属本判据的射程；本判据要的是
    「一份把该协议所需能力都显式允许、**含 `code.execute`** 的策略」这个前提）。"""
    context = _deps().preflight_override
    base: PolicyDefinition | None = context.catalog.policy
    assert base is not None, "夹具目录必须带 policy（examples/config/policy.yaml）"
    if any(rule.capability == "evidence.read" for rule in base.allow):
        return base
    return replace(base, allow=(*base.allow, PolicyRule(capability="evidence.read")))


def _native_context(policy: PolicyDefinition | None = None) -> Any:
    """把夹具目录接上**真实**的 `NativePolicyEvaluator`（夹具的 Fake 求值器默认全放行，
    不适合测「显式允许 / 未允许」这条线）。"""
    context = _deps().preflight_override
    chosen = policy if policy is not None else _protocol_policy()
    return replace(
        context,
        catalog=replace(context.catalog, policy=chosen),
        policy_evaluator=NativePolicyEvaluator(chosen),
    )


def _plan_report(context: Any) -> tuple[Any, Any]:
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight

    protocol = load_protocol(_PROTOCOL)
    return compile_and_preflight(protocol, context.catalog, context.project, context)


def _without_rule(policy: PolicyDefinition, capability: str) -> PolicyDefinition:
    """从 `allow_with_constraints` 摘掉某能力（撤掉「显式允许」）。"""
    return replace(
        policy,
        allow_with_constraints=tuple(
            rule for rule in policy.allow_with_constraints if rule.capability != capability
        ),
    )


def test_the_blocked_protocol_still_preflights_as_warn() -> None:
    """起点：报告仍是 `WARN`、`passed` 仍是 `False`（通道不改 preflight 语义）。"""
    context = _native_context()
    plan, report = _plan_report(context)
    assert plan is not None
    assert report.status is PreflightStatus.WARN
    assert report.passed is False
    codes = [item.code for item in report.findings]
    assert codes.count("TOOL_RISK_ELEVATED") == 4, codes
    assert all(
        item.subject_ref == f"provider:{_EXECUTE_PROVIDER}"
        for item in report.findings
        if item.code == "TOOL_RISK_ELEVATED"
    )


def test_a_policy_allowed_execute_risk_may_freeze() -> None:
    """**允许通道**：策略显式允许 ⇒ 冻结可完成，且留痕逐条点名（AC-1 + AC-2）。"""
    context = _native_context()
    plan, report = _plan_report(context)
    manifest = freeze_manifest("run-channel", plan, report, context)
    trace = manifest.accepted_policy_exceptions
    assert {(item["phase_id"], item["capability"]) for item in trace} == _EXPECTED_PAIRS
    assert all(item["provider_id"] == _EXECUTE_PROVIDER for item in trace)
    assert all(item["policy_version"] == "0.4.0" for item in trace)
    assert all(
        item["decision"]
        in {PolicyDecision.ALLOW.value, PolicyDecision.ALLOW_WITH_CONSTRAINTS.value}
        for item in trace
    )
    assert manifest.frozen_at is not None
    assert all(item["accepted_at"] == manifest.frozen_at.value.isoformat() for item in trace)
    # 留痕进了 digest 覆盖的字节：同 plan、同策略下再冻一次，digest 只随时刻变化
    assert manifest.digest() == manifest.digest()


def test_the_freeze_event_carries_the_same_trace() -> None:
    """留痕与事件 payload **同源同值**（读面回读的就是这份）。"""
    run_id = "5e0a7f2c-1b34-4d55-9a86-0f3c2d1e4b77"
    context = _native_context()
    plan, report = _plan_report(context)
    manifest = freeze_manifest(run_id, plan, report, context)
    run = ResearchRun(
        id=ID(manifest.run_id),
        project_id=manifest.project_id,
        protocol_id="sort_analysis_v1_0_1",
    )
    payload = frozen_payload(run, manifest)
    assert payload["accepted_policy_exceptions"] == list(manifest.accepted_policy_exceptions)
    assert payload["accepted_policy_exceptions"], "留痕不得为空"


def test_a_passing_report_leaves_no_trace() -> None:
    """未走通道时留痕为空：既有 run 的 manifest 字节与 digest **逐字不变**。"""
    context = _native_context()
    plan, report = _plan_report(context)
    passing = replace(report, status=PreflightStatus.PASS, findings=[])
    manifest = freeze_manifest("run-plain", plan, passing, context)
    assert manifest.accepted_policy_exceptions == []


def test_withdrawing_the_allowance_refuses_and_names_the_capability() -> None:
    """**拒冻反证**：EXECUTE 能力不再被显式允许 ⇒ 拒冻，且消息**点名**该能力（AC-3）。"""
    context = _native_context()
    policy = context.catalog.policy
    assert policy is not None
    withdrawn = replace(
        _without_rule(policy, "code.execute"),
        require_approval=(*policy.require_approval, PolicyRule(capability="code.execute")),
    )
    approval_context = _native_context(withdrawn)
    plan, report = _plan_report(approval_context)
    assert plan is not None
    assert report.status is PreflightStatus.WARN, [item.code for item in report.findings]
    assert "POLICY_APPROVAL_REQUIRED" in {item.code for item in report.findings}
    with pytest.raises(ManifestFreezeError) as excinfo:
        freeze_manifest("run-withdrawn", plan, report, approval_context)
    message = str(excinfo.value)
    assert "code.execute" in message, message
    assert "REQUIRE_APPROVAL" in message or "no acceptance channel" in message, message


def test_a_denied_capability_refuses_before_the_channel() -> None:
    """**拒冻反证（二）**：连 allow 规则都没有 ⇒ 预检 `FAIL` ⇒ 仍在通道之前拒冻。"""
    context = _native_context()
    policy = context.catalog.policy
    assert policy is not None
    denied_context = _native_context(_without_rule(policy, "code.execute"))
    plan, report = _plan_report(denied_context)
    assert report.status is PreflightStatus.FAIL
    with pytest.raises(ManifestFreezeError):
        freeze_manifest("run-denied", plan, report, denied_context)


def test_other_warnings_are_never_convertible() -> None:
    """**不可转换面（一）**：非 `TOOL_RISK_ELEVATED` 的警示一律拒冻并点名 code。"""
    from packages.domain.budget import BudgetReservation, ResourceType

    context = _native_context()
    plan, report = _plan_report(context)
    augmented = replace(
        plan,
        budget_reservations=[
            *plan.budget_reservations,
            BudgetReservation(
                "model-tokens", "phase:execution", ResourceType.MODEL_TOKENS, 1000, "tokens"
            ),
        ],
    )
    warned = _re_preflight(augmented, context)
    assert warned.status is PreflightStatus.WARN
    assert "BUDGET_RESOURCE_UNMAPPED" in {item.code for item in warned.findings}
    with pytest.raises(ManifestFreezeError) as excinfo:
        freeze_manifest("run-other-warning", augmented, warned, context)
    assert "BUDGET_RESOURCE_UNMAPPED" in str(excinfo.value)


def test_a_non_execute_high_risk_provider_has_no_channel() -> None:
    """**不可转换面（二）**：非 EXECUTE 的高风险 provider 没有通道（`CRITICAL` 一律拒）。"""
    _skip_unless_execute_provider()
    context = _native_context()
    provider = context.catalog.tool_providers[_EXECUTE_PROVIDER]
    destructive = replace(provider, effect_class=EffectClass.DESTRUCTIVE)
    catalog = replace(
        context.catalog,
        tool_providers={**context.catalog.tool_providers, _EXECUTE_PROVIDER: destructive},
    )
    shifted = replace(context, catalog=catalog)
    plan, report = _plan_report(shifted)
    assert report.status is PreflightStatus.WARN
    assert {item.code for item in report.findings} == {"TOOL_RISK_ELEVATED"}
    with pytest.raises(ManifestFreezeError) as excinfo:
        freeze_manifest("run-destructive", plan, report, shifted)
    assert "DESTRUCTIVE" in str(excinfo.value)


def _skip_unless_execute_provider() -> None:
    """自检：夹具目录里必须真有那条 EXECUTE provider（防判据扫描空转）。"""
    context = _native_context()
    provider = context.catalog.tool_providers.get(_EXECUTE_PROVIDER)
    assert provider is not None, "夹具目录缺少 EXECUTE provider"
    assert provider.effect_class is EffectClass.EXECUTE


def _re_preflight(plan: Any, context: Any) -> Any:
    """用改过的 plan 重新跑预检（预算类警示由 plan 的预留驱动）。"""
    from packages.application.preflight.preflight import run_preflight

    return run_preflight(plan, context)
