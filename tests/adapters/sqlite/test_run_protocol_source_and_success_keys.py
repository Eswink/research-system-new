"""装配来源 durability + 任务身份读面（GOAL-003 cycle 20 / PLAN-20260915-083）。

重启后的续跑要能重建上下文，靠两个 durable 事实：

1. run 行记下**装配来源**（`protocol_source`，路径或草稿修订）——否则无从重建 plan；
2. 任务面能按 idempotency key 回答 canonical 任务身份与状态——否则重建出来的 specs
   既不知道哪些工作已完成（会重跑），也拿不到 canonical task id（引擎按 key 去重，
   新 id 根本 acquire 不到）。

本文件覆盖两个持久化语义：来源的往返与跨迁移保留、读面的判据与排序。
"""

from __future__ import annotations

from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, TaskKind
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

PATH_SOURCE = ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml")
DRAFT_SOURCE = ProtocolSource(draft_id="draft-9", draft_revision=4)
BODY = ProtocolBody.of("id: protocol-1\nversion: 1.0.0\nphases: []\n")


def _run(**kwargs: object) -> ResearchRun:
    base: dict[str, object] = {
        "id": ID.generate(),
        "project_id": "project-1",
        "protocol_id": "protocol-1",
    }
    base.update(kwargs)
    return ResearchRun(**base)  # type: ignore[arg-type]


def _task(run_id: ID, *, key: str) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=key,
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="success-key-contract",
        version="1.0",
        purpose="succeeded task keys are readable per run",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
    )


def test_a_recorded_source_survives_the_store_and_every_transition() -> None:
    """来源是 run 的冻结事实：落库往返一致，且跨状态迁移不被丢掉。"""
    store = SqliteRunStore(":memory:")
    run = _run(protocol_source=PATH_SOURCE)
    store.save_run(run)

    reloaded = store.get_run(run.id.value)

    assert reloaded.protocol_source == PATH_SOURCE
    moved = reloaded.transition(ResearchRunState.Transition.START_COMPILE)
    assert moved.protocol_source == PATH_SOURCE, "逐字段复制必须包含来源"
    store.close()


def test_a_draft_source_round_trips_and_a_legacy_row_stays_empty() -> None:
    """草稿来源同样往返；早于来源登记的旧行显式留空（不猜、不伪造）。"""
    store = SqliteRunStore(":memory:")
    draft = _run(protocol_source=DRAFT_SOURCE)
    legacy = _run()
    store.save_run(draft)
    store.save_run(legacy)

    assert store.get_run(draft.id.value).protocol_source == DRAFT_SOURCE
    assert store.get_run(legacy.id.value).protocol_source is None
    store.close()


def test_the_frozen_body_round_trips_and_a_legacy_row_stays_empty() -> None:
    """冻结正文（GOAL-004 cycle 1）：落库往返一致、跨状态迁移不丢，旧行留空。"""
    store = SqliteRunStore(":memory:")
    frozen = _run(protocol_source=PATH_SOURCE, protocol_body=BODY)
    legacy = _run()
    store.save_run(frozen)
    store.save_run(legacy)

    reloaded = store.get_run(frozen.id.value)
    assert reloaded.protocol_body == BODY, "正文与 digest 都要往返一致"
    moved = reloaded.transition(ResearchRunState.Transition.START_COMPILE)
    assert moved.protocol_body == BODY, "逐字段复制必须包含冻结正文"
    assert store.get_run(legacy.id.value).protocol_body is None
    store.close()


def test_task_identities_answer_the_stable_identity_and_status() -> None:
    """读面按 idempotency key 回答 (key, task_id, status)：重启续跑靠它对回 canonical 任务。"""
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60)
    run_id = ID.generate()
    done_key = f"{run_id.value}:phase-a:agent-1"
    cancelled_key = f"{run_id.value}:phase-b:agent-1"
    done = _task(run_id, key=done_key)
    cancelled = _task(run_id, key=cancelled_key)
    engine.submit(done, _contract())
    engine.submit(cancelled, _contract())
    lease = engine.acquire_lease(done.id.value)
    engine.complete(lease, TaskCompletion(task_id=done.id.value, outcome="SUCCEEDED"))
    engine.cancel(cancelled.id.value)

    identities = engine.task_identities(run_id.value)

    assert [(item.idempotency_key, item.task_id, item.status) for item in identities] == [
        (done_key, done.id.value, ResearchTaskState.State.SUCCEEDED),
        (cancelled_key, cancelled.id.value, ResearchTaskState.State.CANCELLED),
    ]
    assert engine.task_identities(ID.generate().value) == (), "未知 run 恒空"
    engine.close()
