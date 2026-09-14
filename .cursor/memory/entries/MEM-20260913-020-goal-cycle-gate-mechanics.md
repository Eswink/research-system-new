---
id: MEM-20260913-020
title: GOAL 循环首批交付的三个机械门禁事实（component 文件名/函数行数/收口时序）
status: ACTIVE
created_at: 2026-09-13
updated_at: 2026-09-13
scope: repository
confidence: 0.9
review_after: 2026-12-13
source_plans:
  - .cursor/plans/tasks/PLAN-20260912-041-project-registry-and-switcher.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260912-041-project-registry-and-switcher.md
supersedes: []
tags:
  - naming-gate
  - source-limits
  - goal-loop
  - openapi-snapshot
---

# MEM-20260913-020 — GOAL 循环首批交付的三个机械门禁事实

## 做了什么

GOAL-20260912-001 cycle 1（PLAN-041）交付中实测固化三条机械门禁事实：

1. 命名门禁（`tests/architecture/test_module_file_naming.py`）对 PascalCase
   组件文件要求「文件名 = 唯一导出组件名」：`EndpointDelete.tsx` 导出
   `EndpointDeleteAction` 即违规；TS 测试文件必须 kebab（`active-project.test.ts`）。
   **同样适用于 tests/ 目录下的非 .test/.spec TS 模块**（helper/fixture：
   `stubRoutes.ts` → 必须是 `stub-routes.ts`）——Windows 文件系统大小写不敏感，
   本地 m0 全绿但 Linux CI 红（run #58 实测）。新建 tests/ 下任何 .ts 文件一律
   kebab-case。新建前端组件文件时先按导出命名，别靠 LEGACY_PATH_EXCEPTIONS
   登记兜底。
2. 50 行函数门禁同样作用于 composition root 与测试装配（`_assemble_sqlite`、
   `build_postgres_apideps`、`make_run_ready_deps` 加字段即超）。既有惯例是
   提取返回 `dict[str, Any]` 的 helper 再 `**` 展开进 dataclass——照此拆分而不是
   压行。300 行文件阈值是软警告（warn 不 fail），50 行函数是硬失败。
3. GOAL cycle 的 push 时序：openapi 快照再生 + docs 收口必须与代码同批到达
   main，否则 GitHub Actions 的 `test_openapi_snapshot` 门在中间 HEAD 上必红
   （它按代码再生再 diff）。多 commit 批次应攒到 WP-D 收口 commit 一起 push，
   或保证同一 run 覆盖收口 commit。

## 为什么这样做

三条都是「实现正确但门禁红」的假失败来源，且表象（命名/行数/CI）容易误导成
产品缺陷而诱导放宽规则；按不削弱断言方式处置（改名/拆 helper/收口同批）。

## 怎么做与复现

- 复现 1：新增 `Foo.tsx` 导出 `FooAction` 组件 →
  `uv run --frozen --no-sync pytest tests/architecture/test_module_file_naming.py -q` 红。
- 复现 2：给 composition 函数加 >50 行 → `pytest tests/tooling/test_python_source_limits.py -q` 红。
- 复现 3：push 代码 commit 而快照未再生 → Actions run 的 contracts job 红；
  收口 commit（含再生快照）到达后转绿。

## 适用边界

适用于 apps/web 组件/测试命名、services+tests 装配函数扩张、GOAL/多 commit
批次 push 时序；单 commit 内完成代码+再生快照的场景无需引用第 3 条。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260912-041-project-registry-and-switcher.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260912-041-project-registry-and-switcher.md`
- 相关 commit：`b55df92`、`9ba606e`、`57feb37` 及收口 commit
