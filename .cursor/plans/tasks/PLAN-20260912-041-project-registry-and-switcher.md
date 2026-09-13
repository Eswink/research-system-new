---
id: PLAN-20260912-041
slug: project-registry-and-switcher
title: 项目注册表与项目上下文切换（GOAL-001 cycle 1 / EC-01）
status: DONE
created_at: 2026-09-13
updated_at: 2026-09-13
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 1 派生（/goal 开启循环迭代指令；目标与 push-to-main 授权见 GOAL frontmatter）；范围取 GOAL EC-01"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260912-041-project-registry-and-switcher.md
memory_entries:
  - .cursor/memory/entries/MEM-20260913-020-goal-cycle-gate-mechanics.md
---

# PLAN-20260912-041 — 项目注册表与项目上下文切换（EC-01）

## 目标

单用户规模的项目注册表落地：`ProjectDefinition` 域实体 + Port + SQLite store +
`GET/POST/PATCH /projects`；前端 `activeProject` 上下文替换 6 个 API client 的
`example-project` 硬编码；侧边栏项目切换器与 `#/portfolio/projects` 页翻 live。
不触碰 M18（多用户/RBAC/成员）；数据面逐资源隔离只做到「注册表语义可证伪」
程度：runs 列表、项目设置、协议草稿按 project 真实归属；其余资源保持现状并
在 G 表如实标注。

## 范围

- 包含：
  - WP-A 后端注册表：`packages/domain/projects.py`（ProjectDefinition：id/name/
    status ACTIVE|ARCHIVED/created_at/updated_at；有界校验）；Port `ProjectStore`
    （list/get/save，SQLite 配置面，两组成同侧）；`SqliteProjectStore`；
    `GET /projects`（store + 默认 example-project 注册条目合并，与 catalog_merge
    同哲学）、`POST /projects`（name 必填、id 服务端生成、Idempotency-Key）、
    `PATCH /projects/{id}`（rename/archive；未知 404）。
  - WP-B 后端真实归属：`GET /projects/{pid}/runs` 按路径 project 过滤
    （runs_store/registry 两路）；`ProjectSettingsStore.get(project_id)` 精确查
    （仅 example-project 允许 examples 回退，其它项目未配置为诚实空态）；
    草稿 create/list 使用路径 project_id（store 已有列，贯通 service 参数）。
    agents/experiments/memory 数据面保持全局（G2 文案更新，不伪装隔离）。
  - WP-C 前端：`projectsClient` + facade；`activeProject.ts`（localStorage +
    订阅事件 + `activeProjectId()`）；runs/team/protocol/drafts/experiments/
    memory client 的 PROJECT 常量改为读取上下文（显式参数可覆盖）；
    WorkspaceIdentity live 分支渲染项目切换器（GET /projects）；ProjectsPage
    live（列表/创建/归档；fixture 仅 example 模式）；presentationPolicy 移除
    portfolio/projects 强制 example；pageSupport 等级与 GAPS.multiProject 文案
    同步；i18n key。
  - WP-D 收口：openapi 再生；CONTROL_PLANE_API.md projects 节；
    CONSOLE_PAGE_MAP G2 行更新；stub-api projects 桩 + design-fidelity
    portfolio-projects 基线按 live 渲染重录；live e2e 新用例（创建项目→
    列表可见→切换上下文 URL 生效→草稿按项目隔离）；RECHECK-041。
- 不包含：项目成员/RBAC（M18）、逐资源全量租户隔离、项目级凭据域拆分、
  项目删除（保留 archive 语义）。

## 架构与数据流

与 PLAN-037/040 同不变量：读取经 Port/用例，无第二套事实源；mutating 全带
Idempotency-Key；store 未配置诚实 503；UNKNOWN/空态不伪造；SQLite 为配置面
（两组成同侧）、PostgreSQL 仍为研究数据 canonical；OpenAPI 快照单一 truth；
example 树零 `/api` 不变。前端项目上下文是 view-state（localStorage），
不是业务真相；后端 project_id 归属以持久化列为准。

## 验收条件

