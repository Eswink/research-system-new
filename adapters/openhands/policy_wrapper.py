"""PolicyWrappedToolExecutor：OpenHands execute_tool 直通路径的强制策略包装。

R-03 承接：SDK execute_tool() 可绕过 agent loop 的 confirmation/security；
Research OS 只允许经由本包装执行 direct tool execution（AGENTS.md §5）。
每次调用前强制 PolicyEvaluator.evaluate：
- ALLOW → 放行；
- DENY → PermanentPortError(POLICY_DENIED)；
- REQUIRE_APPROVAL → 阻塞该次调用 + approval.requested 事件（M6 无
  交互式审批循环，审批通道 M7）；
- ALLOW_WITH_CONSTRAINTS → 放行（约束由调用方策略执行）。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.agent_runtime import RuntimeEvent, RuntimeEventKind
from packages.application.ports.errors import PermanentPortError
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.domain.enums import FailureCategory, PolicyDecision

# SDK execute_tool 签名：execute_tool(self, tool_name: str, action: Action) -> Observation
ExecuteTool = Any


class PolicyDeniedError(PermanentPortError):
    """策略拒绝：工具调用被 PolicyEvaluator 裁决 DENY。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, failure_category=FailureCategory.POLICY_DENIED)


class PolicyApprovalRequiredError(PermanentPortError):
    """策略要求人工审批：调用被阻塞，等待审批通道（M7）。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, failure_category=FailureCategory.APPROVAL_REJECTED)


class PolicyWrappedToolExecutor:
    """独占执行面：所有直接工具执行必须经过本包装。"""

    def __init__(
        self,
        policy_evaluator: PolicyEvaluator,
        *,
        actor: str,
        scope: str,
        emit: Any = None,
    ) -> None:
        self._policy_evaluator = policy_evaluator
        self._actor = actor
        self._scope = scope
        self._emit = emit or (lambda event: None)

    def evaluate_tool_call(self, tool_name: str) -> PolicyEvaluation:
        """策略裁决；ALLOW/ALLOW_WITH_CONSTRAINTS 放行，否则抛错。"""
        request = PolicyRequest(
            actor=self._actor,
            capability=tool_name,
            action="execute",
            scope=self._scope,
            resource=tool_name,
        )
        evaluation = self._policy_evaluator.evaluate(request)
        if evaluation.decision is PolicyDecision.DENY:
            raise PolicyDeniedError(
                f"policy denied tool execution: {tool_name} ({evaluation.reason})"
            )
        if evaluation.decision is PolicyDecision.REQUIRE_APPROVAL:
            self._emit(
                RuntimeEvent(
                    session_id=self._scope,
                    kind=RuntimeEventKind.APPROVAL_REQUESTED,
                    message=tool_name,
                    payload={"tool_name": tool_name},
                )
            )
            raise PolicyApprovalRequiredError(
                f"tool execution requires approval: {tool_name} ({evaluation.reason})"
            )
        return evaluation

    def execute(
        self,
        execute_tool: ExecuteTool,
        tool_name: str,
        action: Any,
    ) -> Any:
        """经策略门禁后执行 SDK execute_tool；DENY/REQUIRE_APPROVAL 不触达 SDK。"""
        self.evaluate_tool_call(tool_name)
        return execute_tool(tool_name, action)


__all__ = [
    "PolicyWrappedToolExecutor",
    "PolicyDeniedError",
    "PolicyApprovalRequiredError",
]
