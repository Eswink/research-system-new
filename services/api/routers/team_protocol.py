"""Team / Protocol / Preflight / Dry-run 控制面路由。

流程：HTTP → DTO → use case（protocol_compile + preflight）→ Domain / Port。
Dry Run 语义（M13 DoD 5）：只透传 `dry_run_projection` 纯只读投影，
不调用 reserve / execution / memory write / tool call（零 Research side effect）。
"""

from __future__ import annotations

from fastapi import APIRouter

from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.preflight.preflight import (
    compile_and_preflight,
    dry_run_projection,
    run_preflight,
)
from packages.application.protocol_compile.compiler import compile_protocol
from packages.domain.protocols import CompiledRunPlan
from services.api.catalog import (
    load_catalog_snapshot,
    load_project_settings,
    load_protocol_definition,
)
from services.api.dto.team_protocol import (
    AgentSpecDto,
    AgentUpdateDto,
    CompileResultDto,
    DryRunProjectionDto,
    PreflightReportDto,
    ProjectSettingsDto,
    ProtocolSourceDto,
    RoleDefinitionDto,
    TeamTemplateDto,
)
from services.api.errors import ApiError
from services.api.mappers.team_protocol import (
    agent_dto,
    dry_run_dto,
    preflight_dto,
    role_dto,
    template_dto,
)

router = APIRouter(tags=["team-protocol"])


def _context(catalog: CatalogSnapshot, project: ProjectSettings) -> PreflightContext:
    return PreflightContext(
        catalog=catalog,
        project=project,
        credentials=None,
        budget_ledger=None,
        policy_evaluator=None,
    )


def _compile_plan(catalog: CatalogSnapshot, project: ProjectSettings, path: str) -> CompiledRunPlan:
    protocol = load_protocol_definition(path)
    result = compile_protocol(protocol, catalog, project)
    if result.plan is None:
        raise ApiError(
            422,
            "Protocol Compile Failed",
            "; ".join(finding.message for finding in result.findings),
        )
    return result.plan


@router.get("/roles", response_model=list[RoleDefinitionDto])
async def list_roles() -> list[RoleDefinitionDto]:
    """Role 目录（RoleDefinition 不绑定模型；ADR-0011）。"""
    catalog = load_catalog_snapshot()
    return [role_dto(role) for role in catalog.roles.values()]


@router.get("/team-templates", response_model=list[TeamTemplateDto])
async def list_team_templates() -> list[TeamTemplateDto]:
    """Lean / Standard / Rigorous 模板目录。"""
    catalog = load_catalog_snapshot()
    return [template_dto(template) for template in catalog.team_templates.values()]


@router.get("/projects/{project_id}/agents", response_model=list[AgentSpecDto])
async def list_agents(project_id: str) -> list[AgentSpecDto]:
    """Agent 实例目录（Role 的配置实例；可独立绑定模型）。"""
    del project_id
    catalog = load_catalog_snapshot()
    return [agent_dto(agent) for agent in catalog.agents.values()]


@router.get("/projects/{project_id}/settings", response_model=ProjectSettingsDto)
async def get_project_settings(project_id: str) -> ProjectSettingsDto:
    """项目设置视图（wizard 默认项目；M14 后持久化）。"""
    del project_id
    project = load_project_settings()
    return ProjectSettingsDto(
        project_id=project.project_id,
        team_template_id=project.team_template_id,
        default_model_profile_id=project.default_model_profile_id,
        budget_policy_id=project.budget_policy_id,
        workspace_backend=project.workspace_backend,
        compute_profile=project.compute_profile,
        policy_id=project.policy_id,
    )


@router.patch("/agents/{agent_id}", response_model=AgentSpecDto)
async def update_agent(agent_id: str, payload: AgentUpdateDto) -> AgentSpecDto:
    """per-Agent 更新（model_binding 等）。

    M13 诚实边界：配置目录当前来自 examples/ 契约（只读快照）；运行中
    修改 Model/Tool/semantic 配置必须产生 Manifest Revision / Fork，
    持久化配置修改属 M14（PostgreSQL canonical state）。本端点验证
    变更合法性但不写回（返回 501 说明原因），防止伪持久化。
    """
    del payload
    catalog = load_catalog_snapshot()
    if agent_id not in catalog.agents:
        raise ApiError(404, "Not Found", f"agent not found: {agent_id}")
    raise ApiError(
        501,
        "Configuration Persistence Pending",
        "agent 配置持久化属 M14（PostgreSQL canonical state）；"
        "M13 使用 examples/config/agents.yaml 正式绑定（dry-run 投影验证），"
        "运行中语义变更必须走 Manifest Revision / Fork",
    )


@router.post("/protocols/validate", response_model=CompileResultDto)
async def validate_protocol(payload: ProtocolSourceDto) -> CompileResultDto:
    """协议校验：编译（不做任何副作用）。"""
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    try:
        protocol = load_protocol_definition(payload.path)
        result = compile_protocol(protocol, catalog, project)
    except ValueError as exc:
        raise ApiError(422, "Protocol Invalid", str(exc)) from exc
    return CompileResultDto(
        plan_id=str(result.plan.digest()) if result.plan else None,
        protocol_digest=str(result.plan.protocol_digest) if result.plan else None,
        findings=[
            {"code": f.code, "severity": f.severity.value, "message": f.message}
            for f in result.findings
        ],
        successful=result.successful,
    )


@router.post("/projects/{project_id}/compile", response_model=PreflightReportDto)
async def compile_and_preflight_endpoint(
    project_id: str, payload: ProtocolSourceDto
) -> PreflightReportDto:
    """compile + preflight（正式组合入口；预算预留仅发生在 preflight 内）。"""
    del project_id
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    protocol = load_protocol_definition(payload.path)
    _plan, report = compile_and_preflight(
        protocol,
        catalog,
        project,
        _context(catalog, project),
    )
    return preflight_dto(report)


@router.post("/projects/{project_id}/preflight", response_model=PreflightReportDto)
async def preflight_endpoint(project_id: str, payload: ProtocolSourceDto) -> PreflightReportDto:
    """preflight 复检（编译成功后执行）。"""
    del project_id
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    plan = _compile_plan(catalog, project, payload.path)
    report = run_preflight(plan, _context(catalog, project))
    return preflight_dto(report)


@router.post("/projects/{project_id}/dry-run", response_model=DryRunProjectionDto)
async def dry_run_endpoint(project_id: str, payload: ProtocolSourceDto) -> DryRunProjectionDto:
    """Dry Run：纯只读投影，零 Research side effect。

    不启动 Agent、不调用 Research Tool、不执行 Experiment、不写长期
    Memory、不 reserve budget（`dry_run_projection` 是纯函数）。
    """
    del project_id
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    plan = _compile_plan(catalog, project, payload.path)
    report = run_preflight(plan, _context(catalog, project))
    projection = dry_run_projection(plan, _context(catalog, project), report)
    return dry_run_dto(projection)
