"""Control Plane API 测试：Model CRUD / probe / compatibility。"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from tests.api.conftest import create_endpoint


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
