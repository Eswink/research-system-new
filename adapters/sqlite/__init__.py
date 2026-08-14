"""Research OS SQLite 持久化 adapter（M7 Reliable Vertical Slice）。

提供 WorkflowEngine / ArtifactStore / EventPublisher 三个 Port 的
SQLite 持久化实现；只使用标准库 sqlite3，不引入未 pin 依赖。
"""

from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine

__all__ = [
    "SqliteArtifactStore",
    "SqliteOutboxEventPublisher",
    "SqliteWorkflowEngine",
]
