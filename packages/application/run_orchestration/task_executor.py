"""单任务执行循环：lease 获取、heartbeat、会话执行、完成/取消。

at-least-once + idempotency（PORTS.md §1）：submit 由 WorkflowEngine
去重；retry 仅限 TransientPortError 且受 TaskContract.retry_policy 约束
（permanent 失败不重试——retry boundary）。

M7 恢复边界（诚实声明）：Port 为同步语义（M5 D2），run() 阻塞期间
进程内不产生心跳；心跳在会话执行前/后发送。lease TTL 必须大于单任务
执行上限，超出后由 recover_expired_leases 收敛（重启恢复路径）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from packages.application.experiments.evidence_admission import ExperimentEvidenceResult
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.ports.agent_runtime import (
    AgentRuntime,
    AgentSessionResult,
    AgentSessionSpec,
)
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.errors import (
    PermanentPortError,
    PortError,
    TransientPortError,
)
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    TaskLease,
    WorkflowEngine,
)
from packages.domain.enums import FailureCategory
from packages.domain.roles import AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask, RetryPolicy, TaskContract


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    task: ResearchTask
    outcome: str
    session_result: AgentSessionResult | None = None
    experiment_outcome: ExperimentExecutionOutcome | None = None
    experiment_admission: ExperimentEvidenceResult | None = None
    attempts: int = 1
    failure_category: FailureCategory | None = None
    message: str = ""

    @property
    def succeeded(self) -> bool:
        return self.outcome == "SUCCEEDED"


class ResumeManifestMismatchError(Exception):
    """resume 会话的 manifest 与冻结 snapshot 不一致（AGENTS.md §5）。"""


@dataclass(frozen=True, slots=True)
class SessionSpecContext:
    """create_session 所需的领域装配（由 orchestration 层填充）。"""

    role: RoleDefinition
    agent: AgentSpec
    frozen_manifest_digest: str
    frozen_tool_set: tuple[str, ...] = field(default_factory=tuple)
    # M15 债务清偿:phase 归属(观测 PHASE span 分组/父子链接用);缺省 "" 表示
    # 来源不携带 phase 信息(如 resume 重建路径)——此时 TASK 落回 RUN 父
    phase_id: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionDeps:
    """执行循环所需的 Port 组合（composition root 注入）。"""

    engine: WorkflowEngine
    runtime: AgentRuntime
    # M15:失败路径记账需要 BudgetLedger;None 时失败不落账(既有行为)
    budget: BudgetLedger | None = None


def _retry_policy(contract: TaskContract) -> RetryPolicy:
    return contract.retry_policy or RetryPolicy(max_attempts=1)


def _retryable(error: PortError, policy: RetryPolicy) -> bool:
    if not isinstance(error, TransientPortError):
        return False
    if error.failure_category is None:
        return False
    if policy.retryable_categories and error.failure_category not in policy.retryable_categories:
        return False
    return True


def execute_task(
    deps: ExecutionDeps,
    task: ResearchTask,
    contract: TaskContract,
    spec_context: SessionSpecContext,
    trace_id: str,
) -> TaskExecutionResult:
    """执行单个任务：submit → lease → heartbeat → session → complete。

    返回 TaskExecutionResult；业务失败（会话 FAILED / 验收拒绝）以
    outcome=FAILED 表达，不是系统异常。系统级 permanent 失败直接抛出。
    """
    engine = deps.engine
    engine.submit(task, contract)
    policy = _retry_policy(contract)
    attempts = 0
    while True:
        attempts += 1
        acquired = _acquire_or_fail(engine, task)
        if acquired[0] is None:
            # 重放/去重边界：任务已被投递但本执行单元无 lease 权限时安全收敛，
            # 不传播崩溃（同一 run 重放 → RUN FAILED，不产生重复副作用）。
            return _task_failed(task, attempts, None, acquired[1] or "task already delivered")
        lease = acquired[0]
        current = _with_attempt(task, attempts, lease.lease_id)
        result = _attempt_once(
            _AttemptInputs(deps, contract, spec_context, trace_id), current, lease
        )
        if result is not None:
            return result
        if attempts >= policy.max_attempts:
            _record_attempt_usage(deps.budget, current, attempts, "retry budget exhausted")
            return _task_failed(current, attempts, None, "retry budget exhausted")


@dataclass(frozen=True, slots=True)
class _AttemptInputs:
    """单次尝试的输入面（参数对象）。"""

    deps: ExecutionDeps
    contract: TaskContract
    spec_context: SessionSpecContext
    trace_id: str


def _attempt_once(
    inputs: _AttemptInputs,
    task: ResearchTask,
    lease: TaskLease,
) -> TaskExecutionResult | None:
    """单次尝试：heartbeat → session → complete；失败返回 None 表示可重试。"""
    engine = inputs.deps.engine
    try:
        renewed = engine.heartbeat(lease)
        result = _run_session(
            inputs.deps.runtime, task, inputs.contract, inputs.spec_context, inputs.trace_id
        )
        outcome = "SUCCEEDED" if result.status == "SUCCEEDED" else "FAILED"
        engine.complete(renewed, TaskCompletion(task_id=task.id.value, outcome=outcome))
        return TaskExecutionResult(
            task=task,
            outcome=outcome,
            session_result=result,
            attempts=task.attempt,
        )
    except TransientPortError as error:
        _record_attempt_usage(inputs.deps.budget, task, task.attempt, str(error.failure_category))
        if not _retryable(error, _retry_policy(inputs.contract)):
            return _task_failed(task, task.attempt, error.failure_category, str(error))
        return None
    except PermanentPortError as error:
        _record_attempt_usage(inputs.deps.budget, task, task.attempt, str(error.failure_category))
        return _task_failed(task, task.attempt, error.failure_category, str(error))


def _acquire_or_fail(
    engine: WorkflowEngine, task: ResearchTask
) -> tuple[TaskLease | None, str | None]:
    """获取 lease；任务已被投递（重放边界）时返回 (None, message) 安全收敛。"""
    try:
        return engine.acquire_lease(task.id.value), None
    except PermanentPortError as error:
        return None, str(error)


def _record_attempt_usage(
    budget: BudgetLedger | None,
    task: ResearchTask,
    attempt: int,
    reason: str | None,
) -> None:
    """失败/重试耗尽路径记账(M15,attempt 作用域)。"""
    from packages.application.run_orchestration.usage_recording import record_attempt_usage

    record_attempt_usage(budget, task, attempt, reason)


def _task_failed(
    task: ResearchTask,
    attempts: int,
    failure_category: FailureCategory | None,
    message: str,
) -> TaskExecutionResult:
    return TaskExecutionResult(
        task=task,
        outcome="FAILED",
        attempts=attempts,
        failure_category=failure_category,
        message=message,
    )


def _with_attempt(task: ResearchTask, attempt: int, lease_id: str) -> ResearchTask:
    return replace(task, attempt=attempt, lease_id=lease_id)


def _run_session(
    runtime: AgentRuntime,
    task: ResearchTask,
    contract: TaskContract,
    spec_context: SessionSpecContext,
    trace_id: str,
) -> AgentSessionResult:
    """create_session（携带冻结 manifest 引用）+ run；resume 校验冻结语义。"""
    spec = AgentSessionSpec(
        task_id=task.id,
        task_contract=contract,
        role=spec_context.role,
        agent=spec_context.agent,
        frozen_tool_set=spec_context.frozen_tool_set,
        manifest_ref=spec_context.frozen_manifest_digest,
    )
    handle = runtime.create_session(spec)
    _assert_frozen_manifest(spec, spec_context)
    return runtime.run(handle.session_id)


def _assert_frozen_manifest(spec: AgentSessionSpec, context: SessionSpecContext) -> None:
    """resume/会话必须基于冻结 snapshot：manifest 引用与 digest 不一致即拒绝。"""
    if spec.manifest_ref != context.frozen_manifest_digest:
        raise ResumeManifestMismatchError(
            f"session manifest ref {spec.manifest_ref!r} does not match frozen "
            f"{context.frozen_manifest_digest!r}"
        )
