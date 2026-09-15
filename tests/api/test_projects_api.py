"""Project 注册表 API 与项目归属测试（PLAN-041 WP-A/WP-B）。

注册表：默认条目/创建（自动默认设置行）/重命名/归档/冲突与幂等键。
归属（EC-01 可证伪性）：settings 按项目精确（幽灵 404）、草稿跨项目不可见、
runs 列表按项目过滤、幽灵项目启动 404。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID, Timestamp
from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps

_DRAFT_YAML = Path("examples/protocols/sort_analysis_v1.yaml").read_text(encoding="utf-8")


def _idem() -> dict[str, str]:
    import uuid

    return {"Idempotency-Key": f"proj-{uuid.uuid4().hex}"}


def _deps(client: TestClient) -> ApiDeps:
    return cast(ApiDeps, cast(Any, client.app).state.deps)


def _create_project(client: TestClient, name: str) -> dict[str, Any]:
    response = client.post("/projects", json={"name": name}, headers=_idem())
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_default_project_registry(client: TestClient) -> None:
    listed = client.get("/projects")
    assert listed.status_code == 200
    items = listed.json()
    assert items[0]["id"] == "example-project"
    assert items[0]["name"] == "Example ML Research"
    assert items[0]["status"] == "ACTIVE"


def test_create_project_gets_default_settings(client: TestClient) -> None:
    created = _create_project(client, "  Cycle One Study  ")
    assert created["name"] == "Cycle One Study"
    ids = [item["id"] for item in client.get("/projects").json()]
    assert created["id"] in ids

    settings = client.get(f"/projects/{created['id']}/settings")
    assert settings.status_code == 200
    payload = settings.json()
    assert payload["project_id"] == created["id"]
    assert payload["team_template_id"] == "standard"
    assert payload["budget_policy_id"] == "low_cost"


def test_rename_and_archive(client: TestClient) -> None:
    created = _create_project(client, "temp name")
    pid = created["id"]

    renamed = client.patch(f"/projects/{pid}", json={"name": "final name"}, headers=_idem())
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "final name"
    assert renamed.json()["status"] == "ACTIVE"

    archived = client.patch(f"/projects/{pid}", json={"status": "ARCHIVED"}, headers=_idem())
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"

    missing = client.patch("/projects/no-such-project", json={"name": "x"}, headers=_idem())
    assert missing.status_code == 404
    assert client.patch(f"/projects/{pid}", json={}, headers=_idem()).status_code == 422
    assert client.post("/projects", json={"name": "no key"}).status_code == 422


def test_ghost_project_endpoints_are_404(client: TestClient) -> None:
    assert client.get("/projects/ghost/settings").status_code == 404
    assert (
        client.put(
            "/projects/ghost/settings",
            json={
                "team_template_id": "standard",
                "budget_policy_id": "low_cost",
                "workspace_backend": "openhands_docker",
            },
            headers=_idem(),
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/projects/ghost/protocol-drafts",
            json={"name": "d", "yaml_text": _DRAFT_YAML},
            headers=_idem(),
        ).status_code
        == 404
    )
    started = client.post(
        "/projects/ghost/runs",
        json={"protocol_path": "sort_analysis_v1.yaml"},
        headers=_idem(),
    )
    assert started.status_code == 404


def test_drafts_are_scoped_per_project(client: TestClient) -> None:
    project_a = _create_project(client, "draft host A")["id"]
    project_b = _create_project(client, "draft host B")["id"]

    created = client.post(
        f"/projects/{project_a}/protocol-drafts",
        json={"name": "a-draft", "yaml_text": _DRAFT_YAML},
        headers=_idem(),
    )
    assert created.status_code == 201, created.text
    assert created.json()["project_id"] == project_a

    listed_a = client.get(f"/projects/{project_a}/protocol-drafts").json()
    listed_b = client.get(f"/projects/{project_b}/protocol-drafts").json()
    assert [item["draft_id"] for item in listed_a] == [created.json()["draft_id"]]
    assert listed_b == []


def test_runs_list_filters_by_project(client: TestClient) -> None:
    """注册表回退路径（runs_store None）同样按项目过滤（不跨项目泄漏）。"""
    project_a = _create_project(client, "run host A")["id"]
    deps = _deps(client)
    now = Timestamp.now()
    run_a = ID.generate().value
    run_b = ID.generate().value
    for run_id, project_id in ((run_a, project_a), (run_b, "example-project")):
        deps.run_registry[run_id] = ResearchRun(
            id=ID(run_id), project_id=project_id, protocol_id="p", created_at=now, updated_at=now
        )
    listed_a = client.get(f"/projects/{project_a}/runs").json()
    listed_default = client.get("/projects/example-project/runs").json()
    assert [item["id"] for item in listed_a] == [run_a]
    assert [item["id"] for item in listed_default] == [run_b]


# --------------------------------------------------- 删除语义（PLAN-20260915-061）


def test_delete_unreferenced_project_removes_row_and_settings(client: TestClient) -> None:
    """空项目删除即 204：注册行与随项目创建的设置行一起消失，再次删除 404。"""
    project_id = _create_project(client, "delete me")["id"]
    assert client.get(f"/projects/{project_id}/settings").status_code == 200

    deleted = client.delete(f"/projects/{project_id}", headers=_idem())
    assert deleted.status_code == 204, deleted.text
    assert project_id not in [item["id"] for item in client.get("/projects").json()]
    # 设置行不是孤儿：随项目一并清理（项目不存在 ⇒ 设置面诚实 404）。
    assert client.get(f"/projects/{project_id}/settings").status_code == 404
    assert client.delete(f"/projects/{project_id}", headers=_idem()).status_code == 404


def test_delete_refuses_default_project(client: TestClient) -> None:
    """example-project 由 examples 契约合成：删了也还在，因此明确拒绝（不是静默 no-op）。"""
    response = client.delete("/projects/example-project", headers=_idem())
    assert response.status_code == 409, response.text
    assert "examples contract" in response.json()["detail"]


def test_delete_refuses_project_with_runs(client: TestClient) -> None:
    """有 run 的项目 → 409 且逐项计数；run 仍在（不静默级联）。"""
    project_id = _create_project(client, "has runs")["id"]
    deps = _deps(client)
    run_id = ID.generate().value
    now = Timestamp.now()
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id), project_id=project_id, protocol_id="p", created_at=now, updated_at=now
    )
    refused = client.delete(f"/projects/{project_id}", headers=_idem())
    assert refused.status_code == 409, refused.text
    assert "runs=1" in refused.json()["detail"]
    assert [item["id"] for item in client.get(f"/projects/{project_id}/runs").json()] == [run_id]
    assert project_id in [item["id"] for item in client.get("/projects").json()]


def test_delete_refuses_project_with_drafts(client: TestClient) -> None:
    """草稿也是引用：删除被拒，草稿仍可按项目列出。"""
    project_id = _create_project(client, "has drafts")["id"]
    created = client.post(
        f"/projects/{project_id}/protocol-drafts",
        json={"name": "kept", "yaml_text": _DRAFT_YAML},
        headers=_idem(),
    )
    assert created.status_code == 201, created.text
    refused = client.delete(f"/projects/{project_id}", headers=_idem())
    assert refused.status_code == 409, refused.text
    assert "drafts=1" in refused.json()["detail"]
    assert len(client.get(f"/projects/{project_id}/protocol-drafts").json()) == 1


def test_delete_refuses_project_with_ops_records(client: TestClient) -> None:
    """ops 规则/事故同属项目作用域数据：一并计入引用清单。"""
    project_id = _create_project(client, "has ops")["id"]
    rule = client.post(
        f"/projects/{project_id}/ops/alert-rules",
        json={"name": "mute all"},
        headers=_idem(),
    )
    assert rule.status_code == 201, rule.text
    refused = client.delete(f"/projects/{project_id}", headers=_idem())
    assert refused.status_code == 409, refused.text
    detail = refused.json()["detail"]
    assert "ops_rules=1" in detail


def test_delete_refuses_project_with_persisted_run(run_ready_client: TestClient) -> None:
    """有持久化 run 的项目（run-ready 装配，runs_store 生效）同样被拒。

    注：run-ready 夹具的 preflight context 固定为 example-project（受控测试态，
    见 `start_run` 文档），所以这里直接向 runs_store 落一行归属新项目的 run——
    检验的是删除路由对 runs_store 的计数路径，而不是夹具的归属行为。
    """
    created = run_ready_client.post("/projects", json={"name": "persisted host"}, headers=_idem())
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    deps = _deps(run_ready_client)
    assert deps.runs_store is not None
    now = Timestamp.now()
    run_id = ID.generate().value
    deps.runs_store.save_run(
        ResearchRun(
            id=ID(run_id), project_id=project_id, protocol_id="p", created_at=now, updated_at=now
        )
    )
    refused = run_ready_client.delete(f"/projects/{project_id}", headers=_idem())
    assert refused.status_code == 409, refused.text
    assert "runs=1" in refused.json()["detail"]


def test_delete_requires_store(client: TestClient) -> None:
    """store 未装配 → 503（不伪造删除成功）。"""
    deps = _deps(client)
    project_id = _create_project(client, "storeless later")["id"]
    deps.project_store = None
    response = client.delete(f"/projects/{project_id}", headers=_idem())
    assert response.status_code == 503, response.text
