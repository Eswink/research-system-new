-- 016_review_findings: 验收门求值结论的 canonical 记录（GOAL-20261008-035 EC-01）。
--
-- 为什么落库：`GateOutcome.evaluations`（逐条判据 + 逐字判词）此前只在**被拒**时随失败
-- 消息可见；通过的路径上判词无处可读（`ReviewFinding` / `Decision` 从不持久化）⇒
-- 「覆盖判据真的判过、两个维度各自的数是多少」不可复核。**记录，不是重算**：读面必须能
-- 区分「门判过」与「门根本没跑」。
--
-- `finding_id` 主键 ⇒ 同一结论重复写是幂等空操作（append-only，与 pricing_snapshots
-- 同口径）。`findings_json` 是判词的原文数组（读面原文，不重排）。

CREATE TABLE IF NOT EXISTS review_findings (
    finding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    review_type TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    findings_json TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_review_findings_run ON review_findings(run_id);
