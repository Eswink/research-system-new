"""Control Plane 目录合并：SQLite 用户配置覆盖 examples 契约目录（M13-R1）。

Root cause（BLOCKER-B3）：`catalog.py::load_catalog_snapshot()` 每次从
examples/config/*.yaml 加载静态目录（含硬编码 opencode/DeepSeek 示例），
与用户经 wizard 配置、SQLite 持久化的 endpoint/model 完全无关，导致
preflight 恒定失败、用户配置永不进入执行链。

本模块提供合并视图：以 examples 为基底，按 id 用
EndpointStore/ModelStore/AgentStore 中的用户配置覆盖合并（用户配置优先），
并优先读 ProjectSettingsStore 中的项目设置。M14 PostgreSQL canonical
state 落地后本服务由持久化实现替换（CatalogSnapshot Port 不变）。
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Protocol, TypeVar

from adapters.contracts.roles_loaders import role_from_mapping, team_template_from_mapping
from packages.application.ports import CatalogSnapshot, ProjectSettings
from packages.domain.enums import ToolPackState
from packages.domain.tools import ToolProviderSpec
from services.api.catalog import load_catalog_snapshot, load_project_settings
from services.api.composition import ApiDeps
from services.api.custom_catalog import KIND_ROLES, KIND_TEAM_TEMPLATES
from services.api.errors import ApiError


class _Identifiable(Protocol):
    """合并覆盖所需的结构面：实体携带 str id。"""

    @property
    def id(self) -> str: ...


_T = TypeVar("_T", bound=_Identifiable)

_PACK_VERSION_SUFFIX = re.compile(r"_v\d+(\.\d+)*$")


def _merge_overrides(
    items: Mapping[str, _T], store: object, kind: str, build: Callable[[object], _T]
) -> dict[str, _T]:
    """合并用户自定义契约覆盖（WP-B）。

    行隔离：读取只接受创建时已校验的 document；手工改库导致的坏行跳过
    （不阻断整个目录面），与 artifact missing-reference 同一降级哲学。
    """
    merged: dict[str, _T] = dict(items)
    for raw in store.list(kind):  # type: ignore[attr-defined]
        try:
            entity = build(raw)
        except Exception:  # noqa: BLE001 - 坏行跳过，不伪造
            continue
        merged[entity.id] = entity
    return merged


def merged_catalog_snapshot(deps: ApiDeps) -> CatalogSnapshot:
    """合并目录快照：{**examples, **user}（user 按 id 覆盖）。

    Relay 身份覆盖：用户 endpoint 的 name 与 example endpoint id 相同时
    按名称覆盖（控制面单一 relay 语义——example 协议内模型绑定经该 id
    解析到用户 relay，使向导配置真实进入 preflight/run 链）。
    WP-B：Role/TeamTemplate 经 CatalogOverrideStore 用户覆盖（同 id 语义）。
    WP-D/PLAN-060：ACTIVE 的 provider 注册进入 tool_providers，并把它 pin 的
    digest 写进 tool_pack_digests —— preflight 的供应链检查因此看到的是
    "用户实际 pin 的那份"，PENDING/REVOKED 一律不进入（未批准/已吊销不可用）。
    """
    base = load_catalog_snapshot()
    endpoints = dict(base.endpoints)
    for endpoint in deps.endpoint_store.list_endpoints():
        endpoints[endpoint.id] = endpoint
        if endpoint.name in endpoints and endpoint.name != endpoint.id:
            endpoints[endpoint.name] = endpoint
    models = dict(base.models)
    for model in deps.model_store.list_models():
        models[model.id] = model
    agents = dict(base.agents)
    if deps.agent_store is not None:
        for agent in deps.agent_store.list_agents():
            agents[agent.id] = agent
    roles = base.roles
    team_templates = base.team_templates
    if deps.catalog_overrides is not None:
        roles = _merge_overrides(roles, deps.catalog_overrides, KIND_ROLES, role_from_mapping)
        team_templates = _merge_overrides(
            team_templates, deps.catalog_overrides, KIND_TEAM_TEMPLATES, team_template_from_mapping
        )
    tool_providers, tool_pack_digests = _merge_registered_providers(deps, base)
    tool_pack_digests = _merge_installed_packs(deps, tool_pack_digests)
    return replace(
        base,
        endpoints=endpoints,
        models=models,
        agents=agents,
        roles=roles,
        team_templates=team_templates,
        tool_providers=tool_providers,
        tool_pack_digests=tool_pack_digests,
    )


def _merge_registered_providers(
    deps: ApiDeps, base: CatalogSnapshot
) -> tuple[dict[str, ToolProviderSpec], dict[str, str]]:
    """ACTIVE 注册 → 目录 providers + 该 provider 的 pinned digest。

    只合并 ACTIVE：PENDING 是"已提交待批准"，REVOKED 是终态退出；两者进入
    目录都会让 preflight 看到本不该可用的来源。行读取失败按坏行跳过（不阻断
    整个目录面），与 `_merge_overrides` 同一降级哲学。
    """
    providers = dict(base.tool_providers)
    digests = dict(base.tool_pack_digests)
    registry = deps.tool_provider_registry
    if registry is None:
        return providers, digests
    for registration in registry.list_registrations():
        if not registration.active:
            continue
        try:
            spec = registration.spec()
        except Exception:  # noqa: BLE001 - 坏行跳过，不伪造
            continue
        providers[spec.id] = spec
        digests[spec.id] = registration.pinned_revision
    return providers, digests


def _merge_installed_packs(deps: ApiDeps, digests: dict[str, str]) -> dict[str, str]:
    """INSTALLED 的 ToolPack → `tool_pack_digests`（键 = pack id 去掉 `_vN` 后缀）。

    键口径与 examples 契约（`catalog._load_tool_pack_digests`）一致：pack id 带版本后缀，
    而 preflight 的供应链检查按 **provider id** 查表。只有 INSTALLED 贡献 digest——
    待批准的权限扩张不生效、REVOKED 是终态退出（吊销后 pin 消失、检查重新报警）。
    """
    store = deps.tool_pack_store
    if store is None:
        return digests
    merged = dict(digests)
    for record in store.snapshot().values():
        if record.state is not ToolPackState.INSTALLED:
            continue
        merged[_PACK_VERSION_SUFFIX.sub("", record.pack_id)] = str(record.manifest.digest)
    return merged


DEFAULT_PROJECT_ID = "example-project"


def require_registered_project(deps: ApiDeps, project_id: str) -> None:
    """项目注册校验（WP-B）：未注册项目 404，不接收幽灵写入。

    默认 example-project 恒注册（examples 契约合成条目）；其余以
    ProjectStore（注册表）为准。store 未配置时仅默认项目可通过。
    """
    if project_id == DEFAULT_PROJECT_ID:
        return
    store = deps.project_store
    if store is None:
        raise ApiError(404, "Project Not Found", f"project not registered: {project_id}")
    try:
        store.get_project(project_id)
    except KeyError as exc:
        raise ApiError(404, "Project Not Found", f"project not registered: {project_id}") from exc


def merged_project_settings(deps: ApiDeps, project_id: str = DEFAULT_PROJECT_ID) -> ProjectSettings:
    """项目设置：ProjectSettingsStore 按 project_id 精确优先（WP-A/PLAN-041）。

    - 默认 example-project：store 无记录时回退 examples/config/project.yaml
      （wizard 前即有项目上下文，语义与 M13-R1 一致）；
    - 其它注册项目：由 POST /projects 自动创建默认设置行；仍缺失说明数据面
      被旁路修改——诚实 404，不回退默认项目的设置（不伪装归属）。
    """
    if deps.project_settings_store is not None:
        saved = deps.project_settings_store.get(project_id)
        if saved is not None:
            return saved
    if project_id == DEFAULT_PROJECT_ID:
        return load_project_settings()
    if deps.project_settings_store is None:
        raise ApiError(
            503,
            "Settings Store Unavailable",
            "project settings store not configured",
        )
    raise ApiError(404, "Project Settings Not Found", f"project not registered: {project_id}")
