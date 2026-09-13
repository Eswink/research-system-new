"""Team / Protocol / Preflight / Dry-run 控制面路由（M13-R1）。

流程：HTTP → DTO → use case（protocol_compile + preflight）→ Domain / Port。
M13-R1 变更：
- 目录/项目设置来自 merged 视图（SQLite 用户配置覆盖 examples，B3.1）；
- preflight context 注入 NativePolicyEvaluator（B3.3）与实时 endpoint
  健康（B3.4）；
- create/patch agent 真实持久化（AgentStore，B3.5），不再 501 伪拒绝；
- 共享辅助（context/compile/agent DTO）在 team_support.py（300 行阈值拆分）；
- 语义类运行中变更（Manifest Revision / Fork）仍保持诚实 501 边界。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from packages.application.ports import ProjectSettings
from packages.application.preflight.preflight import (
    compile_and_preflight,
    dry_run_projection,
    run_preflight,
)
from packages.application.protocol_compile.compiler import compile_protocol
from packages.domain.core import ID
from packages.domain.protocols import ProtocolDefinition
from services.api.catalog_merge import merged_project_settings, require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps, require_if_match
from services.api.dto.team_protocol import (
    AgentCreateDto,
    AgentSpecDto,
    AgentUpdateDto,
    CompileResultDto,
    DryRunProjectionDto,
    PreflightReportDto,
    ProjectSettingsDto,
    ProjectSettingsUpdateDto,
    ProtocolSourceDto,
    RoleDefinitionDto,
    TeamTemplateDto,
)
from services.api.errors import ApiError
from services.api.mappers.team_protocol import (
    agent_dto,
    agent_version,
    dry_run_dto,
    preflight_dto,
    role_dto,
    template_dto,
)
from services.api.protocol_source import draft_ref_of, load_protocol_for_source
from services.api.team_support import (
    AgentDraft,
    agent_from_dto,
    binding_from_dto,
    build_preflight_context,
    compile_plan_for_protocol,
    merged_context,
    require_agent_store,
    validate_model_reference,
)

router = APIRouter(tags=["team-protocol"])


@router.get("/roles", response_model=list[RoleDefinitionDto])
async def list_roles(request: Request) -> list[RoleDefinitionDto]:
    """Role 目录（RoleDefinition 不绑定模型；ADR-0011；合并视图）。"""
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    return [role_dto(role) for role in catalog.roles.values()]


@router.get("/team-templates", response_model=list[TeamTemplateDto])
async def list_team_templates(request: Request) -> list[TeamTemplateDto]:
    """Lean / Standard / Rigorous 模板目录。"""
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    return [template_dto(template) for template in catalog.team_templates.values()]


@router.get("/projects/{project_id}/agents", response_model=list[AgentSpecDto])
async def list_agents(project_id: str, request: Request) -> list[AgentSpecDto]:
    """Agent 实例目录（Role 的配置实例；可独立绑定模型；合并视图）。"""
    del project_id
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    return [agent_dto(agent) for agent in catalog.agents.values()]


@router.post("/projects/{project_id}/agents", response_model=AgentSpecDto, status_code=201)
async def create_agent(
    project_id: str, payload: AgentCreateDto, request: Request, response: Response
) -> AgentSpecDto:
    """创建 Agent 实例（同 Role 可多实例；role/model 引用真实校验）。"""
    del project_id
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    if payload.role not in catalog.roles:
        raise ApiError(422, "Invalid Role", f"role is unavailable: {payload.role!r}")
    binding = binding_from_dto(payload.model_binding)
    validate_model_reference(catalog, binding)
    agent = agent_from_dto(
        AgentDraft(
            agent_id=ID.generate().value,
            role=payload.role,
            binding=binding,
            workspace_policy=payload.workspace_policy,
            max_context_tokens=payload.max_context_tokens,
            max_iterations=payload.max_iterations,
        )
    )
    require_agent_store(deps).save_agent(agent)
    response.headers["ETag"] = agent_version(agent)
    return agent_dto(agent)


@router.get("/projects/{project_id}/settings", response_model=ProjectSettingsDto)
async def get_project_settings(project_id: str, request: Request) -> ProjectSettingsDto:
    """项目设置视图（WP-B/PLAN-041：ProjectSettingsStore 按 project_id 精确，
    仅默认 example-project 允许 examples 回退；未注册/未配置 404）。"""
    deps: ApiDeps = get_deps(request)
    project = merged_project_settings(deps, project_id)
    return ProjectSettingsDto(
        project_id=project.project_id,
        team_template_id=project.team_template_id,
        default_model_profile_id=project.default_model_profile_id,
        budget_policy_id=project.budget_policy_id,
        workspace_backend=project.workspace_backend,
        compute_profile=project.compute_profile,
        policy_id=project.policy_id,
        reference_protocol=project.reference_protocol,
    )


@router.put("/projects/{project_id}/settings", response_model=ProjectSettingsDto)
async def put_project_settings(
    project_id: str, payload: ProjectSettingsUpdateDto, request: Request
) -> ProjectSettingsDto:
    """项目设置持久化（ProjectSettingsStore；模板/工作区引用校验 + 项目注册校验）。"""
    deps: ApiDeps = get_deps(request)
    if deps.project_settings_store is None:
        raise ApiError(503, "Settings Store Unavailable", "project settings store not configured")
    require_registered_project(deps, project_id)
    catalog, _project = merged_context(deps)
    if payload.team_template_id not in catalog.team_templates:
        raise ApiError(
            422,
            "Invalid Team Template",
            f"template unavailable: {payload.team_template_id!r}",
        )
    if payload.workspace_backend not in catalog.workspaces:
        raise ApiError(
            422,
            "Invalid Workspace",
            f"workspace unavailable: {payload.workspace_backend!r}",
        )
    settings = ProjectSettings(
        project_id=project_id,
        team_template_id=payload.team_template_id,
        default_model_profile_id=payload.default_model_profile_id,
        budget_policy_id=payload.budget_policy_id,
        workspace_backend=payload.workspace_backend,
        compute_profile=payload.compute_profile,
        policy_id=payload.policy_id,
        reference_protocol=payload.reference_protocol,
    )
    deps.project_settings_store.save(settings)
    return ProjectSettingsDto(
        project_id=settings.project_id,
        team_template_id=settings.team_template_id,
        default_model_profile_id=settings.default_model_profile_id,
        budget_policy_id=settings.budget_policy_id,
        workspace_backend=settings.workspace_backend,
        compute_profile=settings.compute_profile,
        policy_id=settings.policy_id,
        reference_protocol=settings.reference_protocol,
    )


@router.patch("/agents/{agent_id}", response_model=AgentSpecDto)
async def update_agent(
    agent_id: str, payload: AgentUpdateDto, request: Request, response: Response
) -> AgentSpecDto:
    """per-Agent 更新（model_binding 等）持久化到 AgentStore。

    语义变更（运行中改 Model/Tool）仍须 Manifest Revision / Fork（M14）。
    """
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    base = catalog.agents.get(agent_id)
    if base is None:
        raise ApiError(404, "Not Found", f"agent not found: {agent_id}")
    require_if_match(request, agent_version(base))
    store = require_agent_store(deps)
    try:
        current = store.get_agent(agent_id)
    except KeyError:
        current = base
    binding = (
        binding_from_dto(payload.model_binding)
        if payload.model_binding is not None
        else current.model_binding
    )
    if payload.model_binding is not None:
        validate_model_reference(catalog, binding)
    agent = agent_from_dto(
        AgentDraft(
            agent_id=agent_id,
            role=current.role,
            binding=binding,
            workspace_policy=payload.workspace_policy
            if payload.workspace_policy is not None
            else (current.workspace_policy.value if current.workspace_policy else None),
            max_context_tokens=payload.max_context_tokens
            if payload.max_context_tokens is not None
            else (current.context.max_context_tokens if current.context else None),
            max_iterations=payload.max_iterations
            if payload.max_iterations is not None
            else (current.context.max_iterations if current.context else None),
        ),
        base=current,
    )
    store.save_agent(agent)
    response.headers["ETag"] = agent_version(agent)
    return agent_dto(agent)


@router.post("/protocols/validate", response_model=CompileResultDto)
async def validate_protocol(payload: ProtocolSourceDto, request: Request) -> CompileResultDto:
    """协议校验：编译（不做任何副作用；合并目录视图；path 或草稿修订同源）。"""
    deps: ApiDeps = get_deps(request)
    catalog, project = merged_context(deps)
    try:
        protocol = _protocol_of(deps, payload)
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


def _protocol_of(deps: ApiDeps, payload: ProtocolSourceDto) -> ProtocolDefinition:
    """DTO → ProtocolDefinition（WP-B：受控 path 或不可变草稿修订引用二选一）。"""
    return load_protocol_for_source(
        deps, payload.path, draft_ref_of(payload.draft_id, payload.draft_revision)
    )


@router.post("/projects/{project_id}/compile", response_model=PreflightReportDto)
async def compile_and_preflight_endpoint(
    project_id: str, payload: ProtocolSourceDto, request: Request
) -> PreflightReportDto:
    """compile + preflight（正式组合入口；真实 health/policy 接线；WP-B 项目归属）。"""
    deps: ApiDeps = get_deps(request)
    catalog, project = merged_context(deps, project_id)
    protocol = _protocol_of(deps, payload)
    _plan, report = compile_and_preflight(
        protocol,
        catalog,
        project,
        build_preflight_context(deps, catalog, project),
    )
    return preflight_dto(report)


@router.post("/projects/{project_id}/preflight", response_model=PreflightReportDto)
async def preflight_endpoint(
    project_id: str, payload: ProtocolSourceDto, request: Request
) -> PreflightReportDto:
    """preflight 复检（编译成功后执行；真实 health/policy 接线；WP-B 项目归属）。"""
    deps: ApiDeps = get_deps(request)
    plan = compile_plan_for_protocol(deps, _protocol_of(deps, payload), project_id)
    catalog, project = merged_context(deps, project_id)
    report = run_preflight(plan, build_preflight_context(deps, catalog, project))
    return preflight_dto(report)


@router.post("/projects/{project_id}/dry-run", response_model=DryRunProjectionDto)
async def dry_run_endpoint(
    project_id: str, payload: ProtocolSourceDto, request: Request
) -> DryRunProjectionDto:
    """Dry Run：纯只读投影，零 Research side effect。

    不启动 Agent、不调用 Research Tool、不执行 Experiment、不写长期
    Memory、不 reserve budget（`dry_run_projection` 是纯函数；context
    不注入 budget ledger，preflight 预留仅为本地 digest 引用）。
    WP-B：按路径项目解析设置（未注册项目 404）。
    """
    deps: ApiDeps = get_deps(request)
    plan = compile_plan_for_protocol(deps, _protocol_of(deps, payload), project_id)
    catalog, project = merged_context(deps, project_id)
    context = build_preflight_context(deps, catalog, project)
    report = run_preflight(plan, context)
    projection = dry_run_projection(plan, context, report)
    return dry_run_dto(projection)
