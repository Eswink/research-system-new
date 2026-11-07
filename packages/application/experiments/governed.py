"""GovernedExperimentExecutor: policy/credential/budget/cancellation seam.

M9's ExperimentExecutor is intentionally low-level and does not own policy,
credentials or budget.  IG-1 requires that no upstream ALLOW is treated as a
permanent downstream authorization.  This wrapper is the authority boundary
for experiment execution: it re-evaluates execution-time policy, runs injected
budget/credential gates, checks cancellation, and records usage after a
successful terminal execution.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

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
        """逐能力求值并**强制**；把求值结果原样返回（供调用方**如实记录**，不在这里再判）。

        **GOAL-20261107-107 EC-10**：约束面（`sandbox_required` / `path_prefix` /
        `max_seconds`）此前只被 `policy/native.py` **返回**，全仓没有消费方 ⇒ 三条声明在
        执行边界上不存在。现在在这里读它们：`ALLOW_WITH_CONSTRAINTS` 的判词**不再等于放行**
        —— 约束不成立同样点名叫停。
        """
        evaluated: dict[str, PolicyDecision] = {}
        for capability in _CAPABILITIES:
            evaluation = self._policy.evaluate(
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
            )
            decision = evaluation.decision
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
            if evaluation.constraints:
                self._enforce_constraints(capability, evaluation.constraints, request)
            evaluated[capability] = decision
        return evaluated

    def _enforce_constraints(
        self,
        capability: str,
        constraints: Mapping[str, object],
        request: ExperimentExecutionRequest,
    ) -> None:
        """把 `allow_with_constraints` 的三条声明落成**可执行**的判定。

        **只检查声明的那些**（缺席 ≠ 默认值）：没有 `sandbox_required` 就不要求沙箱 ——
        本方法让既有声明生效，**不**新增策略。

        沙箱声明：本执行体只包沙箱执行，因此 `sandboxed` 缺席时**不**据此判拒（那会把
        既有装配全打死）；只有请求**明说** `sandboxed=False` 时才拒。这一点如实写在判词里，
        不假装「我们验证了沙箱」——验证沙箱是 `ExecutionBackend` 的事。
        """
        from packages.application.experiments.script_authority import (
            MAX_SECONDS_KEY,
            PATH_PREFIX_KEY,
            SANDBOX_KEY,
        )

        if constraints.get(SANDBOX_KEY) is True and getattr(request, "sandboxed", None) is False:
            raise PermanentPortError(
                f"{capability} requires a sandbox ({SANDBOX_KEY}) but this execution "
                "declares itself unsandboxed",
                failure_category=FailureCategory.POLICY_DENIED,
            )
        prefix = constraints.get(PATH_PREFIX_KEY)
        write_path = getattr(request, "write_path", None)
        if isinstance(prefix, str) and prefix and write_path is not None:
            target = str(write_path).replace("\\", "/")
            if ".." in Path(target).parts or not target.startswith(prefix.replace("\\", "/")):
                raise PermanentPortError(
                    f"{capability} declares writes under {prefix!r} but this execution writes "
                    f"{write_path!r}",
                    failure_category=FailureCategory.POLICY_DENIED,
                )
        limit = constraints.get(MAX_SECONDS_KEY)
        requested = getattr(request, "requested_seconds", None)
        if isinstance(limit, (int, float)) and requested is not None:
            if float(requested) > float(limit):
                raise PermanentPortError(
                    f"{capability} allows at most {limit}s but this execution asks for "
                    f"{requested}s",
                    failure_category=FailureCategory.POLICY_DENIED,
                )
