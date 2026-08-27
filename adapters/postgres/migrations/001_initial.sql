-- 001_initial.sql — M14 PostgreSQL canonical state (WP1)
-- Deterministic, transactional, idempotent via migration_version gate.
-- Mirrors adapters/sqlite/db.py SCHEMA_SQL with Postgres strict types.

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    idempotency_key TEXT,
    attempt INTEGER NOT NULL,
    status TEXT NOT NULL,
    assigned_agent_id TEXT,
    task_json JSONB NOT NULL,
    contract_json JSONB NOT NULL,
    cancelled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_run ON tasks(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_idem ON tasks(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS leases (
    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE CASCADE,
    lease_id TEXT NOT NULL,
    agent_id TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    heartbeat_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leases_expires ON leases(expires_at);

CREATE TABLE IF NOT EXISTS idempotency_records (
    operation_key TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_events (
    event_id TEXT PRIMARY KEY,
    envelope_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    published_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_outbox_pending ON outbox_events(published_at)
    WHERE published_at IS NULL;

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    digest TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    storage_uri TEXT,
    created_by TEXT,
    source_refs_json JSONB NOT NULL,
    classification TEXT,
    retention_policy TEXT,
    state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS migration_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL
);
