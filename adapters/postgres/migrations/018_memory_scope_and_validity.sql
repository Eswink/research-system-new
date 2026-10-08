-- 018_memory_scope_and_validity: 记忆的**适用范围**落 canonical（GOAL-20261008-039 EC-02）。
--
-- 为什么：`MemoryWriteProposal.scope` 一直存在（缺省 `"project"`），但**从不落库** ——
-- `m12_memory` 无该列、`PostgresMemoryStore._proposal_values` 连参数都不带它。AGENTS.md §8
-- 明文要求 Project/Organization Memory「有适用范围」「有过期/复核策略」；前者此前**不可判定**。
--
-- `review_after` / `expires_at` 两列**已在 004**（就位说明，本迁移不动它们）：它们的缺口不在
-- schema，而在**从不被写**（PG 曾硬编码 NULL）与**从不被用来判定**（查询无时效过滤、读面无判定）
-- —— 那两个缺口由本 GOAL 的适配器与读面改动补（EC-03 / EC-04）。
--
-- **只加列 + 缺省回填**：既有行读出 `"project"`（与缺省语义一致），不删改任何既有列的数据。
-- `IF NOT EXISTS` + `DEFAULT` 让本迁移对新旧库都幂等。

ALTER TABLE m12_memory ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'project';
