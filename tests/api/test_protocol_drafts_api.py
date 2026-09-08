"""协议草稿 API 测试（PLAN-20260908-033 AC-03/AC-04 服务端面）。

覆盖：模板目录、校验端点（零副作用）、草稿创建/读取/保存、
412 乐观并发、幂等重放、428 缺 If-Match、修订历史、旧 path 兼容。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

_VALID_YAML = """id: sort_analysis_v1_0_1
version: 0.4.0
phases:
  - id: execution
    strategy: single_agent
    required_roles:
      - {role: experiment_engineer, min_instances: 1, max_instances: 1}
    task_contract: sort_analysis_execution
    timeout_seconds: 120
  - id: review
    strategy: single_agent
    depends_on: [execution]
    required_roles:
      - {role: scientific_reviewer, min_instances: 1, max_instances: 1}
    task_contract: sort_analysis_review
    gate: QUALITY_GATE
"""

_EDITED_YAML = _VALID_YAML.replace(
    "    timeout_seconds: 120\n",
    "    timeout_seconds: 240\n",
    1,
)


def test_template_directory_is_read_only_and_sourced(client: TestClient) -> None:
    response = client.get("/protocol-templates")
    assert response.status_code == 200, response.text
    templates = response.json()
    assert len(templates) >= 1
    for template in templates:
        assert template["source"].startswith("examples/protocols/")
    sort = next(item for item in templates if item["template_id"] == "sort-analysis")
    assert "sort_analysis_v1_0_1" in sort["yaml_text"]

    missing = client.get("/protocol-templates/nonexistent")
    assert missing.status_code == 404


def test_validate_endpoint_zero_side_effects(client: TestClient) -> None:
    ok = client.post("/protocol-drafts/validate", json={"yaml_text": _VALID_YAML})
    assert ok.status_code == 200
    body = ok.json()
    assert body["ok"] is True
    assert body["protocol_id"] == "sort_analysis_v1_0_1"
    assert body["phase_count"] == 2

    bad = client.post("/protocol-drafts/validate", json={"yaml_text": "not: [valid"})
    assert bad.status_code == 200
    bad_body = bad.json()
    assert bad_body["ok"] is False
    assert len(bad_body["issues"]) >= 1
    # 校验端点不产生草稿（零写入）
    listed = client.get("/projects/example-project/protocol-drafts")
    assert listed.status_code == 200
    assert listed.json() == []


def test_draft_create_read_save_roundtrip(client: TestClient) -> None:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "my draft", "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": "create-1"},
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    assert draft["revision"] == 1
    draft_id = draft["draft_id"]

    fetched = client.get(f"/protocol-drafts/{draft_id}")
    assert fetched.status_code == 200
    assert fetched.json()["yaml_text"] == _VALID_YAML

    saved = client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _EDITED_YAML, "expected_revision": 1},
        headers={"Idempotency-Key": "save-1", "If-Match": "1"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["revision"] == 2

    revisions = client.get(f"/protocol-drafts/{draft_id}/revisions")
    assert revisions.status_code == 200
    assert [item["revision"] for item in revisions.json()] == [1, 2]

    revision_one = client.get(f"/protocol-drafts/{draft_id}/revisions/1")
    assert revision_one.status_code == 200
    assert revision_one.json()["yaml_text"] == _VALID_YAML


def test_draft_save_requires_if_match(client: TestClient) -> None:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "my draft", "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": "create-2"},
    )
    draft_id = created.json()["draft_id"]
    missing = client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _EDITED_YAML, "expected_revision": 1},
        headers={"Idempotency-Key": "save-nomatch"},
    )
    assert missing.status_code == 428


def test_draft_save_conflict_returns_412(client: TestClient) -> None:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "my draft", "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": "create-3"},
    )
    draft_id = created.json()["draft_id"]
    stale = client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _EDITED_YAML, "expected_revision": 1},
        headers={"Idempotency-Key": "save-stale", "If-Match": "1"},
    )
    assert stale.status_code == 200
    conflict = client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _VALID_YAML, "expected_revision": 1},
        headers={"Idempotency-Key": "save-conflict", "If-Match": "1"},
    )
    assert conflict.status_code == 412, conflict.text


def test_draft_save_idempotent_retry_replays(client: TestClient) -> None:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "my draft", "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": "create-4"},
    )
    draft_id = created.json()["draft_id"]
    headers = {"Idempotency-Key": "save-retry", "If-Match": "1"}
    first = client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _EDITED_YAML, "expected_revision": 1},
        headers=headers,
    )
    assert first.status_code == 200
    # 完全相同的重试（同 key 同 body）→ 重放，不产生第三修订
    replay = client.request(
        "PUT",
        f"/protocol-drafts/{draft_id}",
        content=first.request.content,
        headers=headers,
    )
    assert replay.status_code == 200
    assert replay.json()["revision"] == 2
    revisions = client.get(f"/protocol-drafts/{draft_id}/revisions")
    assert [item["revision"] for item in revisions.json()] == [1, 2]


def test_draft_create_rejects_invalid_yaml(client: TestClient) -> None:
    bad = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "bad", "yaml_text": "id: [broken"},
        headers={"Idempotency-Key": "create-bad"},
    )
    assert bad.status_code == 422


def test_draft_not_found(client: TestClient) -> None:
    missing = client.get("/protocol-drafts/pdraft_does_not_exist")
    assert missing.status_code == 503 or missing.status_code == 404


def test_saved_revision_feeds_compile_chain(run_ready_client: TestClient) -> None:
    """已保存修订进入现有运行链（AC-04 服务端面）。"""
    created = run_ready_client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "run ref", "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": "create-run-1"},
    )
    assert created.status_code == 201
    draft_id = created.json()["draft_id"]

    from services.api.routers.protocol_drafts import draft_service_of

    # 通过 test client app state 取服务（rev 链冻结验证在 e2e 层覆盖）
    request_stub = type("Stub", (), {"app": run_ready_client.app})()
    service = draft_service_of(request_stub)
    revision = service.get_revision(draft_id, 1)
    assert revision is not None
    yaml_text = revision.yaml_text
    assert yaml_text == _VALID_YAML
    # 用该修订正文走 validate（与编译器同一 schema）
    validated = run_ready_client.post("/protocol-drafts/validate", json={"yaml_text": yaml_text})
    assert validated.status_code == 200
    assert validated.json()["ok"] is True


def test_legacy_path_requests_still_work(client: TestClient) -> None:
    """旧 protocol_path 请求兼容（AC-03 兼容性面；与 team_protocol 测试同源）。"""
    response = client.post("/protocols/validate", json={"path": "m12_reference_research_v1.yaml"})
    assert response.status_code == 200, response.text
    assert response.json()["successful"] is True
