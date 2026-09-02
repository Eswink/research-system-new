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
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'AGENT_SESSION',
    partition INTEGER,
    required_capability TEXT,
    fence_seq INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tasks_run ON tasks(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_idem ON tasks(idempotency_key)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_claim ON tasks(kind, status, partition);

CREATE TABLE IF NOT EXISTS leases (
    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
    lease_id TEXT NOT NULL,
    agent_id TEXT,
    expires_at TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL,
    worker_id TEXT,
    fence INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    protocol_version TEXT NOT NULL,
    runtime_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    backend_kinds_json TEXT NOT NULL DEFAULT '[]',
    partition_slots_json TEXT NOT NULL DEFAULT '[]',
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    registration_generation INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'REGISTERING',
    last_heartbeat TEXT,
    drain_requested INTEGER NOT NULL DEFAULT 0,
    session_token_sha256 TEXT,
    gpu_observation_json TEXT,
    gpu_observed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_jobs (
    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
    spec_json TEXT NOT NULL,
    input_bundle_ref TEXT,
    input_bundle_digest TEXT,
    policy_fingerprint TEXT,
    output_bundle_ref TEXT,
    output_bundle_digest TEXT,
    worker_id TEXT,
    required_capability TEXT,
    partition INTEGER,
    exit_code INTEGER,
    stdout_digest TEXT,
    stderr_digest TEXT,
    failure_category TEXT,
    image_digest TEXT,
    gpu_elapsed_seconds INTEGER,
    peak_gpu_memory_bytes INTEGER,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
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


def _apply_journal_mode(connection: sqlite3.Connection, journal_mode: str) -> None:
    """Set the journal mode via a literal PRAGMA per allowed value.

    journal_mode is an internal, fixed vocabulary (never external input), but
    dispatching to a literal statement per value keeps the SQL text static and
    fails closed on an unknown mode (deep-scan baseline flagged the f-string).
    """
    if journal_mode == "WAL":
        connection.execute("PRAGMA journal_mode=WAL")
    elif journal_mode == "DELETE":
        connection.execute("PRAGMA journal_mode=DELETE")
    elif journal_mode == "TRUNCATE":
        connection.execute("PRAGMA journal_mode=TRUNCATE")
    elif journal_mode == "PERSIST":
        connection.execute("PRAGMA journal_mode=PERSIST")
    elif journal_mode == "MEMORY":
        connection.execute("PRAGMA journal_mode=MEMORY")
    elif journal_mode == "OFF":
        connection.execute("PRAGMA journal_mode=OFF")
    else:
        raise ValueError(f"unsupported journal_mode: {journal_mode!r}")


def connect(db_path: str | Path, *, journal_mode: str = "WAL") -> sqlite3.Connection:
    """创建带 schema 的连接；`:memory:` 与文件路径均支持。"""
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    _apply_journal_mode(connection, journal_mode)
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
