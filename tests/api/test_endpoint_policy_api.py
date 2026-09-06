"""Control Plane API 测试：endpoint URL policy 配置化（M13 复审 FINDING-M13-1）。

证明：
- 默认（无 RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS）→ localhost 端点 probe 被
  policy 拒绝（configuration_failure，fail-closed 保持）；
- 显式开关（RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1）→ probe 可对
  localhost mock relay 执行（开发路径可工作），且测试用 FakeModelGateway
  不依赖真实网络。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.composition import assemble
from services.api.settings import ApiSettings

# Obviously synthetic fixture credential (computed, never a real secret).
_FIXTURE_ENDPOINT_KEY = "fixture-key-" + "0" * 16


def _client_with_policy(allow_localhost: bool, gateway: Any | None = None) -> TestClient:
    settings = ApiSettings(
        db_path=":memory:",
        allow_localhost_endpoints=allow_localhost,
    )
    deps = assemble(settings)
    if gateway is not None:
        deps.gateway = gateway
    app = create_app(deps)
    return TestClient(app)


def test_default_policy_denies_localhost_probe() -> None:
    """默认（fail-closed）：localhost endpoint 的 endpoint test → CONFIGURATION。"""
    from adapters.fakes.model_gateway import FakeModelGateway

    with _client_with_policy(False, gateway=FakeModelGateway()) as client:
        created = client.post(
            "/llm-endpoints",
            json={
                "name": "deny-local",
                "base_url": "http://127.0.0.1:8756/v1",
                "api_key": _FIXTURE_ENDPOINT_KEY,
                "api_style": "chat_completions",
            },
            headers={"Idempotency-Key": "policy-deny-1"},
        )
        assert created.status_code == 201, created.text
        endpoint_id = created.json()["id"]
        model = client.post(
            "/models",
            json={"endpoint_id": endpoint_id, "model_name": "mock-gpt-4o-mini", "enabled": True},
            headers={"Idempotency-Key": "policy-deny-2"},
        )
        assert model.status_code == 201, model.text
        probe = client.post(f"/models/{model.json()['id']}/probe")
        assert probe.status_code == 200, probe.text
        payload = probe.json()
        assert payload["ok"] is False
        assert payload["error_category"] == "CONFIGURATION"
        assert "localhost base_url not allowed by policy" in payload["error_message_redacted"]


def test_allow_localhost_env_enables_probe() -> None:
    """显式开关：localhost endpoint 的 probe 不再被 policy 拦截（Fake 网关）。"""
    from adapters.fakes.model_gateway import FakeModelGateway

    with _client_with_policy(True, gateway=FakeModelGateway()) as client:
        created = client.post(
            "/llm-endpoints",
            json={
                "name": "allow-local",
                "base_url": "http://127.0.0.1:8756/v1",
                "api_key": _FIXTURE_ENDPOINT_KEY,
                "api_style": "chat_completions",
            },
            headers={"Idempotency-Key": "policy-allow-1"},
        )
        assert created.status_code == 201, created.text
        endpoint_id = created.json()["id"]
        model = client.post(
            "/models",
            json={"endpoint_id": endpoint_id, "model_name": "mock-gpt-4o-mini", "enabled": True},
            headers={"Idempotency-Key": "policy-allow-2"},
        )
        assert model.status_code == 201, model.text
        probe = client.post(f"/models/{model.json()['id']}/probe")
        assert probe.status_code == 200, probe.text
        payload = probe.json()
        # FakeModelGateway 在默认装配下可达（mock 网关），policy 不再拦截
        assert payload["error_category"] is None or payload["error_category"] != "CONFIGURATION"
