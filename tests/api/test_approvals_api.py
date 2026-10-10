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


def test_program_gate_approval_is_accepted_only_on_a_terminal_run(
    run_ready_client: TestClient,
) -> None:
    """GOAL-20261010-047 EC-03：**程序级闸门**的准入 = 该 run **已终态**（新增分支）。

    **为什么需要这条分支**：程序闸门是「第 N 轮**跑完之后**」才拦的 ⇒ 那个 run 已经
    `SUCCEEDED`，**不可能**回到 `WAITING_FOR_APPROVAL`（状态机没有终态入边，实测）——
    若沿用 phase 面的准入，声明的闸门**永远无法被裁决**（这正是本 GOAL 的靶子）。

    **这条用例同时钉住「分支很窄」**：只有 `program-gate:` 前缀走新准入；下一条用例
    证明**非**该前缀在**同一个** `SUCCEEDED` run 上仍然 409（既有规则一字未松）。
    """
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState
    from services.api.approvals import PROGRAM_GATE_ACTION_PREFIX

    deps = cast(Any, run_ready_client.app).state.deps
    assert deps.approvals is not None
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.SUCCEEDED,
    )
    deps.run_registry[run_id] = run
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action=f"{PROGRAM_GATE_ACTION_PREFIX}prog-1",
            risk="HUMAN_GATE",
            context="program-round:1",
            policy_source="program-gate",
            requested_event_id="",
        )
    )
    decided = run_ready_client.post(
        f"/approvals/{approval.id}/decide",
        json={"decision": "approve"},
        headers={"If-Match": "*", "Idempotency-Key": f"pg-{uuid.uuid4()}"},
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "APPROVED", decided.json()
    # 终态 run **不得**被这条裁决改状态（接回是**程序面**的推进决定，不是 run 的迁移）
    assert deps.run_registry[run_id].state == ResearchRunState.State.SUCCEEDED


def test_a_non_program_gate_approval_on_a_terminal_run_is_still_refused(
    run_ready_client: TestClient,
) -> None:
    """**准入分支的窄性（反证）**：同一终态 run 上，**非** `program-gate:` 前缀仍 409。

    与上一条**配对**：两条用**同一个** `SUCCEEDED` run、只差 `action` 前缀。若有人把准入
    放宽成「任何终态 run 都可裁决」，本条立刻判红 —— 它守的是 phase 面的既有规则
    （`test_decide_requires_waiting_state` 守的是「非等待态不得裁决」的另一半）。
    """
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast(Any, run_ready_client.app).state.deps
    assert deps.approvals is not None
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.SUCCEEDED,
    )
    deps.run_registry[run_id] = run
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="human-gate:phase-x",
            risk="HUMAN_GATE",
            context="phase-x",
            policy_source="protocol-gate",
            requested_event_id="",
        )
    )
    refused = run_ready_client.post(
        f"/approvals/{approval.id}/decide",
        json={"decision": "approve"},
        headers={"If-Match": "*", "Idempotency-Key": f"hg-{uuid.uuid4()}"},
    )
    assert refused.status_code == 409, refused.text
    assert refused.json()["title"] == "Invalid Transition", refused.json()


def test_pause_resume_use_state_machine(run_ready_client: TestClient) -> None:
    """interventions：pause/resume 走正式状态机；非法迁移 409。

    WP-P5：不再依赖 run 偶然结果（if state != FAILED 守卫恒走终态分支），
    显式注入 RUNNING 状态，断言始终执行。
    """
    from typing import Any
    from typing import cast as cast_any

    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast_any(Any, run_ready_client.app).state.deps
    run_id = str(ID.generate().value)
    running = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    deps.run_registry[run_id] = running

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
    """终态 run pause → 409（显式注入 FAILED，不依赖 run 偶然结果，WP-P5）。"""
    from typing import Any
    from typing import cast as cast_any

    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast_any(Any, run_ready_client.app).state.deps
    run_id = str(ID.generate().value)
    failed = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.FAILED,
    )
    deps.run_registry[run_id] = failed
    paused = run_ready_client.post(
        f"/runs/{run_id}/pause", headers={"Idempotency-Key": f"pause-{uuid.uuid4()}"}
    )
    assert paused.status_code == 409
    assert paused.json()["title"] == "Invalid Transition"


def test_semantic_intervention_is_501(run_ready_client: TestClient) -> None:
    """运行中语义变更必须产生 Manifest Revision / Fork；M13 诚实 501（WP-P2 语义按 kind 分支）。

    PLAN-046 起 budget_adjust 走 BudgetLedger 真实面（其验收见
    tests/api/test_budget_forecast_api.py）；本用例固定 replace_agent 恒 501。
    """
    from typing import Any
    from typing import cast as cast_any

    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast_any(Any, run_ready_client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    response = run_ready_client.post(
        f"/runs/{run_id}/interventions",
        json={"kind": "replace_agent"},
        headers={"Idempotency-Key": f"int-{uuid.uuid4()}"},
    )
    assert response.status_code == 501
    assert response.json()["title"] == "Semantic Intervention Pending"
    # 语义干预不得吞掉 payload 改 PAUSE（WP-P2：run 仍 RUNNING）
    assert run_ready_client.get(f"/runs/{run_id}").json()["state"] == "RUNNING"
