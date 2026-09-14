"""Ops 只读运维投影 API 测试（PLAN-20260914-045 WP-B）。

alerts/incidents/schedules/data-health 四端点：真实派生、能力缺口诚实标注、
未知项目 404、缺失依赖诚实降级。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID
from packages.domain.run import ResearchRun

_PROJECT = "example-project"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_failed_run(client: TestClient) -> str:
    deps = _deps(client)
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id), project_id=_PROJECT, protocol_id="proto", state="FAILED"
    )
    return run_id


def test_alerts_surfaces_failed_run_and_locks_rules(client: TestClient) -> None:
    run_id = _seed_failed_run(client)
    response = client.get(f"/projects/{_PROJECT}/ops/alerts")
    assert response.status_code == 200, response.text
    payload = response.json()
    failed = [item for item in payload["alerts"] if item["kind"] == "RUN_FAILED"]
    assert any(item["subject"] == run_id for item in failed)
    assert payload["rules_available"] is False
    assert payload["rules_reason"]


def test_incidents_lists_failed_run_candidates_without_workflow(client: TestClient) -> None:
    run_id = _seed_failed_run(client)
    response = client.get(f"/projects/{_PROJECT}/ops/incidents")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert any(item["run_id"] == run_id for item in payload["incidents"])
    assert payload["workflow_available"] is False
    assert payload["workflow_reason"]


def test_schedules_reports_process_schedulers_readonly(client: TestClient) -> None:
    response = client.get("/ops/schedules")
    assert response.status_code == 200, response.text
    payload = response.json()
    names = {item["name"] for item in payload["schedules"]}
    assert {"lease_recovery", "outbox_relay", "retention", "worker_reaper"} <= names
    assert all(item["interval_seconds"] > 0 for item in payload["schedules"])
    assert payload["management_available"] is False
    assert payload["management_reason"]


def test_data_health_reports_endpoint_counts_and_locks_aggregate(client: TestClient) -> None:
    response = client.get(f"/projects/{_PROJECT}/ops/data-health")
    assert response.status_code == 200, response.text
    payload = response.json()
    metrics = {item["metric"]: item for item in payload["metrics"]}
    assert "endpoints_total" in metrics
    assert "endpoints_healthy" in metrics
    assert payload["aggregate_available"] is False
    assert payload["aggregate_reason"]


def test_alerts_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/ghost-project/ops/alerts").status_code == 404
    assert client.get("/projects/ghost-project/ops/incidents").status_code == 404
    assert client.get("/projects/ghost-project/ops/data-health").status_code == 404
