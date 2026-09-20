"""Control Plane API 测试：Model CRUD / probe / compatibility。"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.model_gateway import FakeModelGateway, FakeModelGatewayOptions
from services.api.app import create_app
from tests.api.conftest import create_endpoint, make_app_deps


def create_model(client: TestClient, endpoint_id: str, name: str = "model-alpha") -> dict[str, Any]:
    response = client.post(
        "/models",
        json={
            "endpoint_id": endpoint_id,
            "model_name": name,
            "display_name": name.title(),
        },
        headers={"Idempotency-Key": f"model-{name}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_create_model_requires_existing_endpoint(client: TestClient) -> None:
    response = client.post(
        "/models",
        json={"endpoint_id": "missing", "model_name": "m1"},
        headers={"Idempotency-Key": "k-m1"},
    )
    assert response.status_code == 404


def test_model_crud_and_if_match(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    model = create_model(client, str(endpoint["id"]))
    assert model["capabilities"] == {}
    assert model["version"].startswith("sha256:")
    # PATCH 缺失 If-Match → 428
    response = client.patch(
        f"/models/{model['id']}",
        json={"display_name": "Renamed"},
        headers={"Idempotency-Key": "k-m2"},
    )
    assert response.status_code == 428
    # stale → 412
    response = client.patch(
        f"/models/{model['id']}",
        json={"display_name": "Renamed"},
        headers={"Idempotency-Key": "k-m3", "If-Match": "sha256:" + "0" * 64},
    )
    assert response.status_code == 412
    # correct version → 200
    response = client.patch(
        f"/models/{model['id']}",
        json={"display_name": "Renamed"},
        headers={"Idempotency-Key": "k-m4", "If-Match": model["version"]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Renamed"


def test_model_capability_declaration(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    response = client.post(
        "/models",
        json={
            "endpoint_id": endpoint["id"],
            "model_name": "model-beta",
            "capabilities": {
                "CHAT": {"status": "SUPPORTED", "confidence": 1.0, "source": "USER_DECLARED"}
            },
        },
        headers={"Idempotency-Key": "k-m5"},
    )
    assert response.status_code == 201, response.text
    capabilities = response.json()["capabilities"]
    assert capabilities["CHAT"]["source"] == "USER_DECLARED"


def test_probe_merges_probed_assertions(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    model = create_model(client, str(endpoint["id"]))
    response = client.post(f"/models/{model['id']}/probe", headers={"Idempotency-Key": "k-m6"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ok"] is True
    assert result["observed_capabilities"]
    assert result["provider_fingerprint_available"] is True
    assert result["system_fingerprint"] == "fp_1"
    assert result["fingerprint"] is not None
    assert result["fingerprint"]["endpoint_config_digest"].startswith("sha256:")
    # PROBED 断言已持久化到 backend truth
    stored = client.get(f"/models/{model['id']}").json()
    sources = {item["source"] for item in stored["capabilities"].values()}
    assert "PROBED" in sources


def _probe_with_gateway(options: FakeModelGatewayOptions, declared: str) -> dict[str, Any]:
    """用指定替身形态跑一次 probe，返回结果 DTO（EC-05 漂移判据的三种夹具入口）。"""
    deps = make_app_deps(gateway=FakeModelGateway(options))
    with TestClient(create_app(deps)) as client:
        endpoint = create_endpoint(client)
        model = create_model(client, str(endpoint["id"]), name=declared)
        response = client.post(
            f"/models/{model['id']}/probe", headers={"Idempotency-Key": "k-drift"}
        )
        assert response.status_code == 200, response.text
        return cast(dict[str, Any], response.json())


def test_probe_reports_match_when_returned_name_agrees() -> None:
    result = _probe_with_gateway(
        FakeModelGatewayOptions(returned_model_name="model-alpha"), "model-alpha"
    )
    assert result["drift"]["state"] == "MATCH"
    assert result["drift"]["declared_model_name"] == "model-alpha"
    assert result["drift"]["returned_model_name"] == "model-alpha"


def test_probe_reports_drift_and_names_both_values() -> None:
    """中转站在同一 Model ID 后换了模型 ⇒ 读面必须点名两个值，而不是只说「有漂移」。"""
    result = _probe_with_gateway(
        FakeModelGatewayOptions(returned_model_name="model-beta"), "model-alpha"
    )
    drift = result["drift"]
    assert drift["state"] == "DRIFT"
    assert drift["declared_model_name"] == "model-alpha"
    assert drift["returned_model_name"] == "model-beta"
    assert "model-alpha" in drift["detail"]
    assert "model-beta" in drift["detail"]


def test_probe_failure_reports_unknown_not_match() -> None:
    """**未知 ≠ 一致**：探测失败时不得把「未探到」渲染成 MATCH（AGENTS.md §4）。"""
    result = _probe_with_gateway(FakeModelGatewayOptions(auth_fails=True), "model-alpha")
    assert result["ok"] is False
    assert result["drift"]["state"] == "UNKNOWN"
    assert result["drift"]["state"] != "MATCH"
    assert result["drift"]["returned_model_name"] is None


def test_probe_without_credential_reports_not_verified(client: TestClient) -> None:
    payload = {
        "name": "no-key-relay",
        "base_url": "https://relay.example.com/api/v1",
    }
    endpoint = client.post(
        "/llm-endpoints", json=payload, headers={"Idempotency-Key": "k-m7"}
    ).json()
    model = create_model(client, str(endpoint["id"]))
    response = client.post(f"/models/{model['id']}/probe", headers={"Idempotency-Key": "k-m8"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ok"] is False
    assert result["error_category"] == "CONFIGURATION"
    assert result["provider_fingerprint_available"] is False
    assert result["system_fingerprint"] is None


def test_compatibility_view(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    model = create_model(client, str(endpoint["id"]))
    response = client.get(f"/models/{model['id']}/compatibility")
    assert response.status_code == 200, response.text
    view = response.json()
    assert view["endpoint_id"] == endpoint["id"]
    assert view["model"]["model_name"] == "model-alpha"


def test_list_models_filters_by_endpoint(client: TestClient) -> None:
    endpoint_a = create_endpoint(client, name="relay-a")
    endpoint_b = create_endpoint(client, name="relay-b")
    create_model(client, str(endpoint_a["id"]), name="model-a")
    create_model(client, str(endpoint_b["id"]), name="model-b")
    filtered = client.get("/models", params={"endpoint_id": endpoint_a["id"]}).json()
    assert [item["model_name"] for item in filtered] == ["model-a"]
    all_models = client.get("/models").json()
    assert len(all_models) == 2


def _create_model_with_parameters(client: TestClient, endpoint_id: str, key: str) -> dict[str, Any]:
    response = client.post(
        "/models",
        json={
            "endpoint_id": endpoint_id,
            "model_name": "model-declared",
            "context_window_tokens": 512000,
            "thinking_intensity": "MAX",
        },
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_declared_parameters_survive_create_read(client: TestClient) -> None:
    """POST 声明两值 ⇒ 创建响应与 GET 读面都读回（不静默丢失）。"""
    endpoint = create_endpoint(client)
    created = _create_model_with_parameters(client, str(endpoint["id"]), "k-param-1")
    assert created["context_window_tokens"] == 512000
    assert created["thinking_intensity"] == "MAX"
    fetched = client.get(f"/models/{created['id']}").json()
    assert fetched["context_window_tokens"] == 512000
    assert fetched["thinking_intensity"] == "MAX"


def test_declared_parameters_absent_read_back_as_null(client: TestClient) -> None:
    """未声明 ≠ 声明某值：缺省读回 null（不推断默认）。"""
    endpoint = create_endpoint(client)
    model = create_model(client, str(endpoint["id"]), name="model-undeclared")
    assert model["context_window_tokens"] is None
    assert model["thinking_intensity"] is None


def test_patch_declared_parameters_changes_etag(client: TestClient) -> None:
    """PATCH 改声明参数 ⇒ 读回新值，且 ETag 必须变（否则 If-Match 保护失效）。"""
    endpoint = create_endpoint(client)
    model = _create_model_with_parameters(client, str(endpoint["id"]), "k-param-2")
    response = client.patch(
        f"/models/{model['id']}",
        json={"context_window_tokens": 200000, "thinking_intensity": "LOW"},
        headers={"Idempotency-Key": "k-param-3", "If-Match": model["version"]},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["context_window_tokens"] == 200000
    assert updated["thinking_intensity"] == "LOW"
    assert updated["version"] != model["version"]
    fetched = client.get(f"/models/{model['id']}").json()
    assert fetched["context_window_tokens"] == 200000
    assert fetched["thinking_intensity"] == "LOW"


def test_probe_preserves_declared_parameters(client: TestClient) -> None:
    """probe 重建 ModelDefinition 时必须带全声明参数（配置操作不得丢字段）。"""
    endpoint = create_endpoint(client)
    model = _create_model_with_parameters(client, str(endpoint["id"]), "k-param-4")
    probed = client.post(f"/models/{model['id']}/probe", headers={"Idempotency-Key": "k-param-5"})
    assert probed.json()["ok"] is True
    fetched = client.get(f"/models/{model['id']}").json()
    assert fetched["context_window_tokens"] == 512000
    assert fetched["thinking_intensity"] == "MAX"


def test_declared_parameter_validation(client: TestClient) -> None:
    """非法取值在 API 边界被拒（≥1 / 词表内），不落库为坏声明。"""
    endpoint = create_endpoint(client)
    zero_window = client.post(
        "/models",
        json={
            "endpoint_id": endpoint["id"],
            "model_name": "m-zero",
            "context_window_tokens": 0,
        },
        headers={"Idempotency-Key": "k-param-6"},
    )
    assert zero_window.status_code == 422
    bad_intensity = client.post(
        "/models",
        json={
            "endpoint_id": endpoint["id"],
            "model_name": "m-bad",
            "thinking_intensity": "TURBO",
        },
        headers={"Idempotency-Key": "k-param-7"},
    )
    assert bad_intensity.status_code == 422
