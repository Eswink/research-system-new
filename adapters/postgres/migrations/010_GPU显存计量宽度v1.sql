-- Personal GPU workers may report more than 2 GiB of allocated device memory.
-- PostgreSQL INTEGER overflows at 2^31 bytes and prevents result settlement.
-- Widen only the storage type; existing Python/JSON integer values and Worker
-- protocol 1 remain compatible. Apply in the documented maintenance window.
ALTER TABLE execution_jobs
    ALTER COLUMN peak_gpu_memory_bytes TYPE BIGINT;
