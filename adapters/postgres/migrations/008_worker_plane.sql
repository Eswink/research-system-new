-- 008_worker_plane.sql — M16 distributed execution plane (WP1)
-- Additive + idempotent. Establishes the worker registry table and the
-- scheduling/fencing columns on the existing single queue/lease kernel.
-- No second queue or lease table: execution jobs reuse `tasks` (kind column)
-- plus a typed `execution_jobs` payload projection (same pattern as
-- experiment_plans). PostgreSQL remains the sole canonical authority.

-- Worker registry: Control Plane's view of each worker's lifecycle.
-- Bounded identity fields only (no hardware inventory; resource plane is M17).
CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    protocol_version TEXT NOT NULL,
    runtime_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    capabilities_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    backend_kinds_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    partition_slots_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    registration_generation INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'REGISTERING',
    last_heartbeat TIMESTAMPTZ,
    drain_requested BOOLEAN NOT NULL DEFAULT FALSE,
    -- session token is stored ONLY as a sha256 hex digest (never plaintext);
    -- NULL until the gateway issues a session token after handshake.
    session_token_sha256 TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workers_state ON workers(state);
CREATE INDEX IF NOT EXISTS idx_workers_heartbeat ON workers(last_heartbeat);

-- Single-queue scheduling columns on the existing tasks table.
-- kind defaults to AGENT_SESSION so all pre-M16 rows/tasks are unaffected and
-- are never claimable by remote workers.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'AGENT_SESSION';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS partition SMALLINT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS required_capability TEXT;
-- fence_seq: monotonic generation counter; incremented on each (re)claim and
-- copied into leases.fence. lease_id rotation (M14) is unchanged.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS fence_seq BIGINT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_tasks_claim
    ON tasks(kind, status, partition)
    WHERE cancelled = FALSE;

-- Leases gain worker identity + auditable fence (defaults keep M14 semantics).
ALTER TABLE leases ADD COLUMN IF NOT EXISTS worker_id TEXT;
ALTER TABLE leases ADD COLUMN IF NOT EXISTS fence BIGINT NOT NULL DEFAULT 0;

-- Typed payload projection for EXECUTION jobs (NOT a second queue):
-- one row per execution task, keyed by the same task_id.
CREATE TABLE IF NOT EXISTS execution_jobs (
    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE CASCADE,
    spec_json JSONB NOT NULL,
    input_bundle_ref TEXT,
    input_bundle_digest TEXT,
    policy_fingerprint TEXT,
    output_bundle_ref TEXT,
    output_bundle_digest TEXT,
    worker_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
