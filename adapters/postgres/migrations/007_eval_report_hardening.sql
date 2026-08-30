-- 007_eval_report_hardening.sql — M15 eval report integrity hardening
-- The report body remains canonical truth.  This additive migration closes the
-- verdict set, preserves reviewer-facility failures, and makes ingestion order
-- immutable without rewriting migrations already applied in production.

ALTER TABLE eval_reports
    ADD COLUMN IF NOT EXISTS rubric_digest TEXT;

ALTER TABLE eval_reports
    ADD COLUMN IF NOT EXISTS reviewer_failure_count INTEGER NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'eval_reports'::regclass
          AND conname = 'eval_reports_verdict_closed'
    ) THEN
        ALTER TABLE eval_reports
            ADD CONSTRAINT eval_reports_verdict_closed
            CHECK (verdict IN ('PASS', 'PASS_WITH_WARNINGS', 'REVISE', 'BLOCK'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'eval_reports'::regclass
          AND conname = 'eval_reports_pass_count_nonnegative'
    ) THEN
        ALTER TABLE eval_reports
            ADD CONSTRAINT eval_reports_pass_count_nonnegative
            CHECK (pass_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'eval_reports'::regclass
          AND conname = 'eval_reports_fail_count_nonnegative'
    ) THEN
        ALTER TABLE eval_reports
            ADD CONSTRAINT eval_reports_fail_count_nonnegative
            CHECK (fail_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'eval_reports'::regclass
          AND conname = 'eval_reports_infra_error_count_nonnegative'
    ) THEN
        ALTER TABLE eval_reports
            ADD CONSTRAINT eval_reports_infra_error_count_nonnegative
            CHECK (infra_error_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'eval_reports'::regclass
          AND conname = 'eval_reports_reviewer_failure_count_nonnegative'
    ) THEN
        ALTER TABLE eval_reports
            ADD CONSTRAINT eval_reports_reviewer_failure_count_nonnegative
            CHECK (reviewer_failure_count >= 0);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_eval_reports_latest
    ON eval_reports(recorded_at DESC, report_digest DESC);

CREATE OR REPLACE FUNCTION prevent_eval_report_recorded_at_rewrite()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.recorded_at IS DISTINCT FROM OLD.recorded_at THEN
        RAISE EXCEPTION 'eval_reports.recorded_at is immutable';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS eval_reports_recorded_at_immutable ON eval_reports;
CREATE TRIGGER eval_reports_recorded_at_immutable
BEFORE UPDATE OF recorded_at ON eval_reports
FOR EACH ROW
EXECUTE FUNCTION prevent_eval_report_recorded_at_rewrite();
