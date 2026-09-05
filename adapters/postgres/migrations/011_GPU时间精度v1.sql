-- Keep legacy integer reports readable while preserving fractional GPU seconds.
-- Existing rows retain their numeric value. No claim of improved old precision.
ALTER TABLE execution_jobs
    ALTER COLUMN gpu_elapsed_seconds TYPE NUMERIC;
