"""Control Plane API 测试：pause/resume 真执行协调（PLAN-20260914-048）。

证明 pause 不是"只改状态"：
- pause 后派发面（`claim_next`）不再认领该 run 的任务；resume 后重新可认领；
- 响应字段诚实标注 `dispatch` / `continuation` / `execution_context`；
- 状态机守卫不变（只有 RUNNING 可 pause、只有 PAUSED 可 resume）；
- `interventions` 的 pause/resume 与专用端点语义一致（同一实现）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.application.ports.workflow_engine import ClaimRequest
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _post(client: TestClient, path: str, **overrides: Any) -> Any:
    """POST 一律带 Idempotency-Key（控制面写路径的既有要求）。"""
    headers = {"Idempotency-Key": f"k-{uuid.uuid4()}"}
    headers.update(overrides.pop("headers", {}))
    return client.post(path, headers=headers, **overrides)


def _inject_run(client: TestClient, state: str) -> tuple[Any, str]:
    """种子一个指定状态的 run：走正式存储路径（注册表 + runs_store）。"""
    deps = _deps(client)
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=state,
    )
    deps.run_registry[run_id] = run
    if deps.runs_store is not None:
        deps.runs_store.save_run(run)
    return deps, run_id


def _queued_execution_task(run_id: str) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _claim(deps: Any) -> Any:
    return deps.workflow.claim_next(
        ClaimRequest(
            worker_id="w1",
            capabilities=frozenset({"docker"}),
            partitions=frozenset({0}),
        )
    )


def test_pause_holds_dispatch_and_resume_releases_it(run_ready_client: TestClient) -> None:
    """暂停真的拦住派发：pause → claim 为 None；resume → 同一任务可认领。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    task = _queued_execution_task(run_id)
    deps.workflow.submit(task, task_contract())

    paused = _post(run_ready_client, f"/runs/{run_id}/pause")
    assert paused.status_code == 200
    body = paused.json()
    assert body["state"] == ResearchRunState.State.PAUSED
    assert body["dispatch"] == "HELD"
    assert body["execution_context"] == "NONE"
    assert _claim(deps) is None

    resumed = _post(run_ready_client, f"/runs/{run_id}/resume")
    assert resumed.status_code == 200
    body = resumed.json()
    assert body["state"] == ResearchRunState.State.RUNNING
    assert body["dispatch"] == "RELEASED"
    assert body["continuation"] == "NONE"  # 无暂停上下文时不伪造续跑
    lease = _claim(deps)
    assert lease is not None
    assert lease.task_id == task.id.value


def test_pause_requires_running_state(run_ready_client: TestClient) -> None:
    _, run_id = _inject_run(run_ready_client, ResearchRunState.State.SUCCEEDED)
    response = _post(run_ready_client, f"/runs/{run_id}/pause")
    assert response.status_code == 409
    assert response.json()["title"] == "Invalid Transition"


def test_resume_requires_paused_state(run_ready_client: TestClient) -> None:
    _, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    response = _post(run_ready_client, f"/runs/{run_id}/resume")
    assert response.status_code == 409


def test_unknown_run_is_404(run_ready_client: TestClient) -> None:
    assert _post(run_ready_client, "/runs/ghost/pause").status_code == 404
    assert _post(run_ready_client, "/runs/ghost/resume").status_code == 404


def test_interventions_share_pause_resume_semantics(run_ready_client: TestClient) -> None:
    """interventions 的 pause/resume 与专用端点同实现（字段一致，无第二套语义）。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    task = _queued_execution_task(run_id)
    deps.workflow.submit(task, task_contract())

    paused = _post(run_ready_client, f"/runs/{run_id}/interventions", json={"kind": "pause"})
    assert paused.status_code == 200
    assert paused.json()["dispatch"] == "HELD"
    assert _claim(deps) is None

    resumed = _post(run_ready_client, f"/runs/{run_id}/interventions", json={"kind": "resume"})
    assert resumed.status_code == 200
    assert resumed.json()["dispatch"] == "RELEASED"
    assert _claim(deps) is not None
