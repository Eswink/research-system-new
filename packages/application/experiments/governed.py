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
)
from packages.application.ports.errors import PermanentPortError, PortCancelledError
from packages.application.ports.policy_evaluator import (
    PolicyEvaluator,
    PolicyRequest,
)
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
        self._enforce_policy(request)
        if self._budget_check is not None:
            self._budget_check()
        if self._credential_check is not None:
            self._credential_check()
        outcome = self._inner.execute(request)
        self._check_cancelled()
        if self._usage_recorder is not None:
            self._usage_recorder(outcome)
        return outcome

    def _check_cancelled(self) -> None:
        if self._cancellation_check is not None and self._cancellation_check():
            raise PortCancelledError("experiment execution cancelled before/during execution")

    def _enforce_policy(self, request: ExperimentExecutionRequest) -> None:
        for capability in _CAPABILITIES:
            decision = self._policy.evaluate(
                PolicyRequest(
                    actor=self._actor,
                    capability=capability,
                    action="execute",
                    resource=request.run_id.value,
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
