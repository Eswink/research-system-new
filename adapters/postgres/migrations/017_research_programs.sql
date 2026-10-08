-- 017_research_programs: 研究程序的声明与推进决策（GOAL-20261008-037 EC-01）。
--
-- 为什么落库：多轮 run 的程序级编排需要两件 canonical 事实 —— ① 程序的**声明**
-- （项目 + 协议 + 上界护栏 + 声明式续跑规则）；② 每次推进的**决策**（含被引 canonical
-- 事实的原文）。没有它们，「程序推进到第几轮、为什么继续/停」只能靠日志与推断。
--
-- **不设「程序 → run」映射表**：run 的归属在 `runs.run_json` 的 `program_id` /
-- `program_index` 上（与 run 同一次写入落库）；「某程序的全部 run」由 run 面按 JSONB
-- 抽取查询（`RunStore.for_program`）—— 单一真相，避免第二套映射漂移。
--
-- `program_decisions` 是 append-only：自然键 `(program_id, after_index, decided_at)`
-- + `DO NOTHING`（同一时刻的重复写是幂等空操作；**不**覆盖历史决策）。

CREATE TABLE IF NOT EXISTS research_programs (
    program_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    protocol_id TEXT NOT NULL,
    max_runs INTEGER NOT NULL,
    continue_rule_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_programs_project ON research_programs(project_id);

CREATE TABLE IF NOT EXISTS program_decisions (
    program_id TEXT NOT NULL,
    after_index INTEGER NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    kind TEXT NOT NULL,
    reason TEXT NOT NULL,
    cited_run_id TEXT,
    cited_facts_json JSONB NOT NULL,
    PRIMARY KEY (program_id, after_index, decided_at)
);
