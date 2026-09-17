"""Control Plane API 测试：续跑失败的补偿（GOAL-004 cycle 7 = EC-06）。

`resume_paused` 失败会把 run 留在**悬空 `RUNNING`**：既不会再被守护线程碰（它只派发
`PAUSED`），也不能再 `POST /resume`（`PAUSED → RUNNING` 迁移会 409）。本文件在 HTTP 边界
钉住补偿后的四件事：

1. 失败 ⇒ **run 行是 `PAUSED`**（不是 `RUNNING`），响应如实（`continuation=FAILED` +
   原因 + `dispatch=HELD`）；
2. 原因可从 **canonical 事实**读到：事件链里有 `run.resume_failed`（`failure_type` /
   `message` / `compensated_to`）；
3. **可重入**：把注入的失败撤掉再 resume ⇒ 真的续跑成功（不是把 run 钉死在停车态）；
4. 既有语义不变：没有暂停上下文时仍走重建路径（`continuation=NONE`/`REBUILT`），
   竞态（上下文已被取走）仍是既有回答。

失败注入用实例级替身（与既有测试同款手法）：**只替换执行侧**（`has_paused_context` /
`resume_paused`），补偿本身跑真实现（真迁移 + 真事件发布）。
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

_RUN_ID = "8d2f6a41-9c3b-4e57-b0a8-2f4d6c9e1b73"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _post(client: TestClient, path: str) -> Any:
    return client.post(path, headers={"Idempotency-Key": f"k-{uuid.uuid4()}"})


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


def _stored_state(deps: Any, run_id: str) -> str:
    """canonical run 行的状态（读 store，不读响应——响应可能只是"说得好听"）。"""
    row = deps.runs_store.get_run(run_id) if hasattr(deps.runs_store, "get_run") else None
    if row is None:
        row = next(run for run in deps.runs_store.list_runs() if run.id.value == run_id)
    return cast(str, row.state)


def _resume_events(client: TestClient, run_id: str) -> list[dict[str, Any]]:
    events = client.get(f"/runs/{run_id}/events").json()
    return [item for item in events if item["type"] == "run.resume_failed"]


def _fail_resume(deps: Any, message: str) -> None:
    """执行侧注入失败：本进程持有暂停上下文，但续跑抛错。"""
    deps.runs.has_paused_context = lambda run_id: True

    def _boom(run_id: str, run: ResearchRun) -> Any:
        raise RuntimeError(message)

    deps.runs.resume_paused = _boom


def test_a_failed_resume_is_compensated_and_the_reason_is_canonical(
    run_ready_client: TestClient,
) -> None:
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    _fail_resume(deps, "runtime exploded on resume")

    response = _post(run_ready_client, f"/runs/{run_id}/resume")

    assert response.status_code == 200
    body = response.json()
    assert body["continuation"] == "FAILED", "失败要如实说，不伪装成 RESUMED/NONE"
    assert body["dispatch"] == "HELD", "补偿回停车 ⇒ 派发闸门重新关上"
    assert body["state"] == ResearchRunState.State.PAUSED
    assert "runtime exploded on resume" in body["note"]
    assert _stored_state(deps, run_id) == ResearchRunState.State.PAUSED, (
        "canonical 行必须是 PAUSED——悬空 RUNNING 是这条 EC 要消灭的状态"
    )

    events = _resume_events(run_ready_client, run_id)
    assert len(events) == 1, "一次失败一条事件"
    payload = events[0]["payload"]
    assert payload["run_id"] == run_id
    assert payload["failure_type"] == "RuntimeError"
    assert payload["message"] == "runtime exploded on resume"
    assert payload["compensated_to"] == ResearchRunState.State.PAUSED


def test_the_compensated_run_is_not_bricked(run_ready_client: TestClient) -> None:
    """可重入：补偿后 run 回 PAUSED ⇒ 再 resume 不被 409 挡住，且真的续跑成功。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    _fail_resume(deps, "first attempt failed")
    assert _post(run_ready_client, f"/runs/{run_id}/resume").json()["continuation"] == "FAILED"

    deps.runs.resume_paused = lambda run_id, run: replace(run, state=ResearchRunState.State.RUNNING)
    second = _post(run_ready_client, f"/runs/{run_id}/resume")

    assert second.status_code == 200, "PAUSED ⇒ 第二次 resume 是合法迁移（悬空 RUNNING 才是死路）"
    body = second.json()
    assert body["continuation"] == "RESUMED"
    assert body["state"] == ResearchRunState.State.RUNNING
    assert _stored_state(deps, run_id) == ResearchRunState.State.RUNNING
    assert len(_resume_events(run_ready_client, run_id)) == 1, "重入成功不再记失败事件"


def test_without_a_paused_context_the_rebuild_path_is_unchanged(
    run_ready_client: TestClient,
) -> None:
    """既有语义不变：没有本进程上下文 ⇒ 走重建路径，失败不记 `run.resume_failed`。"""
    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    deps.runs.has_paused_context = lambda run_id: False

    body = _post(run_ready_client, f"/runs/{run_id}/resume").json()

    assert body["continuation"] in {"NONE", "REBUILT"}
    assert _resume_events(run_ready_client, run_id) == [], "重建被拒不是续跑失败补偿"


def test_a_consumed_context_race_keeps_its_existing_answer(run_ready_client: TestClient) -> None:
    """竞态（上下文已被另一次 resume 取走）仍是既有回答，不记失败事件。"""
    from packages.application.ports.errors import InvalidInputError

    deps, run_id = _inject_run(run_ready_client, ResearchRunState.State.PAUSED)
    deps.runs.has_paused_context = lambda run_id: True

    def _consumed(run_id: str, run: ResearchRun) -> Any:
        raise InvalidInputError("no paused execution context for run")

    deps.runs.resume_paused = _consumed

    body = _post(run_ready_client, f"/runs/{run_id}/resume").json()

    assert body["continuation"] == "NONE"
    assert "already consumed" in body["note"]
    assert _resume_events(run_ready_client, run_id) == [], "竞态不是失败，不该有补偿事件"
