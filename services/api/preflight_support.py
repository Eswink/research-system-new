"""Preflight 支持：实时 endpoint 健康与策略求值注入（M13-R1）。

Root cause（BLOCKER-B3 之一面）：`PreflightContext.endpoint_health` 默认
空字典 → 所有 endpoint 判 `EndpointHealth.UNKNOWN` → `ENDPOINT_UNHEALTHY`
恒定触发，即使用户 endpoint 真实健康；`policy_evaluator=None` →
`no policy evaluator is injected` 恒定触发。

本模块提供：
- `build_endpoint_health`：对合并目录中凭据可解析的 endpoint 实时探测
  （复用 gateway.probe_connectivity 语义，不新造探测逻辑），单次请求内
  按 endpoint id 去重缓存；
- `build_provider_health`：tool provider 三态健康（WP-D；未注册实现/未声明
  health_check/探测异常 = UNKNOWN，绝不伪装 True）；
- `build_policy_evaluator`：NativePolicyEvaluator 接线（policy 目录存在时）。
"""

from __future__ import annotations

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import CatalogSnapshot, InvalidInputError, PolicyEvaluator
from packages.domain.enums import EndpointHealth, ProviderType
from packages.domain.models import LLMEndpoint
from packages.domain.tools import ToolProviderSpec
from services.api.composition import ApiDeps


def build_endpoint_health(deps: ApiDeps, catalog: CatalogSnapshot) -> dict[str, EndpointHealth]:
    """实时 endpoint 健康（GET /models 探测；凭据缺失/瞬时失败 → UNKNOWN）。

    结果只反映探测时刻连通性，不持久化；preflight 的 _credential_findings
    单独报告 credential 问题，不混淆 health 语义。
    """
    health: dict[str, EndpointHealth] = {}
    for endpoint_id, endpoint in catalog.endpoints.items():
        health[endpoint_id] = _probe_endpoint(deps, endpoint)
    return health


def build_policy_evaluator(catalog: CatalogSnapshot) -> PolicyEvaluator | None:
    """NativePolicyEvaluator 接线：policy 目录存在时构造，否则 None（诚实缺口）。"""
    if catalog.policy is None:
        return None
    return NativePolicyEvaluator(policy=catalog.policy)


def _probe_endpoint(deps: ApiDeps, endpoint: LLMEndpoint) -> EndpointHealth:
    try:
        credential = deps.credentials.resolve(endpoint.credential_ref)
    except InvalidInputError:
        return EndpointHealth.UNKNOWN
    try:
        snapshot = deps.gateway.probe_connectivity(endpoint, credential)
    except Exception:  # noqa: BLE001 - gateway 错误已 redacted；health 按 UNKNOWN 收敛
        return EndpointHealth.UNKNOWN
    return EndpointHealth.HEALTHY if snapshot.ok else EndpointHealth.DEGRADED


def build_provider_health(deps: ApiDeps, catalog: CatalogSnapshot) -> dict[str, EndpointHealth]:
    """Tool provider 三态健康（WP-D；取代恒 True 的伪造接线）。

    探测超时预算由 provider adapter 自有（Port 无 timeout 参数）；控制面
    当前未注册任何外部 ToolProvider 实例时，非 NATIVE provider 诚实收敛为
    UNKNOWN（触发 TOOL_HEALTH_UNPROVEN 警示而非伪装健康）。
    """
    health: dict[str, EndpointHealth] = {}
    for provider_id, spec in catalog.tool_providers.items():
        health[provider_id] = _probe_provider(deps, spec)
    return health


def _probe_provider(deps: ApiDeps, spec: ToolProviderSpec) -> EndpointHealth:
    if spec.kind is ProviderType.NATIVE:
        # 内置 runtime 能力：无外部 transport 可探测，结构性可用。
        return EndpointHealth.HEALTHY
    provider = deps.tool_providers.get(spec.id)
    if provider is None or not spec.health_check:
        return EndpointHealth.UNKNOWN
    try:
        report = provider.check_health(spec)
    except Exception:  # noqa: BLE001 - 探测异常按不可证明收敛，不伪装结果
        return EndpointHealth.UNKNOWN
    return EndpointHealth(report.status)
