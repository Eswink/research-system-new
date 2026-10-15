---
id: PLAN-20261015-483
slug: goal-079-ec04-live-two-arm-run
title: GOAL-079 cycle 4 — 真实中转站上的多臂 run（EC-04）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-079
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-484-goal-079-ec04-live-two-arm-run.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-483 — GOAL-079 cycle 4

## 验收条件

- [x] live 判据扩到断言**多臂**（两臂各自落库 + 两臂指标不同 + 差值可算）
- [x] live 判据的**报告指标断言**改成**逐臂遍历**（此前只查 `entries[0]`）
- [x] 新站真实 run 实跑通过
- [x] 读数落盘（run id / 各臂参数 / 各臂指标 / 差值 / `not_numeric`）
- [x] **live 取证抓出的真缺陷**已修（见下）

## 目标（本 cycle 的可独立验收主题）

**EC-04**：在**新站**上跑一次真实 run —— **真实模型会话产出的计划声明**驱动两臂实验，
读数记档。

## ★ 本 cycle 抓到的**真缺陷**（live 取证的价值）

**症状**（第一次 live 跑）：报告的第 3 节**只有一臂的数字**，而 `_assert_live_report`
只查 `entries[0]` ⇒ **判据本身也看不见**。

**根因（两处，都在产品代码里）**：
1. `report_facts.metrics_of` 按**指标名**归并 ⇒ 两个臂的同名指标**后写覆盖先写**
   （静默丢一臂）；
2. 修掉 ① 后我用 `" | "` 把两臂的值并进**同一格** ⇒ markdown 表格被撑成 **4 列**
   （表头只有 3 列）⇒ **渲染坏掉**（第二次 live 跑实测）。

**处置**：① `metrics_of` 改成**逐臂一行**（带 `experiment_run_id`）；② 报告渲染器在
指标带实验标识时**表头多一列「实验」**、每个 (指标, 实验) 一行 ⇒ 表格列数一致；
③ 判据改成**逐臂遍历** + 表格**管道符计数一致**的机械判据。

## 实施清单

1. **WP-A**（产品修复）：`report_facts.metrics_of` 逐臂一行；`research_report._experiment_section`
   多臂表头。
2. **WP-B**（判据）：live 的 `_assert_live_report` 逐臂遍历；`retrieval_context_support.assert_the_arms_ran`；
   汇编器判据加两条（多臂一行 + 单臂三列零回归）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / ALL_PLAN；读数落盘；m0。

## 影响报告

- **产品代码**：`report_facts.metrics_of`（多臂逐行；单臂形态含新增的 `experiment_run_id`
  列）与 `research_report._experiment_section`（多臂表头）+ 沙箱 live 装配（声明两个臂）。
- **读面 / DTO / 路由 / 快照**：**零改动**。
- **判据面**：live 断言加强（逐臂）+ 汇编器 2 例 + e2e 2 例；既有判据零放宽。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- EC-05（自举收口）不在本 cycle；
- `metrics_of` 的单臂形态现在多带一列 `experiment_run_id`（**生产必填**；
  判据的 `_metric_text` 逐字逻辑未动）—— 这是本轮为了让「哪个实验」可判的**有意变化**，
  如实登记；
- 臂数 > 2 与「哪个臂更好」仍不在射程内（承 EC-02/EC-03 的 `W-2`/`W-3`）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| live 实跑 | **1 passed in 190.08s**（修复后重跑 169.68s / 190.08s 两次均绿） | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 … -m pytest tests/e2e/test_research_report_chain_live.py -q` |
| 多臂读数 | run `e905ab59…`：两臂（`control` / `treatment n_items=120`）各落库、同一镜像 digest；差值 `7990.0 → 178.5 = -7811.5`、`800 → 120 = -680`；`agreement` 进 `not_numeric` | `evidence/GOAL-20261015-079-ec04-arms-evidence.txt` |
| 报告渲染 | 多臂表头 **4 列**、逐臂一行、管道符计数一致 | 汇编器判据 + 落盘报告 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 4 建档（EC-04 的 live 取证 + 已知的报告多臂缺口）。 |
| 2026-10-15 | DONE | live 取证**抓出并修掉**两处产品缺陷（静默覆盖 + 表格撑破）；实跑两次均绿；读数落盘。 |
