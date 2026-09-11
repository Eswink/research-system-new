"""Preflight 的资源检查纯函数。"""

from __future__ import annotations

from packages.application.model_relay.eligibility import decide_eligibility
from packages.application.ports import InvalidInputError, PreflightContext
from packages.domain.core import Digest
from packages.domain.enums import EndpointHealth, RiskClass, TrustLevel
from packages.domain.models import ModelDefinition
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    ModelEligibilityRecord,
    PreflightFinding,
    PreflightFindingCode,
)
from packages.domain.tools import ToolProviderSpec, classify_risk


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _warning(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.WARNING, message, subject)


def _check_record_eligibility(
    record: ModelEligibilityRecord,
    model: ModelDefinition,
) -> list[PreflightFinding]:
    if not record.eligible:
        missing = ", ".join(item.value for item in record.missing_capabilities)
        return [
            _finding(
                PreflightFindingCode.MODEL_ELIGIBILITY.value,
                f"model {record.model_id} is not eligible; missing: {missing or 'unknown'}",
                f"agent:{record.agent_id}",
            )
        ]
    decision = decide_eligibility(model, set(record.hard_capabilities))
    if decision.allowed:
        return []
    missing = ", ".join(item.value for item in decision.missing_capabilities)
    return [
        _finding(
            PreflightFindingCode.MODEL_ELIGIBILITY.value,
            f"model {record.model_id} is no longer eligible; missing: {missing}",
            f"agent:{record.agent_id}",
        )
    ]


def _credential_findings(
    endpoint_id: str,
    credential_ref: str,
    context: PreflightContext,
) -> list[PreflightFinding]:
    subject = f"endpoint:{endpoint_id}"
    if context.credentials is None:
        return [
            _finding(
                PreflightFindingCode.CREDENTIAL_MISSING.value,
                f"credential for endpoint {endpoint_id} cannot be resolved",
                subject,
            )
        ]
    try:
        context.credentials.resolve(credential_ref)
    except InvalidInputError:
        return [
            _finding(
                PreflightFindingCode.CREDENTIAL_MISSING.value,
                f"credential for endpoint {endpoint_id} cannot be resolved",
                subject,
            )
        ]
    return []


def _check_endpoint(
    record: ModelEligibilityRecord,
    model: ModelDefinition,
    context: PreflightContext,
    checked_endpoints: set[str],
) -> list[PreflightFinding]:
    endpoint = context.catalog.endpoints.get(model.endpoint_id)
    if endpoint is None:
        return [
            _finding(
                PreflightFindingCode.ENDPOINT_UNHEALTHY.value,
                f"endpoint {model.endpoint_id} is unavailable",
                f"model:{record.model_id}",
            )
        ]
    if not endpoint.enabled:
        return [
            _finding(
                PreflightFindingCode.ENDPOINT_UNHEALTHY.value,
                f"endpoint {endpoint.id} is disabled",
                f"endpoint:{endpoint.id}",
            )
        ]
    if endpoint.id in checked_endpoints:
        return []
    checked_endpoints.add(endpoint.id)
    findings: list[PreflightFinding] = []
    health = context.endpoint_health.get(endpoint.id, EndpointHealth.UNKNOWN)
    if health is not EndpointHealth.HEALTHY:
        findings.append(
            _finding(
                PreflightFindingCode.ENDPOINT_UNHEALTHY.value,
                f"endpoint {endpoint.id} health is {health.value}",
                f"endpoint:{endpoint.id}",
            )
        )
    findings.extend(_credential_findings(endpoint.id, endpoint.credential_ref, context))
    return findings


def _check_model_record(
    record: ModelEligibilityRecord,
    context: PreflightContext,
    checked_endpoints: set[str],
) -> list[PreflightFinding]:
    model = context.catalog.models.get(record.model_id)
    if model is None:
        return [
            _finding(
                PreflightFindingCode.MODEL_MISSING.value,
                f"model {record.model_id} is unavailable",
                record.model_id,
            )
        ]
    if not model.enabled:
        return [
            _finding(
                PreflightFindingCode.MODEL_MISSING.value,
                f"model {record.model_id} is disabled",
                record.model_id,
            )
        ]
    findings = _check_record_eligibility(record, model)
    findings.extend(_check_endpoint(record, model, context, checked_endpoints))
    return findings


