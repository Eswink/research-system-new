---
id: PLAN-20261018-529
slug: goal-088-ec01-04-experiment-design-from-retrieval
title: GOAL-088 cycle 1 — 实验设计由检索证据派生（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-088
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-530-goal-088-experiment-design-from-retrieval.md
memory_entries: []
---

# PLAN-20261018-529 — GOAL-088 cycle 1

## 验收条件

- [x] **EC-01**：`design_source="retrieval"` ⇒ 臂**就是**本 run 系统取得证据里那一条的
      设计块；换记录 ⇒ 换设计；读出的设计**点名来源证据**。
- [x] **EC-02**：非 `RETRIEVED` 的同一份内容**不算**（点名拒绝）；他 run 的记录读不到。
- [x] **EC-03**：与显式 `arms` 同场 ⇒ 点名「undecidable」；无证据 / 无设计块 / 两份设计 /
      越白名单**各自点名**；未声明 ⇒ 既有语义逐字不变。
- [x] **EC-04**：`DESIGN_SOURCES == (plan, retrieval)`；未认得来源仍点名；`plan` 行为逐字不变。
- [x] **EC-05 不在本 cycle 的射程**（收口 cycle 的交付物）。

## 目标

把「设计从哪来」从「计划作者写了什么」扩展到「系统真的取回了什么」，且**按性质判定**。

## ★ 建档实测（为什么这是缺口）

1. `experiment_support.py` 的 `DESIGN_SOURCE_PLAN = "plan"` 是**唯一**取值；其他一律点名拒绝。
2. 计划内容是**模型正文**（`ENVELOPE_CONTENT_KEY = "content"`）⇒ 「由检索派生」实为
   「由计划作者派生」。
3. 检索证据的 run 作用域读取器**已存在**（`retrieval_context._retrieved_evidence`，
   `run_id` + `TrustLabel.RETRIEVED` + `tool-result:` 前缀）。
4. 性质维度有权威来源（`SourceRecord.trust_label`，唯一盖章点）。

## 实施清单

1. **WP-A（读取器）**：新增 `packages/application/experiments/design_from_retrieval.py` ——
   `read_design_from_retrieval`（run 作用域 + 性质过滤 + 逐条点名 + 单一设计）。
2. **WP-B（共享解析器）**：把 `design_from_plan._design_block` 提升为公开的
   `design_block_in`（两个来源同一份解析；私有名保留为别名 ⇒ 既有判据不受影响）。
3. **WP-C（声明面）**：`experiment_support` 新增 `DESIGN_SOURCE_RETRIEVAL` 与
   `DESIGN_SOURCES`；`_arms_for` 按来源分派（缺 ledger ⇒ 点名）。
4. **WP-D（判据）**：新增 `tests/application/test_experiment_design_from_retrieval.py`（10 条）。

## 影响报告

- **应用层**：新增一个读取器模块；`design_from_plan` 多一个**公开入口**
  （`design_block_in`，行为与私有函数**同一个对象**）；`_arms_for` 的来源分支从
  「单值比较」变成「词表 + 分派」。
- **零回归**：`plan` 来源与未声明来源的行为逐字不变；既有实验判据 **40 passed**。
- **schema / 迁移 / HTTP 面 / DTO / OpenAPI**：未改。
- **无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮读数是判据文件本身）：两个设计来源必须共用**同一个**设计块解析器
（否则「怎么认设计」会漂成两套口径）；性质维度只能读 `SourceRecord.trust_label`
（前缀/命名都是拼接产物，不可作为性质证据）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01…EC-04 | **10 passed** | `... pytest tests/application/test_experiment_design_from_retrieval.py -q` |
| 既有实验判据零回归 | **40 passed** | `... pytest test_experiment_design_decides test_experiment_parameters test_experiment_design_from_the_plan test_two_arm_experiment_offline -q` |
| 静态门 | ruff / format / mypy 全绿 | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-088 建档：检索来源读取器 + 共享解析器 + 声明面 + 10 条判据。 |
| 2026-10-18 | **DONE** | EC-01…EC-04 达成（10 条新判据 + 40 条既有实验判据零回归）。EC-05 留给收口 cycle。 |
