---
id: PLAN-20261016-499
slug: goal-081-ec03-the-prompt-excerpts-are-verbatim-the-read-face
title: GOAL-081 cycle 2 — 提示词那段 == 读面制品（逐条逐字）+ 反证（EC-03）
status: DONE
created_at: 2026-10-16
updated_at: 2026-10-16
parent_goal: GOAL-20261016-081
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-500-goal-081-ec03-the-prompt-excerpts-are-verbatim-the-read-face.md
memory_entries: []
---

# PLAN-20261016-499 — GOAL-081 cycle 2

## 验收条件

- [x] **逐条逐字**判据：提示词那段的每一行 == 读面制品对应条目的 `identifier` + `shown`
      （**行级逐字**，不是「包含」）
- [x] **条数一致**：提示词那段的条目行数 == 读面制品 `entries` 条数（不丢条、不多条）
- [x] **反证臂**：把读面制品的某一条改掉 ⇒ 同一比较**判红**（证明判据有分辨力，
      不是「两边都在场」的同义反复）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写；`ALL_PLAN` 投影

## 目标（本 cycle 的可独立验收主题）

**EC-03**：**「模型拿到了什么」能对着既有读面核对** —— 不靠回忆、不靠日志。

## 实施清单

1. **WP-A**（判据支持件）：`assert_the_prompt_matches_the_read_face(prompt, payloads)`
   —— 行级逐字比对（含截断标注的**逐字**形态）。
2. **WP-B**（e2e 两向）：正向（真实 run 上比对通过）+ 反证（改一条 ⇒ 同一比较判红）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`；m0。

## 影响报告

- **产品代码**：**零改动**（本 cycle 只加判据）。
- **读面 / DTO / 路由 / 快照**：零改动。
- **判据面**：**只增**；既有判据一条不动。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 判的是**文本一致**，不判模型是否读懂（GOAL `W-1` / `W-2`）；
- 真容器/真实模型侧见 EC-04。

## 证据

（执行时回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-16 | IN_PROGRESS | cycle 2 建档（逐条逐字 + 反证臂）。 |
