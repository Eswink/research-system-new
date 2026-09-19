"""Endpoint URL 策略。

默认拒绝 localhost / 私有 / 链路本地地址；可通过豁免集合放行。
domain 层只做纯判定，DNS 解析与连通性验证在 adapter 层。
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class EndpointUrlPolicy:
    """URL 策略配置。"""

    allow_localhost: bool = False
    allow_private: bool = False
    allow_link_local: bool = False
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)


def _host_kind(host: str) -> str:
    """主机分类：localhost / private / link_local / public / domain。"""
    lowered = host.lower()
    if lowered in ("localhost", "127.0.0.1", "::1"):
        return "localhost"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "domain"
    if address.is_private:
        return "private"
    if address.is_link_local:
        return "link_local"
    return "public"


def validate_endpoint_url(base_url: str, policy: EndpointUrlPolicy) -> None:
    """校验 base_url 是否符合策略；违规抛出 ValueError。"""
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"base_url scheme must be http(s): {base_url!r}")
    host = parsed.hostname
    if not host:
        raise ValueError(f"base_url must include a host: {base_url!r}")

    lowered_host = host.lower()
    if lowered_host in {h.lower() for h in policy.allowed_hosts}:
        return

    kind = _host_kind(host)
    if kind == "localhost" and not policy.allow_localhost:
        raise ValueError(f"localhost base_url not allowed by policy: {base_url!r}")
    if kind == "private" and not policy.allow_private:
        raise ValueError(f"private IP base_url not allowed by policy: {base_url!r}")
    if kind == "link_local" and not policy.allow_link_local:
        raise ValueError(f"link-local base_url not allowed by policy: {base_url!r}")


def endpoint_url_refusal(base_url: str, policy: EndpointUrlPolicy) -> str | None:
    """`validate_endpoint_url` 的薄包装：返回拒绝理由，放行时返回 None。

    存在的理由只有一个：门链需要在**两个**位置问同一个问题——`_probe_endpoint`
    要在触网**之前**短路，preflight 要把拒绝**点名**进 findings。用异常返回值而非
    重新判断主机类型，保证全仓只有一份 host 判据（GOAL-007 EC-02）。
    """
    try:
        validate_endpoint_url(base_url, policy)
    except ValueError as exc:
        return str(exc)
    return None
