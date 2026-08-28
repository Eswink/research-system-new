-- 003_experiment_state.sql — M14 DS-1 experiment domain state (WP-DS1)
-- ExperimentPlan / ExperimentRun / ReproducibilityAudit; whole-object JSONB
-- rows (same convention as runs in 002_domain_state.sql); no FKs, consistent
-- with existing practice. Deterministic, transactional via migration_version
-- gate (db.migrate).

CREATE TABLE IF NOT EXISTS experiment_plans (
    plan_id TEXT PRIMARY KEY,
    plan_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    run_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiment_runs_plan ON experiment_runs(plan_id);

CREATE TABLE IF NOT EXISTS reproducibility_audits (
    experiment_run_id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    audit_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repro_audits_audit_id ON reproducibility_audits(audit_id);
