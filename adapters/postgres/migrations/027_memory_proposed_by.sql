-- 027_memory_proposed_by: 记忆的**提议者**落 canonical（GOAL-20261012-065 EC-02）。
--
-- 为什么：`proposed_by` 在**提案**面上（`MemoryWriteProposal`）从序 13 起就有，并且两个内部
-- 调用点（`memory_promotion` / `m12_chain`）**会填它** —— 但 `commit` **丢弃**它，
-- 因为 `MemoryRecord` **根本没有该字段**。**实测**：`dataclasses.fields` 两次对照
-- （提案 `True` / 记录 `False`）+ `hasattr(record, "proposed_by")` 亦为 `False`；
-- **实跑**：带 `proposed_by` 的提案经产品路径提交 ⇒ 落库记录无作者面、编排读面的
-- 20 个键里也没有它 ⇒ 「这条记忆是谁提的」在 canonical **无从可查**。
--
-- 语义：`NULL` = **未声明**（既有行读出**同值**，不被回填）；非空 = 提议者标识。
-- **与 `provenance` 是两件事**：`provenance` 是**来源**（知识从哪来），本列是**谁提议**
-- 把它记下来 —— 两者各自独立、互不顶替（`provenance` 的既有语义**一字不动**）。
-- **不是 ACL**（与 `scope` 的边界同形）：只回答「是谁」，不授权任何访问。
--
-- **只加列**（无缺省回填）；不删改任何既有列。

ALTER TABLE m12_memory
    ADD COLUMN IF NOT EXISTS proposed_by TEXT;
