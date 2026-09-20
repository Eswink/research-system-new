"""Endpoint URL 策略测试。"""

from __future__ import annotations

import pytest

from packages.application.model_relay.endpoint_policy import (
    EndpointUrlPolicy,
    validate_endpoint_url,
)


class TestEndpointUrlPolicy:
    def test_public_https_allowed(self) -> None:
        validate_endpoint_url("https://relay.example.com/v1", EndpointUrlPolicy())

    def test_public_http_allowed(self) -> None:
        validate_endpoint_url("http://relay.example.com/v1", EndpointUrlPolicy())

    def test_ftp_rejected(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("ftp://relay.example.com/v1", EndpointUrlPolicy())

    def test_no_host_rejected(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("https:///v1", EndpointUrlPolicy())

    def test_localhost_rejected_by_default(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("http://localhost:8080/v1", EndpointUrlPolicy())

    def test_localhost_allowed_when_permitted(self) -> None:
        validate_endpoint_url("http://localhost:8080/v1", EndpointUrlPolicy(allow_localhost=True))

    def test_private_ip_rejected_by_default(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("http://192.168.1.10/v1", EndpointUrlPolicy())

    def test_private_ip_allowed_when_permitted(self) -> None:
        validate_endpoint_url("http://192.168.1.10/v1", EndpointUrlPolicy(allow_private=True))

    def test_link_local_ip_rejected(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("http://169.254.169.254/v1", EndpointUrlPolicy())

    def test_allowed_host_override(self) -> None:
        validate_endpoint_url(
            "http://192.168.1.10/v1",
            EndpointUrlPolicy(allowed_hosts=frozenset({"192.168.1.10"})),
        )

    def test_domain_not_resolved_here(self) -> None:
        validate_endpoint_url("http://internal.corp.example/v1", EndpointUrlPolicy())


class TestReservedAndLoopbackClasses:
    """GOAL-008 EC-03：保留类地址必须拒绝，且**环回全段**归 localhost 开关。

    改动前 `_host_kind` 把多播（`224.0.0.1`）与 CGNAT（`100.64.0.1`）判成 `public`
    ⇒ 默认**放行**；`127.0.0.2` 落到 `private` 分支（开关是 `allow_private` 而不是
    `allow_localhost`）。本类逐条钉住新语义。
    """

    @pytest.mark.parametrize(
        "url",
        [
            "http://224.0.0.1/v1",  # IPv4 多播
            "http://[ff02::1]/v1",  # IPv6 多播（链路本地全节点）
            "http://100.64.0.1/v1",  # RFC 6598 共享地址空间（CGNAT）
            "http://198.18.0.5/v1",  # benchmark 段（本机 DNS 走代理时会落到这类地址）
            "http://203.0.113.9/v1",  # TEST-NET-3
            "http://198.51.100.7/v1",  # TEST-NET-2
            "http://240.0.0.1/v1",  # 保留段
            "http://0.0.0.0/v1",  # 未指定
        ],
    )
    def test_reserved_style_hosts_rejected(self, url: str) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url(url, EndpointUrlPolicy())

    @pytest.mark.parametrize("url", ["http://127.0.0.2/v1", "http://[::1]:8080/v1"])
    def test_loopback_span_rejected(self, url: str) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url(url, EndpointUrlPolicy())

    def test_loopback_span_uses_the_localhost_switch(self) -> None:
        validate_endpoint_url("http://127.0.0.2:8080/v1", EndpointUrlPolicy(allow_localhost=True))

    def test_reserved_refusal_names_the_class(self) -> None:
        with pytest.raises(ValueError, match="reserved/multicast"):
            validate_endpoint_url("http://224.0.0.1/v1", EndpointUrlPolicy())

    def test_loopback_refusal_names_the_class(self) -> None:
        with pytest.raises(ValueError, match="localhost base_url not allowed"):
            validate_endpoint_url("http://127.0.0.2/v1", EndpointUrlPolicy())

    def test_no_policy_flag_enables_the_reserved_class(self) -> None:
        """保留类**没有**放行开关：三个 allow_* 全开也不放行（豁免只走 allowed_hosts）。"""
        policy = EndpointUrlPolicy(allow_localhost=True, allow_private=True, allow_link_local=True)
        with pytest.raises(ValueError):
            validate_endpoint_url("http://224.0.0.1/v1", policy)

    def test_allowed_hosts_can_exempt_a_reserved_host(self) -> None:
        validate_endpoint_url(
            "http://224.0.0.1/v1",
            EndpointUrlPolicy(allowed_hosts=frozenset({"224.0.0.1"})),
        )

    def test_public_ipv6_allowed(self) -> None:
        validate_endpoint_url("https://[2606:4700::1111]/v1", EndpointUrlPolicy())

    def test_private_ipv6_rejected(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("https://[fc00::1]/v1", EndpointUrlPolicy())

    def test_ipv4_mapped_private_rejected(self) -> None:
        with pytest.raises(ValueError):
            validate_endpoint_url("https://[::ffff:192.168.1.1]/v1", EndpointUrlPolicy())

    @pytest.mark.parametrize("url", ["http://169.254.169.254/v1", "http://[fe80::1]/v1"])
    def test_link_local_owns_its_switch(self, url: str) -> None:
        """`allow_link_local` 必须真的管用：链路本地归 `link_local` 而不是 `private`。

        改动前 `is_private` 先命中（`ipaddress` 把 `169.254.0.0/16` 与 `fe80::/10`
        也算私有）⇒ `link_local` 分支不可达 ⇒ 拒绝理由指错类别，且开关是**空开关**
        （EC-03 实跑发现）。两类的开关彼此独立，谁都不许顺带放行对方。
        """
        with pytest.raises(ValueError, match="link-local base_url not allowed"):
            validate_endpoint_url(url, EndpointUrlPolicy())
        validate_endpoint_url(url, EndpointUrlPolicy(allow_link_local=True))
        with pytest.raises(ValueError):
            validate_endpoint_url(url, EndpointUrlPolicy(allow_private=True))
