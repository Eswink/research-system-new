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

from dataclasses import replace

from packages.application.ports import CatalogSnapshot, ProjectSettings
from services.api.catalog import load_catalog_snapshot, load_project_settings
from services.api.composition import ApiDeps


def merged_catalog_snapshot(deps: ApiDeps) -> CatalogSnapshot:
    """合并目录快照：{**examples, **user}（user 按 id 覆盖）。

    Relay 身份覆盖：用户 endpoint 的 name 与 example endpoint id 相同时
    按名称覆盖（控制面单一 relay 语义——example 协议内模型绑定经该 id
    解析到用户 relay，使向导配置真实进入 preflight/run 链）。
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
    return replace(base, endpoints=endpoints, models=models, agents=agents)


def merged_project_settings(deps: ApiDeps) -> ProjectSettings:
    """项目设置：ProjectSettingsStore 优先，空时回退 examples/project.yaml。"""
    if deps.project_settings_store is not None:
        saved = deps.project_settings_store.get()
        if saved is not None:
            return saved
    return load_project_settings()
