-- 019_program_attempts: 程序的**每序号尝试上界**落 canonical（GOAL-20261008-040 EC-02）。
--
-- 为什么：`ResearchProgram.max_attempts_per_index` 决定「失败轮能否按声明重试」，
-- 但 017 的表里没有它 ⇒ 声明**从不落库**、驱动读到的永远是缺省（= 不重试）。
-- 与 GOAL-039 同一类缺口：**字段在场 ≠ 事实在场**（声明的价值在于真被读到）。
--
-- **只加列 + 缺省回填**：既有行读出 `1`（= 不重试，与旧行为**逐字一致**）；不删改任何既有列。

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS max_attempts_per_index INTEGER NOT NULL DEFAULT 1;
