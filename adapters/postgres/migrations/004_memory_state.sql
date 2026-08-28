-- 004_memory_state.sql — M14 DS-3 memory canonical state (WP-DS3)
-- PostgresMemoryStore backing table; mirrors adapters/sqlite/memory_store.py
-- _SCHEMA. Deterministic, transactional via migration_version gate (db.migrate).

CREATE TABLE IF NOT EXISTS m12_memory (
    id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    provenance TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    valid_from TIMESTAMPTZ,
    review_after TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    supersedes JSONB NOT NULL,
    contradictions JSONB NOT NULL,
    active BOOLEAN NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_m12_memory_tier ON m12_memory(tier) WHERE active;
