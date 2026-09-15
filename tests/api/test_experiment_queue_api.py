"""G14 队列控制面：入队 / 列表 / 改期 / 取消 + 派发器端到端。

派发器用**真实**实现（不是替身）：`run_once()` 走 `services.api.run_execution`
的同一装配链启动 run，并检查条目状态与 run 行确实落地。run_ready 装配可冻结
Manifest，因此"派发成功"是真的启动了一条研究 run，而不是伪造的状态翻转。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.experiment_store import FakeExperimentStore
from services.api.experiment_queue import ExperimentQueueDispatcher

PROTOCOL = "m12_reference_research_v1.yaml"
PROJECT = "proj-q"
# 默认项目恒注册（examples 契约合成条目）：派发链会解析项目设置，
# 用它验证"派发真的启动了 run"，不让测试去造项目注册前置。
DEFAULT_PROJECT = "example-project"


@pytest.fixture
def queue_client(client: TestClient) -> TestClient:
    """基础装配 + 实验存储（base deps 默认无 store ⇒ 诚实 503）。"""
    cast(Any, client.app).state.deps.experiment_store = FakeExperimentStore()
    return client


@pytest.fixture
def ready_queue_client(run_ready_client: TestClient) -> TestClient:
    """run-ready 装配：派发能真正冻结 Manifest 并落 run 行。"""
    deps = cast(Any, run_ready_client.app).state.deps
    if deps.experiment_store is None:
        deps.experiment_store = FakeExperimentStore()
    return run_ready_client


def _create_plan(client: TestClient, name: str = "queue-plan", key: str = "q-1") -> dict[str, Any]:
    response = client.post(
        "/projects/proj-q/experiments",
        json={"name": name},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def _enqueue(
    client: TestClient,
    plan_id: str,
    *,
    key: str = "q-enqueue",
    **payload: Any,
) -> Any:
    body: dict[str, Any] = {"protocol_path": PROTOCOL, **payload}
    return client.post(
        f"/projects/proj-q/experiments/{plan_id}/queue",
        json=body,
        headers={"Idempotency-Key": key},
    )


# ── HTTP 面 ────────────────────────────────────────────────────────────────


def test_queue_requires_store(client: TestClient) -> None:
    """store 未配置 → 503（不假装队列可用）。"""
    response = client.get(f"/projects/{PROJECT}/experiment-queue")
    assert response.status_code == 503


def test_enqueue_lists_and_cancels(queue_client: TestClient) -> None:
    plan = _create_plan(queue_client)
    created = _enqueue(queue_client, plan["id"])
    assert created.status_code == 201, created.text
    entry = created.json()
    assert entry["state"] == "QUEUED"
    assert entry["plan_name"] == "queue-plan"
    assert entry["protocol_path"] == PROTOCOL
    assert entry["not_before"] is None

    listed = queue_client.get("/projects/proj-q/experiment-queue")
    assert listed.status_code == 200, listed.text
    view = listed.json()
    assert [item["id"] for item in view["entries"]] == [entry["id"]]
    assert "at-least-once" in view["dispatch_note"]

    cancelled = queue_client.delete(
        f"/experiment-queue/{entry['id']}", headers={"Idempotency-Key": "q-cancel"}
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["state"] == "CANCELLED"
    again = queue_client.delete(
        f"/experiment-queue/{entry['id']}", headers={"Idempotency-Key": "q-cancel-2"}
    )
    assert again.status_code == 409


def test_enqueue_with_schedule_then_reschedule(queue_client: TestClient) -> None:
    plan = _create_plan(queue_client, key="q-2")
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    created = _enqueue(queue_client, plan["id"], key="q-enq-2", not_before=later.isoformat())
    assert created.status_code == 201, created.text
    stored = datetime.fromisoformat(created.json()["not_before"])
    assert abs((stored - later).total_seconds()) < 1

    cleared = queue_client.patch(
        f"/experiment-queue/{created.json()['id']}",
        json={"not_before": None},
        headers={"Idempotency-Key": "q-res-1"},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["not_before"] is None
    assert cleared.json()["state"] == "QUEUED"


def test_enqueue_rejects_bad_input(queue_client: TestClient) -> None:
    plan = _create_plan(queue_client, key="q-3")
    # 未知计划 → 404
    missing = _enqueue(queue_client, "nope", key="q-enq-3")
    assert missing.status_code == 404
    # 来源缺失 → 422（域值对象的二选一约束）
    no_source = queue_client.post(
        "/projects/proj-q/experiments/" + plan["id"] + "/queue",
        json={},
        headers={"Idempotency-Key": "q-enq-4"},
    )
    assert no_source.status_code == 422
    # 来源二义 → 422
    both = queue_client.post(
        f"/projects/proj-q/experiments/{plan['id']}/queue",
        json={"protocol_path": PROTOCOL, "draft_id": "d", "draft_revision": 1},
        headers={"Idempotency-Key": "q-enq-5"},
    )
    assert both.status_code == 422
    # 来源不可解析 → 404（入队即解析，不让坏引用排队）
    bad_path = _enqueue(queue_client, plan["id"], key="q-enq-6", protocol_path="nope.yaml")
    assert bad_path.status_code in {404, 422}
    # 非 UTC 时间戳 → 422
    naive = _enqueue(queue_client, plan["id"], key="q-enq-7", not_before="2026-09-15T12:00:00")
    assert naive.status_code == 422


def test_enqueue_rejects_archived_plan(queue_client: TestClient) -> None:
    plan = _create_plan(queue_client, key="q-4")
    archived = queue_client.post(
        f"/experiments/{plan['id']}/archive", headers={"Idempotency-Key": "q-arch-1"}
    )
    assert archived.status_code == 200
    response = _enqueue(queue_client, plan["id"], key="q-enq-8")
    assert response.status_code == 409


def test_experiment_plans_list_is_live(queue_client: TestClient) -> None:
    plan = _create_plan(queue_client, name="listed-plan", key="q-5")
    listed = queue_client.get("/experiment-plans")
    assert listed.status_code == 200, listed.text
    ids = [item["id"] for item in listed.json()]
    assert plan["id"] in ids
    filtered = queue_client.get("/experiment-plans", params={"state": "ARCHIVED"})
    assert plan["id"] not in [item["id"] for item in filtered.json()]


def test_cancel_unknown_entry_is_404(queue_client: TestClient) -> None:
    response = queue_client.delete(
        "/experiment-queue/nope", headers={"Idempotency-Key": "q-cancel-3"}
    )
    assert response.status_code == 404


# ── 派发器（真实装配链） ────────────────────────────────────────────────────


def _dispatcher(client: TestClient) -> ExperimentQueueDispatcher:
    deps = cast(Any, client.app).state.deps
    return ExperimentQueueDispatcher(deps, interval_seconds=60.0, claim_ttl_seconds=300.0)


def test_dispatcher_starts_run_and_records_id(ready_queue_client: TestClient) -> None:
    plan = _create_plan(ready_queue_client, name="dispatch-plan", key="q-6")
    created = ready_queue_client.post(
        f"/projects/{DEFAULT_PROJECT}/experiments/{plan['id']}/queue",
        json={"protocol_path": PROTOCOL},
        headers={"Idempotency-Key": "q-enq-9"},
    )
    assert created.status_code == 201, created.text
    outcomes = _dispatcher(ready_queue_client).run_once()
    assert len(outcomes) == 1
    assert outcomes[0].dispatched is True
    run_id = outcomes[0].run_id
    assert run_id is not None

    listed = ready_queue_client.get(f"/projects/{DEFAULT_PROJECT}/experiment-queue").json()[
        "entries"
    ]
    assert listed[0]["state"] == "DISPATCHED"
    assert listed[0]["run_id"] == run_id
    # run 行确实落在控制面（不是只翻状态）
    runs = ready_queue_client.get(f"/projects/{DEFAULT_PROJECT}/runs")
    assert runs.status_code == 200, runs.text
    assert run_id in [row["id"] for row in runs.json()]
    # 条目离开 QUEUED 后不会再被派发
    assert _dispatcher(ready_queue_client).run_once() == []


def test_dispatcher_fails_entry_when_plan_archived(queue_client: TestClient) -> None:
    """计划在入队后被归档 ⇒ 派发失败并把原因写回条目（不静默重试）。"""
    plan = _create_plan(queue_client, key="q-7")
    assert _enqueue(queue_client, plan["id"], key="q-enq-10").status_code == 201
    archived = queue_client.post(
        f"/experiments/{plan['id']}/archive", headers={"Idempotency-Key": "q-arch-2"}
    )
    assert archived.status_code == 200
    outcome = _dispatcher(queue_client).run_once()
    assert len(outcome) == 1
    assert outcome[0].dispatched is False
    assert "ARCHIVED" in str(outcome[0].reason)
    listed = queue_client.get("/projects/proj-q/experiment-queue").json()["entries"]
    assert listed[0]["state"] == "FAILED"
    assert "ARCHIVED" in listed[0]["failure_reason"]


def test_dispatcher_is_due_aware(queue_client: TestClient) -> None:
    """未到期的排期条目不会被派发（排期是事实，不是展示字段）。"""
    plan = _create_plan(queue_client, key="q-8")
    later = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    _enqueue(queue_client, plan["id"], key="q-enq-11", not_before=later)
    assert _dispatcher(queue_client).run_once() == []
    listed = queue_client.get("/projects/proj-q/experiment-queue").json()["entries"]
    assert listed[0]["state"] == "QUEUED"
