---
id: PLAN-20261015-487
slug: goal-080-ec01-the-design-source-is-declared-and-run-scoped
title: GOAL-080 cycle 1 — 设计来源可声明 + 确定性读取器（EC-01）
status: IN_PROGRESS
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-080
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: null
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-487 — GOAL-080 cycle 1

## 验收条件

- [ ] **读取器在树**：`packages/application/experiments/design_from_plan.py` —— 确定性、
      零出网、**run 作用域读**、逐键过既有白名单
- [ ] **声明面**：装配面可声明「设计取自计划产物」（缺省不声明 ⇒ 既有语义逐字不变）
- [ ] **读不到制品 ⇒ 点名拒绝**（不回落装配常量）
- [ ] **按 run 过滤**（他 run 的计划读不到）+ 反证臂
- [ ] 判据成对（正向 / 反证 / 零回归 / 自检）且有例数下界
- [ ] 三向按压全 RED + 逐字节复原（归档进树、`CR=0`）
- [ ] 记录面（PLAN + RECHECK）与 GOAL 回写；`ALL_PLAN` 投影

## 目标（本 cycle 的可独立验收主题）

**EC-01**：设计来源可声明，且**读**是确定性的、run 作用域的、fail-closed 的。

## ★ 规划期实测更正（已回写 GOAL 的 cycle 0 行）

原设计（把 `research_plan` 写进 phase 的 `inputs:`）**不可行且不该做**：
`test_declared_input_sources.py` 要求声明输入是**仓库文件字节可重算 + 组合根种入**的制品
（逐条判据在树），而计划产物是**本 run 的模型产物**；`inputs` 的既有口径逐字写着
「只声明**外部供应**的输入，**不解析** phase 间的产物引用」。

⇒ 改走**执行期 run 作用域读**（与 GOAL-078 的 `retrieval_context` 同一形态）：
**一条既有判据都不动**。这正是「不为让新目标成立而改判据」那条纪律的现场兑现。

## 实施清单

1. **WP-A**（读取器）：`design_from_plan.py` —— 计划产物内容 → 臂声明（逐键过
   `ALLOWED_PARAMETERS`）；`read_plan_artifact(artifacts, run_id)` 按 run 过滤取制品；
   读不到 ⇒ 点名拒绝。
2. **WP-B**（判据）：`tests/application/test_experiment_design_reader.py`（正向 / 反证 /
   零回归 / 自检）+ e2e。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`；按压归档；m0。

## 影响报告

- **产品代码**：新增一个读取器模块 + 装配面声明位（缺省不变）。
- **读面 / DTO / 路由 / 快照**：**零改动**。
- **判据面**：**只增**（新判据文件）；既有判据一条不动（**特别是**
  `test_declared_input_sources.py` —— 它的两条等号判据是**不能动**的）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

见 GOAL-080 的「残余与未覆盖范围」一节（`W-1`…`W-4`）。

## 证据

（cycle 执行时逐条回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 1 建档（含规划期实测更正：改走执行期 run 作用域读）。 |
