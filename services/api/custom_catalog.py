"""用户自定义契约（Role / TeamTemplate）创建用例（PLAN-040 WP-B）。

与 examples/config 契约同一 JSON Schema（role-definition.schema.json /
team-template.schema.json）+ 同一 domain 构造器（`role_from_mapping` /
`team_template_from_mapping`），保证控制面自定义项与静态目录项在合并视图、
compiler 与 preflight 中不可区分。kind 词表封闭于此模块；存储经
CatalogOverrideStore Port（未配置 → 路由诚实 503）。
"""

from __future__ import annotations

from typing import Any

from adapters.contracts.base import ContractLoadError, load_json_schema, validate_instance
from adapters.contracts.roles_loaders import role_from_mapping, team_template_from_mapping
from packages.application.ports import CatalogOverrideStore
from packages.domain.roles import RoleDefinition, TeamTemplate

KIND_ROLES = "roles"
KIND_TEAM_TEMPLATES = "team_templates"

_SCHEMA_BY_KIND = {
    KIND_ROLES: "role-definition.schema.json",
    KIND_TEAM_TEMPLATES: "team-template.schema.json",
}


class CustomContractInvalid(ValueError):
    """自定义契约 schema/domain 校验失败（路由映射为 422）。"""


def build_contract(kind: str, document: dict[str, Any]) -> RoleDefinition | TeamTemplate:
    """schema + domain 双重校验并构造实体；失败统一 CustomContractInvalid。"""
    schema_name = _SCHEMA_BY_KIND.get(kind)
    if schema_name is None:
        raise CustomContractInvalid(f"unknown custom contract kind: {kind!r}")
    try:
        validate_instance(load_json_schema(schema_name), document, f"custom-{kind}")
        if kind == KIND_ROLES:
            return role_from_mapping(document)
        return team_template_from_mapping(document)
    except (ContractLoadError, KeyError, TypeError, ValueError) as exc:
        raise CustomContractInvalid(str(exc)) from exc


def create_override(store: CatalogOverrideStore, kind: str, document: dict[str, Any]) -> str:
    """校验并 upsert 自定义契约；返回实体 id（冲突判定由路由基于合并视图完成）。"""
    entity = build_contract(kind, document)
    store.upsert(kind, entity.id, document)
    return entity.id
