"""Research OS SQLite 持久化 adapter（M7 Reliable Vertical Slice；M12-R1 WP9 扩展）。

提供 WorkflowEngine / ArtifactStore / EventPublisher / EvidenceLedger /
MemoryStore 五个 Port 的 SQLite 持久化实现；只使用标准库 sqlite3，
不引入未 pin 依赖。

M12-R1：EvidenceLedger / MemoryStore 的 SQLite 实现落地后，M12 生产链
不再使用进程内 Fake（Fake 仅保留测试 fixture），跨进程重启证据可恢复；
PostgreSQL canonical state 仍属 M14。
"""

from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine

__all__ = [
    "SqliteArtifactStore",
    "SqliteEvidenceLedger",
    "SqliteMemoryStore",
    "SqliteOutboxEventPublisher",
    "SqliteWorkflowEngine",
]
