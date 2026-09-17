"""Control Plane API 测试：停车语义读面 `paused_dispatch`（GOAL-004 cycle 2 = EC-02）。

一条 `PAUSED` 的 run 有三种来源，读面必须能回答"它会不会自己走"。这里在 **HTTP 边界**
上钉四件事：

1. 有未到期重排 ⇒ `RETRY_SCHEDULED` + 那条期限（`due_now=false`）；
2. 同一条重排到期后（把库里的事实推到过去）⇒ `due_now=true`；
3. 任务面没有任何重排 ⇒ `USER_PAUSED`（只有人工能动能它）；
4. 没有 workflow 读面 ⇒ `UNKNOWN`；非 `PAUSED` ⇒ `null`；列表与详情同判据。

判据只读 canonical 事实（run 行 + 任务行 `status`/`retry_at`），断言里直接把这些事实
与读面比对，而不是和读面自己的另一份计算比。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.application.ports.workflow_engine import TaskCompletion
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

SESSION_CONTRACT = "session"
BACKOFF_SECONDS = 600


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


def _session_task(run_id: str) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=f"session-{ID.generate().value}",
    )


def _retry_contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id=SESSION_CONTRACT,
        version="1.0",
        purpose="a failed session may be retried",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _parked_retry(deps: Any, run_id: str, *, backoff: int | None) -> ResearchTask:
    """让一个任务真的走到 `RETRY_SCHEDULED`（走引擎，不写库里的字段）。"""
    task = _session_task(run_id)
    deps.workflow.submit(task, _retry_contract(backoff=backoff))
    lease = deps.workflow.acquire_lease(task.id.value)
    deps.workflow.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    return task


def _stored_retry_at(deps: Any, task: ResearchTask) -> str | None:
    """库里真实的期限（canonical 事实；读面必须回答同一条）。"""
    row = deps._connection.execute(  # noqa: SLF001 - 断言用只读事实
        "SELECT retry_at, status FROM tasks WHERE task_id = ?", (task.id.value,)
    ).fetchone()
    assert row is not None, "任务行必须存在"
    assert row["status"] == ResearchTaskState.State.RETRY_SCHEDULED
    retry_at: str | None = row["retry_at"]
    return retry_at


def _instant(text: str) -> datetime:
    """读面/库里的 ISO 文本 → 同一瞬间（两种拼法：`+00:00` 与 `Z`）。"""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _paused_view(client: TestClient, run_id: str) -> Any:
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    return response.json()["paused_dispatch"]


def test_a_parked_retry_reads_as_self_driving(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    task = _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)

    view = _paused_view(run_ready_client, run_id)

    assert view["kind"] == "RETRY_SCHEDULED"
    assert view["due_now"] is False, "期限还没到 ⇒ 现在不会自己走，但到期会"
    assert _instant(view["next_retry_at"]) == _instant(_stored_retry_at(deps, task) or "")


def test_passing_the_deadline_flips_due_now(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    task = _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)
    assert _paused_view(run_ready_client, run_id)["due_now"] is False

    # 把库里的事实推到过去（与 PG/adapter 用例同一招）：产品装配里引擎用的是真实
    # 时钟，测试不注入时钟，所以推进的是 canonical 事实而不是"读面看到的现在"。
    deps._connection.execute(  # noqa: SLF001 - 只改这一条 canonical 事实
        "UPDATE tasks SET retry_at = ? WHERE task_id = ?",
        ("2020-01-01T00:00:00Z", task.id.value),
    )
    deps._connection.commit()  # noqa: SLF001

    view = _paused_view(run_ready_client, run_id)

    assert view["kind"] == "RETRY_SCHEDULED"
    assert view["due_now"] is True, "同一个读面、同一条事实，到期后就该说已到期"
    assert view["next_retry_at"] is None, "没有未到期的重排 ⇒ 没有下一个期限"


def test_a_user_pause_reads_as_manual(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    deps.workflow.submit(_session_task(run_id), _retry_contract(backoff=BACKOFF_SECONDS))

    view = _paused_view(run_ready_client, run_id)

    assert view == {"kind": "USER_PAUSED", "next_retry_at": None, "due_now": False}


def test_without_a_workflow_read_surface_the_view_is_unknown(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    deps.workflow = None

    assert _paused_view(run_ready_client, run_id)["kind"] == "UNKNOWN"


def test_a_run_that_is_not_paused_has_no_view(run_ready_client: TestClient) -> None:
    _, run_id = _inject_run(run_ready_client, ResearchRunState.State.RUNNING)

    assert _paused_view(run_ready_client, run_id) is None, "不适用就 null，不伪造 USER_PAUSED"


def test_the_list_read_face_uses_the_same_judgement(run_ready_client: TestClient) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    task = _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)

    listed = run_ready_client.get("/projects/example-project/runs")
    assert listed.status_code == 200
    rows = [row for row in listed.json() if row["id"] == run_id]

    assert len(rows) == 1
    assert rows[0]["paused_dispatch"] == _paused_view(run_ready_client, run_id)
    stored = _stored_retry_at(deps, task)
    assert stored is not None
    assert _instant(rows[0]["paused_dispatch"]["next_retry_at"]) == _instant(stored)


def test_the_view_does_not_write_anything(run_ready_client: TestClient) -> None:
    """读面是只读的：连读两次不改任何 canonical 事实（含任务行）。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    task = _parked_retry(deps, run_id, backoff=BACKOFF_SECONDS)
    before = (_stored_retry_at(deps, task), deps.workflow.run_state(run_id))

    _paused_view(run_ready_client, run_id)
    _paused_view(run_ready_client, run_id)

    assert (_stored_retry_at(deps, task), deps.workflow.run_state(run_id)) == before
    assert uuid.UUID(run_id)  # run_id 是合法 ID（夹具自检，不参与断言语义）
