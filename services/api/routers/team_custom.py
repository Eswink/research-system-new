"""用户自定义契约路由：Role/TeamTemplate 创建、Agent 克隆与删除（PLAN-040 WP-B）。

`CONTROL_PLANE_API.md` 原高估列出的 `POST /roles/custom`、
`POST /team-templates/custom`、`POST /agents/{id}/clone` 在此落地为真实端点；
DELETE /agents/{id} 补 G10 删除语义（仅用户 store 记录可删，examples 契约基线
不可删除）。自定义契约与 examples 项同 schema、同 domain 构造、同合并视图，
compiler/preflight 不可区分（无第二套事实源）。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from fastapi import APIRouter, Request, Response

from packages.application.ports import CatalogOverrideStore
from packages.domain.core import ID
from services.api.composition import ApiDeps
from services.api.custom_catalog import (
    KIND_ROLES,
    KIND_TEAM_TEMPLATES,
    CustomContractInvalid,
    build_contract,
)
from services.api.deps import get_deps
from services.api.dto.team_protocol import (
    AgentCloneDto,
    AgentSpecDto,
    RoleDefinitionDto,
    TeamTemplateDto,
)
from services.api.errors import ApiError
from services.api.mappers.team_protocol import (
    agent_dto,
    agent_version,
    role_dto,
    template_dto,
)
from services.api.team_support import merged_context, require_agent_store

router = APIRouter(tags=["team-protocol"])


def _require_override_store(deps: ApiDeps) -> CatalogOverrideStore:
    if deps.catalog_overrides is None:
        raise ApiError(
            503,
            "Catalog Override Store Unavailable",
            "catalog override store not configured",
        )
    return deps.catalog_overrides


def _create_contract(
    deps: ApiDeps, kind: str, payload: dict[str, Any], existing: Mapping[str, object]
) -> Any:
    """schema/domain 校验 + id 冲突判定 + upsert；返回构造出的实体。"""
    store = _require_override_store(deps)
    try:
        entity = build_contract(kind, payload)
    except CustomContractInvalid as exc:
        raise ApiError(422, "Custom Contract Invalid", str(exc)) from exc
    if entity.id in existing:
        raise ApiError(409, "Contract Id Exists", f"id already declared: {entity.id}")
    store.upsert(kind, entity.id, payload)
    return entity


@router.post("/roles/custom", response_model=RoleDefinitionDto, status_code=201)
async def create_custom_role(payload: dict[str, Any], request: Request) -> RoleDefinitionDto:
    """创建用户自定义 RoleDefinition（role-definition.schema.json 校验）。"""
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    role = _create_contract(deps, KIND_ROLES, payload, catalog.roles)
    return role_dto(role)


@router.post("/team-templates/custom", response_model=TeamTemplateDto, status_code=201)
async def create_custom_team_template(payload: dict[str, Any], request: Request) -> TeamTemplateDto:
    """创建用户自定义 TeamTemplate（team-template.schema.json 校验）。"""
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    template = _create_contract(deps, KIND_TEAM_TEMPLATES, payload, catalog.team_templates)
    return template_dto(template)


@router.post("/agents/{agent_id}/clone", response_model=AgentSpecDto, status_code=201)
async def clone_agent(
    agent_id: str, payload: AgentCloneDto, request: Request, response: Response
) -> AgentSpecDto:
    """克隆 Agent 配置实例（同 Role/绑定/上下文，新 id；契约基线项亦可克隆为用户记录）。"""
    deps: ApiDeps = get_deps(request)
    catalog, _project = merged_context(deps)
    source = catalog.agents.get(agent_id)
    if source is None:
        raise ApiError(404, "Not Found", f"agent not found: {agent_id}")
    new_id = payload.new_id or ID.generate().value
    if new_id in catalog.agents:
        raise ApiError(409, "Agent Id Exists", f"agent id already declared: {new_id}")
    agent = replace(source, id=new_id)
    require_agent_store(deps).save_agent(agent)
    response.headers["ETag"] = agent_version(agent)
    return agent_dto(agent)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, request: Request) -> None:
    """删除用户 Agent 记录（G10；examples 契约基线不在 store 中 → 404）。"""
    deps: ApiDeps = get_deps(request)
    store = require_agent_store(deps)
    try:
        store.delete_agent(agent_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"user agent not found: {agent_id}") from exc
