"""Control Plane API 测试：Idempotency-Key / If-Match 并发语义。

浏览器按钮禁用不是 concurrency / security guarantee：即使 UI 双击、
网络重试，后端必须对重复提交、陈旧版本、冲突给出稳定语义。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.conftest import create_endpoint, make_endpoint_payload


def test_mutating_request_without_idempotency_key_is_rejected(client: TestClient) -> None:
    response = client.post("/llm-endpoints", json=make_endpoint_payload())
    assert response.status_code == 422
    assert response.json()["title"] == "Idempotency-Key Required"


def test_duplicate_submit_replays_first_response(client: TestClient) -> None:
    payload = make_endpoint_payload()
    first = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "dup-1"})
    second = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "dup-1"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    # 不产生第二条资源
    assert len(client.get("/llm-endpoints").json()) == 1


def test_same_key_with_different_payload_is_conflict(client: TestClient) -> None:
    payload = make_endpoint_payload()
    assert client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "conf-1"})
    changed = {**payload, "name": "different"}
    response = client.post("/llm-endpoints", json=changed, headers={"Idempotency-Key": "conf-1"})
    assert response.status_code == 422
    assert response.json()["title"] == "Idempotency-Key Reused"


def test_replay_preserves_etag(client: TestClient) -> None:
    payload = make_endpoint_payload()
    first = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "etag-1"})
    second = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "etag-1"})
    assert first.headers["etag"] == second.headers["etag"]


def test_stale_if_match_after_concurrent_update(client: TestClient) -> None:
    endpoint = create_endpoint(client)
    path = f"/llm-endpoints/{endpoint['id']}"
    # 第一次更新成功 → version 变化
    updated = client.patch(
        path,
        json={"name": "v2"},
        headers={"Idempotency-Key": "stale-1", "If-Match": endpoint["version"]},
    )
    assert updated.status_code == 200
    # 用旧 version 再更新 → 412（陈旧版本被后端拒绝，前端需刷新）
    stale = client.patch(
        path,
        json={"name": "v3"},
        headers={"Idempotency-Key": "stale-2", "If-Match": endpoint["version"]},
    )
    assert stale.status_code == 412
    # 用新 version 更新 → 200
    current = client.patch(
        path,
        json={"name": "v3"},
        headers={"Idempotency-Key": "stale-3", "If-Match": updated.json()["version"]},
    )
    assert current.status_code == 200
    assert current.json()["name"] == "v3"


def test_probe_is_analysis_and_repeatable(client: TestClient) -> None:
    """probe 是配置分析操作（不要求 Idempotency-Key），可安全重复执行。"""
    endpoint = create_endpoint(client)
    model = client.post(
        "/models",
        json={"endpoint_id": endpoint["id"], "model_name": "model-alpha"},
        headers={"Idempotency-Key": "probe-0"},
    ).json()
    probe_path = f"/models/{model['id']}/probe"
    first = client.post(probe_path)
    second = client.post(probe_path)
    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    # 除 probed_at 时间戳外，probe 结果确定性一致（Fake 语义）
    first_body["probed_at"] = None
    second_body["probed_at"] = None
    assert first_body == second_body


def test_error_responses_are_problem_detail(client: TestClient) -> None:
    response = client.get("/llm-endpoints/nope")
    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == 404
    assert body["instance"] == "/llm-endpoints/nope"


def test_invalid_domain_values_map_to_422(client: TestClient) -> None:
    payload = make_endpoint_payload()
    payload["base_url"] = "not-a-url"
    response = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "bad-1"})
    assert response.status_code == 422


def test_json_body_matches_stored_digest_across_field_order(client: TestClient) -> None:
    payload = make_endpoint_payload()
    first = client.post("/llm-endpoints", json=payload, headers={"Idempotency-Key": "order-1"})
    assert first.status_code == 201
    # 字段顺序不同 → body 字节不同 → 摘要不同 → 同 key 复用被拒绝（422）
    reordered = {k: payload[k] for k in reversed(list(payload))}
    replay = client.post("/llm-endpoints", json=reordered, headers={"Idempotency-Key": "order-1"})
    assert replay.status_code == 422
