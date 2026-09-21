"""Endpoint URL 策略。

默认拒绝 localhost / 环回 / 私有 / 链路本地 / **保留类**（多播、未指定、保留段、CGNAT 等
非全局单播）地址；可通过豁免集合放行。
domain 层只做纯判定，DNS 解析与连通性验证在 adapter 层。

「保留类」的判据是 `ipaddress` 谓词的合取（`is_multicast` / `is_unspecified` /
`is_reserved` / CGNAT / `not is_global`）——**判据只有这一处**，调用方一律经
`validate_endpoint_url` / `endpoint_url_refusal` 取值（GOAL-008 EC-03）。
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urlparse

_IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
#: RFC 6598 共享地址空间（运营商级 NAT）：既非 `is_private` 也非 `is_reserved`，
#: 但在本仓语义下与私有地址同属「不可作为端点」的一类。
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")


@dataclass(frozen=True, slots=True)
class EndpointUrlPolicy:
    """URL 策略配置。"""

    allow_localhost: bool = False
    allow_private: bool = False
    allow_link_local: bool = False
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)


def _is_reserved(address: _IPAddress) -> bool:
    """保留类判定：多播 / 未指定 / 保留段 / CGNAT / 非全局单播。"""
    if address.is_multicast or address.is_unspecified or address.is_reserved:
        return True
    if isinstance(address, ipaddress.IPv4Address) and address in _SHARED_ADDRESS_SPACE:
        return True
    return not address.is_global


def _host_kind(host: str) -> str:
    """主机分类：localhost / link_local / private / reserved / public / domain。

    环回（含 `127.0.0.0/8` 全段与 `::1`）统一归 `localhost`——此前只有 `127.0.0.1`
    被当字面量识别，其余环回地址落到 `private` 分支；两者默认都被拒，但**豁免开关不同**，
    归并后 `allow_localhost` 是唯一的环回开关。

    `is_link_local` 必须排在 `is_private` **之前**：`ipaddress` 把 `169.254.0.0/16`
    与 `fe80::/10` 也算私有，先判私有会让 `link_local` 分支不可达——拒绝理由指错类别，
    且 `allow_link_local` 变成永不生效的空开关（EC-03 实跑发现）。
    """
    lowered = host.lower()
    if lowered == "localhost":
        return "localhost"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "domain"
    if address.is_loopback:
        return "localhost"
    if address.is_link_local:
        return "link_local"
    if address.is_private:
        return "private"
    if _is_reserved(address):
        return "reserved"
    return "public"


def destination_kind(host: str) -> str:
    """`_host_kind` 的公开面：localhost / link_local / private / reserved / public / domain。

    存在的理由只有一个（GOAL-010 EC-05）：判定「默认门离线」的守卫在 **socket 层**裁决，
    手里是**已解析的目的地**，而既有公开面（`validate_endpoint_url` / `endpoint_url_refusal`）
    只吃 **URL**。把判据**暴露**出来而不是另写一套分类，保证全仓仍然**只有一份** host 判据；
    本函数**不新增**任何判定语义，实现就是转发 `_host_kind`。
    """
    return _host_kind(host)


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
        # 措辞保持既有文本（既有判据按子串断言它）；语义已扩到环回全段，见 `_host_kind`。
        raise ValueError(f"localhost base_url not allowed by policy: {base_url!r}")
    if kind == "private" and not policy.allow_private:
        raise ValueError(f"private IP base_url not allowed by policy: {base_url!r}")
    if kind == "link_local" and not policy.allow_link_local:
        raise ValueError(f"link-local base_url not allowed by policy: {base_url!r}")
    if kind == "reserved":
        raise ValueError(
            f"reserved/multicast base_url not allowed by policy: {base_url!r} "
            "(no policy flag enables this class; use allowed_hosts to exempt a specific host)"
        )


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
