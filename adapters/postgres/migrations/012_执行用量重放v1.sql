-- Replaying a completed remote job must not bill the replay polling latency.
-- NULL means the older worker did not report execution wall duration.
ALTER TABLE execution_jobs ADD COLUMN IF NOT EXISTS execution_elapsed_seconds NUMERIC;
