-- 020_program_human_gate: 程序的**人工闸门序号**落 canonical（GOAL-20261010-046 EC-02）。
--
-- 为什么：`ResearchProgram.human_gate_at_index` 让程序**自己声明**「第 N 轮跑完之后停下等人看结果」，
-- 而 017/019 的表里没有它 ⇒ 声明**从不落库**、驱动读到的永远是缺省（= 不设闸门）。
-- 与 GOAL-039（scope/时效）/ GOAL-040（尝试上界）同一类缺口：**字段在场 ≠ 事实在场**。
--
-- 语义：NULL = **不设闸门**（既有行为**逐字不变**）；整数 = 该序号轮**跑完之后**的推进停下等人。
--
-- **只加列**（无缺省回填：NULL 就是缺省语义）；不删改任何既有列。

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS human_gate_at_index INTEGER;
