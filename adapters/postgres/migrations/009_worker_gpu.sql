-- 009_worker_gpu.sql — M17 GPU capability observation (WP1)
-- Additive + idempotent. WorkerGpuObservation is a bounded observed-fact
-- blob on the existing workers registry row — NOT a hardware inventory and
-- NOT a second truth source: registration upsert (generation+1) replaces the
-- observation wholesale (freshness layer 1), the gateway TTL gate reads
-- gpu_observed_at (server clock; freshness layer 2).
-- nvidia-smi raw text never enters canonical state.

ALTER TABLE workers ADD COLUMN IF NOT EXISTS gpu_observation_json JSONB;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS gpu_observed_at TIMESTAMPTZ;

-- M17: the worker's DockerExecutionBackend resolves the actual image digest it
-- ran; propagating it back through the result binds remote reproducibility
-- (the local backend already carries it in compute_usage_summary).
ALTER TABLE execution_jobs ADD COLUMN IF NOT EXISTS image_digest TEXT;
ALTER TABLE execution_jobs ADD COLUMN IF NOT EXISTS gpu_elapsed_seconds INTEGER;
ALTER TABLE execution_jobs ADD COLUMN IF NOT EXISTS peak_gpu_memory_bytes INTEGER;
