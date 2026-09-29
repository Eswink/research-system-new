"""GOAL-026 EC-04（AC-1 / AC-2）：事务性发件箱的**失败注入**原子性与去重面。

既有判据（`tests/adapters/sqlite/test_workflow_engine.py::TestOutbox`、
`tests/postgres/test_outbox_pg.py::test_outbox_atomic_with_task_transition`）
**都只走全绿路径**：它们证明「成功时事件在」，**没有**证明「失败时事件不在」。
本文件补的就是失败注入这一向，并把两条写路径的**实测差异**钉成判据：

1. **引擎路径**（`OutboxWriter`，写调用方事务内）：事件写失败 ⇒ 同一提交块内的
   租约行 / 任务状态**一起回滚**（all-or-nothing）。故障用 SQLite **授权回调**
   注入（拒绝写 `outbox_events` 表），**不拼任何 SQL 文本**。
2. **发布器路径**（`SqliteOutboxEventPublisher`，`publish` **自提交**）：自提交之后，
   同一调用块内的后续失败**不会**把它回滚 —— 事件仍然可见。这是 PA-1 F7 的
   耐久性取舍的**代价**，本判据按**实测**钉住，不按注释钉。
3. **去重面**：同一 `event_id` 重复发布 ⇒ 只留一行，且保留**首次** envelope
   （防篡改）；`pending()` / `mark_published()` 的**投递边界**按行数逐条断言，
   并对受判面下界开口（`_MIN_PENDING_EVENTS`）。
4. **如实登记**：仓内**没有**按事件物化业务事实的应用消费者（发布器自己的
   docstring 就写着「投递/订阅属后续阶段」）⇒ 本文件只证到**存储面**的去重，
   消费端去重**未取证**（登记在 GOAL-026 的残余里）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.serialization import decode_envelope
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest
from packages.domain.core import ID, Timestamp
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

_OUTBOX_TABLE = "outbox_events"
_MIN_PENDING_EVENTS = 2


class _DenyOutboxWrites:
    """授权回调：命中写 `outbox_events` 就拒绝（故障注入，不涉及 SQL 文本）。"""

    def __init__(self) -> None:
        self.armed = False
        self.denied = 0

    def __call__(
        self, action: int, arg1: object, arg2: object, db_name: object, trigger: object
    ) -> int:
        if self.armed and action == sqlite3.SQLITE_INSERT and arg1 == _OUTBOX_TABLE:
            self.denied += 1
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


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
        id="ec04-atomicity",
        version="1.0",
        purpose="outbox atomicity",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )


def _envelope(event_id: str, marker: str) -> EventEnvelope:
    payload = {"marker": marker}
    return EventEnvelope(
        event_id=event_id,
        event_type=EventType.RUN_COMPLETED,
        schema_version="1",
        occurred_at=Timestamp.now(),
        actor="system:test",
        scope="run:ec04",
        payload=payload,
        payload_digest=digest_of_payload(payload),
        run_id="run-ec04",
    )


def _counts(conn: sqlite3.Connection) -> tuple[int, int, int]:
    """(outbox_events, leases, tasks) —— 三张表的行数。"""
    events = conn.execute("SELECT COUNT(*) FROM outbox_events").fetchone()[0]
    leases = conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0]
    tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    return int(events), int(leases), int(tasks)


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def test_event_write_failure_rolls_back_the_whole_claim(tmp_path: Path) -> None:
    """**失败注入**：outbox 写被拒 ⇒ 租约行与任务状态**一起回滚**（all-or-nothing）。

    故障注入在提交块的**最后一条语句**上（`persist_new_lease` 先写租约、再改任务、
    最后发事件）⇒ 业务事实已经写过，本判据问的是「它们有没有跟着回滚」。
    """
    fault = _DenyOutboxWrites()
    conn = connect(str(tmp_path / "atomic.db"))
    engine = SqliteWorkflowEngine(connection=conn)
    task = _task()
    engine.submit(task, _contract())
    conn.set_authorizer(fault)

    fault.armed = True
    with pytest.raises(sqlite3.DatabaseError):
        engine.claim_next(_request())
    fault.armed = False

    assert fault.denied == 1, "故障必须真的触发过（否则是空真）"
    assert _counts(conn) == (0, 0, 1), "事件写失败后不得留下租约行或事件行"
    assert _status(engine, task) == ResearchTaskState.State.QUEUED, "任务不得停在 LEASED"

    recovered = engine.claim_next(_request())
    assert recovered is not None, "回滚后必须还能重新 claim（失败的尝试不留毒）"
    assert _counts(conn) == (1, 1, 1), "重新 claim 后三件一起可见"
    conn.close()


def test_claim_without_fault_commits_event_lease_and_status_together(tmp_path: Path) -> None:
    """正控制：同一路径在无故障时**三件一起可见**（证明上一条不是「什么都不写」）。"""
    fault = _DenyOutboxWrites()
    conn = connect(str(tmp_path / "happy.db"))
    engine = SqliteWorkflowEngine(connection=conn)
    task = _task()
    engine.submit(task, _contract())
    conn.set_authorizer(fault)

    lease = engine.claim_next(_request())

    assert lease is not None, "受判面非空：claim 必须真的成功"
    assert fault.denied == 0
    assert _counts(conn) == (1, 1, 1), "成功路径的事件 / 租约 / 任务三件必须同时可见"
    assert _status(engine, task) == ResearchTaskState.State.LEASED
    conn.close()


def test_publisher_path_event_survives_a_later_failure_in_the_same_block(
    tmp_path: Path,
) -> None:
    """**实测**两条写路径的原子性不同：发布器自提交后，后续失败**不会**回滚它。

    这不是缺陷（PA-1 F7 的耐久性取舍），但**与该文件注释里的说法相反**：
    注释称「a later failure in the same caller-managed `with conn:` block」
    会连它一起回滚。本判据按实测钉住，防止把注释当契约（见 `MEM-170` 的同类教训）。
    """
    db = str(tmp_path / "publisher.db")
    conn = connect(db)
    publisher = SqliteOutboxEventPublisher(connection=conn)

    with pytest.raises(RuntimeError):
        with conn:
            publisher.publish(_envelope("env-1", "first"))
            raise RuntimeError("later failure in the same caller block")

    reader = connect(db)
    try:
        assert int(reader.execute("SELECT COUNT(*) FROM outbox_events").fetchone()[0]) == 1, (
            "自提交的事件在后续失败后仍然可见（实测语义）"
        )
    finally:
        reader.close()
        conn.close()


def test_repeat_publish_dedups_on_event_id_and_keeps_the_first_envelope(tmp_path: Path) -> None:
    """去重键 = `event_id`：重复发布只留**一行**，且内容是**首次**那份（防篡改）。"""
    db = str(tmp_path / "dedup.db")
    conn = connect(db)
    publisher = SqliteOutboxEventPublisher(connection=conn)

    publisher.publish(_envelope("env-dup", "first"))
    publisher.publish(_envelope("env-dup", "tampered"))

    rows = conn.execute("SELECT envelope_json FROM outbox_events").fetchall()
    assert len(rows) == 1, "同 event_id 重复发布只允许留一行"
    stored = decode_envelope(rows[0]["envelope_json"])
    assert stored.event_id == "env-dup"
    assert stored.payload == {"marker": "first"}, "已存在的事件不得被后来的内容顶掉"
    conn.close()


def test_pending_boundary_shrinks_by_exactly_the_published_ids(tmp_path: Path) -> None:
    """投递边界：`pending()` / `mark_published()` 逐条对账（含受判面**下界**）。"""
    db = str(tmp_path / "boundary.db")
    conn = connect(db)
    publisher = SqliteOutboxEventPublisher(connection=conn)
    for index in range(_MIN_PENDING_EVENTS + 1):
        publisher.publish(_envelope(f"env-{index}", f"m{index}"))

    pending = publisher.pending()
    assert len(pending) >= _MIN_PENDING_EVENTS, f"受判面过低（{len(pending)}）"
    ids = tuple(envelope.event_id for envelope in pending)

    publisher.mark_published((ids[0],))
    after = publisher.pending()
    assert [envelope.event_id for envelope in after] == list(ids[1:]), (
        "标记一条必须恰好减少一条，且减少的是那一条"
    )
    assert len(publisher.published) == len(ids), "总表不因标记而减少"

    publisher.mark_published((ids[0],))
    assert [envelope.event_id for envelope in publisher.pending()] == list(ids[1:]), "标记幂等"
    publisher.mark_published(())
    assert [envelope.event_id for envelope in publisher.pending()] == list(ids[1:]), "空集是 noop"
    conn.close()
