"""NotificationReadStore Port：通知已读状态（WP-G）。

事件本体是唯一真相（outbox）；已读只是每事件的 view-state 标记，
不构成第二套事实源；SQLite 控制面存储（用户视图状态，非研究 canonical
state，与 endpoint/agent 配置存储同侧）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NotificationReadStore(Protocol):
    def mark_read(self, event_id: str) -> None: ...

    def read_event_ids(self) -> frozenset[str]: ...

    def close(self) -> None: ...
