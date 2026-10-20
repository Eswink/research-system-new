"""`PhaseRunnerDeps` 的装配（GOAL-20261014-077 EC-02；自 `service.py` 拆出守规模门）。

**为什么单列**：`service.py` 卡在 450 行硬上限上，而本轮新增的第三条执行体声明
（`report_task`）让那里的关键字列表越界。拆法与 GOAL-011 EC-03 拆 `experiment_task`
同源：**装配**（把 service 的回调与 Port 收成一个 `PhaseRunnerDeps`）与**编排**
（compile/preflight/freeze/complete）分列。

**逐字搬运，零语义变化**：每个关键字都与拆出前的那一份**同名同值**（含
`**self._deps.fact_stores()` 的三件事实面与 `round_loop_fields` 的按轮展开）。
`RuntimeFingerprintCollector` 缺省 `None` ⇒ `on_observation=None`（既有语义：没有观测
就不是一次空调用）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from packages.application.run_orchestration.human_gates import pending_human_gates
from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
)
from packages.application.run_orchestration.round_loop_runner import round_loop_fields
from packages.domain.events import EventType

if TYPE_CHECKING:  # 只为类型：避免与 service 形成导入环
    from packages.application.run_orchestration.context import RunContext
    from packages.application.run_orchestration.dependencies import (
        OrchestrationDependencies,
    )
    from packages.application.run_orchestration.service import SessionSpec


@dataclass(frozen=True, slots=True)
class RunnerFaces:
    """service 侧交给执行循环的**回调面**（参数对象，避免参数爆发）。

    每件都是 service 的绑定方法（`self._publish_phase_event` 等）或它的解析器；
    本模块不解释它们，只搬运。**签名逐字取自 `PhaseRunnerDeps` 的字段**（不写
    `Callable[..., object]`：那会让「搬的是不是同一个东西」交给调用点自己保证）。
    """

    publish: Callable[[EventType, dict[str, object], str, str, str | None], None]
    fail_run: Callable[[str, str, bool], RunOutcome]
    degrade_run: Callable[[PhaseContext, tuple[TaskOutcome, ...], str], RunOutcome]
    resolve_sessions: Callable[["RunContext"], tuple["SessionSpec", ...]]


def runner_deps(  # noqa: PLR0913 - 装配面：Port 聚合 + 现场面（齐了才叫一份 deps）
    deps: "OrchestrationDependencies",
    context: "RunContext",
    run_id: str,
    *,
    faces: RunnerFaces,
    paused: list[tuple["SessionSpec", ...]],
    collector: Any | None,
    pause_requested: Callable[[], bool],
) -> PhaseRunnerDeps:
    """本 run 的 `PhaseRunnerDeps`（关键字与拆出前的原实现**同名同值**）。"""
    return PhaseRunnerDeps(
        workflow=deps.workflow,
        runtime=deps.runtime,
        artifacts=deps.artifacts,
        budget=deps.budget,
        **deps.fact_stores(),
        publish=faces.publish,
        fail_run=faces.fail_run,
        degrade_run=faces.degrade_run,
        telemetry=deps.telemetry,
        approvals=deps.approvals,
        # GOAL-20261019-089 EC-01：运行链要解析**跨相输入**的真实制品 id（上游产物）——
        # 身份面就是本装配的 workflow 引擎（与 `cross_phase_evidence` 同一份事实）。
        # 不声明跨相输入的 phase 逐字节不变（`resolve_cross_phase_material` 提前返回空）。
        capabilities=_with_workflow(deps.capabilities, deps.workflow),
        experiment_task=deps.experiment_task,
        # GOAL-20261014-077 EC-02：报告汇编的执行缝（缺省 None ⇒ 声明了 `report` 的
        # 任务点名拒绝；既有装配语义逐字节不变）。
        report_task=deps.report_task,
        # GOAL-20261014-078 EC-01：检索内容 → 会话上下文的装配器（缺省 None ⇒
        # 会话不带检索上下文；既有装配语义逐字节不变）。
        retrieval_context=deps.retrieval_context,
        # GOAL-20261018-082 EC-01：前序知识（缺省 None ⇒ 提示词逐字不变）。
        prior_knowledge=deps.prior_knowledge,
        # GOAL-20261020-091 EC-02：被评对象（缺省 None ⇒ 提示词逐字不变）。
        review_material=deps.review_material,
        output_schema_validator=deps.output_schema_validator,
        human_gated=pending_human_gates(deps.approvals, context.plan, run_id),
        on_pause=paused.append,
        on_observation=None if collector is None else collector.observe,
        pause_requested=pause_requested,
        **round_loop_fields(deps.round_loops, faces.resolve_sessions(context)),
    )


def run_context(  # noqa: PLR0913 - 与拆出前的 `_start_run_impl` 同一组输入（照抄既有豁免）
    deps: "OrchestrationDependencies",
    protocol: Any,
    plan: Any,
    report: Any,
    run: Any,
    catalog: Any,
    project: Any,
    preflight_context: Any,
    command: Any,
) -> Any:
    """冻结之后的那份执行上下文（单列：`_start_run_impl` 卡在 50 行函数门）。

    GOAL-20261019-089 EC-02：**项目方向**在这里解析一次（组合根注入的解析器；
    缺省 `None` ⇒ 提示词既有形态逐字不变）。
    """
    from packages.application.run_orchestration.context import RunContext as _RunContext

    return _RunContext(
        protocol=protocol,
        plan=plan,
        report=report,
        run=run,
        catalog=catalog,
        project=project,
        preflight=preflight_context,
        trace_id=command.trace_id,
        direction=project_direction(deps, project.project_id),
    )


def project_direction(deps: "OrchestrationDependencies", project_id: str) -> str | None:
    """本项目的**研究方向**（GOAL-20261019-089 EC-02；缺省 None ⇒ 提示词不含那一段）。

    **不吞异常**：解析器抛错就让它冒出去 —— 「读不到方向」与「没有方向」是两件事，
    静默当成后者会把一个装配缺陷伪装成「用户没声明方向」。
    """
    resolve = deps.project_direction
    if resolve is None:
        return None
    value = resolve(project_id)
    return value if isinstance(value, str) else None


def _with_workflow(capabilities: Any, workflow: Any) -> Any:
    """把 workflow 身份面补进运行链能力装配（GOAL-20261019-089 EC-01）。

    `CapabilityDeps` 是 frozen dataclass ⇒ 用 `replace` 派生一份，**其它字段逐字保留**。
    装配面缺省 `None`（该步不启用）⇒ 原样返回 `None`（既有语义不变）。
    """
    if capabilities is None:
        return None
    if getattr(capabilities, "workflow", None) is not None:
        return capabilities
    from dataclasses import replace

    return replace(capabilities, workflow=workflow)


__all__ = ["RunnerFaces", "project_direction", "run_context", "runner_deps"]
