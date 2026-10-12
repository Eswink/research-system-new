-- 024_program_gate_nudge_bound: 程序的**超期界**落 canonical（GOAL-20261012-059 EC-02）。
--
-- 为什么：序 24（`GOAL-20261011-056`）让等待面**有始点、能判超期**（域字段
-- `gate_nudge_after_seconds` + 判词点名「等太久了」）；序 25（`GOAL-20261011-057`）
-- 让那条信号**有可注入的出口**（`NudgeSink` + `NullNudgeSink`）。但**实跑取证**
-- 整条链是**三层断的**：
--   a) 声明面：`ProgramCreateDto` / `ProgramDetailDto` **没有该键** ⇒ 界声明不出来；
--   b) 落库面：本表**没有该列** ⇒ `SqliteProgramStore` round-trip **静默丢弃**
--      （实测：进程内声明 `60` ⇒ 落库读回 `None`）；PG 侧同缺；
--   c) 出口面：`services/` 对 `nudges=` / `NudgeSink` **零命中** ⇒ 出口从不被注入。
-- ⇒ 「等待面有始点、可催办」**只在进程内测试里成立**，产品面上不可达。
--
-- 语义：NULL = **未声明**（既有行为逐字不变；不是 `0` —— 域层点名校验「必须是正整数」，
-- 所以 `0` 与「未声明」在域上是两件事，落库层必须能区分）。
-- 与三种闸门声明（`human_gate_at_index` / `_on_verdicts` / `_at_indexes`）**正交**：
-- 它不决定「停不停」，只决定「等太久了要不要报」⇒ **不参与**那三者的互斥校验。
--
-- **只加列**（无缺省回填）；不删改任何既有列。

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS gate_nudge_after_seconds INTEGER;
