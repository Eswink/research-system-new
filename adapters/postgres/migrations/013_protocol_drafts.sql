-- Protocol drafts (PLAN-20260908-033): drafts + immutable revisions.
-- Revisions are append-only; (draft_id, revision) primary key enforces
-- uniqueness; idempotency key unique index prevents duplicate revisions
-- on client retry. Backward compatible: additive tables only.

CREATE TABLE IF NOT EXISTS protocol_drafts (
    draft_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_idempotency_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS protocol_draft_revisions (
    draft_id TEXT NOT NULL REFERENCES protocol_drafts(draft_id),
    revision INTEGER NOT NULL,
    yaml_text TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (draft_id, revision)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_protocol_draft_idem
    ON protocol_draft_revisions(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_protocol_drafts_project
    ON protocol_drafts(project_id, created_at DESC);
