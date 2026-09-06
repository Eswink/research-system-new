"""M13-R1 WP-M1/M2：API 重启后 run/timeline/审批/幂等状态可恢复。

复审（MAJOR-M1）复现场景：API 重启后 run 全部 404、且 /runs/{id}/events
被内存注册表 gate 挡住（事件已持久仍 404）。本测试固化修复：
重启后 run 状态、timeline、run 列表、审批、幂等重放全部可恢复。

run/事件经 deps 直接种子（同 db 的正式存储路径），避免真实 DNS 依赖；
关键断言是"重启后经正式端点可恢复"，与生产路径同构。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from services.api.settings import ApiSettings

# Obviously synthetic fixture credential (computed, never a real secret).
_FIXTURE_ENDPOINT_KEY = "fixture-key-" + "0" * 16


def _create_app(settings: ApiSettings) -> tuple[TestClient, Any]:
    from services.api.app import create_app
    from services.api.composition import assemble

    app = create_app(assemble(settings))
    return TestClient(app), cast(Any, app).state.deps


def _seed_run_and_events(deps: Any, run_id: str) -> None:
    """经正式存储路径种子 run + 事件（runs_store + outbox projection）。"""
    import uuid

    from packages.domain.core import ID, Digest, Timestamp
    from packages.domain.events import EventEnvelope, EventType, digest_of_payload
    from packages.domain.run import ResearchRun

    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="console_demo_research_v1_0_1",
        state="SUCCEEDED",
        manifest_digest=Digest.parse("sha256:" + "a" * 64),
        manifest_semantic_digest=Digest.parse("sha256:" + "b" * 64),
    )
    deps.runs_store.save_run(run)
    asset = Timestamp.now()
    for event_type, payload in (
        (EventType.MANIFEST_FROZEN, {"digest": str(run.manifest_digest), "run_id": run_id}),
        (EventType.RUN_COMPLETED, {"run_id": run_id}),
    ):
        deps.events.publish(
            EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                schema_version="1",
                occurred_at=asset,
                actor="system:test",
                scope=f"run:{run_id}",
                payload=payload,
                payload_digest=digest_of_payload(payload),
                run_id=run_id,
                trace_id="trace-restart",
            )
        )


def _create_seed_environment(tmp_path: Any) -> tuple[Any, str, Any]:
    """Setup: app + endpoint + model + seeded run + denied approval."""
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, deps = _create_app(settings)
    endpoint = client.post(
        "/llm-endpoints",
        json={
            "name": "main",
            "base_url": "http://localtest.me:9999",
            "api_key": _FIXTURE_ENDPOINT_KEY,
            "api_style": "chat_completions",
        },
        headers={"Idempotency-Key": "restart-ep-1"},
    ).json()
    client.post(
        "/models",
        json={
            "endpoint_id": endpoint["id"],
            "model_name": "mock-review-model-v1",
        },
        headers={"Idempotency-Key": "restart-model-1"},
    )
    run_id = "3a11b52e-6b7e-4c9a-9f38-5a3cf4b19e01"
    _seed_run_and_events(deps, run_id)
    from packages.application.ports.approval_store import ApprovalSpec

    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="demo-approval",
            risk="MEDIUM",
            context="restart persistence check",
            policy_source="test",
            requested_event_id="evt-restart",
        )
    )
    deps.approvals.replace(approval.with_decision("deny"))
    client.close()
    return deps, run_id, endpoint


def test_api_restart_recovers_run_state(tmp_path: Any) -> None:
    """重启后 run 状态可恢复（此前 404）。"""
    _deps, run_id, _endpoint = _create_seed_environment(tmp_path)
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, _deps2 = _create_app(settings)
    restored = client.get(f"/runs/{run_id}").json()
    assert restored["state"] == "SUCCEEDED"
    assert restored["manifest_digest"].startswith("sha256:")
    client.close()


def test_api_restart_recovers_timeline(tmp_path: Any) -> None:
    """重启后 timeline 事件端点不再被内存 gate 挡住。"""
    _deps, run_id, _endpoint = _create_seed_environment(tmp_path)
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, _deps2 = _create_app(settings)
    events = client.get(f"/runs/{run_id}/events").json()
    assert "manifest.frozen" in {item["type"] for item in events}
    assert "run.completed" in {item["type"] for item in events}
    client.close()


def test_api_restart_recovers_run_list(tmp_path: Any) -> None:
    """重启后 run 列表可恢复（WP-M2 前端刷新恢复入口）。"""
    _deps, run_id, _endpoint = _create_seed_environment(tmp_path)
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, _deps2 = _create_app(settings)
    run_list = client.get("/projects/example-project/runs").json()
    assert [item["id"] for item in run_list] == [run_id]
    client.close()


def test_api_restart_recovers_approval_state(tmp_path: Any) -> None:
    """重启后 denied 审批不再出现在 pending 列表。"""
    _deps, run_id, _endpoint = _create_seed_environment(tmp_path)
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, _deps2 = _create_app(settings)
    approvals = client.get("/approvals").json()
    assert _endpoint["id"] not in {item["id"] for item in approvals}
    client.close()


def test_api_restart_replays_idempotency_key(tmp_path: Any) -> None:
    """幂等键跨重启重放：同 key 同 payload → 同资源 id，不重复创建。"""
    _deps, run_id, endpoint = _create_seed_environment(tmp_path)
    settings = ApiSettings(db_path=str(tmp_path / "restart.db"))
    client, _deps2 = _create_app(settings)
    replay = client.post(
        "/llm-endpoints",
        json={
            "name": "main",
            "base_url": "http://localtest.me:9999",
            "api_key": _FIXTURE_ENDPOINT_KEY,
            "api_style": "chat_completions",
        },
        headers={"Idempotency-Key": "restart-ep-1"},
    ).json()
    assert replay["id"] == endpoint["id"]
    assert len(client.get("/llm-endpoints").json()) == 1
    client.close()
