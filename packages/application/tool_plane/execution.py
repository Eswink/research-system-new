"""ExecuteToolCall use case：execution-time policy 门禁 → provider 分发。

Double enforcement 的 execution-time 半面（exposure-time 在 preflight）：
调用前经 PolicyEvaluator 重新裁决 capability；DENY 抛
PermanentPortError(POLICY_DENIED)。ToolProvider 不拥有 Policy truth，
本 use case 是唯一策略裁决点。

M15 观测:`telemetry` 可选注入(默认 None);TOOL_CALL span 记录
tool_id/resource_type/attempt 与 outcome,无内容通道(ADR-0026)。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.errors import PermanentPortError
from packages.application.ports.policy_evaluator import PolicyEvaluator, PolicyRequest
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.tool_provider import ToolProvider
from packages.domain.enums import FailureCategory, PolicyDecision
from packages.domain.tools import (
    ToolCallRecord,
    ToolProviderSpec,
    ToolResultRecord,
)

_TOOL_ACTION = "tool_call"


@dataclass(frozen=True, slots=True)
class ExecuteToolCallOutcome:
    decision: PolicyDecision
    result: ToolResultRecord | None = None


def evaluate_execution_policy(
    evaluator: PolicyEvaluator,
    actor: str,
    capability: str,
    resource: str,
) -> PolicyDecision:
    return evaluator.evaluate(
        PolicyRequest(
            actor=actor,
            capability=capability,
            action=_TOOL_ACTION,
            resource=resource,
        )
    ).decision


def _deny(capability: str, resource: str) -> PermanentPortError:
    return PermanentPortError(
        f"execution-time policy denied capability {capability} for {resource}",
        failure_category=FailureCategory.POLICY_DENIED,
    )


def _approval_required(capability: str, resource: str) -> PermanentPortError:
    return PermanentPortError(
        f"tool execution requires approval for capability {capability} ({resource})",
        failure_category=FailureCategory.APPROVAL_REJECTED,
    )


def execute_tool_call(  # noqa: PLR0913 - Port 契约签名,telemetry 为可选尾参
    provider: ToolProvider,
    provider_spec: ToolProviderSpec,
    call: ToolCallRecord,
    policy: PolicyEvaluator,
    actor: str,
    *,
    telemetry: TelemetrySink | None = None,
) -> ExecuteToolCallOutcome:
    """execution-time 检查后执行（与 Policy Wrapper 同语义，四面对齐）。

    DENY → POLICY_DENIED；REQUIRE_APPROVAL → APPROVAL_REJECTED（阻塞，
    不触达 provider；审批通道接通前不得静默放行）；其余决策执行。
    """
    attributes: dict[str, object] = {
        "tool_id": call.tool_id,
        "resource_type": provider_spec.kind.value,
        "attempt": call.attempt,
    }
    with operation(
        telemetry,
        scope=OperationScope.TOOL_CALL,
        name="tool.execute",
        correlation=CorrelationRef(task_id=call.task_id or None),
        attributes=attributes,
    ) as op:
        decision = evaluate_execution_policy(
            policy,
            actor,
            call.capability,
            resource=call.tool_id,
        )
        if decision is PolicyDecision.DENY:
            op.set_outcome(OperationOutcome.DENIED, FailureCategory.POLICY_DENIED.value)
            raise _deny(call.capability, call.tool_id)
        if decision is PolicyDecision.REQUIRE_APPROVAL:
            op.set_outcome(OperationOutcome.DENIED, FailureCategory.APPROVAL_REJECTED.value)
            raise _approval_required(call.capability, call.tool_id)
        try:
            result = provider.execute(provider_spec, call)
        except PermanentPortError as exc:
            category = exc.failure_category or FailureCategory.EXECUTION_FAILURE
            op.set_outcome(OperationOutcome.FAILED, category.value)
            raise
        except Exception:
            op.set_outcome(OperationOutcome.FAILED, FailureCategory.EXECUTION_FAILURE.value)
            raise
        op.set_outcome(OperationOutcome.OK)
        return ExecuteToolCallOutcome(decision=decision, result=result)


def require_frozen_tool_set(
    frozen_tool_set: tuple[str, ...],
    provider_id: str,
) -> None:
    """AgentSession 启动后 Effective Tool Set 冻结（ADR-0004）。

    不在冻结集合内的 provider 一律拒绝执行，防止会话后新增工具面。
    """
    if provider_id not in frozen_tool_set:
        raise PermanentPortError(
            f"provider {provider_id} is not in the frozen tool set",
            failure_category=FailureCategory.POLICY_DENIED,
        )
