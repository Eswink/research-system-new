"""通知投影测试（PLAN-20260910-037 WP-G）。

白名单只呈现用户相关事件（task.* 噪音不呈现）；read 持久化；
projection/read store 缺失 → 503；真实 run 产生的事件可直接投影。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.sqlite.notification_read_store import SqliteNotificationReadStore
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _wire_reads(client: TestClient) -> None:
    deps = _deps(client)
    deps.notification_reads = SqliteNotificationReadStore(connection=deps._connection)  # noqa: SLF001


def _publish(client: TestClient, event_type: EventType, run_id: str | None = None) -> str:
    deps = _deps(client)
    event_id = uuid.uuid4().hex
    payload: dict[str, object] = {"probe": event_type.value}
    deps.events.publish(
        EventEnvelope(
            event_id=event_id,
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor="test:notify",
            scope=f"run:{run_id or 'x'}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
            run_id=run_id,
        )
    )
    return event_id


def test_notifications_store_missing_is_503(client: TestClient) -> None:
    assert _deps(client).notification_reads is None
    assert client.get("/notifications").status_code == 503


def test_whitelist_filters_noise(client: TestClient) -> None:
    _wire_reads(client)
    claimed = _publish(client, EventType.CLAIM_VERIFIED, "run-n")
    _publish(client, EventType.TASK_CREATED, "run-n")
    response = client.get("/notifications")
    assert response.status_code == 200, response.text
    items = response.json()["notifications"]
    assert [item["id"] for item in items] == [claimed]
    assert items[0]["read"] is False


def test_read_marks_persist_and_count(client: TestClient) -> None:
    _wire_reads(client)
    event_id = _publish(client, EventType.RUN_FAILED, "run-r")
    missing_key = client.post(f"/notifications/{event_id}/read")
    assert missing_key.status_code == 422  # Idempotency-Key required
    marked = client.post(f"/notifications/{event_id}/read", headers={"Idempotency-Key": "read-1"})
    assert marked.status_code == 204, marked.text
    items = client.get("/notifications").json()["notifications"]
    assert [item["read"] for item in items if item["id"] == event_id] == [True]
    # 重复标记幂等
    again = client.post(f"/notifications/{event_id}/read", headers={"Idempotency-Key": "read-2"})
    assert again.status_code == 204


def test_real_run_events_project_as_notifications(run_ready_client: TestClient) -> None:
    import uuid as _uuid

    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{_uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    run_id = response.json()["id"]
    _wire_reads(run_ready_client)
    items = run_ready_client.get("/notifications").json()["notifications"]
    types = {item["type"] for item in items}
    assert "manifest.frozen" in types
    assert all(item["run_id"] == run_id for item in items)
    assert "task.created" not in types  # 执行噪音不呈现
