"""Library 库目录 API 测试（PLAN-20260914-044 WP-B）。

三 kind 创建/列表（kind 过滤）/项目归属/未知 404/PATCH 重命名与归档/
空载荷 422/无 DELETE。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from services.api.composition import ApiDeps

_DEFAULT = "example-project"


def _idem() -> dict[str, str]:
    import uuid

    return {"Idempotency-Key": f"lib-{uuid.uuid4().hex}"}


def _deps(client: TestClient) -> ApiDeps:
    return cast(ApiDeps, cast(Any, client.app).state.deps)


def _create(client: TestClient, kind: str, name: str, **extra: Any) -> dict[str, Any]:
    response = client.post(
        f"/projects/{_DEFAULT}/library",
        json={"kind": kind, "name": name, **extra},
        headers=_idem(),
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_create_and_list_by_kind(client: TestClient) -> None:
    prompt = _create(client, "prompt", "Summarize prompt", tags=["research", "nlp"])
    _create(client, "dataset", "Benchmark set")
    _create(client, "notebook", "EDA notebook")

    all_items = client.get(f"/projects/{_DEFAULT}/library").json()
    assert len(all_items) == 3

    prompts = client.get(f"/projects/{_DEFAULT}/library", params={"kind": "prompt"}).json()
    assert len(prompts) == 1
    assert prompts[0]["id"] == prompt["id"]
    assert prompts[0]["kind"] == "prompt"
    assert prompts[0]["tags"] == ["research", "nlp"]
    assert prompts[0]["status"] == "ACTIVE"


def test_created_resource_is_project_scoped(client: TestClient) -> None:
    created = _create(client, "prompt", "Scoped")
    assert created["project_id"] == _DEFAULT
    # 幽灵项目不接收写入（不伪装归属）。
    ghost = client.post(
        "/projects/ghost-project/library",
        json={"kind": "prompt", "name": "x"},
        headers=_idem(),
    )
    assert ghost.status_code == 404


def test_get_unknown_is_404(client: TestClient) -> None:
    assert client.get("/library/does-not-exist").status_code == 404


def test_patch_rename_and_archive(client: TestClient) -> None:
    created = _create(client, "dataset", "Old name")
    renamed = client.patch(f"/library/{created['id']}", json={"name": "New name"}, headers=_idem())
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "New name"

    archived = client.patch(
        f"/library/{created['id']}", json={"status": "ARCHIVED"}, headers=_idem()
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"
    # 归档非删除：条目仍在列表中（过滤默认返回全部状态）。
    listed = client.get(f"/projects/{_DEFAULT}/library").json()
    assert any(item["id"] == created["id"] for item in listed)


def test_patch_empty_payload_is_422(client: TestClient) -> None:
    created = _create(client, "prompt", "x")
    assert client.patch(f"/library/{created['id']}", json={}, headers=_idem()).status_code == 422


def test_delete_is_not_provided(client: TestClient) -> None:
    created = _create(client, "prompt", "x")
    # DELETE 不在路由表内；带合法幂等键以越过中间件，暴露真实 405。
    assert client.delete(f"/library/{created['id']}", headers=_idem()).status_code == 405


def test_invalid_kind_rejected(client: TestClient) -> None:
    response = client.post(
        f"/projects/{_DEFAULT}/library",
        json={"kind": "spreadsheet", "name": "x"},
        headers=_idem(),
    )
    assert response.status_code == 422
