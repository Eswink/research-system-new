---
id: PLAN-20261114-113
slug: memory-last-mile
title: GOAL-113 子计划 —— 记忆的最后一米 + 压缩护栏与测量
status: DONE
created_at: 2026-11-14
updated_at: 2026-11-15
parent_goal: GOAL-20261114-113
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md
---

# PLAN-20261114-113

## 背景与靶子

序 81。建档实测：记忆机制完备（9 模块 / gate 7 阶段）但全仓 200 个 run 库
`m12_memory` 全 0 —— 根因是**组合根从未注入 `memory_gate`**（缺四行装配）。
压缩不存在但当前不需要（5–12 个 view event vs 阈值 80，差一个数量级）⇒ 护栏 + 测量。

## 交付面（checkbox）

- [x] 四行装配：`OrchestrationDependencies.memory_gate` + 两组合根 + `runner_wiring`
- [x] `TaskContract.memory_export` + `MemoryExportSpec`（confidence 用 `Decimal`——
      canonical 序列化拒绝 float，实测 float 让整条链的 manifest digest 判红）
- [x] `promote_memory` 读声明 → `curator_approved=True`（`gate.py` 一行不改）
- [x] 四条判据（正例 / 零回归两条 / curator 门仍咬 / 下一轮读得到）
- [x] `research_manuscript` 声明 `memory_export: {tier: PROJECT}`；真实 run 后
      `m12_memory` 非空
- [x] condenser 护栏（两处 kwarg）+ 三条判据（在 / 不触发 / 真的会压）
- [x] view-event 与 prompt-token 只读读数进 telemetry
- [x] 文档同步（CONTEXT_ENGINE §6.1 + §9）
- [x] 宪章记账（程序表序 81、阶梯「迭代」行、两表各 3 行）
- [x] 收口资产 + `_VERIFIERS` + `IN_SCOPE`

## 复检

`.cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md`

## 验收条件

- 十条 EC 全部 PASS；
- 真实 run 的 `m12_memory` 非空且 PROJECT 档可被下一轮 `prior_knowledge` 读到；
- 全量 m0 witness 绿 + 两树复检 sha256 相同 + CI 八 job 全绿。

## 状态

DONE（收口见复检文件与 GOAL 迭代日志）。
