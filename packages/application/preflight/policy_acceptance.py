"""冻结门的**显式策略通道**（GOAL-20260923-012 EC-01，路径 (A)）。

**为什么需要这条通道**：`classify_risk(EffectClass.EXECUTE, …) → HIGH` 是**无条件**的
（`packages/domain/tools.py`），于是任何引用 EXECUTE provider 的计划都会拿到
`TOOL_RISK_ELEVATED`（WARNING）⇒ 报告 `WARN` ⇒ `freeze_manifest` 的
`if not report.passed: raise` **拒冻**（GOAL-011 cycle 6 首次实测，cycle 9 复现）。
用户于 2026-09-23 拍板：新增一条**显式、留痕、可审计**的接受口径，
而**不是**放宽风险分类、也**不是**让 WARN 无条件可冻。

**通道条件（当且仅当，全部满足才接受）**：

1. 报告状态是 `WARN`（`FAIL` 一律拒——那意味着存在 ERROR finding）；
2. 报告里**没有** `TOOL_RISK_ELEVATED` 以外的 WARNING（其它警示一律**不可转换**）；
3. 每条 `TOOL_RISK_ELEVATED` 的 provider 在冻结目录里可解析，其 `effect_class` 是 `EXECUTE`
   且 `classify_risk(...)` 判 `HIGH`（**只认 EXECUTE**；`CRITICAL` 或别的 effect 一律拒）；
4. 该 provider 服务的**每一条** `ToolRequirement` 经**同一个** `PolicyEvaluator` 求值为
   `ALLOW` 或 `ALLOW_WITH_CONSTRAINTS`（`DENY` / `REQUIRE_APPROVAL` / 求值器缺失 /
   该 provider 没有任何能力需求 ⇒ 一律拒）。

任一条不满足 ⇒ 拒冻，并由 :func:`freeze_refusal_message` **点名**缺哪条策略事实。

**明确不在本模块做的事**：不放宽 `classify_risk`；不改 `PreflightStatus` 与
`PreflightReport.passed` 的语义；不改任何 finding 的生成、code 或严重级。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.policy.native import PolicyRequest
from packages.application.ports import PreflightContext
from packages.application.ports.policy_evaluator import PolicyEvaluator
from packages.application.preflight.policy_check import policy_scope_for
from packages.domain.enums import EffectClass, PolicyDecision, RiskClass
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PreflightFinding,
    PreflightFindingCode,
    PreflightReport,
    PreflightStatus,
    ToolRequirement,
)
from packages.domain.tools import classify_risk

#: 唯一可被接受的警示 code（其余 WARNING **没有**通道）。
ACCEPTABLE_FINDING_CODE = PreflightFindingCode.TOOL_RISK_ELEVATED.value
#: 唯一可被接受的 effect 类别（授权范围逐字：「策略已显式允许的 EXECUTE」）。
ACCEPTABLE_EFFECT = EffectClass.EXECUTE
#: 「显式允许」的决策集：DENY 与 REQUIRE_APPROVAL 都**不算**允许。
_ALLOWING = frozenset({PolicyDecision.ALLOW.value, PolicyDecision.ALLOW_WITH_CONSTRAINTS.value})
_PROVIDER_PREFIX = "provider:"


@dataclass(frozen=True, slots=True)
class FreezeAcceptance:
    """冻结门的接受判定：要么带留痕放行，要么带**点名理由**拒绝。"""

    exceptions: tuple[dict[str, object], ...] = ()
    refusal_reasons: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        return not self.refusal_reasons

    @property
    def used_channel(self) -> bool:
        """True = 这次冻结**走了**显式策略通道（留痕非空）。"""
        return bool(self.exceptions)


def _warnings(report: PreflightReport) -> list[PreflightFinding]:
    return [item for item in report.findings if item.severity is FindingSeverity.WARNING]


def _subject_provider(finding: PreflightFinding) -> str | None:
    subject = finding.subject_ref or ""
    if not subject.startswith(_PROVIDER_PREFIX):
        return None
    return subject[len(_PROVIDER_PREFIX) :] or None


def _serving_requirements(plan: CompiledRunPlan, provider_id: str) -> list[ToolRequirement]:
    return [item for item in plan.tool_requirements if provider_id in item.provider_ids]


def _policy_version(context: PreflightContext) -> str | None:
    policy = context.catalog.policy
    return policy.version.text if policy is not None else None


def _evaluate(
    requirement: ToolRequirement, context: PreflightContext, evaluator: PolicyEvaluator
) -> tuple[str, dict[str, object]]:
    """用**同一个** PolicyEvaluator 与**同一张** scope 表求值（不新造第二套）。"""
    evaluation = evaluator.evaluate(
        PolicyRequest(
            actor=f"project:{context.project.project_id}",
            capability=requirement.capability,
            scope=policy_scope_for(requirement.capability),
            resource=requirement.phase_id,
        )
    )
    return evaluation.decision.value, dict(evaluation.constraints)


def _provider_refusal_reason(
    provider_id: str, plan: CompiledRunPlan, context: PreflightContext
) -> str | None:
    """解析一条 `TOOL_RISK_ELEVATED` 的 provider 面；可接受时返回 None。"""
    provider = context.catalog.tool_providers.get(provider_id)
    if provider is None:
        return f"provider {provider_id} is not resolvable in the frozen catalog"
    if provider.effect_class is not ACCEPTABLE_EFFECT:
        return (
            f"provider {provider_id} has effect class {provider.effect_class.value};"
            f" only an {ACCEPTABLE_EFFECT.value} risk has an acceptance channel"
        )
    if classify_risk(provider.effect_class, provider.trust_level) is not RiskClass.HIGH:
        return (
            f"provider {provider_id} is not HIGH by construction;"
            " only a HIGH EXECUTE risk has an acceptance channel"
        )
    if not _serving_requirements(plan, provider_id):
        return (
            f"provider {provider_id} serves no capability requirement in the compiled plan;"
            " there is no policy fact to allow"
        )
    return None


def _allowed_entries(
    provider_id: str,
    requirements: list[ToolRequirement],
    context: PreflightContext,
    evaluator: PolicyEvaluator,
    accepted_at: str,
) -> tuple[list[dict[str, object]], list[str]]:
    entries: list[dict[str, object]] = []
    reasons: list[str] = []
    version = _policy_version(context)
    for requirement in requirements:
        decision, constraints = _evaluate(requirement, context, evaluator)
        if decision not in _ALLOWING:
            reasons.append(
                f"capability {requirement.capability} (phase:{requirement.phase_id}) is not"
                f" explicitly allowed by policy {version}: decision={decision}"
            )
            continue
        entries.append({
            "capability": requirement.capability,
            "phase_id": requirement.phase_id,
            "provider_id": provider_id,
            "policy_version": version,
            "decision": decision,
            "constraints": constraints,
            "accepted_at": accepted_at,
        })
    return entries, reasons


def _dedupe(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    """同一 (provider, phase, capability) 只留一条：一条警示按 provider 出，而
    `check_tools` 是**按需求**逐条产出的 ⇒ 不去重会让留痕按需求数翻倍。"""
    unique: list[dict[str, object]] = []
    seen: set[tuple[object, object, object]] = set()
    for entry in entries:
        key = (entry["provider_id"], entry["phase_id"], entry["capability"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _channel_entries(
    plan: CompiledRunPlan,
    report: PreflightReport,
    context: PreflightContext,
    evaluator: PolicyEvaluator,
    accepted_at: str,
) -> tuple[list[dict[str, object]], list[str]]:
    entries: list[dict[str, object]] = []
    reasons: list[str] = []
    for finding in _warnings(report):
        if finding.code != ACCEPTABLE_FINDING_CODE:
            subject = finding.subject_ref or "no subject"
            reasons.append(
                f"WARNING {finding.code} ({subject}) is not an explicitly allowed EXECUTE risk;"
                " it has no acceptance channel"
            )
            continue
        provider_id = _subject_provider(finding)
        if provider_id is None:
            reasons.append(
                f"WARNING {finding.code} has no provider subject_ref; it has no acceptance channel"
            )
            continue
        refusal = _provider_refusal_reason(provider_id, plan, context)
        if refusal is not None:
            reasons.append(refusal)
            continue
        found, denied = _allowed_entries(
            provider_id, _serving_requirements(plan, provider_id), context, evaluator, accepted_at
        )
        entries.extend(found)
        reasons.extend(denied)
    return _dedupe(entries), reasons


def evaluate_freeze_acceptance(
    plan: CompiledRunPlan,
    report: PreflightReport,
    context: PreflightContext,
    *,
    accepted_at: str,
) -> FreezeAcceptance:
    """判定这次冻结能否被接受；不可接受时返回**点名**的理由（fail-closed）。"""
    if report.status is PreflightStatus.PASS:
        return FreezeAcceptance()
    if report.status is PreflightStatus.FAIL:
        return FreezeAcceptance(refusal_reasons=("the preflight report has ERROR findings",))
    if not _warnings(report):
        return FreezeAcceptance(refusal_reasons=("the preflight report has no WARNING finding",))
    evaluator = context.policy_evaluator
    if evaluator is None:
        return FreezeAcceptance(
            refusal_reasons=("no policy evaluator is injected in preflight context",)
        )
    entries, reasons = _channel_entries(plan, report, context, evaluator, accepted_at)
    if reasons:
        return FreezeAcceptance(refusal_reasons=tuple(reasons))
    return FreezeAcceptance(exceptions=tuple(entries))


def freeze_refusal_message(acceptance: FreezeAcceptance) -> str:
    """拒冻消息：既有前缀 + **逐条点名**缺失的策略事实（GOAL-012 EC-01 的 (c)）。"""
    return "cannot freeze manifest before a passing preflight: " + "; ".join(
        acceptance.refusal_reasons
    )
