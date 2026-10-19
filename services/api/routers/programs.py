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

from packages.domain.core import ID
from packages.domain.program import (
    HybridGateDeclaration,
    ProgramContinueRule,
    ProgramDecision,
    ResearchProgram,
)
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.programs import (
    HybridGateDto,
    ProgramAdvanceDto,
    ProgramCreateDto,
    ProgramDecisionDto,
    ProgramDetailDto,
    ProgramRunDto,
)
from services.api.errors import ApiError
from services.api.program_advance import advance_for, runs_of, store_of

router = APIRouter(tags=["programs"])
projects_router = APIRouter(tags=["programs"])


def _decision_dto(decision: ProgramDecision) -> ProgramDecisionDto:
    return ProgramDecisionDto(
        after_index=decision.after_index,
        kind=decision.kind.value,
        reason=decision.reason,
        cited_run_id=decision.cited_run_id,
        cited_facts=list(decision.cited_facts),
        decided_at=decision.decided_at.value.isoformat(),
    )


def declared_gate_fields(payload: ProgramCreateDto) -> dict[str, Any]:
    """建程序声明面的**闸门字段**（每条声明各自转换；缺省 ⇒ `None` ⇒ 既有行为逐字不变）。

    **为什么单列**：`create_program` 有 50 行硬上限，四条声明 + 超期界的转换一度把它顶爆
    —— 逐条搬到这里（**语义一字未动**，只是换落点），并守住那道门。

    四条声明**互斥**由域层点名拒绝（这里**不**预判，也不静默挑一条）。
    """
    hybrid = payload.human_gate_hybrid
    return {
        "max_attempts_per_index": payload.max_attempts_per_index,
        # GOAL-20261010-046 EC-02：程序级人工闸门（缺省 None = 不设闸门 ⇒ 逐字不变）。
        "human_gate_at_index": payload.human_gate_at_index,
        # GOAL-20261010-048 EC-02：条件式闸门（缺省 None = 不设 ⇒ 逐字不变）。
        "human_gate_on_verdicts": (
            tuple(payload.human_gate_on_verdicts)
            if payload.human_gate_on_verdicts is not None
            else None
        ),
        # GOAL-20261011-055 EC-02：多点闸门（缺省 None = 不设 ⇒ 逐字不变）。
        "human_gate_at_indexes": (
            tuple(payload.human_gate_at_indexes)
            if payload.human_gate_at_indexes is not None
            else None
        ),
        # GOAL-20261012-059 EC-02：超期界（缺省 None = 未声明 ⇒ 逐字不变）。
        "gate_nudge_after_seconds": payload.gate_nudge_after_seconds,
        # GOAL-20261012-060 EC-02：混合式闸门（缺省 None = 不设 ⇒ 逐字不变）。
        "human_gate_hybrid": (
            HybridGateDeclaration(
                at_indexes=tuple(hybrid.at_indexes),
                on_verdicts=tuple(hybrid.on_verdicts),
            )
            if hybrid is not None
            else None
        ),
    }


@projects_router.post(
    "/projects/{project_id}/programs", response_model=ProgramDetailDto, status_code=201
)
async def create_program(
    project_id: str, payload: ProgramCreateDto, request: Request
) -> ProgramDetailDto:
    """建一次研究程序（声明面；协议路径按启动 run 的同一校验解析 ⇒ 不存在即 422）。"""
    from services.api.protocol_source import load_protocol_for_source

    deps: ApiDeps = get_deps(request)
    store = store_of(deps)
    if not payload.continue_on_verdicts:
        raise ApiError(
            422, "Continue Rule Required", "continue_on_verdicts must name at least one verdict"
        )
    try:
        protocol = load_protocol_for_source(deps, payload.protocol_path, None)
    except ValueError as exc:
        raise ApiError(422, "Protocol Not Loadable", str(exc)) from exc
    rule = ProgramContinueRule(verdict_in=tuple(payload.continue_on_verdicts))
    decl = declared_gate_fields(payload)
    program = ResearchProgram(
        id=ID.generate().value,
        project_id=project_id,
        protocol_id=payload.protocol_path,
        max_runs=payload.max_runs,
        continue_rule=rule,
        max_attempts_per_index=cast(int, decl["max_attempts_per_index"]),
        human_gate_at_index=cast(int | None, decl["human_gate_at_index"]),
        human_gate_on_verdicts=cast(tuple[str, ...] | None, decl["human_gate_on_verdicts"]),
        human_gate_at_indexes=cast(tuple[int, ...] | None, decl["human_gate_at_indexes"]),
        gate_nudge_after_seconds=cast(int | None, decl["gate_nudge_after_seconds"]),
        human_gate_hybrid=cast(HybridGateDeclaration | None, decl["human_gate_hybrid"]),
    )
    del protocol  # 只用其可解析性做校验；声明面存的是路径（canonical 里的协议标识）
    store.create(program)
    return _detail_dto(deps, store, program.id)


def _detail_dto(deps: ApiDeps, store: Any, program_id: str) -> ProgramDetailDto:
    """读面：声明 + 各轮 run 摘要 + 逐条决策（`runs` 经 canonical `for_program`）。"""
    try:
        program = store.get(program_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"program not found: {program_id}") from exc
    runs = runs_of(deps).for_program(program_id)
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
        human_gate_at_indexes=(
            list(program.human_gate_at_indexes)
            if program.human_gate_at_indexes is not None
            else None
        ),
        # GOAL-20261012-059 EC-02：超期界的声明（缺省 None = 未声明）。
        gate_nudge_after_seconds=program.gate_nudge_after_seconds,
        # GOAL-20261012-060 EC-02：混合式闸门的声明（缺省 None = 未声明）。
        human_gate_hybrid=(
            HybridGateDto(
                at_indexes=list(program.human_gate_hybrid.at_indexes),
                on_verdicts=list(program.human_gate_hybrid.on_verdicts),
            )
            if program.human_gate_hybrid is not None
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
    return _detail_dto(deps, store_of(deps), program_id)


@projects_router.get("/projects/{project_id}/programs", response_model=list[ProgramDetailDto])
async def list_programs(project_id: str, request: Request) -> list[ProgramDetailDto]:
    """项目内程序列表（按 id 排序；逐条给决策面）。"""
    deps: ApiDeps = get_deps(request)
    store = store_of(deps)
    return [_detail_dto(deps, store, program.id) for program in store.for_project(project_id)]


@router.post("/programs/{program_id}/advance", response_model=ProgramAdvanceDto)
async def advance(program_id: str, request: Request) -> ProgramAdvanceDto:
    """推进一次：判定取**落库事实**；必要时经既有 start-run 链起下一轮。"""
    deps: ApiDeps = get_deps(request)
    # GOAL-089 EC-03：**唯一的推进装配**（`program_advance.advance_for`）——
    # 周期作业 `program_advance` 调的就是这同一个函数（不建第二套语义）。
    # 未知程序由该函数抛 404（与既有语义逐字相同）。
    result = advance_for(deps, program_id)
    return ProgramAdvanceDto(
        program_id=result.program_id,
        decision=_decision_dto(result.decision),
        started_run_id=result.started_run_id,
        run_count=result.run_count,
    )
