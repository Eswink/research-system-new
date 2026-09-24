"""GovernedExperimentExecutor: policy/credential/budget/cancellation seam.

M9's ExperimentExecutor is intentionally low-level and does not own policy,
credentials or budget.  IG-1 requires that no upstream ALLOW is treated as a
permanent downstream authorization.  This wrapper is the authority boundary
for experiment execution: it re-evaluates execution-time policy, runs injected
budget/credential gates, checks cancellation, and records usage after a
successful terminal execution.
"""

from __future__ import annotations

from collections.abc import Callable

from packages.application.experiments.execute import ExperimentExecutor
from packages.application.experiments.types import (
    ExperimentExecutionOutcome,
    ExperimentExecutionRequest,
    with_policy_decisions,
)
from packages.application.ports.errors import PermanentPortError, PortCancelledError
from packages.application.ports.policy_evaluator import (
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.preflight.policy_check import policy_scope_for
from packages.domain.enums import FailureCategory, PolicyDecision

_CAPABILITIES = ("code.execute", "workspace.write.code", "artifact.write")


class GovernedExperimentExecutor:
    """Wraps ExperimentExecutor with cross-contract governance gates."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        inner: ExperimentExecutor,
        policy: PolicyEvaluator,
        actor: str = "system:experiment",
        budget_check: Callable[[], None] | None = None,
        credential_check: Callable[[], None] | None = None,
        cancellation_check: Callable[[], bool] | None = None,
        usage_recorder: Callable[[ExperimentExecutionOutcome], None] | None = None,
        idempotency_check: Callable[[ExperimentExecutionRequest], ExperimentExecutionOutcome | None]
        | None = None,
    ) -> None:
        self._inner = inner
        self._policy = policy
        self._actor = actor
        self._budget_check = budget_check
        self._credential_check = credential_check
        self._cancellation_check = cancellation_check
        self._usage_recorder = usage_recorder
        self._idempotency_check = idempotency_check

    def execute(self, request: ExperimentExecutionRequest) -> ExperimentExecutionOutcome:
        self._check_cancelled()
        if self._idempotency_check is not None:
            existing = self._idempotency_check(request)
            if existing is not None:
                return existing
        evaluated = self._enforce_policy(request)
        if self._budget_check is not None:
            self._budget_check()
        if self._credential_check is not None:
            self._credential_check()
        outcome = with_policy_decisions(self._inner.execute(request), evaluated)
        self._check_cancelled()
        if self._usage_recorder is not None:
            self._usage_recorder(outcome)
        return outcome

    def _check_cancelled(self) -> None:
        if self._cancellation_check is not None and self._cancellation_check():
            raise PortCancelledError("experiment execution cancelled before/during execution")

    def _enforce_policy(self, request: ExperimentExecutionRequest) -> dict[str, PolicyDecision]:
        """逐能力求值并**强制**；把求值结果原样返回（供调用方**如实记录**，不在这里再判）。"""
        evaluated: dict[str, PolicyDecision] = {}
        for capability in _CAPABILITIES:
            decision = self._policy.evaluate(
                PolicyRequest(
                    actor=self._actor,
                    capability=capability,
                    action="execute",
                    resource=request.run_id.value,
                    # 执行期必须补齐 preflight 用的那个 scope。带 scope 的 allow 规则
                    # （`artifact.write → run`）要求请求里的 scope 相等才匹配；不补就落到
                    # `default_effect: DENY`，于是同一能力「preflight 放行、执行期拒绝」
                    # （GOAL-011 cycle 9 实测：真实 policy.yaml 下沙箱实验在这一行被拒）。
                    # 工具面的同款补法是 `phase_capabilities.ScopedPolicy`；scope 表**同一张**
                    # （`policy_scope_for`），本处不新造映射。
                    scope=policy_scope_for(capability),
                )
            ).decision
            if decision is PolicyDecision.DENY:
                raise PermanentPortError(
                    f"execution-time policy denied {capability} for experiment "
                    f"{request.run_id.value}",
                    failure_category=FailureCategory.POLICY_DENIED,
                )
            if decision is PolicyDecision.REQUIRE_APPROVAL:
                raise PermanentPortError(
                    f"execution-time policy requires approval for {capability}",
                    failure_category=FailureCategory.APPROVAL_REJECTED,
                )
            evaluated[capability] = decision
        return evaluated
