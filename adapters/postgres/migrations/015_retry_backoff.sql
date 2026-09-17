-- 015_retry_backoff: 重排后的退避（PLAN-20260915-079）。
--
-- 一次失败被判为 RETRY 时，complete 写下 `retry_at = now() + 策略时延`
-- （时延由 Domain 纯函数 `TaskContract.retry_delay` 算）。claim 的候选查询
-- 按 `retry_at IS NULL OR retry_at <= now()` 过滤：没到期的重试不占候选窗口，
-- 到期后与首次排队同权；交付时清回 NULL。
--
-- 旧 row 的 retry_at 为 NULL = 不等待，与退避字段出现之前完全一致。

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS retry_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_tasks_retry_at ON tasks(retry_at);
