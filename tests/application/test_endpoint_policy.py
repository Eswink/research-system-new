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
