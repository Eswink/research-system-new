-- 023_memory_conflict_resolutions: 记忆的**冲突消解记载**落 canonical（GOAL-20261012-058 EC-02）。
--
-- 为什么：序 19 让「有冲突」成为**可判定的处置**（第五态 `CONFLICTED`）、序 22 让**声明本身**
-- 必须可查（被引 id 存在性 + 不得自指），但**「冲突被解决了」这件事读不出来**：
--   a) `resolve_conflict` / `arbitrate` / `prefer_` / `supersede_conflict` / `CONFLICT_RESOLVED`
--      在 `packages/`·`adapters/` **全零命中**；
--   b) `update_memory` / `amend_memory` / `edit_memory` / `rewrite` **全零命中** ⇒ 没有任何
--      「改一条已落库记忆的声明」的手段；
--   c) `lifecycle.py` 的三个写路径都不处理「冲突」这一维。
-- ⇒ 一经声明那条记录**永远** `CONFLICTED`；人若人工判定「A 对、B 错」，系统里**没有地方**能记下来。
--
-- 语义：JSON 数组 = **逐对**的消解记载（`other_id` / `resolved_by` / `resolved_at`）；
-- 缺省 `'[]'::jsonb` = **一对都没消解** ⇒ 既有行读出同一语义（**声明一字不动** ——
-- `contradictions` 是**历史事实**，消解是**另一件事**）。
--
-- **只加列**（带缺省回填 `'[]'` ⇒ 既有行立刻合法）；不删改任何既有列。

ALTER TABLE m12_memory
    ADD COLUMN IF NOT EXISTS resolutions JSONB NOT NULL DEFAULT '[]'::jsonb;
