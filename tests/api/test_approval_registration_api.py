"""Human-gate 审批注册与恢复闭环测试（PLAN-20260910-037 WP-H）。

证明：生产执行路径会真实注册 ApprovalRecord（approvalsEmpty 缺口解除）；
approve 续跑收敛；deny 收敛 FAILED；进程重启丢上下文时 approve 诚实 503
且不消费审批。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

_PROTOCOL = "human_gate_demo_v1.yaml"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _start(run_ready_client: TestClient) -> dict[str, Any]:
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"gate-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def _pending_approval(run_ready_client: TestClient, run_id: str) -> dict[str, Any]:
    approvals = run_ready_client.get("/approvals").json()
    mine = [item for item in approvals if item["run_id"] == run_id]
    assert mine, f"no approval registered for {run_id}: {approvals}"
    return mine[0]


def _decide(
    run_ready_client: TestClient, approval: dict[str, Any], decision: str
) -> Any:
    return run_ready_client.post(
        f"/approvals/{approval['id']}/decide",
        json={"decision": decision},
        headers={
            "If-Match": approval["version"],
            "Idempotency-Key": f"decide-{uuid.uuid4()}",
        },
    )


def test_human_gate_pauses_run_and_registers_approval(run_ready_client: TestClient) -> None:
    run = _start(run_ready_client)
    assert run["state"] == "WAITING_FOR_APPROVAL"
    assert run["manifest_digest"] is not None  # freeze 完成后才暂停
    approval = _pending_approval(run_ready_client, run["id"])
    assert approval["action"] == "human-gate:discovery"
    assert approval["status"] == "PENDING"
    events = run_ready_client.get(f"/runs/{run['id']}/events").json()
    assert "approval.requested" in {item["type"] for item in events}


def test_approve_resumes_and_converges(run_ready_client: TestClient) -> None:
    run = _start(run_ready_client)
    approval = _pending_approval(run_ready_client, run["id"])
    decided = _decide(run_ready_client, approval, "approve")
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "APPROVED"
    fetched = run_ready_client.get(f"/runs/{run['id']}").json()
    # 续跑：discovery 成功 → run 收敛（SUCCEEDED 或诚实 FAILED，取决于受控执行）
    assert fetched["state"] in {"SUCCEEDED", "FAILED"}
    assert fetched["state"] != "RUNNING"
    events = run_ready_client.get(f"/runs/{run['id']}/events").json()
    types = {item["type"] for item in events}
    assert "approval.decided" in types
    assert "approval.requested" in types


def test_deny_rejects_run(run_ready_client: TestClient) -> None:
    run = _start(run_ready_client)
    approval = _pending_approval(run_ready_client, run["id"])
    decided = _decide(run_ready_client, approval, "deny")
    assert decided.status_code == 200, decided.text
    fetched = run_ready_client.get(f"/runs/{run['id']}").json()
    assert fetched["state"] == "FAILED"


def test_restart_loses_execution_context_and_refuses_fake_resume(
    run_ready_client: TestClient,
) -> None:
    run = _start(run_ready_client)
    approval = _pending_approval(run_ready_client, run["id"])
    _deps(run_ready_client).runs._waiting.clear()  # noqa: SLF001 - 模拟进程重启
    refused = _decide(run_ready_client, approval, "approve")
    assert refused.status_code == 503
    # 审批未被消费：仍 PENDING，可继续观察/取消 run；不产生假 RUNNING
    still = _pending_approval(run_ready_client, run["id"])
    assert still["status"] == "PENDING"
    fetched = run_ready_client.get(f"/runs/{run['id']}").json()
    assert fetched["state"] == "WAITING_FOR_APPROVAL"
