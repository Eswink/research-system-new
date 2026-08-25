"""Control Plane API 测试：Run 生命周期 / Timeline SSE / 状态机映射。

证明（M13 DoD 6/8）：Run 状态来自正式状态机；Timeline 来自 outbox 事件
projection（无第二套 DB）；SSE 支持 cursor/resume 与 event_id 去重；
非法 transition 由 Domain 拒绝并映射 409。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

_PROTOCOL = "m12_reference_research_v1.yaml"


def start_run(run_ready_client: TestClient) -> dict[str, Any]:
    """启动 run（freeze 成功 + 执行失败收敛 FAILED 的诚实语义）。"""
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def test_start_run_freezes_manifest_and_records_failure(run_ready_client: TestClient) -> None:
    """M12 协议：preflight PASS → Manifest 冻结（事件落 outbox）；执行期
    phase 无契约 → run 收敛 FAILED（manifest digest 保留，诚实不伪装成功）。"""
    run = start_run(run_ready_client)
    assert run["id"]
    assert run["state"] == "FAILED"
    assert run["manifest_digest"] is not None
    assert run["manifest_digest"].startswith("sha256:")
    # MANIFEST_FROZEN 事件已在 outbox（Timeline 可重建）
    events = run_ready_client.get(f"/runs/{run['id']}/events").json()
    assert "manifest.frozen" in {item["type"] for item in events}


def test_start_run_warn_preflight_refuses_freeze(run_ready_client: TestClient) -> None:
    """preflight WARN（TOOL_RISK_ELEVATED）→ freeze 门禁拒绝（M2 语义），
    状态 FAILED 且无 manifest digest（不伪造冻结）。"""
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "sort_analysis_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["state"] == "FAILED"
    assert run["manifest_digest"] is None


def test_start_run_without_pins_fails_honestly(client: TestClient) -> None:
    """未 pin tool pack → preflight 如实 FAIL（AGENTS.md §9 unpinned deny）。"""
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["state"] == "FAILED"
    assert run["manifest_digest"] is None


def test_get_run_restores_from_api(run_ready_client: TestClient) -> None:
    run = start_run(run_ready_client)
    fetched = run_ready_client.get(f"/runs/{run['id']}").json()
    assert fetched["id"] == run["id"]
    assert fetched["manifest_digest"] == run["manifest_digest"]


def test_cancel_terminal_run_is_rejected_by_state_machine(run_ready_client: TestClient) -> None:
    """已 FAILED（terminal）的 run 不可取消：Domain 状态机拒绝 → 409。

    证明（M13 DoD 8）：非法 transition 由正式状态机拒绝并映射稳定错误，
    API 不自行实现 workflow state machine。
    """
    run = start_run(run_ready_client)
    assert run["state"] == "FAILED"
    response = run_ready_client.post(
        f"/runs/{run['id']}/cancel", headers={"Idempotency-Key": f"cancel-{uuid.uuid4()}"}
    )
    assert response.status_code == 409, response.text
    assert response.json()["title"] == "Invalid Transition"


def test_cancel_unknown_run_is_404(client: TestClient) -> None:
    response = client.post(
        "/runs/does-not-exist/cancel", headers={"Idempotency-Key": "cancel-unknown"}
    )
    assert response.status_code == 404


def test_events_are_outbox_projection(run_ready_client: TestClient) -> None:
    """Timeline 是 outbox 事件 projection（JSON replay）：含 MANIFEST_FROZEN。"""
    run = start_run(run_ready_client)
    response = run_ready_client.get(f"/runs/{run['id']}/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    types = {item["type"] for item in events}
    assert "manifest.frozen" in types


def test_events_replay_with_cursor(run_ready_client: TestClient) -> None:
    """cursor 续传：cursor 之后的事件才返回（client dedupe 基础）。"""
    run = start_run(run_ready_client)
    events = run_ready_client.get(f"/runs/{run['id']}/events").json()
    assert len(events) >= 1
    last_id = events[-1]["event_id"]
    resumed = run_ready_client.get(
        f"/runs/{run['id']}/events", headers={"Last-Event-ID": last_id}
    ).json()
    assert all(item["event_id"] > last_id for item in resumed)


def test_events_replay_deduped(run_ready_client: TestClient) -> None:
    """outbox event_id 唯一（publish 幂等）；同一 run 事件不重复。"""
    run = start_run(run_ready_client)
    first = run_ready_client.get(f"/runs/{run['id']}/events").json()
    second = run_ready_client.get(f"/runs/{run['id']}/events").json()
    assert first == second
    assert len(first) == len({item["event_id"] for item in first})


def test_sse_stream_sends_event_frames(run_ready_client: TestClient) -> None:
    """SSE 模式（Accept: text/event-stream + poll=0）输出 id:/event:/data: 帧。"""
    run = start_run(run_ready_client)
    response = run_ready_client.get(
        f"/runs/{run['id']}/events?poll=0", headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert "event:" in text
    assert "data:" in text
    assert "id: " in text
    # 事件帧含 run 事件类型
    assert "manifest.frozen" in text


def test_tasks_projection_from_canonical_state(run_ready_client: TestClient) -> None:
    run = start_run(run_ready_client)
    tasks = run_ready_client.get(f"/runs/{run['id']}/tasks")
    assert tasks.status_code == 200, tasks.text
    payload = tasks.json()
    assert isinstance(payload, list)
    for task in payload:
        assert task["task_id"]
        assert task["contract_id"]
        assert task["status"] in ("QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED")


def test_events_payload_redacted_no_secret(run_ready_client: TestClient) -> None:
    """事件 payload 不含 secret（AGENTS.md §10：事件永远不包含 Secret）。"""
    run = start_run(run_ready_client)
    body = run_ready_client.get(f"/runs/{run['id']}/events").text
    assert "sk-" not in body
    assert "Bearer" not in body
