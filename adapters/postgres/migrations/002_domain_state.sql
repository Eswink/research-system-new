-- 002_domain_state.sql — M14 PG domain stores (WP-F1)
-- Runs / EvidenceLedger (m12_*) / BudgetLedger / Approvals
-- Artifacts table already in 001_initial.sql; no change.
-- Deterministic, transactional via migration_version gate (db.migrate).

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    run_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project_id);

CREATE TABLE IF NOT EXISTS m12_sources (
    origin TEXT PRIMARY KEY,
    content_digest TEXT NOT NULL,
    trust_label TEXT NOT NULL,
    access_time TIMESTAMPTZ,
    license_terms TEXT,
    authors JSONB NOT NULL,
    parser_version TEXT
);

CREATE TABLE IF NOT EXISTS m12_evidence (
    id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    extracted_by TEXT,
    captured_at TIMESTAMPTZ,
    artifact_id TEXT,
    run_id TEXT,
    experiment_run_id TEXT,
    metric_refs JSONB NOT NULL,
    workspace_snapshot_before TEXT,
    workspace_snapshot_after TEXT,
    image_digest TEXT,
    environment_digest TEXT,
    tool_refs JSONB NOT NULL,
    skill_refs JSONB NOT NULL,
    model_refs JSONB NOT NULL,
    manifest_digest TEXT
);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON m12_evidence(source_ref);

CREATE TABLE IF NOT EXISTS m12_claims (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    status TEXT NOT NULL,
    author TEXT,
    evidence_relations JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS m12_relations (
    claim_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    strength DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (claim_id, evidence_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_relations_evidence ON m12_relations(evidence_id);

CREATE TABLE IF NOT EXISTS budget_reservations (
    reservation_ref TEXT PRIMARY KEY,
    reservations_json JSONB NOT NULL,
    policy_json JSONB NOT NULL,
    released BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS budget_usage_entries (
    entry_id TEXT PRIMARY KEY,
    entry_json JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    approval_json JSONB NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approvals_run ON approvals(run_id);
