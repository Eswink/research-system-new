"""重启后的续跑入口：按 run 记下的装配来源重建执行上下文（GOAL-003 cycle 20）。

cycle 18/19 让"重排未到期"把 run 停 `PAUSED` 并让**本进程**的守护线程按时续跑，但
续跑上下文（`RunContext` + 剩余 specs）只活在 `RunOrchestrationService._paused` 里：
探针 `scratch/goal3-cycle20-probe1-restart-loses-the-plan.py` 量出重启后
`has_paused_context=False`、`resume_paused` 抛 `InvalidInputError`、守护线程派发 0
——已到期的重排**没有任何交付入口**。

本模块补上那个入口：用 run 行记下的 `protocol_source` 重新装配（协议 → 目录 → 项目
→ preflight），重建 `RunContext`，再由 `RunOrchestrationService.resume_rebuilt` 重算
剩余工作并执行。**不建第二套装配链**：来源解析、目录合并、preflight 上下文都复用
`execution_inputs`（`POST /runs` 与队列派发器用的同一条）。

两个调用方共用本模块（HTTP 面 `POST /runs/{id}/resume` 与守护线程
`RetryDispatchScheduler`），差别只在怎么把结论交出去：HTTP 面要一份能写进响应的
`ResumeAttempt`，守护线程要把"被拒"变成异常才能用一处 `except` 把 run 放回停车状态。

诚实边界（全部不改变 run 状态）：

- 没有登记来源的旧 run ⇒ 拒绝（"没有来源就无法重建 plan"），不猜协议；
- **有冻结正文**（GOAL-004 cycle 1）⇒ 只用正文重装配，外部来源消失/被改都不影响；
- 没有冻结正文时来源不可解析（路径消失 / 修订不存在 / 草稿服务缺失）⇒ 拒绝，
  拒绝原因同时点名"没有冻结正文"与具体解析失败，不换一份协议；
- 重编译的 preflight 未通过 ⇒ 拒绝；
- 冻结语义漂移（plan/catalog/契约/定价）⇒ `assert_semantics_frozen` 拒绝
  （在 `resume_rebuilt` 内），本模块只把拒绝原因如实带出来。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from packages.application.preflight.preflight import compile_and_preflight
from packages.application.run_orchestration.commands import ResumeRunCommand
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.phase_runner import RunOutcome
from packages.application.run_orchestration.service import RunOrchestrationService
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps
from services.api.run_execution import ExecutionRequest, execution_inputs


@dataclass(frozen=True, slots=True)
class ResumeAttempt:
    """一次重建续跑的结论：成功带 outcome，被拒带原因（都如实表达）。"""

    outcome: RunOutcome | None = None
    refusal: str | None = None

    @property
    def resumed(self) -> bool:
        return self.outcome is not None


class RebuildRefused(RuntimeError):
    """重建被诚实拒绝（来源缺失/不可解析/preflight 不过/冻结语义漂移）。"""


def continue_from_rebuild(
    rebuild: Callable[[ResearchRun], ResumeAttempt], run: ResearchRun
) -> RunOutcome:
    """守护线程的第二入口：按 durable 来源重建后续跑，被拒 ⇒ `RebuildRefused`。

    与 HTTP 面共用同一个 `rebuild_and_resume`（composition root 注入），这里只把
    "带回来的是 refusal 而不是 outcome"翻译成异常——放回停车状态是调用方的决定。
    """
    attempt = rebuild(run)
    outcome: RunOutcome | None = getattr(attempt, "outcome", None)
    if outcome is None:
        raise RebuildRefused(str(getattr(attempt, "refusal", "rebuild refused")))
    return outcome


def rebuild_and_resume(deps: ApiDeps, run: ResearchRun) -> ResumeAttempt:
    """按 durable 装配来源重建上下文并续跑（调用方已把 canonical 迁到 RUNNING）。

    先迁状态再调本函数不是可选顺序：协作式暂停谓词读的就是 canonical run 状态，
    "还停在 PAUSED"对执行循环就是"继续暂停"（cycle 19 的教训）。

    输入优先级（GOAL-004 cycle 1）：run 行里的**冻结正文**说了算——有它就不碰
    文件系统/草稿库（外部来源消失/漂移都不再影响这条 run）；没有它才走来源解析
    （旧 run 的兼容路径），此时拒绝原因必须**同时点名**缺的是"冻结正文"与
    "来源不可解析"两件事实。
    """
    service = deps.runs
    if service is None:
        return ResumeAttempt(refusal="run orchestration service is not configured")
    source = run.protocol_source
    body = run.protocol_body
    if source is None and body is None:
        return ResumeAttempt(
            refusal="run has no recorded protocol source (predates source recording)"
        )
    if run.manifest_digest is None:
        return ResumeAttempt(refusal="run has no frozen manifest digest; cannot verify rebuild")

    trace_id = f"api-resume-{run.id.value}"
    try:
        return _resume_from_source(service, deps, run, source, trace_id)
    except Exception as exc:  # noqa: BLE001 - 任何重建/校验失败都诚实拒绝，不改状态
        prefix = "" if body is not None else "run has no frozen protocol body; "
        return ResumeAttempt(refusal=f"{prefix}{type(exc).__name__}: {exc}")


def _resume_from_source(
    service: RunOrchestrationService,
    deps: ApiDeps,
    run: ResearchRun,
    source: ProtocolSource | None,
    trace_id: str,
) -> ResumeAttempt:
    """同一条装配链重建上下文 → 续跑（装配失败原样抛出，由调用方转成拒绝原因）。"""
    inputs = execution_inputs(
        ExecutionRequest(
            deps=deps,
            protocol_path=source.protocol_path if source is not None else None,
            run_id=run.id,
            trace_id=trace_id,
            draft_ref=source.draft_ref if source is not None else None,
            project_id=run.project_id,
            protocol_body=run.protocol_body,
        )
    )
    plan, report = compile_and_preflight(
        inputs.protocol, inputs.catalog, inputs.project, inputs.preflight
    )
    if plan is None or not report.passed:
        return ResumeAttempt(refusal="rebuilt preflight does not pass; refusing to resume")
    context = RunContext(
        protocol=inputs.protocol,
        plan=plan,
        report=report,
        run=run,
        catalog=inputs.catalog,
        project=inputs.project,
        preflight=inputs.preflight,
        trace_id=trace_id,
    )
    outcome = service.resume_rebuilt(
        context,
        ResumeRunCommand(
            run_id=run.id,
            frozen_manifest_digest=str(run.manifest_digest),
            trace_id=trace_id,
        ),
    )
    if report.reserved_budget_ref is not None:
        # 重建的 preflight 预留与首次冻结同源（ref 由 policy+reservations 确定性派生，
        # 重复预留是同一行的幂等写），登记后收敛路径才能在终态释放它。
        service.register_reservation_ref(run.id.value, report.reserved_budget_ref)
    return ResumeAttempt(outcome=outcome)
