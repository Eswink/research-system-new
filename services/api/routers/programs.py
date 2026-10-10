"""研究程序控制面路由（GOAL-20261008-037 EC-02）。

三条路由：

- `POST /projects/{project_id}/programs` —— 建程序（声明：协议 + 上界护栏 + 声明式
  续跑规则）；
- `POST /programs/{program_id}/advance` —— 推进一次：读**落库事实**判定 → 落决策 →
  （必要时）经**既有 start-run 链**起下一轮；
- `GET /programs/{program_id}` —— 读面：程序 + 各轮 run 摘要 + 逐条决策（含被引事实原文）。

**诚实边界（逐条）**：

- store 未配置 ⇒ 503（不伪装空列表）；
- 程序 / 协议不存在 ⇒ 404 / 422（点名）；
- 推进时**缺启动面** ⇒ 决策落 `WAIT` 且理由**点名**「未提供启动面」（不静默 200 冒充已启动）；
- 决策是 **append-only** 事实：重复推进产生多条决策（不覆盖历史）。

**「为何继续 / 为何停」的可读性**：`ProgramDecisionDto.reason` 是**当时写下的原话**，
`cited_facts` 是被引 canonical 事实的**原文**（判词逐字 / 状态逐字）—— 读面不重算、
不加工（承 GOAL-035 的「记录，不是重算」）。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request

from packages.application.ports.program_store import ProgramStore
from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.core import ID
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ResearchProgram,
)
from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.programs import (
    ProgramAdvanceDto,
    ProgramCreateDto,
    ProgramDecisionDto,
    ProgramDetailDto,
    ProgramRunDto,
)
from services.api.errors import ApiError

router = APIRouter(tags=["programs"])
projects_router = APIRouter(tags=["programs"])

_STORE_ABSENT = "Research Program Store Unavailable"
_STORE_ABSENT_DETAIL = "program store not configured"


def _store_of(deps: ApiDeps) -> ProgramStore:
    store = deps.program_store
    if store is None:
        raise ApiError(503, _STORE_ABSENT, _STORE_ABSENT_DETAIL)
    return cast(ProgramStore, store)


def _runs_of(deps: ApiDeps) -> Any:
    if deps.runs_store is None:
        raise ApiError(503, "Run Store Unavailable", "run store not configured")
    return deps.runs_store


def _decision_dto(decision: ProgramDecision) -> ProgramDecisionDto:
    return ProgramDecisionDto(
        after_index=decision.after_index,
        kind=decision.kind.value,
        reason=decision.reason,
        cited_run_id=decision.cited_run_id,
        cited_facts=list(decision.cited_facts),
        decided_at=decision.decided_at.value.isoformat(),
    )


def _start_run_for_program(deps: ApiDeps, program: ResearchProgram, index: int) -> str:
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


@projects_router.post(
    "/projects/{project_id}/programs", response_model=ProgramDetailDto, status_code=201
)
async def create_program(
    project_id: str, payload: ProgramCreateDto, request: Request
) -> ProgramDetailDto:
    """建一次研究程序（声明面；协议路径按启动 run 的同一校验解析 ⇒ 不存在即 422）。"""
    from services.api.protocol_source import load_protocol_for_source

    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    if not payload.continue_on_verdicts:
        raise ApiError(
            422, "Continue Rule Required", "continue_on_verdicts must name at least one verdict"
        )
    try:
        protocol = load_protocol_for_source(deps, payload.protocol_path, None)
    except ValueError as exc:
        raise ApiError(422, "Protocol Not Loadable", str(exc)) from exc
    rule = ProgramContinueRule(verdict_in=tuple(payload.continue_on_verdicts))
    program = ResearchProgram(
        id=ID.generate().value,
        project_id=project_id,
        protocol_id=payload.protocol_path,
        max_runs=payload.max_runs,
        continue_rule=rule,
        # GOAL-20261008-040 EC-02：失败后可选的有界重试（缺省 1 = 不重试）。
        max_attempts_per_index=payload.max_attempts_per_index,
        # GOAL-20261010-046 EC-02：程序级人工闸门（缺省 None = 不设闸门 ⇒ 逐字不变）。
        human_gate_at_index=payload.human_gate_at_index,
        # GOAL-20261010-048 EC-02：条件式闸门（缺省 None = 不设 ⇒ 逐字不变）。
        human_gate_on_verdicts=(
            tuple(payload.human_gate_on_verdicts)
            if payload.human_gate_on_verdicts is not None
            else None
        ),
    )
    del protocol  # 只用其可解析性做校验；声明面存的是路径（canonical 里的协议标识）
    store.create(program)
    return _detail_dto(deps, store, program.id)


def _detail_dto(deps: ApiDeps, store: ProgramStore, program_id: str) -> ProgramDetailDto:
    """读面：声明 + 各轮 run 摘要 + 逐条决策（`runs` 经 canonical `for_program`）。"""
    try:
        program = store.get(program_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"program not found: {program_id}") from exc
    runs = _runs_of(deps).for_program(program_id)
    return ProgramDetailDto(
        id=program.id,
        project_id=program.project_id,
        protocol_id=program.protocol_id,
        max_runs=program.max_runs,
        continue_on_verdicts=list(program.continue_rule.verdict_in),
        max_attempts_per_index=program.max_attempts_per_index,
        human_gate_at_index=program.human_gate_at_index,
        human_gate_on_verdicts=(
            list(program.human_gate_on_verdicts)
            if program.human_gate_on_verdicts is not None
            else None
        ),
        created_at=program.created_at.value.isoformat(),
        updated_at=program.updated_at.value.isoformat(),
        runs=[
            ProgramRunDto(
                run_id=run.id.value,
                program_index=run.program_index or 0,
                state=run.state,
                manifest_digest=str(run.manifest_digest) if run.manifest_digest else None,
            )
            for run in runs
        ],
        decisions=[_decision_dto(item) for item in store.decisions_of(program_id)],
        run_count=len(runs),
    )


@router.get("/programs/{program_id}", response_model=ProgramDetailDto)
async def get_program(program_id: str, request: Request) -> ProgramDetailDto:
    """程序读面（含「为何继续 / 为何停」的逐条决策）。"""
    deps: ApiDeps = get_deps(request)
    return _detail_dto(deps, _store_of(deps), program_id)


@projects_router.get("/projects/{project_id}/programs", response_model=list[ProgramDetailDto])
async def list_programs(project_id: str, request: Request) -> list[ProgramDetailDto]:
    """项目内程序列表（按 id 排序；逐条给决策面）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    return [_detail_dto(deps, store, program.id) for program in store.for_project(project_id)]


