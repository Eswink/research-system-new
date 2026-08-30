-- 006_pricing_snapshot.sql — M15 WP3a 定价快照 canonical state
-- PricingSnapshotStore backing table;(version, digest) 可寻址,
-- append-only:digest 是内容摘要,同键必同内容,改价产生新 (version, digest)
-- 对而历史快照保留——已冻结 run 的历史投影不可被改价改写(BLOCKER-6)。

CREATE TABLE IF NOT EXISTS pricing_snapshots (
    version TEXT NOT NULL,
    digest TEXT NOT NULL,
    table_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (version, digest)
);
