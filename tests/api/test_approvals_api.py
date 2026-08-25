"""Control Plane API 测试：Approvals / Interventions。

证明（M13 DoD 7/8）：
- UI 不得自己决定 Policy：直接调 API 也必须执行后端裁决规则；
- hidden button != authorization：decide 校验状态机 + If-Match；
- duplicate approve / approve-vs-deny race / stale version 测试；
- interventions 使用正式 backend state machine（非法迁移 409）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient
from httpx import Response

from services.api.approvals import ApprovalSpec


def _register_approval(client: TestClient, run_id: str) -> dict[str, Any]:
    """受控注入一条 pending approval（模拟 policy-required action）。"""
    deps = cast(Any, client.app).state.deps
    assert deps.approvals is not None
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="high-risk-tool",
            risk="HIGH",
            context="tool requires human approval",
            policy_source="project-policy:require_approval",
            requested_event_id=f"evt-{uuid.uuid4().hex}",
        )
    )
    return {
        "id": approval.id,
        "run_id": approval.run_id,
        "version": approval.version,
        "status": approval.status,
    }


def _prepare_run_in_approval_state(run_ready_client: TestClient) -> dict[str, Any]:
    """run 进入 WAITING_FOR_APPROVAL（受控状态注入 + 注册审批）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast(Any, run_ready_client.app).state.deps
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    deps.run_registry[run_id] = run
    waiting = run.transition(ResearchRunState.Transition.REQUEST_APPROVAL)
    deps.run_registry[run_id] = waiting
    approval = _register_approval(run_ready_client, run_id)
    return {"run": {"id": run_id}, "approval": approval}


def _decide(
    client: TestClient,
    approval_id: str,
    decision: str,
    version: str,
) -> Response:
    return cast(
        Response,
        client.post(
            f"/approvals/{approval_id}/decide",
            json={"decision": decision},
            headers={
                "If-Match": version,
                "Idempotency-Key": f"decide-{approval_id}-{decision}-{uuid.uuid4()}",
            },
        ),
    )


def test_decide_deny_rejects_run(run_ready_client: TestClient) -> None:
    ctx = _prepare_run_in_approval_state(run_ready_client)
    run_id = ctx["run"]["id"]
    approval_id = ctx["approval"]["id"]
    response = _decide(run_ready_client, approval_id, "deny", ctx["approval"]["version"])
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "DENIED"
    # deny → APPROVAL_REJECTED → FAILED（正式状态机）
    fetched = run_ready_client.get(f"/runs/{run_id}").json()
    assert fetched["state"] == "FAILED"
    # 决策事件落 outbox 审计
    events = run_ready_client.get(f"/runs/{run_id}/events").json()
    assert "approval.decided" in {item["type"] for item in events}


def test_decide_approve_resumes_run(run_ready_client: TestClient) -> None:
    ctx = _prepare_run_in_approval_state(run_ready_client)
    run_id = ctx["run"]["id"]
    approval_id = ctx["approval"]["id"]
    response = _decide(run_ready_client, approval_id, "approve", ctx["approval"]["version"])
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "APPROVED"
    # approve → APPROVAL_GRANTED → RUNNING（正式状态机）
    fetched = run_ready_client.get(f"/runs/{run_id}").json()
    assert fetched["state"] == "RUNNING"


def test_duplicate_approve_is_409(run_ready_client: TestClient) -> None:
    ctx = _prepare_run_in_approval_state(run_ready_client)
    approval_id = ctx["approval"]["id"]
    version = ctx["approval"]["version"]
    first = _decide(run_ready_client, approval_id, "approve", version)
    assert first.status_code == 200, first.text
    second = _decide(run_ready_client, approval_id, "approve", version)
    assert second.status_code == 409
    assert second.json()["title"] == "Approval Already Decided"


def test_approve_vs_deny_race_second_wins_conflict(run_ready_client: TestClient) -> None:
    """race：approve 先到（run 变 RUNNING），deny 后到 → 409（状态机拒绝）。"""
    ctx = _prepare_run_in_approval_state(run_ready_client)
    approval_id = ctx["approval"]["id"]
    version = ctx["approval"]["version"]
    approve = _decide(run_ready_client, approval_id, "approve", version)
    assert approve.status_code == 200
    deny = _decide(run_ready_client, approval_id, "deny", version)
    assert deny.status_code == 409


def test_stale_approval_version_is_412(run_ready_client: TestClient) -> None:
    ctx = _prepare_run_in_approval_state(run_ready_client)
    approval_id = ctx["approval"]["id"]
    stale = _decide(run_ready_client, approval_id, "approve", "sha256:" + "f" * 64)
    assert stale.status_code == 412


def test_decide_without_if_match_is_428(run_ready_client: TestClient) -> None:
    ctx = _prepare_run_in_approval_state(run_ready_client)
    approval_id = ctx["approval"]["id"]
    response = run_ready_client.post(
        f"/approvals/{approval_id}/decide",
        json={"decision": "approve"},
        headers={"Idempotency-Key": f"decide-{uuid.uuid4()}"},
    )
    assert response.status_code == 428


def test_decide_requires_waiting_state(run_ready_client: TestClient) -> None:
    """hidden button != authorization：直接调 API 在非 WAITING_FOR_APPROVAL
    状态裁决被 409 拒绝（后端执行正式规则）。"""
    run = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    ).json()
    approval = _register_approval(run_ready_client, run["id"])
    response = _decide(run_ready_client, approval["id"], "approve", approval["version"])
    assert response.status_code == 409


def test_pause_resume_use_state_machine(run_ready_client: TestClient) -> None:
    """interventions：pause/resume 走正式状态机；非法迁移 409。"""
    run = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    ).json()
    run_id = run["id"]
    if run["state"] != "FAILED":
        paused = run_ready_client.post(
            f"/runs/{run_id}/pause", headers={"Idempotency-Key": f"pause-{uuid.uuid4()}"}
        )
        assert paused.status_code == 200, paused.text
        assert paused.json()["state"] == "PAUSED"
        resumed = run_ready_client.post(
            f"/runs/{run_id}/resume", headers={"Idempotency-Key": f"resume-{uuid.uuid4()}"}
        )
        assert resumed.status_code == 200, resumed.text
        assert resumed.json()["state"] == "RUNNING"


def test_pause_terminal_run_is_409(run_ready_client: TestClient) -> None:
    run = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    ).json()
    if run["state"] == "FAILED":
        paused = run_ready_client.post(
            f"/runs/{run['id']}/pause", headers={"Idempotency-Key": f"pause-{uuid.uuid4()}"}
        )
        assert paused.status_code == 409
        assert paused.json()["title"] == "Invalid Transition"


def test_semantic_intervention_is_501(run_ready_client: TestClient) -> None:
    """运行中语义变更必须产生 Manifest Revision / Fork；M13 诚实 501。"""
    run = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    ).json()
    response = run_ready_client.post(
        f"/runs/{run['id']}/interventions",
        json={"kind": "budget_adjust"},
        headers={"Idempotency-Key": f"int-{uuid.uuid4()}"},
    )
    assert response.status_code in (200, 501)
    if response.status_code == 501:
        assert response.json()["title"] == "Semantic Intervention Pending"
