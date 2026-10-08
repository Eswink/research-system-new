"""dev 路径的配置/注册面 store 装配（从 `composition.py` 原样搬出，控制 450 行上限）。

PG canonical 仍是研究数据真相；store=None → 诚实 503 的边界保持。
"""

from __future__ import annotations

import sqlite3
from typing import Any

from adapters.sqlite.agent_store import SqliteAgentStore
from adapters.sqlite.catalog_override_store import SqliteCatalogOverrideStore
from adapters.sqlite.experiment_store import SqliteExperimentStore
from adapters.sqlite.library_store import SqliteLibraryStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.sqlite.notification_read_store import SqliteNotificationReadStore
from adapters.sqlite.ops_store import SqliteOpsStore
from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
from adapters.sqlite.project_store import SqliteProjectStore
from adapters.sqlite.schedule_store import SqliteScheduleStore
from adapters.sqlite.tool_pack_store import SqliteToolPackStore
from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
from adapters.sqlite.worker_registry import SqliteWorkerRegistry


def config_store_parts(connection: sqlite3.Connection) -> dict[str, Any]:
    """dev 路径配置/注册面 store（PLAN-040 WP-A / PLAN-041 WP-A）。

    PLAN-066（EC-03）：`schedule_registry` 与 `schedule_store` 一起装配——守护线程与 HTTP
    写面必须共用同一个实例，否则 `trigger` 找不到执行体。
    """
    from services.api.schedule_support import build_registry

    schedule_store = SqliteScheduleStore(connection=connection)
    return {
        "agent_store": SqliteAgentStore(connection=connection),
        "catalog_overrides": SqliteCatalogOverrideStore(connection=connection),
        "project_settings_store": SqliteProjectSettingsStore(connection=connection),
        "project_store": SqliteProjectStore(connection=connection),
        "notification_reads": SqliteNotificationReadStore(connection=connection),
        "library_store": SqliteLibraryStore(connection=connection),
        "memory": SqliteMemoryStore(connection=connection),
        "experiment_store": SqliteExperimentStore(connection=connection),
        "ops_store": SqliteOpsStore(connection=connection),
        "tool_provider_registry": SqliteToolProviderRegistry(connection=connection),
        "tool_pack_store": SqliteToolPackStore(connection=connection),
        "worker_registry": SqliteWorkerRegistry(connection=connection),
        "schedule_store": schedule_store,
        "schedule_registry": build_registry(schedule_store),
    }


__all__ = ["config_store_parts"]
