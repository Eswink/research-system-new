"""Control Plane API 测试：LLM Endpoint CRUD / test / discover / health。"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.conftest import (
    _FIXTURE_ENDPOINT_KEY,
    create_endpoint,
    make_app_deps,
    make_endpoint_payload,
)

# Computed fixture credential (never a real secret).
_ROTATED_ENDPOINT_KEY = "rotated-" + "9" * 12


def test_create_endpoint_returns_safe_dto(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    assert endpoint["id"]
    assert endpoint["name"] == "relay-a"
    assert endpoint["base_url"] == "https://relay.example.com/api/v1"
    assert endpoint["api_style"] == "chat_completions"
    assert endpoint["credential"] == "configured"
    assert endpoint["version"].startswith("sha256:")
    # secret 不回显：任何响应字段都不是明文 key
    raw = client.get(f"/llm-endpoints/{endpoint['id']}").text
    assert _FIXTURE_ENDPOINT_KEY not in raw


def test_create_endpoint_without_key_marks_missing(client: TestClient) -> None:
    payload = make_endpoint_payload()
    del payload["api_key"]
    response = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "k-2"})
    assert response.status_code == 201, response.text
    assert response.json()["credential"] == "missing"


def test_list_endpoints_returns_all(client: TestClient) -> None:
    create_endpoint(client, name="relay-a")
    create_endpoint(client, name="relay-b")
    response = client.get("/llm-endpoints")
    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert set(names) == {"relay-a", "relay-b"}


def test_get_missing_endpoint_is_404(client: TestClient) -> None:
    response = client.get("/llm-endpoints/does-not-exist")
    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


def test_patch_endpoint_requires_if_match(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    path = f"/llm-endpoints/{endpoint['id']}"
    # 缺失 If-Match → 428
    missing = client.patch(path, json={"name": "renamed"}, headers={"Idempotency-Key": "k-3"})
    assert missing.status_code == 428
    # stale If-Match → 412
    stale = client.patch(
        path,
        json={"name": "renamed"},
        headers={"Idempotency-Key": "k-4", "If-Match": "sha256:" + "0" * 64},
    )
    assert stale.status_code == 412
    # 正确版本 → 200
    ok = client.patch(
        path,
        json={"name": "renamed"},
        headers={"Idempotency-Key": "k-5", "If-Match": endpoint["version"]},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["name"] == "renamed"


def test_patch_can_update_api_key_without_echo(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    path = f"/llm-endpoints/{endpoint['id']}"
    response = client.patch(
        path,
        json={"api_key": _ROTATED_ENDPOINT_KEY},
        headers={"Idempotency-Key": "k-6", "If-Match": endpoint["version"]},
    )
    assert response.status_code == 200, response.text
    raw = client.get(path).text
    assert _ROTATED_ENDPOINT_KEY not in raw


def test_endpoint_test_flow(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    model = client.post(
        "/models",
        json={
            "endpoint_id": endpoint["id"],
            "model_name": "model-alpha",
            "display_name": "Alpha",
        },
        headers={"Idempotency-Key": "k-7"},
    )
    assert model.status_code == 201, model.text
    model_id = model.json()["id"]
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/test",
        json={"model_id": model_id},
        headers={"Idempotency-Key": "k-8"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ok"] is True
    assert result["returned_model_name"] == "model-alpha"
    assert result["system_fingerprint"] == "fp_1"


def test_endpoint_test_requires_model_on_endpoint(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    other = create_endpoint(client, name="relay-b")
    model = client.post(
        "/models",
        json={"endpoint_id": other["id"], "model_name": "model-beta"},
        headers={"Idempotency-Key": "k-9"},
    ).json()
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/test",
        json={"model_id": model["id"]},
        headers={"Idempotency-Key": "k-10"},
    )
    assert response.status_code == 422


def test_discover_models_returns_gateway_list(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/discover-models",
        headers={"Idempotency-Key": "k-11"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["model_ids"] == ["model-alpha", "model-beta"]


def test_discover_models_respects_allow_list(client: TestClient) -> None:
    payload = make_endpoint_payload()
    payload["discovery"] = {"enabled": True, "allow_models": ["model-beta"]}
    endpoint = client.post(
        "/llm-endpoints", json=payload, headers={"Idempotency-Key": "k-12"}
    ).json()
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/discover-models",
        headers={"Idempotency-Key": "k-13"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["model_ids"] == ["model-beta"]


def test_health_reflects_auth_failure() -> None:
    from adapters.fakes.model_gateway import FakeModelGateway, FakeModelGatewayOptions

    gateway = FakeModelGateway(FakeModelGatewayOptions(auth_fails=True))
    deps = make_app_deps(gateway=gateway)
    app = create_app(deps)
    with TestClient(app) as client:
        endpoint = create_endpoint(client)
        healthy = client.get(f"/llm-endpoints/{endpoint['id']}/health")
        assert healthy.status_code == 200
        assert healthy.json()["ok"] is False
        assert healthy.json()["error_category"] == "MODEL_AUTH"


def test_credential_does_not_survive_a_restart(tmp_path: Path) -> None:
    """EC-03：注册的密钥只活在**进程内**——「重启」后行还在，凭据回到 missing。

    这不是缺陷而是**如实声明的边界**（不落盘 ⇒ 重启需重新注入）。这里用
    「同一配置面文件 + 全新装配（新凭据解析器）」模拟重启：解析器实例即进程级状态，
    换一个实例就是换一个进程的效果——这正是 UI 文案与
    `docs/integration/LLM_ENDPOINTS.md` §9 对本行为的口径。
    """
    db_path = str(tmp_path / "config-face.db")
    with TestClient(create_app(make_app_deps(db_path=db_path))) as first:
        endpoint = create_endpoint(first, api_key=_FIXTURE_ENDPOINT_KEY)
        assert endpoint["credential"] == "configured"
        endpoint_id = str(endpoint["id"])
        base_url = str(endpoint["base_url"])

    with TestClient(create_app(make_app_deps(db_path=db_path))) as second:
        reread = second.get(f"/llm-endpoints/{endpoint_id}")
        assert reread.status_code == 200
        body = reread.json()
        # 配置面行仍在（落盘的是配置），但密钥不在（它从不落盘）。
        assert body["base_url"] == base_url
        assert body["credential"] == "missing"
        assert _FIXTURE_ENDPOINT_KEY not in reread.text


def test_endpoint_test_missing_credential_reports_ok_false(client: TestClient) -> None:
    payload = make_endpoint_payload()
    del payload["api_key"]
    endpoint = client.post(
        "/llm-endpoints", json=payload, headers={"Idempotency-Key": "k-14"}
    ).json()
    model = client.post(
        "/models",
        json={"endpoint_id": endpoint["id"], "model_name": "model-alpha"},
        headers={"Idempotency-Key": "k-15"},
    ).json()
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/test",
        json={"model_id": model["id"]},
        headers={"Idempotency-Key": "k-16"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ok"] is False
    assert result["error_category"] == "CONFIGURATION"
