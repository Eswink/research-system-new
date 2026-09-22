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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adapters.execution import DockerExecutionBackend
from adapters.workspace import FileWorkspaceBackend
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    GovernedExperimentExecutor,
)
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
    #: 实验产物读面（`GET /runs/{id}/experiments`）读的是**实验存储**：执行完必须把
    #: `ExperimentRun` 存进去，否则"实验真的跑了"在读面上看不见。None ⇒ 不落库（调用方
    #: 自担：读面会如实为空，不伪造）。
    experiment_store: Any | None = None
    script: str | None = None
    root: str | None = None
    environment: dict[str, str] = field(default_factory=dict)


def sandbox_experiment_runner(
    assembly: SandboxExperimentAssembly,
) -> Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult]:
    """构造可直接放进 `PhaseRunnerDeps.experiment_task` 的派发器。

    每次调用执行**一次**实验：准备沙箱工作区 → 预注册计划 → 交给既有执行链 →
    结果由 `execute_experiment_task` 登记/门禁（调用方 `phase_runner` 继续处理）。
    """
    deps = ExperimentTaskDeps(
        executor=_governed_executor(assembly),
        artifacts=assembly.artifacts,
        ledger=assembly.ledger,
        request_builder=_request_builder(assembly),
        provenance_builder=_provenance_builder,
    )

    def run(
        task: ResearchTask,
        contract: TaskContract,
        spec_context: SessionSpecContext,
        trace_id: str,
    ) -> TaskExecutionResult:
        result = execute_experiment_task(deps, task, contract, spec_context, trace_id)
        _persist_run(assembly, result)
        return result

    return run


def _persist_run(assembly: SandboxExperimentAssembly, result: TaskExecutionResult) -> None:
    """把这次实验落进实验存储（读面的事实来源）；没有存储或没有结局时不做任何事。"""
    outcome = result.experiment_outcome
    if assembly.experiment_store is not None and outcome is not None:
        assembly.experiment_store.save_run(outcome.run)


def _governed_executor(assembly: SandboxExperimentAssembly) -> GovernedExperimentExecutor:
    """执行体 = 装配方给的既有后端；工作区 = 本模块自建的**沙箱**工作区。

    `workspace_dir` 返回脚本已落盘的那个根（容器只挂它）。租约由 `ExperimentExecutor`
    自己取（`acquire_lease(request.workspace, request.agent_session_id)`），本模块不重复取。
    """
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
        execution=assembly.execution,
        workspaces=workspaces,
        artifacts=assembly.artifacts,
        workspace_dir=lambda lease: root,
    )
    return GovernedExperimentExecutor(inner=inner, policy=assembly.policy)


def _request_builder(
    assembly: SandboxExperimentAssembly,
) -> Callable[[ResearchTask, TaskContract, SessionSpecContext], ExperimentExecutionRequest]:
    def build(
        task: ResearchTask, contract: TaskContract, spec_context: SessionSpecContext
    ) -> ExperimentExecutionRequest:
        declaration = contract.experiment
        if declaration is None:  # 派发方只在声明非空时调用本函数；这里挡住装配期误用。
            raise InvalidInputError(f"contract {contract.id} declares no sandboxed experiment")
        experiment_run_id = experiment_run_id_of(str(task.run_id.value))
        return ExperimentExecutionRequest(
            plan=_preregistered_plan(task),
            run_id=ID(experiment_run_id),
            command=declaration.command,
            workspace=_sandbox_workspace(),
            agent_session_id=f"session-{task.id.value}",
            seed=7,
            # 实验脚本要能在 `experiment_result.json` 里回声**执行器期望的**那个 id
            # （解析器逐字比对，不等即 `InvalidInputError`）⇒ 由装配面交进去，不靠猜。
            environment={"EXPERIMENT_RUN_ID": experiment_run_id, **assembly.environment},
            timeout_seconds=declaration.timeout_seconds,
        )

    return build


def _sandbox_workspace() -> Workspace:
    return Workspace(id=SANDBOX_WORKSPACE_ID, name=PLAN_NAME)


def _preregistered_plan(task: ResearchTask) -> ExperimentPlan:
    """本次任务的实验计划（预注册态）。

    id 必须**合法 UUID** 且**按任务确定性派生**（同一任务重跑得同一个 id，重启后可复算）。
    这里此前是 `experiment_run_id_of(f"plan-{task.id.value}")`：那个函数要求输入本身是
    UUID（`UUID(ID(x).value)`），而 `plan-<uuid>` 不是 ⇒ **任何一次真实派发都在这一行抛**
    `ValueError: invalid UUID`（GOAL-011 cycle 9 实测；cycle 6 接缝时该路径从未被派发过）。
    改用同一个模块里既有的确定性派生 `derived_id`（审计 id 用的就是它），不新造第二套命名。
    """
    plan = ExperimentPlan(
        id=ID(derived_id("sandbox-plan", str(task.id.value))),
        name=PLAN_NAME,
        hypothesis=f"sandboxed experiment for task {task.id.value}",
    )
    return plan.transition(ExperimentPlanState.Transition.PREREGISTER)


def _provenance_builder(task: ResearchTask) -> ExperimentProvenance:
    return ExperimentProvenance(run_id=str(task.run_id.value), manifest_digest=None)


def docker_experiment_assembly(  # noqa: PLR0913 -- 装配面的量就这么多；缺省值让调用点只给必需的
    *,
    artifacts: Any,
    policy: Any,
    script: str,
    image: str = "research-os-sandbox:m9-test",
    ledger: Any | None = None,
    experiment_store: Any | None = None,
) -> SandboxExperimentAssembly:
    """本地装配：执行体 = **既有** `DockerExecutionBackend`（不新增后端/依赖）。"""
    return SandboxExperimentAssembly(
        execution=DockerExecutionBackend(image=image),
        artifacts=artifacts,
        policy=policy,
        image=image,
        ledger=ledger,
        experiment_store=experiment_store,
        script=script,
    )
