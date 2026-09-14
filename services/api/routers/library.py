"""Library 库目录路由（PLAN-20260914-044 WP-B，EC-03 第一批）。

prompts / datasets / notebooks 三页共享的目录事实：按项目登记具名条目。
无 DELETE：归档即终态（历史保留）。未知 id → 404；store 未配置 → 503。
项目归属校验复用注册表（未注册项目 404，不回退他项目）。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports import LibraryStore
from packages.domain.core import ID, Timestamp
from packages.domain.library import LibraryResource, ResourceKind, ResourceStatus
from services.api.catalog_merge import require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.library import (
    LibraryResourceCreateDto,
    LibraryResourceDto,
    LibraryResourceUpdateDto,
)
from services.api.errors import ApiError

router = APIRouter(tags=["library"])


def _store_of(deps: ApiDeps) -> LibraryStore:
    if deps.library_store is None:
        raise ApiError(503, "Library Store Unavailable", "library store not configured")
    return deps.library_store


def _dto(resource: LibraryResource) -> LibraryResourceDto:
    return LibraryResourceDto(
        id=resource.id,
        project_id=resource.project_id,
        kind=resource.kind.value,
        name=resource.name,
        description=resource.description,
        content_ref=resource.content_ref,
        tags=list(resource.tags),
        status=resource.status.value,
        created_at=resource.created_at.value.isoformat(),
        updated_at=resource.updated_at.value.isoformat(),
    )


@router.get("/projects/{project_id}/library", response_model=list[LibraryResourceDto])
async def list_library(
    project_id: str, request: Request, kind: ResourceKind | None = None
) -> list[LibraryResourceDto]:
    """项目库条目（确定性排序：created_at, id）；可选 kind 过滤。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    store = _store_of(deps)
    return [_dto(resource) for resource in store.list_resources(project_id, kind)]


@router.post("/projects/{project_id}/library", response_model=LibraryResourceDto, status_code=201)
async def create_library(
    project_id: str, payload: LibraryResourceCreateDto, request: Request
) -> LibraryResourceDto:
    """创建库条目：服务端生成 id + 路径项目归属（未注册项目 404）。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    store = _store_of(deps)
    now = Timestamp.now()
    resource = LibraryResource(
        id=ID.generate().value,
        project_id=project_id,
        kind=ResourceKind(payload.kind),
        name=payload.name.strip(),
        description=payload.description,
        content_ref=payload.content_ref,
        tags=tuple(tag.strip() for tag in payload.tags if tag.strip()),
        status=ResourceStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    store.save_resource(resource)
    return _dto(resource)


@router.get("/library/{resource_id}", response_model=LibraryResourceDto)
async def get_library(resource_id: str, request: Request) -> LibraryResourceDto:
    """单条库条目；未知 id → 404。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        return _dto(store.get_resource(resource_id))
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"library resource not found: {resource_id}") from exc


@router.patch("/library/{resource_id}", response_model=LibraryResourceDto)
async def update_library(
    resource_id: str, payload: LibraryResourceUpdateDto, request: Request
) -> LibraryResourceDto:
    """重命名与/或归档（ACTIVE ⇄ ARCHIVED）；未知 id 404；空载荷 422。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        resource = store.get_resource(resource_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"library resource not found: {resource_id}") from exc
    if payload.name is None and payload.status is None:
        raise ApiError(422, "Empty Patch", "name or status is required")
    if payload.name is not None:
        resource = resource.renamed(payload.name.strip(), at=Timestamp.now())
    if payload.status is not None:
        resource = resource.with_status(ResourceStatus(payload.status), at=Timestamp.now())
    store.save_resource(resource)
    return _dto(resource)
