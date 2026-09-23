---
id: MEM-20260923-123
title: "「为什么不做」要写成可核对的事实（点名真实页面与等级），且等级声明必须与产品源码一致"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-24
scope: repository
confidence: 0.9
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-154-ops-matrix-disclosure-first-class.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-155-ops-matrix-disclosure-first-class.md
supersedes: []
---

## 做了什么

GOAL-20260923-013 EC-04 要求 `ops/matrix` 这条唯一的 `gap` 页给出「**为什么不做**实时运维状态」，
并明文**不得**用「设计如此」一句话代替。本 cycle 把它写成可核对的事实：
实时运维状态有它自己的读面与页面 —— `#/ops/observability`、`#/ops/compute`（`FULL`）、
`#/ops/data-health`（`partial`，读面已交付、缺口是聚合质量报告）；本页只陈述
**组件状态词表**（loading / empty / error / permission / unknown）。

**同一轮里我自己的判据抓出了一处假声明**：起草时写成「三页均 `FULL`」，
一致性判据判红（`点名了 ops/data-health，但它在 pageSupport 里不是 full`）⇒ 回读源码改正。

## 为什么这样做

- 「设计如此」不可复核，读者无法判断这是**决定**还是**遗忘**；
- 点名了具体页面与等级，就把这句话变成**能判对错**的陈述 —— 也就能被机械判据守着：
  等级不是从文档里抄的，是从 `pageSupport.ts` 读的。

## 怎么做与复现

- 一致性判据 `apps/web/tests/unit/matrix-disclosure.test.ts` ③：解析 `pageSupport.ts` 的
  `ops/*` 等级表，要求两处文档各点名 ≥2 个候选页、每个被点名的都必须**存在于该表**、
  且其中**至少一个**是 `full`，并要求文档写了等级字样（`FULL`）。
- 复现：把文档里的等级写成与源码不符，判据即红。
- 页面判据 `apps/web/tests/e2e/matrix-states.spec.ts`：`?source=live#/ops/matrix` 断言
  说明文案可见；默认来源断言示例身份（不冒充实时运维状态）。

## 适用边界

- 这套写法适用于任何「不做某事」的登记（矩阵的 `SURFACE:`/`FIELD:` 行同理）：
  **点名相邻的真实能力**比形容词更有力。
- 反过来，**不要**在文档里写产品源码里读不到的等级/字段 —— 一旦写了，就该有判据守着它。

## 来源

- `apps/web/tests/unit/matrix-disclosure.test.ts`（一致性判据）、
  `apps/web/tests/e2e/matrix-states.spec.ts`（页面判据）。
- 「为什么不做」的落点：`docs/frontend/CONSOLE_PAGE_MAP.md` 的 `#/ops/matrix` 小节、
  `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md` 第 15 行。
- 判红实跑（本机 `scratch/`，不进仓库）：`goal013-c5-press-doc.txt`（按文档源 ⇒ 红）、
  `goal013-c5-press-page.txt`（按页面 ⇒ 红）。
