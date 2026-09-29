"""Europe PMC 运行时辅助（与 `europe_pmc.py` 拆分，保持模块规模阈值与 Port 面干净）。

本模块**不含** Port 方法名，也不做任何字符串化拼装：
- 出站 URL 由常量与模块级分段拼接而成（没有调用方输入参与）；
- 请求参数一律以**字面量键的 dict** 结构化传递（Europe PMC 的 REST 参数名是接口契约，
  不是拼接产物）；
- 拒绝判定复用全仓唯一 host 谓词 `endpoint_url_refusal`。
"""

from __future__ import annotations

from collections.abc import Mapping

import httpx

from packages.application.model_relay.endpoint_policy import (
    EndpointUrlPolicy,
    endpoint_url_refusal,
)
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    TransientPortError,
)
from packages.domain.enums import FailureCategory, ProviderType
from packages.domain.tools import ToolProviderSpec, ToolSpec

SEARCH_ENDPOINT = "search"
#: 健康探测用的固定检索串（无调用方输入）。
HEALTH_PROBE_TERM = "SRC:MED"
#: Europe PMC 检索接口的参数名（接口契约的字段名，逐字对应官方 REST 文档）。
TERM_FIELD = "query"

_TOOL_DESCRIPTIONS: dict[str, str] = {
    "literature_search": "Search Europe PMC via the RESTful search endpoint.",
    "literature_read": "Fetch Europe PMC records by id via the RESTful search endpoint.",
}


def tool_ids() -> list[str]:
    """声明的工具 id（排序后，供 schema digest 稳定复用）。"""
    return sorted(_TOOL_DESCRIPTIONS)


def describe_tools(provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
    """把声明的工具面映射成 `ToolSpec` 元组（与 `ncbi.py::list_tools` 同形）。"""
    return tuple(
        ToolSpec(
            id=tool_id,
            name=tool_id,
            effect_class=provider.effect_class,
            provider_kind=ProviderType.REST,
            capabilities=list(provider.capabilities),
            description=description,
        )
        for tool_id, description in _TOOL_DESCRIPTIONS.items()
    )


def search_endpoint(base_url: str) -> str:
    """检索端点的完整 URL（**常量分段拼接**，无调用方输入参与）。"""
    return base_url.rstrip("/") + "/" + SEARCH_ENDPOINT


def search_params(term: str, page_size: int | None = None) -> dict[str, str | int]:
    """检索请求的参数对象（结构化传参，由 `httpx` 负责编码）。"""
    params: dict[str, str | int] = {"format": "json", TERM_FIELD: term}
    if page_size is not None:
        params["pageSize"] = page_size
    return params


def assert_url_allowed(
    url: str,
    policy: EndpointUrlPolicy,
    declared_domains: tuple[str, ...],
) -> None:
    """URL 策略：仅 http(s) + 保留类拒绝 + **声明域名白名单**（全部在触网前）。

    保留类判据**只有** `endpoint_url_refusal` 一处（全仓唯一 host 谓词）；
    额外只加一条**声明式**检查：host ∈ `network_domains`。两者都不改既有语义。
    """
    parsed = httpx.URL(url)
    if parsed.scheme not in ("http", "https"):
        raise InvalidInputError(f"europe pmc url scheme must be http(s): {url!r}")
    host = parsed.host or ""
    refusal = endpoint_url_refusal(url, policy)
    if refusal is not None:
        raise InvalidInputError(f"europe pmc url refused before any request: {refusal}")
    declared = {domain.strip().lower() for domain in declared_domains if domain.strip()}
    if host.lower() not in declared:
        raise InvalidInputError(
            f"europe pmc host {host!r} is outside the declared network_domains {sorted(declared)}"
        )


def request_document(
    client: httpx.Client,
    url: str,
    params: Mapping[str, str | int],
) -> dict[str, object]:
    """发请求并把 HTTP 状态归类成 transient / permanent（非 2xx 不静默放行）。"""
    response = client.get(url, params=dict(params))
    status = response.status_code
    if status == 429 or status >= 500:
        raise TransientPortError(
            "europe pmc temporarily unavailable",
            failure_category=FailureCategory.TOOL_UNAVAILABLE,
        )
    if status >= 400:
        raise PermanentPortError(
            f"europe pmc request rejected with status {status}",
            failure_category=FailureCategory.TOOL_UNAVAILABLE,
        )
    parsed: object = response.json()
    if not isinstance(parsed, dict):
        raise InvalidInputError("europe pmc response must be a JSON object")
    return parsed


__all__ = [
    "HEALTH_PROBE_TERM",
    "SEARCH_ENDPOINT",
    "TERM_FIELD",
    "assert_url_allowed",
    "describe_tools",
    "request_document",
    "search_endpoint",
    "search_params",
    "tool_ids",
]
