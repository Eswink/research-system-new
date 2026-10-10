-- 021_program_conditional_gate: 程序的**条件式**人工闸门落 canonical（GOAL-20261010-048 EC-02）。
--
-- 为什么：`ResearchProgram.human_gate_on_verdicts` 让程序声明「上一轮落库判词命中其中之一时，
-- 停下等人看结果」，而 020 只加了**按序号**的闸门列 ⇒ 条件声明**从不落库**、驱动读到的
-- 永远是缺省（= 不设条件式闸门）。与 GOAL-039/040/046 同一类缺口：**字段在场 ≠ 事实在场**。
--
-- 语义：NULL = **未声明**（既有行为逐字不变）；JSON 数组 = 声明的判词取值集合。
-- **NULL 与 `[]` 语义不同**（未声明 vs 坏声明 —— 后者在域层已被点名拒绝），所以存 NULL 而不是空数组。
--
-- **只加列**（无缺省回填）；不删改任何既有列。

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS human_gate_on_verdicts_json JSONB;
