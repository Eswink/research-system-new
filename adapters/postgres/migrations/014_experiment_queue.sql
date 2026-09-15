-- 014_experiment_queue.sql — G14 experiment queue/scheduling (cycle 12)
-- ExperimentQueueEntry: one row per queued launch request. Claim-relevant facts
-- live in real columns (state / not_before / claimed_at) so the dispatcher can
-- claim atomically with FOR UPDATE SKIP LOCKED; the whole domain object stays in
-- entry_json (same convention as experiment_plans / experiment_runs). No FKs,
-- consistent with existing practice. Deterministic, transactional via
-- migration_version gate (db.migrate).

CREATE TABLE IF NOT EXISTS experiment_queue (
    entry_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    state TEXT NOT NULL,
    not_before TIMESTAMPTZ,
    claimed_at TIMESTAMPTZ,
    entry_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiment_queue_project ON experiment_queue(project_id);
CREATE INDEX IF NOT EXISTS idx_experiment_queue_state ON experiment_queue(state);