@router.post("/programs/{program_id}/advance", response_model=ProgramAdvanceDto)
async def advance(program_id: str, request: Request) -> ProgramAdvanceDto:
    """推进一次：判定取**落库事实**；必要时经既有 start-run 链起下一轮。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        program = store.get(program_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"program not found: {program_id}") from exc
    result = advance_program(
        program,
        runs=_runs_of(deps),
        programs=store,
        findings=deps.review_findings,
        # GOAL-20261010-044 EC-02/EC-03：审批面（**复用既有实例**，不建第二套存储）——
        # 驱动据此把「停在人工闸门」与「还在跑」判成**不同种类**并点名待审批。
        # 缺审批面 ⇒ 传 None（驱动**点名**「本装配未提供审批面」，不静默当成没有待审批）。
        approvals=deps.approvals,
        # 缺编排面 ⇒ 传 None（驱动据此落一条**点名**「未提供启动面」的 WAIT 决策）；
        # 不是抛 503 —— 「需要起 run 但没有启动面」是**可读的决策事实**，不是传输层故障。
        start_run=(
            (lambda index: _start_run_for_program(deps, program, index))
            if deps.runs is not None
            else None
        ),
    )
    return ProgramAdvanceDto(
        program_id=result.program_id,
        decision=_decision_dto(result.decision),
        started_run_id=result.started_run_id,
        run_count=result.run_count,
    )
