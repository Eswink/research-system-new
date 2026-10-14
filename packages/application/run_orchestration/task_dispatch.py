"""「**谁执行这件工作**」的派发点（GOAL-20261014-077 EC-02；自 `phase_runner.py` 拆出）。

**为什么单列**：`phase_runner.py` 恰好卡在 450 行硬上限上（与 `experiment_task.py` 当初
被拆出来是同一条理由），而本轮的**第三条**执行体声明（`report`）让那里的派发分支越界。
拆法与全仓既有手法一致：**判定**（哪一条声明在场决定派给谁）与**执行循环**
（`phase_runner` 的 span / 分组 / 停车）分开。

**判定依据是契约事实，不是合约 id 的字面量**：`TaskContract.report` / `experiment`
两个声明位就是「谁执行」的**唯一**权威。写死一个合约名会漏掉语义相同的别的合约
（这正是 GOAL-011 EC-03 把「声明化」立起来的理由）。

**两个声明互斥**（`TaskContract.__post_init__` 点名拒绝），所以这里的顺序**不是**优先级
—— 只是两条互斥分支的书写顺序；判据面另有一条反证（两个声明同时在场 ⇒ 构造即拒）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from packages.application.run_orchestration.experiment_task import dispatch_experiment
from packages.application.run_orchestration.report_task import dispatch_report
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    TaskExecutionResult,
    execute_task,
)

if TYPE_CHECKING:  # 只为类型：避免与 phase_runner 形成导入环
    from packages.application.run_orchestration.phase_runner import (
        PhaseRunnerDeps,
        TaskContext,
    )


def dispatch_task_execution(deps: "PhaseRunnerDeps", tctx: "TaskContext") -> TaskExecutionResult:
    """按**契约声明**选执行体：报告汇编 / 沙箱实验 / 会话（会话是缺省，既有语义）。

    三条分支与各自动作逐字取自 `phase_runner` 的原实现（纯搬迁 + 新增一条声明分支）：
    声明了 `report` ⇒ 报告汇编器；声明了 `experiment` ⇒ 沙箱实验后端；
    两者都缺席 ⇒ **会话**（这是绝大多数任务，语义逐字节不变）。
    """
    if tctx.contract.report is not None:
        return dispatch_report(deps, tctx)
    if tctx.contract.experiment is not None:
        return dispatch_experiment(deps, tctx)
    return execute_task(
        # budget 必须接进来:失败/重试路径的 attempt 记账在
        # `record_attempt_usage` 里以 `budget is None` 提前返回,原先这里
        # 漏传导致生产 run 的失败尝试**从不落账**——"失败消耗不丢失"无从成立
        # (M15 复审 BLOCKER-5 的第二半)。
        ExecutionDeps(deps.workflow, deps.runtime, budget=deps.budget),
        tctx.task,
        tctx.contract,
        tctx.spec_context,
        trace_id=tctx.ctx.trace_id,
    )


__all__ = ["dispatch_task_execution"]
