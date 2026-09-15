"""Ops 写面 API 测试（G7 / GOAL-20260915-002 EC-04 / PLAN-20260915-059）。

锁住两件事：

1. 规则/事故是**被消费的**——启用规则让告警带 `muted`/`muted_by` 并计入
   `muted_count`；未关闭事故让来源 run 的告警带 `incident_id`，并让失败 Run 从
   `candidates` 移到 `incidents`；
2. 边界诚实——store 缺失 503（读面 rules/workflow=False + 原因）、未知 id 404、
   未知枚举 422、空 patch 422、已关闭事故再处置 409。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID, Timestamp
from packages.domain.run import ResearchRun

PROJECT_ID = "example-project"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _headers() -> dict[str, str]:
    return {"Idempotency-Key": f"ops-{uuid.uuid4().hex}"}


def _rule(client: TestClient, **overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {"name": "mute worker noise", "kind": "WORKER_OFFLINE"}
    payload.update(overrides)
    response = client.post(
        f"/projects/{PROJECT_ID}/ops/alert-rules", json=payload, headers=_headers()
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _failed_run(client: TestClient, run_id: str) -> None:
    deps = _deps(client)
    run = ResearchRun(
        id=ID(run_id),
        project_id=PROJECT_ID,
        protocol_id="proto",
        state="FAILED",
        updated_at=Timestamp.now(),
    )
    deps.run_registry[run_id] = run


def _incident(client: TestClient, **overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {"title": "run 失败排查", "severity": "CRITICAL"}
    payload.update(overrides)
    response = client.post(
        f"/projects/{PROJECT_ID}/ops/incidents", json=payload, headers=_headers()
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_project_without_store_reports_locks(client: TestClient) -> None:
    deps = _deps(client)
    deps.ops_store = None
    _failed_run(client, str(ID.generate().value))

    rules = client.get(f"/projects/{PROJECT_ID}/ops/alert-rules").json()
    alerts = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()

    assert rules["rules_available"] is False
    assert "OpsStore" in rules["rules_reason"]
    assert alerts["rules_available"] is False
    assert alerts["rules_applied"] == 0
    assert (
        client.post(
            f"/projects/{PROJECT_ID}/ops/alert-rules", json={"name": "x"}, headers=_headers()
        ).status_code
        == 503
    )


def test_rule_crud_lifecycle(client: TestClient) -> None:
    created = _rule(client, max_severity="INFO")
    assert created["kind"] == "WORKER_OFFLINE"
    assert created["enabled"] is True
    assert created["created_at"] is not None

    listed = client.get(f"/projects/{PROJECT_ID}/ops/alert-rules").json()
    assert listed["rules_available"] is True
    assert [row["id"] for row in listed["rules"]] == [created["id"]]

    patched = client.patch(
        f"/ops/alert-rules/{created['id']}",
        json={"name": "mute all worker noise", "clear_kind": True},
        headers=_headers(),
    ).json()
    assert patched["name"] == "mute all worker noise"
    assert patched["kind"] is None
    assert patched["max_severity"] == "INFO"

    disabled = client.patch(
        f"/ops/alert-rules/{created['id']}", json={"enabled": False}, headers=_headers()
    ).json()
    assert disabled["enabled"] is False

    assert client.delete(f"/ops/alert-rules/{created['id']}", headers=_headers()).status_code == 204
    assert client.get(f"/projects/{PROJECT_ID}/ops/alert-rules").json()["rules"] == []


def test_rule_validation_and_not_found(client: TestClient) -> None:
    assert (
        client.post(
            f"/projects/{PROJECT_ID}/ops/alert-rules",
            json={"name": "bad", "kind": "NOT_A_KIND"},
            headers=_headers(),
        ).status_code
        == 422
    )
    created = _rule(client)
    empty = client.patch(f"/ops/alert-rules/{created['id']}", json={}, headers=_headers())
    assert empty.status_code == 422
    assert (
        client.patch(
            "/ops/alert-rules/missing", json={"enabled": False}, headers=_headers()
        ).status_code
        == 404
    )
    assert client.delete("/ops/alert-rules/missing", headers=_headers()).status_code == 404


def test_enabled_rule_mutes_matching_alerts_without_hiding_them(client: TestClient) -> None:
    run_id = str(ID.generate().value)
    _failed_run(client, run_id)
    before = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()
    assert before["muted_count"] == 0
    assert {row["subject"] for row in before["alerts"]} >= {run_id}

    rule = _rule(client, kind="RUN_FAILED", max_severity="CRITICAL")
    after = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()

    # 静音不是隐藏：告警仍在列表里，只是带标记。
    subjects_before = {row["subject"] for row in before["alerts"]}
    assert {row["subject"] for row in after["alerts"]} == subjects_before
    muted = [row for row in after["alerts"] if row["muted"]]
    assert [row["subject"] for row in muted] == [run_id]
    assert muted[0]["muted_by"] == rule["id"]
    assert after["muted_count"] == 1
    assert after["rules_applied"] == 1


def test_disabled_rule_stops_muting(client: TestClient) -> None:
    run_id = str(ID.generate().value)
    _failed_run(client, run_id)
    rule = _rule(client, kind="RUN_FAILED")

    client.patch(f"/ops/alert-rules/{rule['id']}", json={"enabled": False}, headers=_headers())
    after = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()

    assert after["muted_count"] == 0
    assert after["rules_applied"] == 0


def test_rule_scope_limits_which_severities_are_muted(client: TestClient) -> None:
    run_id = str(ID.generate().value)
    _failed_run(client, run_id)
    _rule(client, kind="RUN_FAILED", max_severity="INFO")

    body = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()

    # RUN_FAILED 派生为 CRITICAL，高于 INFO ⇒ 不被静音。
    assert body["muted_count"] == 0
    assert body["rules_applied"] == 1


def test_incident_lifecycle_and_candidate_split(client: TestClient) -> None:
    run_id = str(ID.generate().value)
    _failed_run(client, run_id)

    before = client.get(f"/projects/{PROJECT_ID}/ops/incidents").json()
    assert before["workflow_available"] is True
    assert [row["run_id"] for row in before["candidates"]] == [run_id]
    assert before["incidents"] == []

    incident = _incident(client, run_id=run_id)
    assert incident["status"] == "OPEN"
    assert incident["assignee"] is None

    after = client.get(f"/projects/{PROJECT_ID}/ops/incidents").json()
    assert [row["id"] for row in after["incidents"]] == [incident["id"]]
    assert after["candidates"] == []

    assigned = client.post(
        f"/ops/incidents/{incident['id']}/assign", json={"assignee": "alice"}, headers=_headers()
    ).json()
    assert assigned["status"] == "ASSIGNED"
    assert assigned["assignee"] == "alice"

    closed = client.post(
        f"/ops/incidents/{incident['id']}/close",
        json={"resolution": "root cause fixed"},
        headers=_headers(),
    ).json()
    assert closed["status"] == "CLOSED"
    assert closed["resolution"] == "root cause fixed"
    assert closed["closed_at"] is not None

    again = client.post(
        f"/ops/incidents/{incident['id']}/close",
        json={"resolution": "again"},
        headers=_headers(),
    )
    assert again.status_code == 409
    assert (
        client.post(
            "/ops/incidents/missing/assign", json={"assignee": "bob"}, headers=_headers()
        ).status_code
        == 404
    )


def test_open_incident_links_its_run_alert(client: TestClient) -> None:
    run_id = str(ID.generate().value)
    _failed_run(client, run_id)

    incident = _incident(client, run_id=run_id, severity="CRITICAL")
    linked = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()
    row = next(item for item in linked["alerts"] if item["subject"] == run_id)
    assert row["incident_id"] == incident["id"]

    client.post(
        f"/ops/incidents/{incident['id']}/close",
        json={"resolution": "handled"},
        headers=_headers(),
    )
    unlinked = client.get(f"/projects/{PROJECT_ID}/ops/alerts").json()
    row = next(item for item in unlinked["alerts"] if item["subject"] == run_id)
    assert row["incident_id"] is None

    # 关闭仍是"已登记"：该 run 不再作为未处理候选重复出现（有记录就不该反复提醒），
    # 事故本身留在 incidents 里可追溯；只有未关闭的事故才给告警挂 incident_id。
    after_close = client.get(f"/projects/{PROJECT_ID}/ops/incidents").json()
    assert after_close["candidates"] == []
    assert [item["id"] for item in after_close["incidents"]] == [incident["id"]]


def test_incident_validation(client: TestClient) -> None:
    assert (
        client.post(
            f"/projects/{PROJECT_ID}/ops/incidents",
            json={"title": ""},
            headers=_headers(),
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/projects/{PROJECT_ID}/ops/incidents",
            json={"title": "t", "severity": "NOPE"},
            headers=_headers(),
        ).status_code
        == 422
    )
    incident = _incident(client)
    assert (
        client.post(
            f"/ops/incidents/{incident['id']}/assign", json={"assignee": ""}, headers=_headers()
        ).status_code
        == 422
    )


def test_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/ghost/ops/alert-rules").status_code == 404
    assert client.get("/projects/ghost/ops/incidents").status_code == 404
