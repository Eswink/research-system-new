"""Control Plane API 测试：审批通过后续跑失败的补偿（GOAL-005 cycle 2 = EC-02）。

`resume_paused` 的补偿在 GOAL-004 cycle 7（EC-06）已收口；**同形缺口**留在审批入口：
`POST /approvals/{id}/decide`（approve）先按状态机把 run 落成 `RUNNING`，再调
`resume_after_approval`——后者**先 pop 暂存上下文再执行**。执行失败时，若把异常冒给
端点，canonical 会停在**悬空 `RUNNING`**：没有执行者、`_waiting` 已被 pop、
`PAUSED → RUNNING` 那条重入路也走不到（状态已经是 RUNNING）。

本文件在 HTTP 边界钉住补偿后的四件事：

1. 失败 ⇒ **run 行是 `PAUSED`**（不是 `RUNNING`），审批裁决本身仍如实返回 `APPROVED`；
2. 原因可从 **canonical 事实**读到：事件链里有 `run.resume_failed`（`failure_type` /
   `message` / `compensated_to`）；
3. **可重入**：补偿后 run 回停车态 ⇒ 后续 `POST /runs/{id}/resume` 不被 409 挡住；
4. 既有语义不变：正常续跑不记失败事件；上下文竞态（`InvalidInputError`）仍是既有的
   no-op（那种情况下**另一个** resume 正在跑这个 run，`RUNNING` 是正确状态）。

失败注入用实例级替身（与 `test_resume_compensation_api.py` 同款手法）：**只替换执行侧**
（`has_waiting_context` / `resume_after_approval`），补偿本身跑真实现（真迁移 + 真事件发布）。
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.approvals import ApprovalSpec


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_waiting_run(client: TestClient) -> tuple[Any, str, str, str]:
    """种子：run 处于 `WAITING_FOR_APPROVAL` + 一条 human-gate 审批（approve 触发续跑）。"""
    deps = _deps(client)
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    waiting = run.transition(ResearchRunState.Transition.REQUEST_APPROVAL)
    deps.run_registry[run_id] = waiting
    if deps.runs_store is not None:
        deps.runs_store.save_run(waiting)
    assert deps.approvals is not None
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="human-gate:review",
            risk="HIGH",
            context="human gate requires approval",
            policy_source="project-policy:require_approval",
            requested_event_id=f"evt-{uuid.uuid4().hex}",
        )
    )
    return deps, run_id, approval.id, approval.version


def _approve(client: TestClient, approval_id: str, version: str) -> Any:
    return client.post(
        f"/approvals/{approval_id}/decide",
        json={"decision": "approve"},
        headers={
            "If-Match": version,
            "Idempotency-Key": f"decide-{approval_id}-{uuid.uuid4()}",
        },
    )


def _stored_state(deps: Any, run_id: str) -> str:
    """canonical run 行的状态（读 store，不读响应——响应可能只是"说得好听"）。"""
    row = deps.runs_store.get_run(run_id) if hasattr(deps.runs_store, "get_run") else None
    if row is None:
        row = next(run for run in deps.runs_store.list_runs() if run.id.value == run_id)
    return cast(str, row.state)


def _resume_events(client: TestClient, run_id: str) -> list[dict[str, Any]]:
    events = client.get(f"/runs/{run_id}/events").json()
    return [item for item in events if item["type"] == "run.resume_failed"]


def _fail_approval_resume(deps: Any, message: str) -> None:
    """执行侧注入失败：本进程持有暂存上下文，但审批后的续跑抛错。"""
    deps.runs.has_waiting_context = lambda run_id: True

    def _boom(run_id: str) -> Any:
        raise RuntimeError(message)

    deps.runs.resume_after_approval = _boom


def test_a_failed_approval_resume_is_compensated_and_the_reason_is_canonical(
    run_ready_client: TestClient,
) -> None:
    deps, run_id, approval_id, version = _seed_waiting_run(run_ready_client)
    _fail_approval_resume(deps, "runtime exploded after approval")

    response = _approve(run_ready_client, approval_id, version)

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "APPROVED", "裁决本身成功，失败的是续跑"
    assert _stored_state(deps, run_id) == ResearchRunState.State.PAUSED, (
        "canonical 行必须是 PAUSED——悬空 RUNNING 是这条 EC 要消灭的状态"
    )

    events = _resume_events(run_ready_client, run_id)
    assert len(events) == 1, "一次失败一条事件"
    payload = events[0]["payload"]
    assert payload["run_id"] == run_id
    assert payload["failure_type"] == "RuntimeError"
    assert payload["message"] == "runtime exploded after approval"
    assert payload["compensated_to"] == ResearchRunState.State.PAUSED


def test_the_compensated_approval_run_is_not_bricked(run_ready_client: TestClient) -> None:
    """可重入：补偿后 run 回 PAUSED ⇒ 后续 resume 不被 409 挡住，且能真的续起来。"""
    deps, run_id, approval_id, version = _seed_waiting_run(run_ready_client)
    _fail_approval_resume(deps, "first attempt failed")
    assert _approve(run_ready_client, approval_id, version).status_code == 200
    assert _stored_state(deps, run_id) == ResearchRunState.State.PAUSED

    deps.runs.has_paused_context = lambda run_id: True
    deps.runs.resume_paused = lambda run_id, run: replace(
        run, state=ResearchRunState.State.RUNNING
    )
    resumed = run_ready_client.post(
        f"/runs/{run_id}/resume", headers={"Idempotency-Key": f"k-{uuid.uuid4()}"}
    )

    assert resumed.status_code == 200, resumed.text
    body = resumed.json()
    assert body["continuation"] == "RESUMED"
    assert body["state"] == ResearchRunState.State.RUNNING
    assert _stored_state(deps, run_id) == ResearchRunState.State.RUNNING
    assert len(_resume_events(run_ready_client, run_id)) == 1, "重入成功不再记失败事件"


def test_a_successful_approval_resume_records_no_failure_event(
    run_ready_client: TestClient,
) -> None:
    """边界：正常续跑保持既有语义（RUNNING + 无 `run.resume_failed`）。"""
    deps, run_id, approval_id, version = _seed_waiting_run(run_ready_client)
    deps.runs.has_waiting_context = lambda run_id: True
    deps.runs.resume_after_approval = lambda run_id: replace(
        deps.run_registry[run_id], state=ResearchRunState.State.RUNNING
    )

    assert _approve(run_ready_client, approval_id, version).status_code == 200

    assert _stored_state(deps, run_id) == ResearchRunState.State.RUNNING
    assert _resume_events(run_ready_client, run_id) == [], "成功路径不该有补偿事件"


def test_a_consumed_context_race_keeps_its_existing_answer(run_ready_client: TestClient) -> None:
    """竞态（上下文已被另一次续跑取走）仍是既有 no-op：不补偿、不记失败事件。

    这种情形下 `RUNNING` 是**正确**状态——另一个入口正在跑这个 run。
    """
    deps, run_id, approval_id, version = _seed_waiting_run(run_ready_client)
    deps.runs.has_waiting_context = lambda run_id: True

    def _consumed(run_id: str) -> Any:
        raise InvalidInputError("no waiting execution context for run")

    deps.runs.resume_after_approval = _consumed

    assert _approve(run_ready_client, approval_id, version).status_code == 200

    assert _stored_state(deps, run_id) == ResearchRunState.State.RUNNING
    assert _resume_events(run_ready_client, run_id) == [], "竞态不是失败，不该有补偿事件"
