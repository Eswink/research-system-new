"""Control Plane API 测试：统一派发读面 `dispatch`（GOAL-004 cycle 6 = EC-05 ②）。

一条 run 有没有**活的派发方**、是哪一个——两个派发方此前各持一半事实（retry dispatch
只看 `PAUSED` 的重排到期；worker plane 的租约不在读面），本读面在 HTTP 边界上把三态问齐：

1. worker claim 持有（`RUNNING`）⇒ `WORKER_CLAIM`，持有者点名 task/worker/fence/到期，
   且**不含 `lease_id`**（作业面凭据不进控制面读面）；
2. retry dispatch 持有（`PAUSED` + 重排）⇒ `RETRY_DISPATCH`，数字与库里那条 `retry_at` 同源；
3. 两者皆无 ⇒ `NONE`（同时 `paused_dispatch` 如实回答 `USER_PAUSED`——两个视图各答各的问题）；
4. 两个派发方都在 ⇒ `BOTH`；没有 workflow 读面 ⇒ `UNKNOWN`（不是 `NONE`）。

断言直接与 canonical 事实（任务行 `retry_at`、租约行）比对，而不是与读面自己的另一份
计算比；另有只读性用例（读两次不改任何 canonical 事实）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)

BACKOFF_SECONDS = 600
_CAPABILITY = "python_exec"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _inject_run(client: TestClient, state: str) -> tuple[Any, str]:
    """种子一个指定状态的 run（注册表 + 存储两条读路径都能看到）。"""
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


def _contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id="dispatch-view-contract",
        version="1.0",
        purpose="who is dispatching this run",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _task(run_id: str, *, kind: str, capability: str | None) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=kind,
        idempotency_key=f"task-{ID.generate().value}",
        required_capability=capability,
    )


def _claimed_task(deps: Any, run_id: str, *, capability: str = _CAPABILITY) -> str:
    """交付一个 EXECUTION 任务给 worker（走真 claim 路径，不写库里的字段）。"""
    task = _task(run_id, kind=TaskKind.EXECUTION, capability=capability)
    deps.workflow.submit(task, _contract(backoff=None))
    lease = deps.workflow.claim_next(
        ClaimRequest(
            worker_id="worker-one",
            capabilities=frozenset({capability}),
            partitions=frozenset({0}),
        )
    )
    assert lease is not None and lease.task_id == task.id.value, "夹具必须先真的拿到租约"
    return task.id.value


def _parked_retry(deps: Any, run_id: str, *, backoff: int | None) -> str:
    """让一个会话任务真的走到 `RETRY_SCHEDULED`（走引擎，不写库里的字段）。"""
    task = _task(run_id, kind=TaskKind.AGENT_SESSION, capability=None)
    deps.workflow.submit(task, _contract(backoff=backoff))
    lease = deps.workflow.acquire_lease(task.id.value)
    deps.workflow.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    return task.id.value


def _stored_lease(deps: Any, task_id: str) -> Any:
    return deps._connection.execute(  # noqa: SLF001 - 断言用只读事实
        "SELECT worker_id, fence, expires_at FROM leases WHERE task_id = ?", (task_id,)
    ).fetchone()


def _stored_retry_at(deps: Any, task_id: str) -> str | None:
    row = deps._connection.execute(  # noqa: SLF001
        "SELECT retry_at, status FROM tasks WHERE task_id = ?", (task_id,)
    ).fetchone()
    assert row is not None and row["status"] == ResearchTaskState.State.RETRY_SCHEDULED
    retry_at: str | None = row["retry_at"]
    return retry_at


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _dispatch(client: TestClient, run_id: str) -> Any:
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    return response.json()["dispatch"]


def test_a_worker_claim_is_visible_without_leaking_the_lease_credential(
    run_ready_client: TestClient,
) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    task_id = _claimed_task(deps, run_id)

    dispatch = _dispatch(run_ready_client, run_id)

    assert dispatch["kind"] == "WORKER_CLAIM"
    assert dispatch["retry"] == {"scheduled": 0, "due": 0, "next_retry_at": None}
    assert len(dispatch["holders"]) == 1
    holder = dispatch["holders"][0]
    assert holder["task_id"] == task_id
    assert holder["worker_id"] == "worker-one", "持有者点名真实工人身份"
    assert holder["fence"] == 1
    stored = _stored_lease(deps, task_id)
    assert stored is not None
    assert _instant(holder["expires_at"]) == _instant(stored["expires_at"]), "到期来自租约行"
    assert "lease_id" not in holder, "作业面凭据不进控制面读面"


def test_a_parked_retry_reads_as_the_retry_dispatcher(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    task_id = _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)

    dispatch = _dispatch(run_ready_client, run_id)

    assert dispatch["kind"] == "RETRY_DISPATCH"
    assert dispatch["holders"] == [], "重排的是任务、持有者列表为空"
    assert dispatch["retry"]["scheduled"] == 1 and dispatch["retry"]["due"] == 0
    assert _instant(dispatch["retry"]["next_retry_at"]) == _instant(
        _stored_retry_at(deps, task_id) or ""
    )


def test_a_run_without_any_dispatcher_reads_as_none(run_ready_client: TestClient) -> None:
    """两者皆无：停车但没人会自己动它（同一个 run 上两个视图各答各的问题）。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    queued = _task(run_id, kind=TaskKind.EXECUTION, capability=_CAPABILITY)
    deps.workflow.submit(queued, _contract(backoff=None))

    detail = run_ready_client.get(f"/runs/{run_id}").json()

    assert detail["dispatch"]["kind"] == "NONE"
    assert detail["dispatch"]["holders"] == []
    assert detail["paused_dispatch"]["kind"] == "USER_PAUSED", "没有重排 ⇒ 不会自己走"


def test_both_dispatchers_are_reported_at_once(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)
    _claimed_task(deps, run_id)

    dispatch = _dispatch(run_ready_client, run_id)

    assert dispatch["kind"] == "BOTH"
    assert dispatch["retry"]["scheduled"] == 1
    assert len(dispatch["holders"]) == 1
    assert dispatch["holders"][0]["worker_id"] == "worker-one"


def test_without_a_workflow_read_surface_the_answer_is_unknown(
    run_ready_client: TestClient,
) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    deps.workflow = None

    dispatch = _dispatch(run_ready_client, run_id)

    assert dispatch["kind"] == "UNKNOWN", "读不到 ≠ 没有派发方"
    assert dispatch["retry"] == {"scheduled": 0, "due": 0, "next_retry_at": None}
    assert dispatch["holders"] == []


def test_the_list_read_face_reports_the_same_ownership(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    _claimed_task(deps, run_id)

    listed = run_ready_client.get("/projects/example-project/runs")

    assert listed.status_code == 200
    rows = [row for row in listed.json() if row["id"] == run_id]
    assert len(rows) == 1
    assert rows[0]["dispatch"] == _dispatch(run_ready_client, run_id)


def test_the_read_face_does_not_write_anything(run_ready_client: TestClient) -> None:
    """读面是只读的：读两次不改 canonical 事实（任务行与租约行都不动）。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)
    task_id = _claimed_task(deps, run_id)
    before = (
        _stored_lease(deps, task_id)["fence"],
        deps.workflow.run_state(run_id),
        _dispatch(run_ready_client, run_id),
    )

    _dispatch(run_ready_client, run_id)

    assert (
        _stored_lease(deps, task_id)["fence"],
        deps.workflow.run_state(run_id),
        _dispatch(run_ready_client, run_id),
    ) == before
