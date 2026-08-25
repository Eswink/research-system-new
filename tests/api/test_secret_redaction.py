"""Control Plane API 测试：secret redaction 四面扫描。

规则（M13 DoD 13）：明文 Key 不得进入响应体、错误体、日志/记录摘要。
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from tests.api.conftest import create_endpoint, make_endpoint_payload

_SECRET = "sk-super-secret-abc123"
_PATTERN = re.compile(re.escape(_SECRET))


def test_created_response_never_contains_secret(client: TestClient) -> None:
    payload = make_endpoint_payload(api_key=_SECRET)
    response = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "s-1"})
    assert response.status_code == 201
    assert _PATTERN.search(response.text) is None


def test_list_get_patch_responses_never_contain_secret(client: TestClient) -> None:
    endpoint = create_endpoint(client, api_key=_SECRET)
    id_ = endpoint["id"]
    for method in ("GET", "PATCH"):
        response = client.request(
            method,
            f"/llm-endpoints/{id_}",
            headers={"If-Match": endpoint["version"], "Idempotency-Key": f"s-{method}"},
            json={"name": f"renamed-{method}"} if method == "PATCH" else None,
        )
        assert response.status_code in (200, 201)
        assert _PATTERN.search(response.text) is None
    assert _PATTERN.search(client.get("/llm-endpoints").text) is None


def test_error_responses_never_contain_secret(client: TestClient) -> None:
    endpoint = create_endpoint(client, api_key=_SECRET)
    id_ = endpoint["id"]
    # stale If-Match 错误响应不回显 secret
    stale = client.patch(
        f"/llm-endpoints/{id_}",
        json={"name": "x"},
        headers={"Idempotency-Key": "s-err", "If-Match": "sha256:" + "0" * 64},
    )
    assert stale.status_code == 412
    assert _PATTERN.search(stale.text) is None
    # 404 错误响应不回显 secret
    missing = client.get("/llm-endpoints/missing")
    assert missing.status_code == 404
    assert _PATTERN.search(missing.text) is None


def test_secret_value_repr_is_redacted(client: TestClient) -> None:
    from packages.application.ports.credential_resolver import SecretValue

    representation = repr(SecretValue(_SECRET))
    assert _SECRET not in representation


def test_error_message_redaction_never_contains_secret(client: TestClient) -> None:
    """probe/test 失败消息经 domain redaction，不回显 key 明文。"""
    payload = make_endpoint_payload()
    payload["base_url"] = "http://localhost:9999/v1"
    endpoint = client.post(
        "/llm-endpoints", json=payload, headers={"Idempotency-Key": "s-redact"}
    ).json()
    # base_url 非法（localhost 默认策略拒绝）→ configuration 失败，消息 redacted
    model = client.post(
        "/models",
        json={"endpoint_id": endpoint["id"], "model_name": "model-alpha"},
        headers={"Idempotency-Key": "s-redact-2"},
    ).json()
    response = client.post(
        f"/llm-endpoints/{endpoint['id']}/test",
        json={"model_id": model["id"]},
        headers={"Idempotency-Key": "s-redact-3"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is False
    assert "sk-" not in response.text
