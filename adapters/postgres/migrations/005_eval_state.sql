-- 005_eval_state.sql — M15 WP3 eval report canonical state
-- EvalReportStore backing table; verbatim body 是 canonical truth,
-- 其余列是可重建的 derived index (rebuild-from-bodies 保证)。

CREATE TABLE IF NOT EXISTS eval_reports (
    report_digest TEXT PRIMARY KEY,
    body TEXT NOT NULL,
    comparison_digest TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    dataset_digest TEXT NOT NULL,
    gate_config_id TEXT NOT NULL,
    gate_config_version TEXT NOT NULL,
    gate_config_digest TEXT NOT NULL,
    scorer_versions JSONB NOT NULL,
    system_version TEXT NOT NULL,
    case_ids JSONB NOT NULL,
    evaluator_identities JSONB NOT NULL,
    verdict TEXT NOT NULL,
    pass_count INTEGER NOT NULL,
    fail_count INTEGER NOT NULL,
    infra_error_count INTEGER NOT NULL,
    usage_ref TEXT,
    cost_ref TEXT,
    run_id TEXT,
    recorded_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eval_reports_comparison ON eval_reports(comparison_digest, recorded_at);
CREATE INDEX IF NOT EXISTS idx_eval_reports_run ON eval_reports(run_id);
