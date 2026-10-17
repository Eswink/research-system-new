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
from datetime import timedelta
from typing import Any, cast

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
    RetryNotDueError,
    TransientPortError,
)
from packages.application.ports.workflow_engine import (
    TaskCompletion,
    TaskLease,
    WorkflowEngine,
)
from packages.application.run_orchestration.usage_recording import record_attempt_usage
from packages.domain.enums import FailureCategory, TrustLabel
from packages.domain.memory import ContextSnapshot
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.roles import AgentSpec, RoleDefinition
from packages.domain.run import ResearchRun
from packages.domain.tasks import ResearchTask, RetryPolicy, TaskContract


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    task: ResearchTask
    outcome: str
    session_result: AgentSessionResult | None = None
    experiment_outcome: ExperimentExecutionOutcome | None = None
    experiment_admission: ExperimentEvidenceResult | None = None
    #: GOAL-20261014-077 EC-02：契约声明 `report` 时，本任务由**报告汇编器**执行 ⇒
    #: 这里装它的产物（`report_task.ReportAdmission`；注解取 `Any` 以免 application 层
    #: 两个模块互相 import 成环）。缺省 `None` ⇒ 该任务不是报告汇编。
    report_outcome: Any | None = None
    attempts: int = 1
    failure_category: FailureCategory | None = None
    message: str = ""
    # 这次失败**不是终局**：durable 侧已经是 RETRY_SCHEDULED，下一次尝试要等
    # deadline，由派发方（run 级：resume / 控制面；worker 级：claim）再来取。
    # run 级据此把 run 停在 PAUSED 而不是判失败——FAILED 是终态，会把声明的重排
    # 变成孤儿（PLAN-20260915-081）。
    retry_deferred: bool = False

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
    # EC-03（PLAN-20260919-109）：**执行目标**——这次会话要调用哪个 endpoint / 哪个
    # model。它此前只存在于 preflight 与 manifest，spec 不携带，于是真实 adapter 无从
    # 装配 LLM（生产把 3 参工厂塞给按 1 参调用的 SessionBuilder ⇒ 一调用就 TypeError）。
    # 在 catalog 在手的 orchestration 层解析，adapter 只消费、不反向依赖 catalog。
    # 凭据**值**不进 spec：只带 endpoint 自带的 `credential_ref`，值由 adapter 侧经
    # CredentialResolver 取。未解析出时保持 None ⇒ 真实 adapter **点名拒绝**，不静默
    # 拿空目标去装配；Fake 侧不看这两个字段，默认路径逐字节不变。
    endpoint: LLMEndpoint | None = None
    model: ModelDefinition | None = None
    # M15 债务清偿:phase 归属(观测 PHASE span 分组/父子链接用);缺省 "" 表示
    # 来源不携带 phase 信息(如 resume 重建路径)——此时 TASK 落回 RUN 父
    phase_id: str = ""
    # GOAL-010 EC-02：本 phase **声明的输入制品 id**（源头是 `ProtocolPhase.inputs`，
    # 一个此前无消费者的槽位）。它随 spec 走到会话结果注册处，在那里被登记成
    # 「**非**模型自述」的来源：内容由 ArtifactStore 复核、digest 可重算。
    # 缺省空 = 该 phase 未声明输入 ⇒ 不产生来源 ⇒ `EVIDENCE_COVERAGE` **不会**被满足
    # （这是如实的失败，不是缺陷）。命名空间与模型产出**不相交**：模型产出恒为
    # `{task_id}:{name}`，工具结果是 `tool-result:...`，本处由组合根以独立前缀种入。
    declared_input_artifacts: tuple[str, ...] = field(default_factory=tuple)
    # GOAL-20261016-081 EC-04：本 phase 从**上游 phase 的产物**读输入（编译期已校验：
    # 产出方是自己的上游、该产物在它的 `outputs` 里、产出方唯一）。每项
    # `(产出方, 产物名, 性质)`；运行期由编排把产出方的**真实任务**解析出来，再拼成
    # `{task_id}:{artifact_name}`。第三项（`TrustLabel`）**由产出方决定**，不在这里推导。
    # 与 `declared_input_artifacts` 的**性质差别**：那一类是组合根供给（`USER_PROVIDED`），
    # 这一类是**上游 phase 自己取回/产出**的东西 —— 它的 trust label 由产出方的声明性质决定。
    cross_phase_inputs: tuple[tuple[str, str, TrustLabel], ...] = field(default_factory=tuple)
    # GOAL-011 EC-01：本 phase **由运行链执行**的能力所属 provider id（源头是协议 phase 的
    # `capability_execution: run_chain`）。它们是冻结集的**子集**，被拿掉的只有「会话工具」
    # 这一个面：冻结集 / preflight / 策略判定都不变 ⇒ **声明化排除**，不是静默丢弃。
    # 缺省空 = 未声明 ⇒ 会话工具列表逐字节等于冻结集（既有语义）。
    run_chain_tool_ids: tuple[str, ...] = field(default_factory=tuple)
    # GOAL-028 EC-01：本 phase 的**会话工具绑定** `(provider_id, tool_name)`（源头是协议
    # phase 的 `session_tool_bindings`，唯一解释点在 `session_resolution`）。它只描述
    # 「哪个 provider 用哪个 SDK 工具名装配」——「那个名字对应哪个实现」是装配方的事。
    # 缺省空 = 未声明 ⇒ provider id 直接交给 SDK（既有语义，未注册即点名失败）。
    session_tool_bindings: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    # GOAL-20261008-034 EC-01：**本轮**的运行链调用声明（多轮循环按轮替换；空 = 沿用
    # 装配面那一批，既有语义逐字节不变）。
    round_calls: tuple[Any, ...] = field(default_factory=tuple)
    #: **上一轮**任务的制品前缀（`artifact_from_previous_round` 的收窄条件；执行期才知道）。
    previous_round_task_prefixes: tuple[str, ...] = field(default_factory=tuple)
    #: GOAL-20261014-077 EC-02：**本次 run 的领域实体**（本 phase 所属的那一个）。
    #:
    #: 为什么需要它（而不是去 `RunStore` 读）：run 行由**控制面**在编排返回**之后**才落库
    #: （`services/api/run_execution.run_from_execution`），所以执行**期间**存储里还没有这一行
    #: —— 一个在 run 内运行的任务若去存储读，只会读到「未知 run」。这里把**在场的那份事实**
    #: （`RunContext.run`）随 spec 交下去：与 `run_id_argument` 同层 —— 取值的来源是执行期
    #: 才有的对象，不是装配方能写死的量。缺省 `None` ⇒ 该装配不提供（既有语义逐字节不变）。
    run: "ResearchRun | None" = None
    #: GOAL-20261014-078 EC-01：**检索内容进会话上下文**的装配结果
    #: （`retrieval_context.build_retrieval_context` 的产物）。它随 spec 走到会话创建点，
    #: 在那里落进 `AgentSessionSpec.context_snapshot` —— 这是阶梯「检索」域 L1 → L2 的
    #: 机械含义：上游取回的文献**内容**进入模型上下文，而不只是落证据链与报告。
    #: 缺省 `None` ⇒ 本 phase 不带检索上下文（既有语义逐字节不变）。
    retrieval_context: Any | None = None
    #: GOAL-20261018-082 EC-01：前序知识的装配结果（与 `retrieval_context` 并列；None ⇒ 无该段）。
    prior_knowledge: Any | None = None


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

    **一次尝试一套账**（PLAN-20260915-080）：尝试序号取 durable 的交付代次
    （`lease.fence`），每一次尝试失败都先 `complete(FAILED, category)` 落账，再由 durable
    判据决定重排/死信。收口前这里用局部计数、每次交付都能"再来一遍预算"——实测
    `max_attempts=3` 在 3 次交付下执行了 9 次，退避声明也管不住这个循环。
    """
    engine = deps.engine
    engine.submit(task, contract)
    policy = _retry_policy(contract)
    while True:
        acquired = _acquire_or_fail(engine, task)
        if isinstance(acquired, _AcquireFailure):
            return _refused(task, acquired)
        lease = acquired
        attempt = max(lease.fence, 1)
        current = _with_attempt(task, attempt, lease.lease_id)
        outcome = _attempt_once(
            _AttemptInputs(deps, contract, spec_context, trace_id), current, lease
        )
        if isinstance(outcome, TaskExecutionResult):
            return outcome
        if attempt >= policy.max_attempts:
            # 不在此处记账:`_attempt_once` 已经为**这一次** attempt 记过账
            # (同 attempt 号 → 同 entry_id)。原先这里再记一次,导致
            # `InvalidInputError: duplicate usage entry` 穿出 use case,把一次
            # 干净的 task FAILED 变成未处理异常(M15 复审 BLOCKER-5,实测
            # transient/timeout 两条路径必现)。耗尽这一事实由返回值的
            # message 表达,不需要第二条 ledger entry。
            return _task_failed(current, attempt, outcome.category, "retry budget exhausted")
        if contract.retry_delay(attempt=attempt) > timedelta(0):
            # 声明了退避 ⇒ **不**在这个进程里等，把下一次尝试交回派发方
            # （PLAN-20260915-080）：deadline 是 durable 的事实，进程内自旋会绕过它。
            return _task_failed(
                current,
                attempt,
                outcome.category,
                "retry deferred to the dispatcher",
                deferred=True,
            )


@dataclass(frozen=True, slots=True)
class _Retryable:
    """这次尝试以可重试的失败结束（已经落账）；调用方决定还要不要再试一次。"""

    category: FailureCategory | None


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
) -> TaskExecutionResult | _Retryable:
    """单次尝试：heartbeat → session → complete。

    失败一律先落账（`complete` 带上失败类别），再返回 `_Retryable` 表示"还可以再试"。
    收口前这条路径直接返回 None 且**从不 complete**：任务停在 LEASED，durable 的重排/
    死信/退避判据一个都够不着（PLAN-20260915-080）。
    """
    engine = inputs.deps.engine
    live = lease
    try:
        live = engine.heartbeat(lease)
        result = _run_session(
            inputs.deps.runtime, task, inputs.contract, inputs.spec_context, inputs.trace_id
        )
        outcome = "SUCCEEDED" if result.status == "SUCCEEDED" else "FAILED"
        engine.complete(live, TaskCompletion(task_id=task.id.value, outcome=outcome))
        return TaskExecutionResult(
            task=task,
            outcome=outcome,
            session_result=result,
            attempts=task.attempt,
        )
    except TransientPortError as error:
        record_attempt_usage(
            inputs.deps.budget, task, task.attempt, _failure_reason(error.failure_category)
        )
        if not _retryable(error, _retry_policy(inputs.contract)):
            _complete_attempt(inputs, live, error.failure_category)
            return _task_failed(task, task.attempt, error.failure_category, str(error))
        # 可重试：把这次失败**落账**（带类别），让 durable 判据决定重排/死信——
        # 是否在同一次调用里继续下一轮由 execute_task 按处置结果决定。
        _complete_attempt(inputs, live, error.failure_category)
        return _Retryable(category=error.failure_category)
    except PermanentPortError as error:
        record_attempt_usage(
            inputs.deps.budget, task, task.attempt, _failure_reason(error.failure_category)
        )
        _complete_attempt(inputs, live, error.failure_category)
        return _task_failed(task, task.attempt, error.failure_category, str(error))


def _complete_attempt(
    inputs: _AttemptInputs, lease: TaskLease, category: FailureCategory | None
) -> None:
    """把这次失败的尝试落账（失败类别交给 durable 判据）。

    收口前失败路径**从不** complete：任务停在 LEASED、durable 侧看不到失败，
    `RETRY_SCHEDULED`/`DEAD_LETTER`/退避一个都够不着（PLAN-20260915-080）。

    传进来的必须是**当前**租约：heartbeat 会轮换 `lease_id`（M14 fencing），失败发生在
    心跳之后 ⇒ 手里的旧租约已经作废。
    """
    inputs.deps.engine.complete(
        lease,
        TaskCompletion(task_id=lease.task_id, outcome="FAILED", failure_category=category),
    )


def _failure_reason(category: FailureCategory | None) -> str | None:
    """failure category → ledger `unavailable_reason`;None 保持 None。

    原先是 `str(error.failure_category)`。诚实边界:`TransientPortError` /
    `PermanentPortError` 的构造签名要求非空分类,所以这两条路径上 None 实际
    不可达——"写入字面量 'None'" 是理论隐患,不是已发生的缺陷。基类字段仍是
    `FailureCategory | None`,因此保留显式全函数转换而不是依赖 `str()`。
    """
    return category.value if category is not None else None


@dataclass(frozen=True, slots=True)
class _AcquireFailure:
    """拿不到 lease 的两种情形：**还没到期**（可以再停）与真的交付不了。"""

    message: str
    not_due: bool = False


def _refused(task: ResearchTask, failure: _AcquireFailure) -> TaskExecutionResult:
    """acquire 被拒：还没到 deadline ⇒ 交回派发方重新停车；其余照旧安全收敛。

    重放/去重边界（任务已被投递但本执行单元无 lease 权限）仍然不传播崩溃
    （同一 run 重放 → RUN FAILED，不产生重复副作用）。
    """
    if failure.not_due:
        return _task_failed(task, max(task.attempt, 1), None, failure.message, deferred=True)
    return _task_failed(
        task, max(task.attempt, 1), None, failure.message or "task already delivered"
    )


def _acquire_or_fail(engine: WorkflowEngine, task: ResearchTask) -> TaskLease | _AcquireFailure:
    """获取 lease 或把拒绝原因交回调用方；**不在这里**决定 run 的生死。"""
    try:
        return engine.acquire_lease(task.id.value)
    except RetryNotDueError as error:
        return _AcquireFailure(str(error), not_due=True)
    except PermanentPortError as error:
        return _AcquireFailure(str(error))


def _task_failed(
    task: ResearchTask,
    attempts: int,
    failure_category: FailureCategory | None,
    message: str,
    *,
    deferred: bool = False,
) -> TaskExecutionResult:
    return TaskExecutionResult(
        task=task,
        outcome="FAILED",
        attempts=attempts,
        failure_category=failure_category,
        message=message,
        retry_deferred=deferred,
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
        run_chain_tool_ids=spec_context.run_chain_tool_ids,
        session_tool_bindings=spec_context.session_tool_bindings,
        manifest_ref=spec_context.frozen_manifest_digest,
        # GOAL-20261014-078 EC-01：检索内容进会话上下文（缺省 None ⇒ 逐字节不变）。
        context_snapshot=_context_snapshot(spec_context),
        # GOAL-20261016-081 EC-01：同一份摘录**进提示词**（缺省 None ⇒ 提示词逐字不变）。
        # 渲染是**确定性纯函数**（有界 / 截断可见 / 同一份 `entry.shown`）；
        # 取值点与快照**同一处** —— 两者消费同一个视图，不各自去查一次。
        retrieval_prompt=_retrieval_prompt(spec_context),
        # GOAL-20261018-082 EC-01：**前序知识那一段**（缺省 None ⇒ 提示词逐字不变）。
        # 与检索段**并列**：两段语义不同（前几轮已知 vs 这一轮取回），不合并、不互相替代。
        prior_knowledge_prompt=_prior_knowledge_prompt(spec_context),
        endpoint=spec_context.endpoint,
        model=spec_context.model,
    )
    handle = runtime.create_session(spec)
    _assert_frozen_manifest(spec, spec_context)
    return runtime.run(handle.session_id)


def _context_snapshot(spec_context: SessionSpecContext) -> ContextSnapshot | None:
    """会话上下文快照（GOAL-20261014-078 EC-01）。

    `retrieval_context` 是 `retrieval_context.RetrievalContextView`（装配结果：快照 +
    逐条读数 + 空集合的理由）；**缺省 `None` ⇒ 返回 `None`**（不带上下文 —— 与这个槽位
    出现之前**逐字节相同**）。本处只**取值**、不构造：构造发生在编排层的装配点
    （那里才有 ledger / artifacts 与 run 标识）。
    """
    view = spec_context.retrieval_context
    if view is None:
        return None
    return cast(ContextSnapshot | None, view.snapshot)


def _retrieval_prompt(spec_context: SessionSpecContext) -> str | None:
    """检索摘录 → 提示词那一段（GOAL-20261016-081 EC-01）。

    `retrieval_context` 是装配结果视图；**缺省 `None` ⇒ 返回 `None`**（提示词里不加
    那一段 —— 与这个槽位出现之前**逐字节相同**）。渲染器是纯函数，**不读**原始字节、
    **不新造**上限：它只把视图里已经摘录好的 `shown` 排成段落。
    """
    view = spec_context.retrieval_context
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import render_retrieval_prompt

    rendered = render_retrieval_prompt(view)
    return rendered or None


def _prior_knowledge_prompt(spec_context: SessionSpecContext) -> str | None:
    """前序知识 → 提示词那一段（GOAL-20261018-082 EC-01）。

    `prior_knowledge` 是装配结果视图；**缺省 `None` ⇒ 返回 `None`**（提示词里不加那一段
    —— 与这个槽位出现之前**逐字节相同**）。渲染器是纯函数：只把视图里已经摘录好的
    `shown` 排成段落，**不读**原始正文、**不新造**上限。
    """
    view = spec_context.prior_knowledge
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import (
        render_prior_knowledge_prompt,
    )

    rendered = render_prior_knowledge_prompt(view)
    return rendered or None


def _assert_frozen_manifest(spec: AgentSessionSpec, context: SessionSpecContext) -> None:
    """resume/会话必须基于冻结 snapshot：manifest 引用与 digest 不一致即拒绝。"""
    if spec.manifest_ref != context.frozen_manifest_digest:
        raise ResumeManifestMismatchError(
            f"session manifest ref {spec.manifest_ref!r} does not match frozen "
            f"{context.frozen_manifest_digest!r}"
        )
