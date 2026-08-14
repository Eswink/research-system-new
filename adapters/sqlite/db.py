"""SQLite 共享基础设施：连接工厂与 schema。

M7 持久化边界声明（docs/reliability/WORKFLOW_RELIABILITY.md）：
SQLite 提供单进程 ACID 与进程重启级持久化；PostgreSQL 是生产升级路径
（同一 Port 契约，无接口变更）；跨进程分布式调度属 Temporal 阶段。

本模块只使用标准库 sqlite3，不引入未 pin 依赖。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

# tasks：ResearchTask 持久化 + 取消标记 + 状态投影
# leases：TaskLease（at-least-once 投递去重）
# idempotency_records：operation_key → task 去重
# outbox_events：Transactional Outbox（event_id UNIQUE 幂等）
# artifacts：Artifact 元数据（内容存 blob 目录）
# leases：TaskLease（at-least-once 投递去重）
# idempotency_records：operation_key → task 去重
# outbox_events：Transactional Outbox（event_id UNIQUE 幂等）
# artifacts：Artifact 元数据（内容存 blob 目录）
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    idempotency_key TEXT,
    attempt INTEGER NOT NULL,
    status TEXT NOT NULL,
    assigned_agent_id TEXT,
    task_json TEXT NOT NULL,
    contract_json TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_run ON tasks(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_idem ON tasks(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS leases (
    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
    lease_id TEXT NOT NULL,
    agent_id TEXT,
    expires_at TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    operation_key TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_events (
    event_id TEXT PRIMARY KEY,
    envelope_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    digest TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    storage_uri TEXT,
    created_by TEXT,
    source_refs_json TEXT NOT NULL,
    classification TEXT,
    retention_policy TEXT,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect(db_path: str | Path, *, journal_mode: str = "WAL") -> sqlite3.Connection:
    """创建带 schema 的连接；`:memory:` 与文件路径均支持。"""
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA journal_mode={journal_mode}")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(SCHEMA_SQL)
    return connection


def now_iso(now: Callable[[], datetime] | None) -> str:
    """domain Timestamp 的 ISO 文本（UTC RFC3339）。"""
    value = datetime.now(timezone.utc) if now is None else now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(text: str) -> datetime:
    """ISO 文本 → timezone-aware datetime。"""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))
