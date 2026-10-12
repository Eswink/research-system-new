-- 025_program_hybrid_gate: 程序的**混合式**人工闸门落 canonical（GOAL-20261012-060 EC-02）。
--
-- 为什么：序 14（`human_gate_at_index`）/ 序 16（`human_gate_on_verdicts`）/
-- 序 23（`human_gate_at_indexes`）三条声明**互斥**（`_validate_gate_exclusivity` 点名拒绝）
-- ⇒ 「第 1、3 轮停，**且**判词为 X 时也停」**结构上做不到**；而三条各自的机制
-- （注册 / 判定 / 触发，序 14/15/16/23）**都已全在** ⇒ 缺的只是**组合维度**。
--
-- 语义：两列**成对**出现 —— 都是 `NULL` = **未声明**（既有行为逐字不变）；
-- 都有值 = 混合式（序号组 × 取值集合，两维同时生效）。**两列不成对**是外部改写
-- （域层值对象保证「只声明一半」写不出来）⇒ 读面按**未声明**处理（**不猜**）。
--
-- **只加列**（无缺省回填）；不删改任何既有列。与 020/021/022 三条闸门列**并存**
-- （四条声明的互斥由域层点名拒绝；落库层不加约束 —— 那会把「坏声明」变成「落库失败」，
-- 而既有纪律是**点名拒绝**）。

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS human_gate_hybrid_indexes_json JSONB;

ALTER TABLE research_programs
    ADD COLUMN IF NOT EXISTS human_gate_hybrid_verdicts_json JSONB;
