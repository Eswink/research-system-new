"""GOAL-20261007-032 EC-02：`PgOutboxRelay` 的**取证判据**（`R26-5` 的追认）。

背景（`R26-5` 的事实更正）：GOAL-026 把 `R26-5` 登记为「应用级事件消费者不存在 ⇒
新建消费者 = 新能力」，但 2026-10-07 的建档实测显示 **relay 自 `ed2fa0e`（M14）起就在树，
且生产 PG 组合根默认启用**（`services/api/pg_composition.py` 设
`deps.outbox_relay_enabled = True`）。登记过期；**取证面**（relay 一轮真的投递并 mark、
崩溃语义、消费端按 `event_id` 去重、未启用组合根的如实登记）**从未有过专门判据** ——
本文件补的就是它。

四条（逐条对 GOAL-032 EC-02(c)）：

1. **一轮真的投递并 mark**：`run_once()` 把 pending 送给 sink **并**把事件标记为已发布
   （pending 归零 / sink 收到逐条 / 返回值 == 投递数）；空 outbox ⇒ 返回 0 且零投递；
2. **崩溃语义（at-least-once 实证）**：`publish` 后、`mark` 前崩溃 ⇒ **重新投递**
   （注入一个「投递后立刻抛错」的 sink ⇒ 本轮中断、事件仍未 mark；下一轮 drain 仍含它）；
3. **消费端按 `event_id` 去重**：重复投递不产生第二条事实（sink 按其契约幂等 ⇒ 已见 id
   不再计入交付）；数据层同判据 = `outbox_events` 主键 `event_id` 的唯一性 +
   publisher 的 `INSERT OR IGNORE`；
4. **未启用组合根如实登记**：SQLite 组合根的 `outbox_relay_enabled = False`
   ⇒ `_start_outbox_scheduler` 返回 None（**不假装有派发方**）；`/ops/schedules` 读面
   `executor_attached=False`（既有判据已钉，本文件只引用其符号面，不重复）。

**射程与诚实边界**：PG 判据标 `postgres`（DSN 不可达时 skip；`RESEARCHOS_REQUIRE_POSTGRES=1`
时 fail-closed）；**skip 不是 PASS**（本 GOAL 的台账口径）。「真实进程崩溃」由既有
`tools/probes/probe_outbox.py`（M14 一次性审计探针，场景 B/C/D）与
`tests/postgres/test_cross_process_real.py` 覆盖；本文件的崩溃语义是**注入式**
（在本进程内模拟「publish 后 mark 前」这一刻），**不是**真实进程 kill —— 这条边界
写在用例名与 docstring 里，不冒充更强结论。
"""

from __future__ import annotations

import os
import uuid
from dataclasses import replace
from typing import Any

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.outbox_relay import PgOutboxRelay
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.domain.events import EventEnvelope
from tests.contracts.fixtures import research_task, task_contract

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


def _truncate() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def _clean() -> None:
    _truncate()


class _RecordingSink:
    """消费端替身：**按 `event_id` 去重**（EventPublisher 契约；重复投递只计一次）。"""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self.delivered: list[EventEnvelope] = []
        self.duplicates: list[str] = []

    def publish(self, envelope: EventEnvelope) -> None:
        if envelope.event_id in self._seen:
            self.duplicates.append(envelope.event_id)
            return
        self._seen.add(envelope.event_id)
        self.delivered.append(envelope)


class _CrashAfterPublishSink(_RecordingSink):
    """**崩溃注入**：投递第一条后立刻抛错（模拟 publish 后、mark 前那一刻崩溃）。"""

    def __init__(self) -> None:
        super().__init__()
        self.crashed = False

    def publish(self, envelope: EventEnvelope) -> None:
        super().publish(envelope)
        if not self.crashed:
            self.crashed = True
            raise RuntimeError("injected crash after publish, before mark")


def _seed_events(count: int = 2) -> PostgresWorkflowEngine:
    """在 PG outbox 里造 `count` 条未投递事件（经**真实**业务路径）。

    每次用**唯一 idempotency_key / task_id**（共享夹具的 `research_task()` 用固定
    `idem-1` ⇒ 第二条会被 `submit` 幂等去重，拿不到第二条事件 —— 这正是本文件
    首版实测踩到的坑）。
    """
    engine = PostgresWorkflowEngine(dsn=_dsn())
    for _ in range(count):
        task = replace(
            research_task(task_id=str(uuid.uuid4())),
            idempotency_key=f"relay-forensics-{uuid.uuid4()}",
        )
        engine.submit(task, task_contract())
        engine.acquire_lease(task.id.value)
    return engine