def check_models(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    checked_endpoints: set[str] = set()
    return [
        finding
        for record in plan.model_eligibility
        for finding in _check_model_record(record, context, checked_endpoints)
    ]


def _is_pinned_digest(value: str | None) -> bool:
    try:
        Digest.parse(value or "")
    except ValueError:
        return False
    return True


def check_tools(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    for requirement in plan.tool_requirements:
        if not requirement.provider_ids:
            findings.append(
                _finding(
                    PreflightFindingCode.TOOL_UNAVAILABLE.value,
                    f"no provider is available for capability {requirement.capability}",
                    f"phase:{requirement.phase_id}",
                )
            )
            continue
        available = False
        for provider_id in requirement.provider_ids:
            provider = context.catalog.tool_providers.get(provider_id)
            if provider is None or provider.trust_level in {
                TrustLevel.REVOKED,
                TrustLevel.UNTRUSTED,
            }:
                continue
            health = context.provider_health.get(provider_id, EndpointHealth.HEALTHY)
            if health in {EndpointHealth.OPEN_CIRCUIT, EndpointHealth.DISABLED}:
                continue
            available = True
            findings.extend(_provider_health_findings(provider_id, health))
            findings.extend(_provider_trust_findings(plan, provider_id, provider))
        if not available:
            findings.append(
                _finding(
                    PreflightFindingCode.TOOL_UNAVAILABLE.value,
                    f"no healthy provider is available for capability {requirement.capability}",
                    f"phase:{requirement.phase_id}",
                )
            )
    return findings


def _provider_trust_findings(
    plan: CompiledRunPlan, provider_id: str, provider: ToolProviderSpec
) -> list[PreflightFinding]:
    """effect/trust 风险分层与 ToolPack pin 检查（M8 供应链面）。"""
    findings: list[PreflightFinding] = []
    risk = classify_risk(provider.effect_class, provider.trust_level)
    if risk in {RiskClass.HIGH, RiskClass.CRITICAL}:
        findings.append(
            _warning(
                PreflightFindingCode.TOOL_RISK_ELEVATED.value,
                f"provider {provider_id} has elevated risk class {risk.value}",
                f"provider:{provider_id}",
            )
        )
    if provider.kind.value != "NATIVE":
        if not _is_pinned_digest(plan.tool_pack_digests.get(provider_id)):
            findings.append(
                _finding(
                    PreflightFindingCode.SUPPLY_CHAIN_UNPINNED.value,
                    f"provider {provider_id} has no pinned ToolPack digest",
                    f"provider:{provider_id}",
                )
            )
    return findings


def _provider_health_findings(provider_id: str, health: EndpointHealth) -> list[PreflightFinding]:
    """WP-D 三态健康语义：UNKNOWN/DEGRADED 警示不阻断（不伪装健康）。"""
    if health is EndpointHealth.UNKNOWN:
        return [
            _warning(
                PreflightFindingCode.TOOL_HEALTH_UNPROVEN.value,
                f"provider {provider_id} health is not proven (no runnable probe)",
                f"provider:{provider_id}",
            )
        ]
    if health is EndpointHealth.DEGRADED:
        return [
            _warning(
                PreflightFindingCode.TOOL_HEALTH_DEGRADED.value,
                f"provider {provider_id} probe reported degraded health",
                f"provider:{provider_id}",
            )
        ]
    return []


def check_workspaces(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    for requirement in plan.workspace_requirements:
        if requirement.workspace_backend not in context.catalog.workspaces:
            findings.append(
                _finding(
                    PreflightFindingCode.WORKSPACE_UNAVAILABLE.value,
                    f"workspace {requirement.workspace_backend} is not available",
                    f"phase:{requirement.phase_id}",
                )
            )
        elif context.workspace_available.get(requirement.workspace_backend, True) is False:
            findings.append(
                _finding(
                    PreflightFindingCode.WORKSPACE_UNAVAILABLE.value,
                    f"workspace {requirement.workspace_backend} allocation is unavailable",
                    f"phase:{requirement.phase_id}",
                )
            )
    return findings
