"""GOAL-20261008-033 EC-01 判据：**死信人工恢复的*产品*入口**。

**它补的是什么**：ADR-0033 把「人工恢复一条死信任务」做成 Port 上的一等能力
（`WorkflowEngine.requeue`），GOAL-032 把它在**引擎面**判到成立。但产品面**没有入口**：
建档实测 `services/` 内 `requeue` / `DEAD_LETTER` 零命中、无 HTTP 路由、`engine.requeue`
的调用方全部在 `tests/` 下。运维要恢复一条死信只能进 REPL 或改库 —— 本文件把
`POST /tasks/{task_id}/retry` 这个**产品路径**钉住。

六件事（对应 EC-01 (b)~(e)）：

1. **成功路径 + 调用证据**：端点恢复一条死信 ⇒ 任务面真的回 `QUEUED` 且**可再交付**
   （`acquire_lease` 成功）。**不是**只断言「返回 200」——「注册了 / 返回成功」不算数，
   下游消费证据才算（GOAL-032 的纪律）。
2. **三类点名拒绝**：不存在 ⇒ 404 / 状态不符（含「已恢复」）⇒ 409 / 未装配 ⇒ 503，
   三者消息各自点名任务 id 与原因；**不得**静默。
3. **幂等第一层（控制面）**：同 `Idempotency-Key` + 同 payload 重放 ⇒ 复用首次响应，
   且**不第二次触达引擎**（以任务面事件计数为判据 —— 计数取样在重放**之前**，
   承 GOAL-026 EC-03 的假绿教训）。
4. **幂等第二层（引擎侧）**：**新** key 打在**已恢复**的任务上 ⇒ 409 点名拒绝
   （`only DEAD_LETTER can be requeued`），事件计数不增、状态不变。
5. **端点真的走 Port**：断言产品调用方存在（`services/api/routers/tasks.py` 调用
   `requeue`）且**不建第二套**（该文件不出现状态机迁移调用 / 不写任务行）。
6. **认证面自动覆盖**：端点落在写面保护面内 —— 由既有对抗性判据的**代码枚举面**判
   （本文件只断言「它没被排除在枚举口径外」，即路径出现在 app 的 OpenAPI 里且方法是 POST）。

**射程边界（如实登记）**：本文件判**产品入口**；引擎面的三实现同判由
`tests/contracts/test_dead_letter_manual_recovery_contract.py` 判，恢复后的**整条回环**
（恢复到跑完）由 `tests/e2e/test_dead_letter_recovery_full_loop.py` 判 —— 本文件不重复。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract
from services.api.app import create_app
from services.api.composition import ApiDeps
from tests.api.run_fixtures import make_run_ready_deps

_RETRY_PATH = "/tasks/{task_id}/retry"


@pytest.fixture
def deps() -> ApiDeps:
    return make_run_ready_deps()


@pytest.fixture
def client(deps: ApiDeps) -> Iterator[TestClient]:
    with TestClient(create_app(deps)) as test_client:
        yield test_client


def _engine(deps: ApiDeps) -> SqliteWorkflowEngine:
    engine = deps.workflow
    assert isinstance(engine, SqliteWorkflowEngine), "本判据要求真实 SQLite workflow 面"
    return engine


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="task-retry-contract",
        version="1.0",
        purpose="product entry for dead-letter recovery",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=1, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )


def _dead_letter(deps: ApiDeps) -> ResearchTask:
    """造一条真死信：`max_attempts=1` + 可重试失败 ⇒ `decide_failure` 落死信。

    走**引擎的真实完成路径**（submit → acquire → complete(FAILED)），不是直接把状态写死：
    「这条任务是死信」因此是引擎判定出来的，不是判据自己摆出来的。
    """
    engine = _engine(deps)
    task = _task()
    engine.submit(task, _contract())
    lease = engine.acquire_lease(task.id.value)
    from packages.application.ports.workflow_engine import TaskCompletion

    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    return task


def _status_of(engine: SqliteWorkflowEngine, run_id: str, task_id: str) -> str:
    return next(
        row.task.status for row in engine.list_tasks(run_id) if row.task.id.value == task_id
    )


def _requeue_events(engine: SqliteWorkflowEngine) -> list[dict[str, Any]]:
    """本 run 的 `task.retry_scheduled` 事件 payload（幂等计数取样面）。"""
    return [
        dict(envelope.payload)
        for envelope in engine.pending_outbox()
        if envelope.event_type == EventType.TASK_RETRY_SCHEDULED
    ]


def _post_retry(client: TestClient, task_id: str, key: str) -> Any:
    return client.post(_RETRY_PATH.format(task_id=task_id), headers={"Idempotency-Key": key})


class TestTheEndpointRecoversADeadLetter:
    def test_a_dead_letter_is_requeued_and_becomes_deliverable_again(
        self, client: TestClient, deps: ApiDeps
    ) -> None:
        """**主判据（成功路径 + 下游消费证据）**。

        三件读数缺一不可：① 端点返回引擎的权威结论；② 任务面真的回 `QUEUED`；
        ③ **它能被再次交付**（`acquire_lease` 不再被终态守卫拒绝）—— 第 ③ 条才是
        「恢复在产品上真的成立」，只断言 ① 与 ② 会漏掉「状态写回了但自动路径仍不认它」。
        """
        engine = _engine(deps)
        task = _dead_letter(deps)
        assert _status_of(engine, task.run_id.value, task.id.value) == (
            ResearchTaskState.State.DEAD_LETTER
        ), "前置：这条任务真的进了死信"

        response = _post_retry(client, task.id.value, "goal033-ec01-happy")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["task_id"] == task.id.value
        assert body["result"] == "restored", "端点带回引擎的权威结论，不另造词表"
        assert body["note"], "响应必须说明这次动作能做什么、不能做什么"

        assert _status_of(engine, task.run_id.value, task.id.value) == (
            ResearchTaskState.State.QUEUED
        ), "② 任务面回到可交付面"

        lease = engine.acquire_lease(task.id.value)
        assert lease.task_id == task.id.value, "③ 恢复后**真的可再交付**（自动路径不再拒绝它）"

    def test_the_endpoint_calls_the_port_instead_of_reimplementing_recovery(
        self, deps: ApiDeps, client: TestClient
    ) -> None:
        """**调用证据 + 不建第二套**：路由模块调用 `requeue`，且**不**自己迁移状态。

        结构性断言（读源码）与行为断言（真的恢复成功了）配对：只看行为会漏掉「路由顺手
        再写一遍状态机」这种旁路，只看源码会漏掉「那段代码根本不可达」。
        """
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[2] / "services" / "api" / "routers" / "tasks.py"
        ).read_text(encoding="utf-8")
        assert ".requeue(" in source, "产品路径必须调用既有 Port，而不是自己实现恢复"
        assert "ResearchTaskState.transition" not in source, (
            "路由不得自行迁移状态（那会变成第二套恢复逻辑，绕过 domain 状态机）"
        )
        assert "UPDATE tasks" not in source.upper(), "路由不得直接写任务行"


class TestRefusalsAreNamedNotSilent:
    def test_an_unknown_task_is_a_404_that_names_it(self, client: TestClient) -> None:
        ghost = ID.generate().value
        response = _post_retry(client, ghost, "goal033-ec01-ghost")
        assert response.status_code == 404, response.text
        assert ghost in response.text, "404 必须点名任务 id（点名失败而非静默）"

    def test_a_task_that_is_not_dead_letter_is_a_409_that_names_it(
        self, client: TestClient, deps: ApiDeps
    ) -> None:
        """非死信起态（`QUEUED`）⇒ 409 且点名 id 与实际状态。"""
        engine = _engine(deps)
        task = _task()
        engine.submit(task, _contract())

        response = _post_retry(client, task.id.value, "goal033-ec01-not-dead")
        assert response.status_code == 409, response.text
        assert task.id.value in response.text
        assert ResearchTaskState.State.QUEUED in response.text, "409 必须点名实际状态"

    def test_the_response_status_splits_unknown_from_wrong_state(
        self, client: TestClient, deps: ApiDeps
    ) -> None:
        """两类拒绝**不同码**：否则调用方分不清「打错了」与「打晚了」。"""
        ghost = ID.generate().value
        unknown = _post_retry(client, ghost, "goal033-ec01-split-a")

        engine = _engine(deps)
        task = _task()
        engine.submit(task, _contract())
        wrong_state = _post_retry(client, task.id.value, "goal033-ec01-split-b")

        assert (unknown.status_code, wrong_state.status_code) == (404, 409), (
            "「任务不存在」与「状态不符」必须可区分",
            unknown.status_code,
            wrong_state.status_code,
        )

    def test_an_unassembled_workflow_face_is_a_503(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """workflow 面缺席 ⇒ 503（不伪造成功，也不退化成 404 说"任务不存在"）。"""
        deps = make_run_ready_deps()
        monkeypatch.setattr(deps, "workflow", None)
        with TestClient(create_app(deps)) as client:
            response = _post_retry(client, ID.generate().value, "goal033-ec01-no-face")
        assert response.status_code == 503, response.text
        assert "workflow" in response.text.lower()


class TestRecoveryIsIdempotentOnBothLayers:
    def test_a_replayed_idempotency_key_does_not_touch_the_engine_twice(
        self, client: TestClient, deps: ApiDeps
    ) -> None:
        """**幂等第一层**：同 key 重放复用首次响应，**不**第二次触达引擎。

        判据是**事件计数**而不是状态串：状态在一次恢复之后就不再变化（第二次也被拒），
        所以只看状态会假绿。计数取样必须在重放**之前**（承 GOAL-026 EC-03 的教训）。
        """
        engine = _engine(deps)
        task = _dead_letter(deps)
        before = len(_requeue_events(engine))

        first = _post_retry(client, task.id.value, "goal033-ec01-replay")
        assert first.status_code == 200, first.text
        events_after_first = len(_requeue_events(engine))
        assert events_after_first == before + 1, "首次恢复写入恰好一条恢复事件"

        replay = _post_retry(client, task.id.value, "goal033-ec01-replay")
        assert replay.status_code == first.status_code, "同 key 重放必须复用首次响应"
        assert replay.json() == first.json(), "重放内容与首次一致（控制面承诺）"
        assert len(_requeue_events(engine)) == events_after_first, (
            "重放**不得**第二次触达引擎（事件计数不增）"
        )

    def test_a_new_key_on_an_already_recovered_task_is_refused_by_name(
        self, client: TestClient, deps: ApiDeps
    ) -> None:
        """**幂等第二层**：新 key 打在已恢复的任务上 ⇒ 409 点名拒绝，零新副作用。"""
        engine = _engine(deps)
        task = _dead_letter(deps)

        assert _post_retry(client, task.id.value, "goal033-ec01-first").status_code == 200
        events_after_first = len(_requeue_events(engine))
        status_after_first = _status_of(engine, task.run_id.value, task.id.value)

        second = _post_retry(client, task.id.value, "goal033-ec01-second")
        assert second.status_code == 409, second.text
        assert task.id.value in second.text and "only DEAD_LETTER" in second.text
        assert len(_requeue_events(engine)) == events_after_first, "不得产生第二次副作用"
        assert _status_of(engine, task.run_id.value, task.id.value) == status_after_first


class TestTheEndpointIsInsideTheWriteFaceProtection:
    def test_the_route_is_enumerable_from_the_app(self, client: TestClient) -> None:
        """端点进入 app 的 OpenAPI 且是写方法 ⇒ 既有对抗性判据的枚举面**自动**覆盖它。

        本断言只证明「它没被藏在枚举口径之外」：保护面的定义是方法分类
        （`_MUTATING_METHODS`），而枚举来自 `app.openapi()` —— 两件事都不在路径清单上，
        所以新端点无需登记就落在保护面内。真正的 401 断言由
        `tests/api/test_write_face_cannot_be_bypassed.py` 覆盖全部写面端点（含本条）。
        """
        from services.api.middleware import _MUTATING_METHODS

        spec = client.app.openapi()  # type: ignore[attr-defined]
        path = "/tasks/{task_id}/retry"
        assert path in spec["paths"], f"端点不在 OpenAPI 里：{sorted(spec['paths'])}"
        assert "post" in spec["paths"][path], "恢复动作是写方法"
        assert "POST" in _MUTATING_METHODS, "写面分类必须包含 POST（保护面由此推出）"
