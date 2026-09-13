"""Project 注册表路由（PLAN-041 WP-A，EC-01）。

单用户项目注册表：GET 合并视图（默认 example-project 由 examples 契约合成，
用户项目/改名/归档以 SQLite 覆盖——与 catalog_merge 同一"examples 基底 +
用户 override"哲学）；POST 创建即带默认设置行（复制 examples/project.yaml
模板，可随后编辑）；PATCH 重命名/归档。无 DELETE：项目是历史归属，归档即终态。
不触碰 M18（成员/RBAC/授权）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from packages.application.ports import ProjectSettings, ProjectStore
from packages.domain.core import ID, Timestamp
from packages.domain.projects import ProjectDefinition, ProjectStatus
from services.api.catalog import load_project_name, load_project_settings
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.projects import ProjectCreateDto, ProjectDto, ProjectUpdateDto
from services.api.errors import ApiError

router = APIRouter(tags=["projects"])

DEFAULT_PROJECT_ID = "example-project"
_EPOCH = Timestamp(datetime(1970, 1, 1, tzinfo=UTC))


def _store_of(deps: ApiDeps) -> ProjectStore:
    if deps.project_store is None:
        raise ApiError(503, "Project Store Unavailable", "project store not configured")
    return deps.project_store


def _default_project() -> ProjectDefinition:
    """example-project 注册条目：身份取 examples 契约（name 可被 store 行覆盖）。"""
    return ProjectDefinition(
        id=DEFAULT_PROJECT_ID,
        name=load_project_name(DEFAULT_PROJECT_ID),
        status=ProjectStatus.ACTIVE,
        created_at=_EPOCH,
        updated_at=_EPOCH,
    )


def _merged_projects(deps: ApiDeps) -> dict[str, ProjectDefinition]:
    merged: dict[str, ProjectDefinition] = {DEFAULT_PROJECT_ID: _default_project()}
    store = deps.project_store
    if store is not None:
        for project in store.list_projects():
            merged[project.id] = project
    return merged


def _dto(project: ProjectDefinition) -> ProjectDto:
    return ProjectDto(
        id=project.id,
        name=project.name,
        status=project.status.value,
        created_at=project.created_at.value.isoformat(),
        updated_at=project.updated_at.value.isoformat(),
    )


@router.get("/projects", response_model=list[ProjectDto])
async def list_projects(request: Request) -> list[ProjectDto]:
    """注册表视图（确定性排序：created_at, id；默认项目恒在首位）。"""
    deps: ApiDeps = get_deps(request)
    projects = sorted(
        _merged_projects(deps).values(),
        key=lambda item: (item.created_at.value, item.id),
    )
    return [_dto(project) for project in projects]


@router.post("/projects", response_model=ProjectDto, status_code=201)
async def create_project(payload: ProjectCreateDto, request: Request) -> ProjectDto:
    """创建项目：服务端生成 id + 自动落默认设置行（examples 模板副本）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    project_id = ID.generate().value
    now = Timestamp.now()
    project = ProjectDefinition(
        id=project_id,
        name=payload.name.strip(),
        status=ProjectStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    store.save_project(project)
    if deps.project_settings_store is not None:
        # 默认设置 = examples 模板的项目 id 副本；PUT /projects/{id}/settings 可编辑。
        template: ProjectSettings = load_project_settings()
        deps.project_settings_store.save(
            ProjectSettings(
                project_id=project_id,
                team_template_id=template.team_template_id,
                default_model_profile_id=template.default_model_profile_id,
                budget_policy_id=template.budget_policy_id,
                workspace_backend=template.workspace_backend,
                compute_profile=template.compute_profile,
                policy_id=template.policy_id,
                reference_protocol=template.reference_protocol,
            )
        )
    return _dto(project)


@router.patch("/projects/{project_id}", response_model=ProjectDto)
async def update_project(
    project_id: str, payload: ProjectUpdateDto, request: Request
) -> ProjectDto:
    """重命名与/或归档（ACTIVE ⇄ ARCHIVED）；未知 id 404；空载荷 422。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    current = _merged_projects(deps).get(project_id)
    if current is None:
        raise ApiError(404, "Not Found", f"project not found: {project_id}")
    if payload.name is None and payload.status is None:
        raise ApiError(422, "Empty Patch", "name or status is required")
    project = current
    if payload.name is not None:
        project = project.renamed(payload.name.strip(), at=Timestamp.now())
    if payload.status is not None:
        project = project.with_status(ProjectStatus(payload.status), at=Timestamp.now())
    store.save_project(project)
    return _dto(project)