- [x] AC-01（WP-A）：ProjectDefinition/Port/Store 有单测；`GET/POST/PATCH /projects`
  行为完整（201 创建、未知/幽灵 404、重命名、归档幂等 200——重复归档仅前移
  updated_at，不引入 409）；默认 example-project 恒可解析且排序首位。
- [x] AC-02（WP-B）：runs 按 project 过滤有断言（两项目各只见自己的 run）；
  settings.get 按 project 精确（非 example 未配置 → 诚实空默认）；草稿
  create/list 归属路径项目且有跨项目不可见断言。
- [x] AC-03（WP-C）：`rg '"example-project"' apps/web/src/api` 无硬编码常量
  （仅默认值一处）；切换器 live 可用；projects 页 live；example-isolation
  仍 0 `/api`；tsc/eslint/unit/build 全绿。
- [x] AC-04（WP-D）：openapi 零漂移；G 表/CONTROL_PLANE_API 与代码一致；
  stub e2e + live e2e（含新增项目链用例）+ m0 分组全绿；RECHECK-041 回填。

## 实施清单

- [x] WP-A 注册表（domain/port/store/router）
- [x] WP-B 真实归属（runs/settings/drafts + G 文案）
- [x] WP-C 前端上下文与页面 live
- [x] WP-D 收口（openapi/docs/e2e/RECHECK）

## 证据

- WP-A/B：commit `b55df92`；`pytest tests/adapters/sqlite/test_project_store.py
  tests/api/test_projects_api.py` = 13 passed（store 语义 + 注册表行为 + 归属/
  幽灵 404/跨项目不可见断言）；`del project_id` 残留 grep 复核仅全局资源。
- WP-C：commit `9ba606e`；web lint(0 warn)/tsc/unit 73/73/build 全绿；
  `test_security_scan` 6 passed；design-fidelity 恰 2 基线重录（projects 翻面 +
  run-timeline 顶栏切换器，9ba606e diff 核对）；live e2e 11/11（含项目注册表链）、
  stub e2e 30/30。
- 命名/行数修正：commit `57feb37`；naming + source-limits 复跑 805 passed。
- WP-D：openapi 再生（含 /projects×3，snapshot 测试复跑无漂移）；
  CONTROL_PLANE_API/CONSOLE_PAGE_MAP G2 与实现一致；全量 pytest（DSN 固化）
  exit 0、0 failed；m0 python 6 / typescript 9 / framework 8 全绿；
  RECHECK-20260912-041 = PASS_WITH_WARNINGS（F-1~F-3 收口处置，F-4~F-6 记录）。
- CI：push 分两批（代码批 →57feb37；收口批随后），GitHub Actions m0-quality
  终态记于 GOAL 迭代日志。

## 状态历史

- 2026-09-13 由 GOAL-20260912-001 cycle 1 派生（/goal 指令），进入执行。
- 2026-09-13 WP-A/B/C/D 完成；独立复检 RECHECK-20260912-041 = PASS_WITH_WARNINGS（F-2 AC 文案与 F-3 docstring 在收口修正，F-1 push 时序在收口批解决）；PLAN-041 DONE。

## 影响报告

- Domain/API/schema：新增 `ProjectDefinition` 域 + `ProjectStore` Port +
  `GET/POST/PATCH /projects`；`ProjectSettingsStore.get(project_id)` 签名扩展
  （Port 语义收紧为按项目精确，examples 回退仅默认项目）；openapi 再生。
  M5 冻结 Port 只增（ProjectStore 为新 Port；settings get 为控制面内部契约，
  无外部实现方——两 composition 均注入 Sqlite 实现）。
- 安全/凭据：无新秘密面；projects 写路径强制 Idempotency-Key；活动项目为
  本地 view-state（无凭据）。
- 兼容性/迁移：`projects` 表由 adapter 自建；旧 settings JSON 行主键即
  project_id（既有列），无需迁移；默认项目行为不变（examples 回退保持）。
- 上游版本影响：无。
- 下一项任务：GOAL cycle 2 = PLAN-042（EC-02：reports/integrations/全局血缘
  经既有 deliverable builder、tool_plane、跨 run 投影的 HTTP 面 + 页面翻 live）。
