"""沙箱实验阶段的装配面（GOAL-011 EC-03）。

把**既有**实验执行链接进运行编排的 `PhaseRunnerDeps.experiment_task` 缝——接的是
`ExperimentExecutor` + `GovernedExperimentExecutor` + `DockerExecutionBackend`
（M9 已完成 6 容器 E2E 的那一个，见 `docs/roadmap/M12_COMPLETION_RECORD.md` DoD #5）。
**不新增执行后端、不新增依赖。**

为什么需要这一层：`phase_runner` 早就有这道缝（`experiment_task`，默认 `None`），但
**没有任何装配方接过它**——唯一的驱动方是 `tests/integration/test_ig1_phase_runner.py`，
且用的是 Fake 执行后端。`docs/roadmap/M12_COMPLETION_RECORD.md` §12 第 4 条把同类缺口
记成「预留在 run_orchestration 边界；对账已实现，**接入需 composition root**」。

三条**如实边界**（本模块不声称已解决）：

- 实验脚本按 `script` 声明复制进**实验沙箱工作区**（容器只挂工作区，不挂仓库）；
  契约没 pin 脚本时用装配面给的默认脚本——两者都没有则 `InvalidInputError`（不猜）。
- 实验的工作区是**独立**的沙箱工作区（本模块自建），与会话工作区不是同一个。
- 实验产出的**证据准入**走既有 `register_experiment_evidence`（
  `execute_experiment_task` 内部），本模块不另开准入路径。
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from adapters.workspace import FileWorkspaceBackend
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    GovernedExperimentExecutor,
)
from packages.application.experiments.arms import arm_experiment_id, declare_arms
from packages.application.experiments.plan_parameters import parameter_environment
from packages.application.m12_reference.clean_run_stages import derived_id, experiment_run_id_of
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.experiment_task import (
    ExperimentTaskDeps,
    execute_experiment_task,
)
from packages.application.run_orchestration.task_executor import (
    SessionSpecContext,
    TaskExecutionResult,
)
from packages.domain.core import ID
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.tasks import ResearchTask, TaskContract
from packages.domain.workspace import Workspace

#: 实验沙箱工作区里脚本的固定文件名（契约的 `command` 按它写）。
SCRIPT_NAME = "experiment.py"
#: 实验计划/运行的确定性命名空间（同一次 run 的实验 id 可复算）。
PLAN_NAME = "sandboxed-experiment"
#: 实验沙箱工作区的 workspace id（与会话工作区**不是**同一个）。
SANDBOX_WORKSPACE_ID = "sandbox-experiment"


@dataclass(frozen=True, slots=True)
class SandboxExperimentAssembly:
    """装配面需要的 Port 与量（与既有 clean-run 同形，取其最小子集）。

    `execution` 由调用方给出（本地装配给 `DockerExecutionBackend`）；本模块不构造
    执行后端，免得把「用哪个后端」写死在产品件里。
    """

    execution: Any
    artifacts: Any
    policy: Any
    image: str
    ledger: Any | None = None
    #: GOAL-20261026-097 EC-03：**执行后端的工厂**（`(image) -> ExecutionBackend`）。
    #: 非空 ⇒ `execution` 不得同时给（「两个后端」不可判定）；第一次派发时才调用它
    #: ⇒ **装配期零连接**（``docker.from_env`` 在构造时就摸 daemon，组合根若在装配期
    #: 构造后端，默认门里没有 Docker 的机器上 `assemble()` 直接炸）。
    #: 缺省 `None` ⇒ 逐字沿用 `execution`（既有语义不变）。
    execution_factory: Any | None = None
    #: 实验产物读面（`GET /runs/{id}/experiments`）读的是**实验存储**：执行完必须把
    #: `ExperimentRun` 存进去，否则"实验真的跑了"在读面上看不见。None ⇒ 不落库（调用方
    #: 自担：读面会如实为空，不伪造）。
    experiment_store: Any | None = None
    script: str | None = None
    root: str | None = None
    environment: dict[str, str] = field(default_factory=dict)
    #: GOAL-20261015-079 EC-01：**声明的实验参数**（白名单校验后进容器环境；
    #: 缺省空 ⇒ 请求里的环境与今天逐字相同 —— 脚本回落既有模块常量）。
    #: EC-02：声明了 `arms` 时，本字段作为**单臂**（未声明臂名）的缺省参数。
    parameters: dict[str, object] = field(default_factory=dict)
    #: GOAL-20261015-079 EC-02：**声明的实验臂**（`{臂名: 参数}` 或
    #: `[{name, parameters}]`）。缺省 `None` ⇒ **单臂**（今天的语义，逐字不变）；
    #: 声明 ≥ 1 个臂 ⇒ 每个臂各跑一次实验（各有自己的实验 id 与参数环境）。
    arms: object | None = None
    #: GOAL-20261015-080 EC-02：**设计的来源**。缺省 `None` ⇒ 臂来自本装配面（今天
    #: 的语义，逐字不变）；`"plan"` ⇒ 臂从**本 run 的计划产物内容**里读出（读取器见
    #: `design_from_plan`；读不到 / 白名单外 / 畸形一律**点名拒绝**，**不**回落本字段）。
    #: **与 `arms` 互斥**：两者同时声明 ⇒ 点名拒绝（「哪个说了算」不可判定）。
    design_source: str | None = None


#: `design_source` 认得的取值（**两个来源**，互斥）。
DESIGN_SOURCE_PLAN = "plan"
#: GOAL-20261018-088 EC-01：臂从**本 run 的系统取得证据**（`TrustLabel.RETRIEVED`）里读出
#: （读取器见 `experiments/design_from_retrieval`）。与 `"plan"` 互斥。
DESIGN_SOURCE_RETRIEVAL = "retrieval"
#: 认得的全部来源（点名拒绝时逐条列出）。
DESIGN_SOURCES: tuple[str, ...] = (DESIGN_SOURCE_PLAN, DESIGN_SOURCE_RETRIEVAL)


def sandbox_experiment_runner(
    assembly: SandboxExperimentAssembly,
) -> Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult]:
    """构造可直接放进 `PhaseRunnerDeps.experiment_task` 的派发器。

    每次调用执行**一次**实验：准备沙箱工作区 → 预注册计划 → 交给既有执行链 →
    结果由 `execute_experiment_task` 登记/门禁（调用方 `phase_runner` 继续处理）。

    **执行后端在首次派发时才取**（GOAL-20261026-097 EC-01/EC-03）：`execution_factory`
    非空时，本函数**不**碰它 —— 装配期零连接；镜像取**声明优先**解析后的那个
    （契约 pin 了就用契约的，否则用装配面的）。
    """
    execution = _DeferredExecution(assembly)

    def run(
        task: ResearchTask,
        contract: TaskContract,
        spec_context: SessionSpecContext,
        trace_id: str,
    ) -> TaskExecutionResult:
        """执行本任务的实验：声明了臂 ⇒ 逐臂各跑一次，否则单臂（返回主臂 = 第一个）。"""
        script, image = declared_or_assembled(assembly, contract)
        resolved = replace(assembly, script=script, image=image, execution=execution.proxy(image))
        deps = ExperimentTaskDeps(
            executor=_governed_executor(resolved),
            artifacts=assembly.artifacts,
            ledger=assembly.ledger,
            request_builder=_request_builder(assembly),
            provenance_builder=_provenance_builder,
        )
        arms = _arms_for(assembly, task)
        per_arm = {arm.name: _arm_deps(assembly, arm, deps) for arm in arms}
        if not arms:
            result = execute_experiment_task(deps, task, contract, spec_context, trace_id)
            _persist_run(assembly, result)
            return result
        results: list[TaskExecutionResult] = []
        for arm in arms:
            arm_result = execute_experiment_task(
                per_arm[arm.name], task, contract, spec_context, trace_id
            )
            _persist_run(assembly, arm_result)
            results.append(arm_result)
        return _primary_arm_result(results)

    return run


def declared_or_assembled(
    assembly: SandboxExperimentAssembly, contract: TaskContract
) -> tuple[str | None, str]:
    """本任务**该跑哪个脚本、哪个镜像**（GOAL-20261026-097 EC-03：声明优先）。

    与 `ExperimentExecutionSpec` 的 docstring 逐字一致：契约 pin 了就必须照用
    （**装配方不得覆盖契约 pin 的量**）；为空（`experiment_execution: {}` 的既有语义）
    ⇒ **逐字**回到装配面那两件。两个字段**各自独立**判 —— 只 pin 脚本的契约仍用装配面镜像。
    """
    declaration = contract.experiment
    script = assembly.script
    image = assembly.image
    if declaration is not None:
        script = declaration.script or script
        image = declaration.image or image
    return script, image


class _DeferredExecution:
    """按镜像**惰性**取得执行后端，同一镜像复用同一实例（GOAL-20261026-097 EC-01）。

    为什么必须惰性：`DockerExecutionBackend.__init__` 就 `docker.from_env()`（构造即连
    daemon）。组合根在装配期构造它 ⇒ 没有 Docker 的机器上 `assemble()` 直接炸，而
    `assemble()` 是默认门里被反复调用的装配入口。为什么按镜像缓存：契约可以 `pin` 不同
    镜像（EC-03），同一镜像重跑不该每次重建连接。
    """

    def __init__(self, assembly: SandboxExperimentAssembly) -> None:
        self._assembly = assembly
        self._by_image: dict[str, Any] = {}

    def proxy(self, image: str) -> Any:
        """本镜像的**惰性代理**（第一次 `execute` 时才取后端）。

        为什么是代理而不是「先取后端」：`_governed_executor(assembly)` 的签名不能变
        （既有判据用 `lambda _assembly: executor` 替换它）⇒ 「何时连 Docker」必须由
        `assembly.execution` 这个**值**自己决定。代理对 `ExperimentExecutor` 是透明的：
        它只被调用 `execute(...)`。
        """
        factory = self._assembly.execution_factory
        if factory is None:
            return self._assembly.execution

        def execute(spec: Any, timeout_seconds: int | None = None, **kwargs: Any) -> Any:
            backend = self._by_image.get(image)
            if backend is None:
                backend = factory(image)
                self._by_image[image] = backend
            return backend.execute(spec, timeout_seconds, **kwargs)

        return SimpleNamespace(execute=execute)  # 代理面 = `experiment` 用到的那一个方法


def _arms_for(assembly: SandboxExperimentAssembly, task: ResearchTask) -> tuple[Any, ...]:
    """本任务的实验臂（**来源唯一**：装配面声明，或计划产物 —— 不可兼有）。

    - `design_source is None` ⇒ 装配面声明（`declare_arms`，缺省空 ⇒ 单臂，逐字不变）；
    - `design_source == "plan"` ⇒ 读**本 run** 的计划产物内容（确定性、零出网、fail-closed）；
    - `design_source == "retrieval"`（GOAL-20261018-088）⇒ 读**本 run 的系统取得证据**
      （`TrustLabel.RETRIEVED`）—— 两个来源各自 fail-closed，互不回落；
    - **与 `arms` 同时非空** ⇒ 点名拒绝：两条来源都在时「哪个说了算」不可判定
      （静默取其一正是本 GOAL 要消灭的那种含混）；
    - 未认得的来源名 ⇒ 点名拒绝（**不**当成「没有来源」）。
    """
    source = getattr(assembly, "design_source", None)
    if source is None:
        return declare_arms(assembly)
    if source not in DESIGN_SOURCES:
        raise InvalidInputError(
            f"unknown experiment design source: {source!r} "
            f"(declared sources: {', '.join(DESIGN_SOURCES)})"
        )
    declared = declare_arms(assembly)
    if declared:
        raise InvalidInputError(
            f"both a {source}-derived design source and an explicit arm declaration are in "
            "effect; which one decides the experiment would be undecidable "
            f"(declared arms: {', '.join(arm.name for arm in declared)})"
        )
    if source == DESIGN_SOURCE_RETRIEVAL:
        from packages.application.experiments.design_from_retrieval import (
            read_design_from_retrieval,
        )

        # 没有证据账本就**没有「系统取得」这一面** ⇒ 点名拒绝（不是空设计、更不是回落到
        # 装配面的臂）：与「读不到就说读不到」同一条纪律。
        if assembly.ledger is None:
            raise InvalidInputError(
                "a retrieval-derived experiment design needs an evidence ledger "
                "(this assembly has none, so nothing could have been retrieved)"
            )
        retrieved = read_design_from_retrieval(
            assembly.artifacts, assembly.ledger, run_id=str(task.run_id.value)
        )
        return tuple(retrieved.arms)
    from packages.application.experiments.design_from_plan import read_design_from_plan

    design = read_design_from_plan(
        assembly.artifacts, assembly.ledger, run_id=str(task.run_id.value)
    )
    return tuple(design.arms)


def _arm_deps(assembly: SandboxExperimentAssembly, arm: Any, base: Any) -> Any:
    """某臂的执行依赖（**同一执行链**，只换 request builder：该臂的参数与实验 id）。

    执行器/制品店/账本与单臂共用同一批实例（**不另开执行路径**）。
    """
    from packages.application.run_orchestration.experiment_task import ExperimentTaskDeps

    return ExperimentTaskDeps(
        executor=base.executor,
        artifacts=base.artifacts,
        ledger=base.ledger,
        request_builder=_request_builder(assembly, arm=arm),
        provenance_builder=_provenance_builder,
    )


def _primary_arm_result(results: list[TaskExecutionResult]) -> TaskExecutionResult:
    """主臂结果（声明顺序的第一个）+ 在消息里**点名**全部臂。

    为什么门禁只看主臂：门要的是**一个**裁决（`TaskExecutionResult` 就是一次任务）。
    多臂不是「多次任务」，而是「一次任务的多次运行」⇒ 主臂代表这次任务，其余臂的
    读数在**读面**上逐条可查（EC-03 的靶子）。声明顺序因此是**语义**的一部分：
    第一个臂是主臂。
    """
    primary = results[0]
    labels = ", ".join(
        str(result.experiment_outcome.run.id.value)
        for result in results
        if result.experiment_outcome is not None
    )
    return replace(primary, message=f"{primary.message} (arms: {labels})")


def _persist_run(assembly: SandboxExperimentAssembly, result: TaskExecutionResult) -> None:
    """把这次实验（含**可复现审计**）落进实验存储（读面的事实来源）；没有存储或没有结局时不做任何事。

    GOAL-20261008-035 EC-02：审计随实验一起落库 —— 读面（`GET /runs/{id}/experiments`）
    读的是**存储**，只放在执行体内存里的结论对读面等于不存在（而那正是本轮之前的状态：
    审计只在遗留 M12 链产出）。
    """
    outcome = result.experiment_outcome
    if assembly.experiment_store is not None and outcome is not None:
        assembly.experiment_store.save_run(outcome.run)
        if outcome.audit is not None:
            assembly.experiment_store.save_audit(outcome.audit)


def _governed_executor(assembly: SandboxExperimentAssembly) -> GovernedExperimentExecutor:
    """执行体 = 装配方给的既有后端；工作区 = 本模块自建的**沙箱**工作区。

    `workspace_dir` 返回脚本已落盘的那个根（容器只挂它）。租约由 `ExperimentExecutor`
    自己取（`acquire_lease(request.workspace, request.agent_session_id)`），本模块不重复取。

    `assembly.execution` 可以是一个**惰性代理**（`_DeferredExecution.proxy(image)`）——
    它在第一次真正执行时才构造后端（GOAL-097 EC-01：装配期零 Docker 连接）；
    直接给实例时行为与既有逐字相同。
    """
    backend = assembly.execution
    root = Path(assembly.root or tempfile.mkdtemp(prefix="sandbox-root-"))
    root.mkdir(parents=True, exist_ok=True)
    if assembly.script is not None:
        shutil.copyfile(assembly.script, root / SCRIPT_NAME)
    workspaces = FileWorkspaceBackend(root / "_backend")
    # 工作区必须先在该后端**登记**：`ExperimentExecutor` 会对 `request.workspace`
    # 取租约，而后端对没登记过的 id 直接 `unknown workspace`（GOAL-011 cycle 9 实测：
    # 漏这一步 ⇒ 每次派发都在取租约处失败，一个容器都不起）。M12 clean-run 那条路
    # 也是先 `create_workspace` 再跑（见 `tools/m12_reference_workflow.py`）。
    workspaces.create_workspace(_sandbox_workspace())
    inner = ExperimentExecutor(
        execution=backend,
        workspaces=workspaces,
        artifacts=assembly.artifacts,
        workspace_dir=lambda lease: root,
    )
    return GovernedExperimentExecutor(inner=inner, policy=assembly.policy)


def _request_builder(
    assembly: SandboxExperimentAssembly,
    *,
    arm: Any | None = None,
) -> Callable[[ResearchTask, TaskContract, SessionSpecContext], ExperimentExecutionRequest]:
    """本装配（或**某个臂**）的执行请求构造器。

    `arm is None` ⇒ **单臂**（既有语义：`experiment_run_id_of(run_id)` + `assembly.parameters`）；
    `arm` 非空 ⇒ 该臂的实验 id 由 `arm_experiment_id(run_id, arm.name)` 派生、参数取该臂声明的
    （`params = {**assembly.parameters, **arm.parameters}` —— 臂可覆盖装配缺省，也可只给差异）。
    """

    def build(
        task: ResearchTask, contract: TaskContract, spec_context: SessionSpecContext
    ) -> ExperimentExecutionRequest:
        declaration = contract.experiment
        if declaration is None:  # 派发方只在声明非空时调用本函数；这里挡住装配期误用。
            raise InvalidInputError(f"contract {contract.id} declares no sandboxed experiment")
        run_id_text = str(task.run_id.value)
        experiment_run_id = (
            arm_experiment_id(run_id_text, arm.name)
            if arm is not None
            else experiment_run_id_of(run_id_text)
        )
        parameters = (
            dict(assembly.parameters)
            if arm is None
            else {**assembly.parameters, **dict(arm.parameters)}
        )
        return ExperimentExecutionRequest(
            plan=_preregistered_plan(task, arm=arm),
            run_id=ID(experiment_run_id),
            command=declaration.command,
            workspace=_sandbox_workspace(),
            agent_session_id=f"session-{task.id.value}",
            seed=7,
            # 实验脚本要能在 `experiment_result.json` 里回声**执行器期望的**那个 id
            # （解析器逐字比对，不等即 `InvalidInputError`）⇒ 由装配面交进去，不靠猜。
            # GOAL-20261015-079 EC-01：**声明的参数**一并进容器（白名单校验；缺省空
            # ⇒ 与今天逐字相同）。参数值因此是**声明事实**，不是脚本里的常量。
            environment={
                "EXPERIMENT_RUN_ID": experiment_run_id,
                **assembly.environment,
                **parameter_environment(parameters),
            },
            timeout_seconds=declaration.timeout_seconds,
        )

    return build


def _sandbox_workspace() -> Workspace:
    return Workspace(id=SANDBOX_WORKSPACE_ID, name=PLAN_NAME)


def _preregistered_plan(task: ResearchTask, *, arm: Any | None = None) -> ExperimentPlan:
    """本次任务的实验计划（预注册态）；**每个臂一份**（计划 id 含臂名 ⇒ 不复用同一个计划）。

    id 必须**合法 UUID** 且**按任务确定性派生**（同一任务重跑得同一个 id，重启后可复算）。
    这里此前是 `experiment_run_id_of(f"plan-{task.id.value}")`：那个函数要求输入本身是
    UUID（`UUID(ID(x).value)`），而 `plan-<uuid>` 不是 ⇒ **任何一次真实派发都在这一行抛**
    `ValueError: invalid UUID`（GOAL-011 cycle 9 实测；cycle 6 接缝时该路径从未被派发过）。
    改用同一个模块里既有的确定性派生 `derived_id`（审计 id 用的就是它），不新造第二套命名。

    GOAL-20261015-079 EC-02：`arm` 非空时**种子的字符串带上臂名** ⇒ 各臂的计划 id 不同
    （同一个计划 id 被两个臂复用会让「哪个计划属于哪个臂」不可判）；`arm is None` ⇒
    逐字沿用既有种子（零回归）。
    """
    seed = str(task.id.value) if arm is None else f"{task.id.value}:{arm.name}"
    plan = ExperimentPlan(
        id=ID(derived_id("sandbox-plan", seed)),
        name=PLAN_NAME if arm is None else f"{PLAN_NAME}:{arm.name}",
        hypothesis=f"sandboxed experiment for task {task.id.value}",
    )
    return plan.transition(ExperimentPlanState.Transition.PREREGISTER)


def _provenance_builder(task: ResearchTask) -> ExperimentProvenance:
    return ExperimentProvenance(run_id=str(task.run_id.value), manifest_digest=None)


def docker_experiment_assembly(**kwargs: Any) -> Any:
    """转发到 `experiment_factories`（**构造即连 Docker**；判据/工具侧用）。"""
    from services.api import experiment_factories

    return experiment_factories.docker_experiment_assembly(**kwargs)


def lazy_docker_experiment_assembly(**kwargs: Any) -> Any:
    """转发到 `experiment_factories`（**装配期零连接**；组合根用）。"""
    from services.api import experiment_factories

    return experiment_factories.lazy_docker_experiment_assembly(**kwargs)


__all__ = [
    "DESIGN_SOURCE_PLAN",
    "DESIGN_SOURCE_RETRIEVAL",
    "DESIGN_SOURCES",
    "SANDBOX_WORKSPACE_ID",
    "SCRIPT_NAME",
    "SandboxExperimentAssembly",
    "declared_or_assembled",
    "docker_experiment_assembly",
    "lazy_docker_experiment_assembly",
    "sandbox_experiment_runner",
]
