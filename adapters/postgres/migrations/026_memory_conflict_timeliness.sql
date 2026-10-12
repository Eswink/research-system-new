-- 026_memory_conflict_timeliness: 记忆的**冲突声明时效**落 canonical（GOAL-20261012-061 EC-02）。
--
-- 为什么：`contradictions` 可声明（序 13）、可落库、可处置（序 19 第五态 `CONFLICTED`）、
-- 可消解（序 26），但**时效面零命中**：`conflict_valid` / `contradiction_valid` /
-- `conflict_review` 在三个产品根**全零**，且 `ConflictResolution` 只有
-- （对端 / 消解者 / 时点）⇒ **一条很久以前声明的冲突永久算数**，与记忆自身的
-- `review_after` / `expires_at` 机制（序 7 起）**不对称**。
--
-- 语义：两列**各自可选**（`NULL` = **未声明** ⇒ 既有行为逐字不变）：
--   * `conflict_review_after` 到点 ⇒ 该复核这条冲突声明（`REVIEW_DUE`）；
--   * `conflict_expires_at` 到点 ⇒ 这条冲突声明**失效**（`STALE`，更强的状态）。
-- 域层校验两条坏形态（**声明了时效却没有任何冲突** ⇒ 拒绝；
-- `conflict_expires_at` **早于** `conflict_review_after` ⇒ 拒绝）。
--
-- **只加列**（无缺省回填）；不删改任何既有列。

ALTER TABLE m12_memory
    ADD COLUMN IF NOT EXISTS conflict_review_after TIMESTAMPTZ;

ALTER TABLE m12_memory
    ADD COLUMN IF NOT EXISTS conflict_expires_at TIMESTAMPTZ;
