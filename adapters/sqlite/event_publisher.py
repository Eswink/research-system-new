"""SqliteOutboxEventPublisher：EventPublisher Port 的 Transactional Outbox 实现。

publish 按 event_id 幂等（UNIQUE 约束 + INSERT OR IGNORE），重复发布
保留首次 envelope（防篡改，EVENT_MODEL.md §3）。
outbox_events 表与 SqliteWorkflowEngine 共享：业务状态变更与事件写入
在同一连接事务中完成（Transactional Outbox 语义）；relay 由
pending()/mark_published() 提供，Consumer 按 event_id 去重。

边界声明：本实现是持久化 outbox，不是消息总线；投递/订阅属后续阶段。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from adapters.sqlite.serialization import decode_envelope, encode_envelope
from packages.application.ports.errors import InvalidInputError
from packages.domain.events import EventEnvelope


class SqliteOutboxEventPublisher(SqliteAdapterBase):
    """SQLite 持久化 EventPublisher；event_id 幂等。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("event_publisher")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def publish(self, envelope: EventEnvelope) -> None:
        self._ensure_open()
        if not envelope.event_id:
            self._record("publish", "", error="InvalidInputError")
            raise InvalidInputError("event_id must not be empty")
        # PA-1 F7: durability + cross-connection visibility. Without this the
        # event INSERT rode the shared connection's implicit transaction until
        # some unrelated store happened to commit — a crash lost the event, and
        # a second connection (API restart) could not read it. Every sibling
        # sqlite store self-commits on each write (`with self._conn:` across
        # the whole tree), so self-commit here matches the established
        # semantics — including rolling back together with other writes when a
        # LATER operation in the same caller-managed `with conn:` block fails
        # (conn-level rollback is all-or-nothing; nothing in the tree relies
        # on deferred visibility of outbox events).
        with self._conn:
            cursor = self._conn.execute(
                "INSERT OR IGNORE INTO outbox_events (event_id, envelope_json, created_at)"
                " VALUES (?, ?, ?)",
                (envelope.event_id, encode_envelope(envelope), now_iso(None)),
            )
        result = "published" if cursor.rowcount > 0 else "deduped"
        self._record("publish", envelope.event_id, result=result)

    @property
    def published(self) -> tuple[EventEnvelope, ...]:
        """outbox 内全部事件（含 workflow engine 事务写入），按创建顺序。"""
        rows = self._conn.execute(
            "SELECT envelope_json FROM outbox_events ORDER BY created_at, event_id"
        ).fetchall()
        return tuple(decode_envelope(row["envelope_json"]) for row in rows)

    def pending(self) -> tuple[EventEnvelope, ...]:
        """未投递事件（relay 轮询视图）。"""
        rows = self._conn.execute(
            "SELECT envelope_json FROM outbox_events WHERE published_at IS NULL"
            " ORDER BY created_at, event_id"
        ).fetchall()
        return tuple(decode_envelope(row["envelope_json"]) for row in rows)

    def mark_published(self, event_ids: tuple[str, ...]) -> None:
        """标记事件已投递（幂等）。"""
        if not event_ids:
            return
        with self._conn:
            for event_id in event_ids:
                self._conn.execute(
                    "UPDATE outbox_events SET published_at = ? WHERE event_id = ?",
                    (now_iso(None), event_id),
                )
