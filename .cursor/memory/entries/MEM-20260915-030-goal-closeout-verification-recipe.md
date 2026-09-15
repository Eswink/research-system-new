---
id: MEM-20260915-030
title: GOAL 收口复检的可复现配方：证据面断言 + 分布现算 + skip 逐条核对
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2027-03-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-053-goal-001-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-053-goal-001-closeout.md
supersedes: []
tags:
  - goal
  - closeout
  - verification
---

# GOAL 收口复检的可复现配方

## 做了什么

给 GOAL 的收口独立复检（ACHIEVED 前置）定了一套**只读当前树**的机检配方，
并在 GOAL-20260912-001 的 cycle 13 上实跑通过：

1. 证据面断言脚本 `scratch/verify_goal001_closeout.py`：逐 EC 断言「当前树仍支持该结论」——
   OpenAPI 快照里的路径与方法、`apps/web/src/navigation/pageSupport.ts` 里的显式路由等级、
   EC 关键源码与 migration 文件存在；任一断言失败即非零退出。
2. 守卫与分布现算：`apps/web` 下 `pnpm run test`（EC-05 守卫 3 例，含反证）+
   `scratch/route_dist.mjs`（registry × pageSupport 现算分布，本轮 33 = 10 full / 22 partial / 1 gap）。
3. 全量套件 + skip 逐条核对：`python -m pytest tests -q -rs`。

## 为什么这样做

- **不复述历史 RECHECK 文本**：历史记录可能写着"已修复/已绿"而当前树已漂移；收口的
  判定必须能在当前树上复现，否则 ACHIEVED 只是一段历史叙事的复述。
- **分布要现算**：文档里的 `10 full / 22 partial / 1 gap` 是某次快照的数字，路由增删后
  会静默失真；从 registry × pageSupport 现算才能发现漂移。
- **0 failed 不够**：skip 也是"没跑"的一种。必须逐条读原因，确认没有 EC 覆盖被静默跳过
  （本轮 6 条：Windows symlink 特权 ×2、fail-open 专项套件接手 ×2、live relay 需环境变量 ×1、
  OTel collector 未启动 ×1，全部合法）。

## 怎么做与复现

```
python scratch/verify_goal001_closeout.py      # PASS: EC-01..EC-06 证据面与当前树一致
cd apps/web && pnpm run test                   # 76 passed（含守卫 3 例）
node --import ./tests/helpers/registerStyles.mjs --import tsx ../../scratch/route_dist.mjs
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  RESEARCHOS_DATABASE_URL= DATABASE_URL= POSTGRES_DSN= \
  python -m pytest tests -q -rs --ignore=tests/architecture/python/test_dependency_boundaries.py
sh scratch/run-m0-cycle12.sh                   # profile=m0; 23 deterministic checks
```

## 适用边界

- 断言脚本按**当前**结构写（路由键 `domain/page`、快照文件 `docs/api/openapi.m13.json`）；
  结构演进时脚本会红，**当断言失败来修，不要放宽断言**。
- 复检只证明"当前树支持这些结论"，不重演历史实现；历史 RECHECK 的判定偏差只能通过
  "当前树不支持该结论"暴露（这一口径写进了 RECHECK-053 的检查范围）。
- `pageSupport` 的等级可能与直觉不同：`portfolio/projects` 是 `partial` +
  `disabledOperations: ["delete"]`，不是 `full`——写断言前先读源码。

## 来源

- PLAN-20260915-053（GOAL-20260912-001 cycle 13 收口复检），RECHECK-20260915-053 = PASS_WITH_WARNINGS。
- 相关：`.cursor/plans/goals/README.md`（ACHIEVED 前置）、MEM-20260915-027/028（collector-quality 口径纠正）。
