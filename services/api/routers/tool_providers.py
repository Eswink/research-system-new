"""Tool Provider 控制面只读路由（PLAN-043 WP-A，EC-02）。

`GET /tool-providers`：把既有 catalog `tool_providers`（Skill→Capability→
ToolResolver→Tool 结构的来源目录）与 preflight 已有的三态健康投影为只读视图。
NATIVE provider 结构性可用（HEALTHY）；外部 provider 未注册实例时诚实收敛为
UNKNOWN（不伪装健康）。

PLAN-060（EC-05）起，管理动作（注册/更新/批准/吊销/健康复核）在
`/tool-provider-registrations`（`routers/tool_registrations.py`）。本端点仍是
只读目录：只反映**已批准（ACTIVE）**的注册与 examples 契约，PENDING/REVOKED
不出现在这里。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.domain.enums import EndpointHealth
from packages.domain.tools import ToolProviderSpec
from services.api.catalog_merge import merged_catalog_snapshot
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.tool_providers import ToolProviderDto, ToolProviderListDto
from services.api.preflight_support import build_provider_health
from services.api.tool_registry_support import REGISTRY_UNAVAILABLE_REASON

router = APIRouter(tags=["tool-providers"])


def _dto(spec: ToolProviderSpec, health: str) -> ToolProviderDto:
    return ToolProviderDto(
        id=spec.id,
        kind=spec.kind.value,
        trust_level=spec.trust_level.value,
        effect_class=spec.effect_class.value,
        capabilities=sorted(spec.capabilities),
        transport=spec.transport,
        protocol_version=spec.protocol_version,
        network_domains=sorted(spec.network_domains),
        health_check=spec.health_check,
        health=health,
    )


@router.get("/tool-providers", response_model=ToolProviderListDto)
async def list_tool_providers(request: Request) -> ToolProviderListDto:
    """Tool Provider 目录（确定性排序）+ 三态健康。

    只读：无 install/approve/revoke（供应链治理写面在 /tool-provider-registrations），
    无凭据回显。注册表未装配时 management_available=false 并给出原因。
    """
    deps: ApiDeps = get_deps(request)
    catalog = merged_catalog_snapshot(deps)
    health = build_provider_health(deps, catalog)
    providers = [
        _dto(spec, health.get(provider_id, EndpointHealth.UNKNOWN).value)
        for provider_id, spec in sorted(catalog.tool_providers.items())
    ]
    manageable = deps.tool_provider_registry is not None
    return ToolProviderListDto(
        providers=providers,
        management_available=manageable,
        management_reason=None if manageable else REGISTRY_UNAVAILABLE_REASON,
    )
