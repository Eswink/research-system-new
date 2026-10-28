"""报告汇编阶段的装配面（GOAL-20261014-077 EC-02）。

把**既有**汇编器（`deliverable/research_report.py`）链接进运行编排的
`PhaseRunnerDeps.report_task` 缝 —— 与 `experiment_support.sandbox_experiment_runner`
**同形同层**：那个模块缝沙箱实验，本模块缝报告汇编。

**为什么需要这一层**：`phase_runner` 早就有 `experiment_task` 这道缝的先例，而报告汇编
在 GOAL-077 EC-01 之前**根本没有产品路径**（汇编器只会被测试调用）。本模块把它接上：
装配方给出三件**已有的** Port（制品店 / 证据账本 / 评审结论存储），派发体自己走
`execute_report_task`（读事实 → 汇编 → 准入 canonical）；本模块**不新增**执行后端、
**不新增**依赖、**不另开**准入路径。

**如实边界**（本模块不声称已解决）：

- 报告是**确定性汇编**，不是模型撰写（那属报告域的再下一级）；
- 汇编**不做**跨 run 聚合：它只覆盖**本 run** 的持久事实（跨 run 的结论不在其中，
  报告自己在「局限」节写明这一条）；
- 未接上（`report_task=None`）时，声明了 `report` 的任务以**点名拒绝**收敛
  （fail-closed，不静默回退到会话）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from packages.application.run_orchestration.report_narrative_task import llm_narrator
from packages.application.run_orchestration.report_task import (
    ReportTaskDeps,
    execute_report_task,
)
from packages.application.run_orchestration.task_executor import (
    SessionSpecContext,
    TaskExecutionResult,
)
from packages.domain.tasks import ResearchTask, TaskContract


def report_task_runner(
    *,
    artifacts: Any,
    ledger: Any,
    review_findings: Any,
    narrator: Any | None = None,
    manuscript: bool = False,
) -> Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult]:
    """构造可直接放进 `PhaseRunnerDeps.report_task` 的派发器。

    三件 Port（制品店 / 证据账本 / 评审结论存储）都是**既有**装配件的引用（组合根持有）；
    本函数只把它们收成一个 `ReportTaskDeps` 并把调用转给 `execute_report_task`。

    `narrator`（GOAL-20261022-062）：接上了 ⇒ 正文由模型撰写（数字留在确定性事实表）；
    缺省 `None` ⇒ 逐字回到确定性汇编。**装配方必须显式选**，不由本函数猜。

    `manuscript`（GOAL-20261028-099）：开了 ⇒ 同一相**另外**汇出 `manuscript.md`
    （正文来自本 run 的 `manuscript_narrative` 制品；没有该制品 ⇒ 不产出，既有报告
    逐字节不变）。它**不是** `narrator` 的替代品：`narrator` 写的是报告第 1…4 节，
    手稿正文是另一个相的产物。
    """
    deps = ReportTaskDeps(
        artifacts=artifacts,
        ledger=ledger,
        reviews=review_findings,
        narrator=narrator,
        manuscript=manuscript,
    )

    def run(
        task: ResearchTask,
        contract: TaskContract,
        spec_context: SessionSpecContext,
        trace_id: str,
    ) -> TaskExecutionResult:
        return execute_report_task(deps, task, contract, spec_context, trace_id)

    return run


def narrative_runner(
    *,
    gateway: Any,
    credentials: Any,
    endpoint: Any,
    model_name: str,
    credential_ref: str,
) -> Any:
    """模型叙述者的**产品闭包**（与 `report_task_runner` 同形同层；只是多给一个可注入面）。

    它只转调 `llm_narrator`：端点 / 模型 / 凭据引用由**装配方**解析后传入 ⇒ 本模块不读
    配置、不读目录、不碰凭据值（与 `experiment_support` 的边界同一纪律）。
    """
    return llm_narrator(
        gateway=gateway,
        credentials=credentials,
        endpoint=endpoint,
        model_name=model_name,
        credential_ref=credential_ref,
    )


__all__ = ["narrative_runner", "report_task_runner"]
