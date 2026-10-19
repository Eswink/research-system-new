"""研究程序推进的**唯一装配面**（自 `routers/programs.py` 抽出：GOAL-20261019-089 EC-03）。

**为什么抽出**：EC-03 让周期作业也能推进程序，而「推进」这件事的装配（读哪些 canonical
事实、给什么时钟、注入什么出口、起 run 走哪条链）**必须只有一份** —— 否则人工端点与
自动作业会各有一套语义，而「自动」与「手动」的判词就可能不一致。抽出之后：

- `POST /programs/{id}/advance` 调 `advance_for(deps, program_id)`；
- `ProgramAdvanceScheduler` 也调 `advance_for(deps, program_id)`（同一函数、同一装配）。

**逐字保留**：本模块的每一处装配与抽出前 `advance()` 里的那份**同名同值**（含审批面、
启动面、时钟、nudge 出口与「缺编排面 ⇒ 传 None 让驱动点名」的分支）。
"""

from __future__ import annotations

from typing import Any, cast

from packages.application.ports.program_store import ProgramStore
from packages.application.run_orchestration.program_runner import (
    ProgramAdvance,
    advance_program,
)
from packages.application.run_orchestration.program_waiting import GateClock
from packages.domain.core import ID, Timestamp
from packages.domain.program import ResearchProgram
from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps
from services.api.errors import ApiError

STORE_ABSENT = "Research Program Store Unavailable"
STORE_ABSENT_DETAIL = "program store not configured"


def store_of(deps: ApiDeps) -> ProgramStore:
    store = deps.program_store
    if store is None:
        raise ApiError(503, STORE_ABSENT, STORE_ABSENT_DETAIL)
    return cast(ProgramStore, store)


def runs_of(deps: ApiDeps) -> Any:
    if deps.runs_store is None:
        raise ApiError(503, "Run Store Unavailable", "run store not configured")
    return deps.runs_store


def advance_clock(runs: Any, program_id: str) -> GateClock | None:
    """**等待时长**所需的一对时点（GOAL-20261011-056）——取不到时返回 `None`。

    - `waited_since` = 「**最后一条** run 的 `updated_at`」：状态转移**会刷新它** ⇒
      停在等待态（`AWAITING_HUMAN` / `PAUSED`）的 run 上，它就是**进入等待的时刻**；
    - `now` = **本请求到达的时刻**（由这里给 ⇒ 等待面**不读挂钟**，判词可复现）。

    **取不到就返回 `None`**（**不猜、不编一个假时点**）：等待面收到 `None` ⇒ 判词里
    **不含任何时长**（既有行为），而不是报一个**编出来的**秒数。
    **只读**：只查一次既有 run 面，不写任何东西。
    """
    try:
        existing = runs.for_program(program_id)
    except Exception:  # noqa: BLE001 - 取不到就**不报时长**（不静默编造）
        return None
    if not existing:
        return None
    return GateClock(now=Timestamp.now(), waited_since=existing[-1].updated_at)


def start_run_for_program(deps: ApiDeps, program: ResearchProgram, index: int) -> str:
    """起第 `index` 轮：**同一条** start-run 链（协议来源解析 → preflight → freeze → execute）。

    程序归属**随 run 的写入同一次**落 canonical（`program_id` / `program_index` 进
    `ExecutionRequest`），不设「先起 run 后绑定」的窗口（GOAL-037 EC-01 的硬约束）。
    """
    from services.api.run_access import save_run
    from services.api.run_execution import ExecutionRequest, execution_inputs, run_from_execution

    run_id = ID.generate()
    req = ExecutionRequest(
        deps=deps,
        protocol_path=program.protocol_id,
        run_id=run_id,
        trace_id=None,
        draft_ref=None,
        project_id=program.project_id,
        program_id=program.id,
        program_index=index,
    )
    inputs = execution_inputs(req)
    # 先落 run 行（含程序归属）再执行：读链里的工具可能在**执行期**回读本 run 的行
    # （`research_state.read` 由 run_id 反查程序归属 ⇒ 没有这一行就点不到程序）。
    # 行先落 = 与 HTTP 面的写序同侧（那里是执行后落），此处**必须**反过来，否则
    # 「本 run 是自己的程序成员」这件事实在执行期不可见。
    provisional = ResearchRun(
        id=run_id,
        project_id=inputs.project.project_id,
        protocol_id=inputs.protocol.id,
        program_id=program.id,
        program_index=index,
    )
    save_run(deps, provisional)
    run = run_from_execution(deps, run_id, inputs.project.project_id, inputs.protocol.id, inputs)
    save_run(deps, run)
    return run_id.value


def advance_for(deps: ApiDeps, program_id: str) -> ProgramAdvance:
    """推进一次（**人工端点与周期作业共用的唯一装配**）。

    读面事实全部取自 canonical（run store / 程序 store / 评审存储）；启动面是
    `start_run_for_program`；缺编排面 ⇒ 传 `None` 让驱动落一条**点名**「未提供启动面」的
    `WAIT` 决策（不是抛 503 —— 那是可读的决策事实，不是传输层故障）。
    """
    store = store_of(deps)
    try:
        program = store.get(program_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"program not found: {program_id}") from exc
    runs = runs_of(deps)
    return advance_program(
        program,
        runs=runs,
        programs=store,
        findings=deps.review_findings,
        # GOAL-20261010-044 EC-02/EC-03：审批面（**复用既有实例**，不建第二套存储）。
        approvals=deps.approvals,
        start_run=(
            (lambda index: start_run_for_program(deps, program, index))
            if deps.runs is not None
            else None
        ),
        # GOAL-20261011-056 EC-02/EC-03：等待时长的一对时点（取不到 ⇒ None）。
        clock=advance_clock(runs, program.id),
        # GOAL-20261012-059 EC-03：超期信号的出口（缺省 NullNudgeSink ⇒ 静默）。
        nudges=deps.nudges,
    )


__all__ = [
    "advance_clock",
    "advance_for",
    "runs_of",
    "start_run_for_program",
    "store_of",
]
