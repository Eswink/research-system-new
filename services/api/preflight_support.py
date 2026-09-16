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

from dataclasses import dataclass

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import CatalogSnapshot, InvalidInputError, PolicyEvaluator
from packages.domain.enums import EndpointHealth, ProviderType
from packages.domain.models import LLMEndpoint
from packages.domain.tools import ToolProviderSpec
from services.api.composition import ApiDeps
from services.api.tool_provider_endpoints import resolve_endpoint_binding, unbound_reason


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
    return {
        provider_id: probe_provider_spec(deps, spec).status
        for provider_id, spec in catalog.tool_providers.items()
    }


NATIVE_PROBE_DETAIL = "NATIVE provider：内置 runtime 能力，无外部 transport 可探测（结构性可用）"


@dataclass(frozen=True, slots=True)
class ProviderProbe:
    """一次 provider 探测的完整结果（状态 + 说明 + 被探测方声明的 schema 指纹）。

    `observed_schema_digest` 是提供方**这次**声明的能力面指纹；适配器已算出
    （MCP/REST/NCBI 三处都填 `ToolHealthReport.observed_schema_digest`），
    本结构把它带出探测边界，供注册面记录与漂移比对。None 表示这次**没观测到**
    ——不等于"没有变化"（见 `ProviderRegistration.record_health` 的口径）。
    """

    status: EndpointHealth
    detail: str
    observed_schema_digest: str | None = None


def probe_provider_spec(deps: ApiDeps, spec: ToolProviderSpec) -> ProviderProbe:
    """provider 三态健康 + 探测说明 + schema 指纹（读面投影与注册面 health-check 共用）。

    单一路径的理由：注册面"健康复核"写下的必须是读面看到的那个事实，否则会
    出现"复核说健康、目录说不可证明"的两套真相。UNKNOWN 一律带原因（未注册
    实例 / 未声明 health_check / 探测异常 / **声明的端点环境变量未设置**），不伪装成功。

    端点门槛（PLAN-20260915-072）：provider 声明了 `endpoint_env` 就意味着它自己说
    "我的端点来自这个环境变量"——变量没设置时它不可用，因此**不探测**、直接 UNKNOWN
    并点名变量（名字不是秘密；值不进任何读面）。未声明该字段的 provider 行为不变。
    """
    if spec.kind is ProviderType.NATIVE:
        return ProviderProbe(EndpointHealth.HEALTHY, NATIVE_PROBE_DETAIL)
    unbound = unbound_reason(resolve_endpoint_binding(spec))
    if unbound is not None:
        return ProviderProbe(EndpointHealth.UNKNOWN, unbound)
    provider = deps.tool_providers.get(spec.id)
    if provider is None:
        return ProviderProbe(EndpointHealth.UNKNOWN, "控制面未注册可探测的 provider 实例")
    if not spec.health_check:
        return ProviderProbe(EndpointHealth.UNKNOWN, "provider 未声明 health_check，无探测入口")
    try:
        report = provider.check_health(spec)
    except Exception:  # noqa: BLE001 - 探测异常按不可证明收敛，不伪装结果
        return ProviderProbe(EndpointHealth.UNKNOWN, "健康探测抛出异常（已按不可证明收敛）")
    status = EndpointHealth(report.status)
    detail = str(getattr(report, "detail", "") or "")
    digest = getattr(report, "observed_schema_digest", None)
    return ProviderProbe(
        status=status,
        detail=detail or f"provider adapter 报告 {status.value}",
        observed_schema_digest=str(digest) if digest is not None else None,
    )
