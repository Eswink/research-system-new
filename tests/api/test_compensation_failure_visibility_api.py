"""补偿失败在读面可见（GOAL-20260918-006 cycle 6 = EC-06 (b)）。

守护线程面的补偿失败此前是 `except: pass`——run 停在原状态、下一轮重新评估，但**这件事本身
没有 canonical 痕迹**（RECHECK-090 W-4）。本文件在 HTTP 边界钉住"现在能判"：真的跑一轮
`RetryDispatchScheduler`，把补偿的**落库**打坏，然后从 `GET /runs/{id}/events` 读到
`run.resume_compensation_failed`。

注入只打坏 store 的**写面**（读面照常），事件真的发到 app 的事件链上，读的是同一个
`GET /runs/{id}/events` ⇒ "读面能判"不是靠替身伪造事件。

**诚实边界**（同一轮登记）：失败发生在补偿的**落库**这一步时，canonical 行已经停在前一步写的
`RUNNING`，而 `_dispatch_due` 只扫 `PAUSED` ⇒ 下一轮不会自动把它捞回来。这条事件是它唯一的
痕迹：**可见 ≠ 自动恢复**（自动修复属新机制与产品决策，不在本 EC 内）。
"""

from __future__ import annotations

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
from services.api.scheduler import RetryDispatchDeps, RetryDispatchScheduler

_CAPABILITY = "python_exec"
_EVENT = "run.resume_compensation_failed"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _parked_run_with_a_due_retry(client: TestClient) -> tuple[Any, str]:
    """种一条 `PAUSED` 且有**到期重排**的 run：守护线程的派发判据正是这两条。"""
    deps = _deps(client)
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.PAUSED,
    )
    deps.run_registry[run_id] = run
    deps.runs_store.save_run(run)
    task = ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=f"task-{ID.generate().value}",
    )
    deps.workflow.submit(
        task,
        TaskContract(
            id="compensation-visibility-contract",
            version="1.0",
            purpose="a due retry makes the guardian thread pick this run up",
            acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
            retry_policy=RetryPolicy(
                max_attempts=3,
                retryable_categories=[FailureCategory.MODEL_TIMEOUT],
                backoff_seconds=None,
            ),
        ),
    )
    lease = deps.workflow.acquire_lease(task.id.value)
    deps.workflow.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    assert deps.workflow.due_retry_task_ids(run_id) == (task.id.value,), "夹具必须先有到期重排"
    return deps, run_id


def _fail_the_compensation_write(deps: Any) -> None:
    """只打坏补偿的落库：第一次 save（续跑迁移）成功，之后的写全部失败。"""
    real = deps.runs_store.save_run
    writes = {"count": 0}

    def _save(run: ResearchRun) -> None:
        writes["count"] += 1
        if writes["count"] > 1:
            raise RuntimeError("store write down")
        real(run)

    deps.runs_store.save_run = _save


def _failed_resume(deps: Any) -> None:
    """续跑本身失败（本进程持有暂停上下文）：把流程推进补偿路径。"""
    deps.runs.has_paused_context = lambda run_id: True

    def _boom(run_id: str, run: ResearchRun) -> Any:
        raise RuntimeError("runtime exploded on resume")

    deps.runs.resume_paused = _boom


def _events(client: TestClient, run_id: str, event_type: str) -> list[dict[str, Any]]:
    events = client.get(f"/runs/{run_id}/events").json()
    return [item for item in events if item["type"] == event_type]


def test_a_failed_compensation_is_readable_on_the_event_chain(
    run_ready_client: TestClient,
) -> None:
    deps, run_id = _parked_run_with_a_due_retry(run_ready_client)
    _failed_resume(deps)
    _fail_the_compensation_write(deps)
    scheduler = RetryDispatchScheduler(
        RetryDispatchDeps(runs=deps.runs, runs_store=deps.runs_store, workflow=deps.workflow)
    )

    dispatched = scheduler._execute_pass()

    assert dispatched == 0, "补偿都没做成的 run 不算派发成功"
    attempts = _events(run_ready_client, run_id, "run.resume_failed")
    assert len(attempts) == 1, "先钉住：补偿真的被尝试过（否则下面的事件没有前提）"

    failures = _events(run_ready_client, run_id, _EVENT)
    assert len(failures) == 1, "补偿失败必须在读面留下一条痕迹"
    payload = failures[0]["payload"]
    assert payload["run_id"] == run_id
    assert payload["failure_type"] == "RuntimeError"
    assert payload["message"] == "store write down", "记的是**补偿**这次的失败"
    assert payload["canonical_state"] == ResearchRunState.State.RUNNING, (
        "如实回答补偿失败时 run 停在哪——不伪造成 PAUSED"
    )
    stored = deps.runs_store.get_run(run_id) if hasattr(deps.runs_store, "get_run") else None
    if stored is None:
        stored = next(run for run in deps.runs_store.list_runs() if run.id.value == run_id)
    assert stored.state == ResearchRunState.State.RUNNING, (
        "canonical 行没被这条失败事件改写（事件是痕迹，不是状态修正）"
    )


def test_a_compensation_that_could_be_recorded_leaves_no_failure_event(
    run_ready_client: TestClient,
) -> None:
    """反空洞：同样跑一轮，只把续跑打坏（补偿能落库）⇒ **没有**补偿失败事件。"""
    deps, run_id = _parked_run_with_a_due_retry(run_ready_client)
    _failed_resume(deps)
    scheduler = RetryDispatchScheduler(
        RetryDispatchDeps(runs=deps.runs, runs_store=deps.runs_store, workflow=deps.workflow)
    )

    assert scheduler._execute_pass() == 0

    assert _events(run_ready_client, run_id, _EVENT) == [], "补偿成功就不该有失败痕迹"
    stored = next(run for run in deps.runs_store.list_runs() if run.id.value == run_id)
    assert stored.state == ResearchRunState.State.PAUSED, "补偿成功 ⇒ 放回停车（既有语义）"
