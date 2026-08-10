---
id: MEM-YYYYMMDD-NNN
title: 工程记忆标题
status: ACTIVE
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
scope: repository
confidence: 0.00
review_after: YYYY-MM-DD
source_plans:
  - .cursor/plans/tasks/PLAN-YYYYMMDD-NNN-short-slug.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-YYYYMMDD-NNN-short-slug.md
supersedes: []
tags: []
---

# MEM-YYYYMMDD-NNN — 工程记忆标题

## 做了什么

记录已经验证的稳定结果。

## 为什么这样做

记录约束、权衡和未采用方案，不把推断写成事实。

## 怎么做与复现

1. 可复现步骤。
2. 校验命令与预期状态。

## 适用边界

- 适用于：
- 不适用于：

## 失效与复核触发器

- 到达 `review_after`。
- 相关架构、Schema、依赖、Skill digest 或运行行为变化。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/...` | 待填写 |
| recheck | `.cursor/plans/rechecks/...` | 待填写 |
| repository | `path:line` 或 digest | 待填写 |