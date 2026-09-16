"""Ops 运维投影 API 测试（PLAN-20260914-045 WP-B；PLAN-20260915-059 更新）。

alerts/incidents/data-health 三端点：真实派生、能力缺口诚实标注、未知项目 404、
缺失依赖诚实降级（`schedules` 自 PLAN-066 / EC-03 起是可管理面，见 ops_schedules）。

**PLAN-20260915-059（EC-04）更新了两条既有断言**，因为产品行为按 EC 要求改变，
不是为了让门禁变绿：alerts 的 `rules_available` 由 False（"无规则 CRUD"）变为
store 配置时的 True；incidents 的 `incidents` 现在只装**已登记**事故，失败 Run
候选移到 `candidates`。对应的锁断言改成"有 store 时可用"与"候选与登记分离"。
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


def test_alerts_surfaces_failed_run_with_rules_available(client: TestClient) -> None:
    run_id = _seed_failed_run(client)
    response = client.get(f"/projects/{_PROJECT}/ops/alerts")
    assert response.status_code == 200, response.text
    payload = response.json()
    failed = [item for item in payload["alerts"] if item["kind"] == "RUN_FAILED"]
    assert any(item["subject"] == run_id for item in failed)
    # store 已装配 ⇒ 规则面可用；无规则时没有任何项被静音（不是"没有规则"的假象）。
    assert payload["rules_available"] is True
    assert payload["rules_reason"] is None
    assert payload["rules_applied"] == 0
    assert payload["muted_count"] == 0
    assert all(item["muted"] is False for item in payload["alerts"])


def test_incidents_lists_failed_run_candidates_separately_from_registered(
    client: TestClient,
) -> None:
    run_id = _seed_failed_run(client)
    response = client.get(f"/projects/{_PROJECT}/ops/incidents")
    assert response.status_code == 200, response.text
    payload = response.json()
    # 失败 Run 只是**候选**：不自动登记为事故，两者字段分开。
    assert any(item["run_id"] == run_id for item in payload["candidates"])
    assert payload["incidents"] == []
    assert payload["workflow_available"] is True
    assert payload["workflow_reason"] is None


def test_schedules_reports_definitions_with_management_available(client: TestClient) -> None:
    """PLAN-066（GOAL-003 / EC-03）：`/ops/schedules` 不再是只读事实。

    产品行为按 EC 要求改变（可写定义 + 运行事实），断言随新行为改：
    `management_available=True`（store 已装配）、四个内置定义仍在、`builtin=True`。
    深度行为（写面被读面消费、trigger 与定时 pass 同函数）在
    `test_ops_schedules_api.py`。
    """
    response = client.get("/ops/schedules")
    assert response.status_code == 200, response.text
    payload = response.json()
    names = {item["name"] for item in payload["schedules"]}
    assert {"lease_recovery", "outbox_relay", "retention", "worker_reaper"} <= names
    assert all(item["interval_seconds"] > 0 for item in payload["schedules"])
    assert payload["management_available"] is True
    assert payload["management_reason"] is None
    assert all(item["builtin"] is True for item in payload["schedules"])


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