def test_one_pass_delivers_pending_and_marks_them_published() -> None:
    """**判据 ①**：一轮真的把 pending 投递并 mark（含读数：before/after + 返回值）。"""
    engine = _seed_events(2)
    try:
        pending_before = len(engine.pending_outbox())
        assert pending_before == 2, f"前置：应有 2 条未投递（实测 {pending_before}）"
        sink = _RecordingSink()
        relay = PgOutboxRelay(engine, sink)

        published = relay.run_once()

        assert published == 2, f"一轮应投递全部 pending（实测 {published}）"
        assert len(sink.delivered) == 2, "sink 逐条收到"
        assert {e.event_id for e in sink.delivered} == {
            e.event_id for e in engine.pending_outbox()
        } | {e.event_id for e in sink.delivered}
        assert engine.pending_outbox() == (), "mark 之后 pending 归零"

        # 空 outbox ⇒ 一轮零投递（不空转成假读数）
        assert relay.run_once() == 0
        assert len(sink.delivered) == 2, "第二轮不得重复投递已 mark 的事件"
    finally:
        engine.close()


def test_crash_after_publish_before_mark_redelivers_next_pass() -> None:
    """**判据 ②（崩溃语义）**：publish 后 mark 前崩溃 ⇒ 事件**重新投递**（at-least-once）。

    注入式（非真实进程 kill）：第一条投递后抛错 ⇒ 本轮中断、**该条未 mark**；
    下一轮（正常 sink）必须再看到它 ⇒ 「至少一次」的最小实证。
    """
    engine = _seed_events(1)
    try:
        crash_sink = _CrashAfterPublishSink()
        relay = PgOutboxRelay(engine, crash_sink)

        with pytest.raises(RuntimeError):
            relay.run_once()

        assert len(crash_sink.delivered) == 1, "第一条确实被投递出去了（崩溃发生在投递之后）"
        still_pending = engine.pending_outbox()
        assert len(still_pending) == 1, "未 mark ⇒ 仍在 pending（这正是重投的来源）"

        replay_sink = _RecordingSink()
        assert PgOutboxRelay(engine, replay_sink).run_once() == 1
        assert [e.event_id for e in replay_sink.delivered] == [e.event_id for e in still_pending], (
            "重新投递的是**同一条**（event_id 逐字相同）"
        )
        assert engine.pending_outbox() == (), "这一轮才 mark"
    finally:
        engine.close()


def test_repeated_delivery_does_not_produce_a_second_fact() -> None:
    """**判据 ③（消费端去重）**：重复投递不产生第二条事实。

    两个臂：① **行为臂** —— 同一条事件投两次（手工放回 pending 再 relay）⇒
    按契约去重的 sink 只计一次交付、第二次进 `duplicates`；② **数据臂** ——
    `event_id` 是 `outbox_events` 主键（同 id 不会有两行）。
    """
    engine = _seed_events(1)
    try:
        (envelope,) = engine.pending_outbox()
        sink = _RecordingSink()
        relay = PgOutboxRelay(engine, sink)
        assert relay.run_once() == 1
        assert len(sink.delivered) == 1

        # 把同一条**放回** pending（模拟 at-least-once 的重复投递），再 relay 一轮
        _reset_published(envelope.event_id)
        assert relay.run_once() == 1, "重复投递确实发生了（relay 侧不隐藏它）"
        assert len(sink.delivered) == 1, "消费端按 event_id 去重 ⇒ 交付事实仍是一条"
        assert sink.duplicates == [envelope.event_id], "重复被消费者记录（不是静默丢弃）"

        # 数据臂：主键唯一 ⇒ 无第二行
        import psycopg

        conn = psycopg.connect(_dsn(), autocommit=True)
        row = conn.execute(
            "SELECT count(*) FROM outbox_events WHERE event_id = %s", (envelope.event_id,)
        ).fetchone()
        conn.close()
        assert row is not None and int(row[0]) == 1, "同一 event_id 只有一行（主键唯一）"
    finally:
        engine.close()


def _reset_published(event_id: str) -> None:
    """把一条事件的 `published_at` 清空（制造 at-least-once 的重复投递形态）。"""
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("UPDATE outbox_events SET published_at = NULL WHERE event_id = %s", (event_id,))
    conn.commit()
    conn.close()


def test_the_scheduler_wraps_the_same_relay_pass() -> None:
    """**实现面核实**：守护线程的 pass **就是** `PgOutboxRelay.run_once`
    （不建第二套执行路径；`_execute_pass` 只做 telemetry 包装）。
    """
    from services.api.scheduler import OutboxRelayScheduler

    engine = _seed_events(1)
    try:
        sink = _RecordingSink()
        sched = OutboxRelayScheduler(engine, sink, interval_seconds=5.0)
        outcome: Any = sched.run_once()
        assert outcome is None, "pass 无返回值（`_execute_pass` 的契约）"
        assert len(sink.delivered) == 1, "守护线程那一轮也真的投递了"
        assert engine.pending_outbox() == ()
    finally:
        engine.close()
