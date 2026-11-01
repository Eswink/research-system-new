---
id: MEM-20261101-237
title: "「声明了但从未构造」要判调用行：字段在树 ≠ 接线在"
status: ACTIVE
created_at: 2026-11-01
updated_at: 2026-11-01
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261101-103-phase-events-and-frontend-visible-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md
supersedes: []
---

# 「声明了但从未构造」要判调用行

## 做了什么

本轮新增的每一条「接线」判据都写成**源码点名调用行**，而不是「字段/函数在树」：
`run_phases_dto(` 出现在 `routers/runs.py`、`apply_retmax(declared, deps.retmax)` 出现在
能力步、`_with_project_retmax(` 出现在 `runner_wiring`。

## 为什么这样做

本轮实测过一次真红：`apply_retmax` 写好了、测试也写了，但组合根调用的是不带
`project_retmax` 的形态 —— 字段一路到目录、到不了调用表，而**所有单元判据都是绿的**
（它们直接调函数）。同型的既有缺陷在本仓反复出现（`ContextSnapshot` 声明多年、
`context_snapshot=` 全仓零命中）。

## 怎么做与复现

1. 新增一个 DTO 字段 / 配置字段 / 装配函数时，**同时**写一条「谁调用它」的判据
   （读源码点名调用行，或断言某个具体 kwargs 名出现在调用点）；
2. 只有「单元行为绿」不够：它证明**函数对**，不证明**函数被用**；
3. 若取值点有 per-run / per-request 语义，判据还要钉**在哪一层**取（见 MEM-20261101-236）。

## 适用边界

- 读源码的判据对**改名 / 换调用形态**脆弱（它会判红）—— 这正是它的用途：换形态时
  必须同轮改判据，不允许静默漂移；
- 它不证明运行时那条路径真的被执行过（那要靠行为判据 / 真跑）；两类判据要成对。

## 来源

- GOAL-20261101-103 EC-02 / EC-05 / EC-06
- `.cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md`
- 判据：`tests/application/test_retmax_project_setting.py`、
  `tests/api/test_read_face_field_completeness.py`
