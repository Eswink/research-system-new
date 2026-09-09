---
id: MEM-20260910-018
title: 前端树增长后的质量门禁机械事实（spawnSync 缓冲与浏览器全局声明）
status: ACTIVE
created_at: 2026-09-10
updated_at: 2026-09-10
scope: repository
confidence: 0.9
review_after: 2026-12-10
source_plans:
  - .cursor/plans/tasks/PLAN-20260909-035-console-reference-reconstruction.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260910-037-console-reference-reconstruction.md
supersedes: []
tags: [quality-gates, dependency-cruiser, eslint, spawnSync, web-console]
---

# MEM-20260910-018 — 前端树增长后的质量门禁机械事实

## 做了什么

PLAN-20260909-035 复刻过程中实测并处置三个会反复出现的质量门禁机械问题：

1. `tests/architecture/typescript/production-boundaries.test.mjs` 用 spawnSync 捕获
   dependency-cruiser 完整 JSON；web 源码树增长（example-console 并入后 843+ 模块、
   JSON ≈1.8MB）超过 spawnSync 默认 1MB maxBuffer，表现为 `result.status === null` +
   ENOBUFS 的假失败。处置：该测试子进程显式 `maxBuffer: 64MB`，断言不变
   （violations==[] 实测 0 违规）。
2. `tools/**/*.mjs` 与 `scratch/**` 都在 root `eslint .` 范围内（root 配置不忽略
   gitignored 目录）。其中经 Playwright `page.evaluate/addInitScript` 进入浏览器上下文的
   `document/localStorage/getComputedStyle/innerWidth` 引用必须用文件级
   `/* global ... */` 声明，否则 no-undef；这是声明而非规则禁用。
3. 架构门禁拒绝 `apps/web/src/features/**` 源码（含注释）出现
   `PASS|FAIL|BLOCK|REVISE` 与币种代码字面量。

## 为什么这样做

门禁是机械正则与固定缓冲，不会随源码规模自适应；失败表象（status null、no-undef、
正则命中）容易被误读为产品缺陷或诱导放宽规则。逐项以“不削弱断言”的方式修正：
缓冲只扩进程管道、全局用声明、状态词从 fixture/后端值派生而非字面量。

## 怎么做与复现

- 复现 1：web 树 >~800 模块时运行 `pnpm run test`，观察
  “apps/web 生产源码通过全部生产架构边界” ENOBUFS；对照
  `dependency-cruise --output-type err apps/web/src` 直接运行 0 违规。
- 复现 2：在 `tools/*.mjs` 写 `page.evaluate(() => document.body)` 后运行
  `pnpm run lint`；文件头加 `/* global document */` 即通过。
- 合规模式：示例页状态从 fixture 严重度推导
  （`apps/web/src/features/example-console/reference/preflightModel.ts`）；
  实时页只回显后端 DTO 值、色调由 findings 严重度派生；`WARN` 不在禁词内。
  新增 `@/` 别名 import 会触发 depcruise `not-to-unresolvable`（root tsconfig 无该
  paths），features/layout 内保持相对导入。

## 适用边界

适用于本仓库 root 门禁（`pnpm run check` 链）与 apps/web 源码树；若未来把
dependency-cruiser 输出改为 `err` 模式或拆分 web 包，第 1 条自然消失。不改变
门禁正则本身，也不豁免任何目录。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260909-035-console-reference-reconstruction.md`
  （EV-09..16）。
- 复检：`.cursor/plans/rechecks/RECHECK-20260910-037-console-reference-reconstruction.md`
  （F-01..F-04）。
