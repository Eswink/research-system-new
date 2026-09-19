"""CompiledRunPlan 的 Preflight、dry-run 与 Manifest freeze。

成本估算语义：M2 不估算成本，`PreflightReport.estimated_cost` 与
`DryRunProjection.estimated_cost` 恒为 None，序列化输出 null，表示
"未估算"（不是 0 成本）。M5/M7 成本模型接入前不得用 0 填充该字段。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.cost.pricing import PricingTable
from packages.application.ports import PreflightContext, ProjectSettings
from packages.application.ports.pricing_snapshot_store import PricingSnapshotStore
from packages.application.preflight.budget import BudgetCheck, check_budget, reserve_budget
from packages.application.preflight.checks import check_models, check_tools, check_workspaces
from packages.application.preflight.dry_run import (
    DryRunProjection as DryRunProjection,
)
from packages.application.preflight.dry_run import (
    dry_run_projection as dry_run_projection,
)
from packages.application.preflight.policy_check import check_policy
from packages.application.preflight.role_checks import check_team
from packages.application.protocol_compile.compiler import compile_protocol
from packages.domain.core import Timestamp
from packages.domain.manifest import RunManifest
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PreflightFinding,
    PreflightFindingCode,
    PreflightReport,
    PreflightStatus,
)


class ManifestFreezeError(ValueError):
    """Preflight 未通过时禁止冻结 Manifest。"""


@dataclass(frozen=True, slots=True)
class PricingFreeze:
    """Optional pricing snapshot pair carried into Manifest freezing."""

    table: PricingTable | None = None
    store: PricingSnapshotStore | None = None


def _status(findings: list[PreflightFinding]) -> PreflightStatus:
    if any(item.severity is FindingSeverity.ERROR for item in findings):
        return PreflightStatus.FAIL
    if any(item.severity is FindingSeverity.WARNING for item in findings):
        return PreflightStatus.WARN
    return PreflightStatus.PASS


def _budget_finding(message: str) -> PreflightFinding:
    return PreflightFinding(
        PreflightFindingCode.BUDGET_EXHAUSTED.value,
        FindingSeverity.ERROR,
        message,
        "budget",
    )


def _resource_checks(
    plan: CompiledRunPlan,
    context: PreflightContext,
    compile_findings: tuple[PreflightFinding, ...],
) -> tuple[list[PreflightFinding], list[str]]:
    findings = list(compile_findings)
    findings.extend(check_models(plan, context))
    findings.extend(check_tools(plan, context))
    findings.extend(check_workspaces(plan, context))
    findings.extend(check_team(plan, context))
    policy_findings, risks = check_policy(plan, context)
    findings.extend(policy_findings)
    return findings, risks


def _budget_findings(check: BudgetCheck, risks: list[str]) -> list[PreflightFinding]:
    findings = [
        _budget_finding(f"budget {key} requires {quantity}, limit is {limit}")
        for key, (quantity, limit) in check.exceeded.items()
    ]
    for key in check.unknown_limits:
        findings.append(
            PreflightFinding(
                PreflightFindingCode.BUDGET_LIMIT_UNKNOWN.value,
                FindingSeverity.WARNING,
                f"budget limit is not configured: {key}",
                "budget",
            )
        )
        risks.append(f"budget limit not configured: {key}")
    for resource_type in check.unmapped_types:
        findings.append(
            PreflightFinding(
                PreflightFindingCode.BUDGET_RESOURCE_UNMAPPED.value,
                FindingSeverity.WARNING,
                f"budget resource type has no limit mapping: {resource_type.value}",
                "budget",
            )
        )
        risks.append(f"budget resource type unmapped: {resource_type.value}")
    return findings


def _budget_preflight(
    plan: CompiledRunPlan,
    context: PreflightContext,
    findings: list[PreflightFinding],
    risks: list[str],
) -> str | None:
    budget_policy = context.catalog.budget_policies.get(context.project.budget_policy_id)
    if budget_policy is None:
        findings.append(
            PreflightFinding(
                PreflightFindingCode.BUDGET_MISSING.value,
                FindingSeverity.ERROR,
                f"budget policy {context.project.budget_policy_id} is unavailable",
                "budget",
            )
        )
        return None
    reservations = tuple(plan.budget_reservations)
    budget_check = check_budget(reservations, budget_policy)
    findings.extend(_budget_findings(budget_check, risks))
    if any(item.severity in {FindingSeverity.ERROR, FindingSeverity.WARNING} for item in findings):
        return None
    return reserve_budget(reservations, budget_policy, context.budget_ledger).reservation_ref


def run_preflight(
    plan: CompiledRunPlan,
    context: PreflightContext,
    compile_findings: tuple[PreflightFinding, ...] = (),
) -> PreflightReport:
    findings, risks = _resource_checks(plan, context, compile_findings)
    reservation_ref = _budget_preflight(plan, context, findings, risks)
    return PreflightReport(
        status=_status(findings),
        findings=findings,
        reserved_budget_ref=reservation_ref,
        unresolved_risks=sorted(set(risks)),
    )


def compile_and_preflight(
    protocol: Any,
    catalog: Any,
    project: ProjectSettings,
    context: PreflightContext,
) -> tuple[CompiledRunPlan | None, PreflightReport]:
    """编译并预检的组合入口。

    编译失败（plan 为 None 或存在 ERROR finding）时直接返回 FAIL 报告，
    防止调用方丢弃 compile findings 后错误地冻结 Manifest。
    """
    compile_result = compile_protocol(protocol, catalog, project)
    if compile_result.plan is None:
        report = PreflightReport(
            status=PreflightStatus.FAIL,
            findings=list(compile_result.findings),
        )
        return None, report
    report = run_preflight(compile_result.plan, context, compile_result.findings)
    return compile_result.plan, report


def freeze_manifest(
    run_id: str,
    plan: CompiledRunPlan,
    report: PreflightReport,
    context: PreflightContext,
    *,
    pricing_freeze: PricingFreeze | None = None,
) -> RunManifest:
    """Freeze a manifest and, when configured, persist its pricing snapshot.

    A non-empty pricing pair is fail-closed: the pricing reference and the
    snapshot must be written together so later projections never fall back to
    the table loaded at read time.
    """
    if not report.passed:
        raise ManifestFreezeError("cannot freeze manifest before a passing preflight")
    return _manifest_of(
        run_id,
        plan,
        report,
        context,
        _release_pricing(pricing_freeze),
    )


@dataclass(frozen=True, slots=True)
class _PricingRefs:
    version: str | None
    digest: str | None


def _release_pricing(pricing_freeze: PricingFreeze | None) -> _PricingRefs:
    table = pricing_freeze.table if pricing_freeze is not None else None
    store = pricing_freeze.store if pricing_freeze is not None else None
    if table is None:
        return _PricingRefs(None, None)
    if store is None:
        raise ManifestFreezeError(
            "cannot freeze a pricing reference without a pricing snapshot store;"
            " the projection would address a snapshot that was never persisted"
        )
    store.put(table)
    return _PricingRefs(table.version, table.pricing_digest())


def _manifest_of(
    run_id: str,
    plan: CompiledRunPlan,
    report: PreflightReport,
    context: PreflightContext,
    pricing: _PricingRefs,
) -> RunManifest:
    policy_version = context.catalog.policy.version.text if context.catalog.policy else None
    frozen_contracts: dict[str, object] = {
        ref: context.catalog.task_contracts[ref]
        for ref in plan.task_contract_refs
        if ref in context.catalog.task_contracts
    }
    return RunManifest(
        run_id=run_id,
        project_id=context.project.project_id,
        protocol_version=plan.protocol_version,
        protocol_digest=plan.protocol_digest,
        compiled_plan_digest=plan.digest(),
        role_definitions=dict(context.catalog.roles),
        agent_specs=dict(context.catalog.agents),
        resolved_models=dict(plan.resolved_models),
        model_runtime_fingerprints=dict(context.runtime_fingerprints),
        effective_tools={
            f"{item.phase_id}:{item.capability}": list(item.provider_ids)
            for item in plan.tool_requirements
        },
        tool_pack_digests=sorted(plan.tool_pack_digests.values()),
        task_contracts=frozen_contracts,
        policy_version=policy_version,
        workspace_backend=context.project.workspace_backend,
        # PLAN-20260919-107（EC-01）：执行基质由组合根声明（选择面）；未声明保持
        # None —— M7 的「不伪填充」口径不变，只是以前无来源、现在有来源。
        execution_backend=context.execution_substrate,
        budget_reservation_ref=report.reserved_budget_ref,
        frozen_at=Timestamp.now(),
        pricing_version=pricing.version,
        pricing_digest=pricing.digest,
    )


def preflight_report_payload(report: PreflightReport) -> dict[str, Any]:
    estimated_cost = None
    if report.estimated_cost is not None:
        estimated_cost = report.estimated_cost.minor_units / 100
    estimated_cost_currency = (
        report.estimated_cost.currency if report.estimated_cost is not None else None
    )
    return {
        "status": report.status.value,
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity.value,
                "message": finding.message,
                "subject_ref": finding.subject_ref,
            }
            for finding in report.findings
        ],
        "estimated_cost": estimated_cost,
        "estimated_cost_currency": estimated_cost_currency,
        "reserved_budget_ref": report.reserved_budget_ref,
        "unresolved_risks": list(report.unresolved_risks),
    }
