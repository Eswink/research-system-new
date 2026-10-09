"""Preflight 的 Policy 评估：NativePolicyEvaluator 包装与 human gate 检查。"""

from __future__ import annotations

from packages.application.policy.native import PolicyRequest
from packages.application.ports import PolicyEvaluator, PreflightContext
from packages.domain.enums import GateType, PolicyDecision
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PreflightFinding,
    PreflightFindingCode,
    ToolRequirement,
)


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _warning(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.WARNING, message, subject)


def _info(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    """声明性控制门（HUMAN_GATE，WP-H）：INFO 呈现 + unresolved_risks 登记，
    不阻断 freeze；执行循环在该 phase 前注册审批并进入 WAITING_FOR_APPROVAL。"""
    return PreflightFinding(code, FindingSeverity.INFO, message, subject)


# capability → policy scope 映射。单一事实源：examples/config/policy.yaml 中
# 显式带 scope 的规则；新增带 scope 的规则时必须同步更新本常量（有测试锁死一致性）。
_CAPABILITY_SCOPE: dict[str, str] = {
    "workspace.read": "project",
    "artifact.read": "project",
    "evidence.read": "project",
    # GOAL-20261006-031 EC-01（授权 1）：同轮同步的 6 条只读放行（与 policy.yaml 的
    # allow 同源；两张表的并集由 `tests/application/test_m2_audit.py` 的既有判据锁死，
    # 改一侧不改另一侧即判红）。
    "run.read": "project",
    "claim.read": "project",
    "deliverable.read": "project",
    "budget.read": "project",
    "experiment.read": "project",
    "experiment_plan.read": "project",
    "artifact.write": "run",
    "literature.search": "approved_tool_providers",
    "literature.read": "approved_tool_providers",
    # GOAL-20261006-031 EC-02（授权 2）：`citation.validate` 放行的镜像条目（与
    # `policy.yaml` 的同一组规则同源；并集相等由既有 `test_m2_audit` 判据锁死）。
    "citation.validate": "approved_tool_providers",
    # GOAL-20261008-036 EC-02（授权承继 (0)）：`review.read` 放行的镜像条目（与
    # `policy.yaml` 的同一条规则同源；并集相等同上由既有 `test_m2_audit` 判据锁死）。
    "review.read": "project",
    # GOAL-20261008-037 EC-03：`research_state.read` 放行的镜像条目（与 policy.yaml 的
    # allow 同源；scope 与同级读能力对齐 = project）。
    "research_state.read": "project",
    # GOAL-20261009-042 EC-02：`memory.read` 放行的镜像条目（与 policy.yaml 的 allow 同源；
    # scope 与同级读能力对齐 = project）。并集相等由既有 `test_m2_audit` 判据锁死。
    "memory.read": "project",
    "network.academic": "approved_domains",
}


# 门链时刻能力（非 preflight 工具需求）：同一能力在多个 scope 上分别声明，
# scope 由调用方按领域语义给出（memory.write → memory tier）。与 _CAPABILITY_SCOPE
# 一起构成 policy.yaml 的镜像契约（有测试锁死两者并集 == 声明对）。
_GATE_CAPABILITY_SCOPES: dict[str, frozenset[str]] = {
    "memory.write": frozenset({"SESSION", "RUN", "PROJECT", "ORGANIZATION"}),
}


def _policy_scope(capability: str) -> str | None:
    return _CAPABILITY_SCOPE.get(capability)


def policy_scope_for(capability: str) -> str | None:
    """能力 → 求值 scope（GOAL-011 EC-01：**执行期**复用 preflight 的同一张表）。

    带 scope 的 allow 规则要求请求里的 scope 相等才匹配；执行期若不补这一字段，
    preflight 放行的能力会在执行期落到 `default_effect`（DENY）——同一能力两处结论。
    """
    return _policy_scope(capability)


def gate_capability_scopes() -> dict[str, frozenset[str]]:
    """门链能力 → 求值 scope 集合（控制面可见性读取；返回值不就地修改）。"""
    return _GATE_CAPABILITY_SCOPES


def _evaluate_requirement(
    requirement: ToolRequirement,
    evaluator: PolicyEvaluator,
    context: PreflightContext,
) -> tuple[PreflightFinding | None, str | None]:
    result = evaluator.evaluate(
        PolicyRequest(
            actor=f"project:{context.project.project_id}",
            capability=requirement.capability,
            scope=_policy_scope(requirement.capability),
            resource=requirement.phase_id,
        )
    )
    if result.decision is PolicyDecision.DENY:
        return (
            _finding(
                PreflightFindingCode.POLICY_DENIED.value,
                f"policy denied capability {requirement.capability}: {result.reason}",
                f"phase:{requirement.phase_id}",
            ),
            None,
        )
    if result.decision is PolicyDecision.REQUIRE_APPROVAL:
        return (
            _warning(
                PreflightFindingCode.POLICY_APPROVAL_REQUIRED.value,
                f"approval required for capability {requirement.capability}",
                f"phase:{requirement.phase_id}",
            ),
            f"approval required: {requirement.capability}",
        )
    if result.decision is PolicyDecision.ALLOW_WITH_CONSTRAINTS:
        constraints = ", ".join(sorted(result.constraints))
        return None, f"policy constraints for {requirement.capability}: {constraints}"
    return None, None


def check_policy(
    plan: CompiledRunPlan,
    context: PreflightContext,
) -> tuple[list[PreflightFinding], list[str]]:
    policy = context.catalog.policy
    if policy is None:
        return [
            _finding(PreflightFindingCode.POLICY_MISSING.value, "no policy definition is available")
        ], []
    evaluator = context.policy_evaluator
    if evaluator is None:
        return [
            _finding(
                PreflightFindingCode.POLICY_MISSING.value,
                "no policy evaluator is injected in preflight context",
            )
        ], []
    findings: list[PreflightFinding] = []
    risks: list[str] = []
    for requirement in plan.tool_requirements:
        finding, risk = _evaluate_requirement(requirement, evaluator, context)
        if finding is not None:
            findings.append(finding)
        if risk is not None:
            risks.append(risk)
    for gate in plan.gates:
        if gate.gate is GateType.HUMAN_GATE:
            findings.append(
                _info(
                    PreflightFindingCode.HUMAN_GATE_REQUIRED.value,
                    f"human gate required for phase {gate.phase_id}",
                    f"phase:{gate.phase_id}",
                )
            )
            risks.append(f"human gate required: {gate.phase_id}")
    return findings, risks
