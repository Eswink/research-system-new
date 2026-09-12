---
id: PLAN-20260912-040
slug: frontend-backend-seams-and-surfacing
title: 后端组成浮现与前后端接缝闭合（040/041/042 系列第一轮）
status: IN_PROGRESS
created_at: 2026-09-12
updated_at: 2026-09-12
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-12 用户要求补充后端（前端预留接口或数据）并完整对接；Plan Mode 批准 PLAN-040/041/042 系列（040 接缝与既有能力浮现 → 041 GAP 新域与页面翻 live → 042 语义深水区）；本轮 040 按批准计划执行"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260912-040 — 后端组成浮现与前后端接缝闭合

## 目标

把"已有实现但没接线/没端点/契约不闭合"的接缝全部接上：SQLite 开发组成改用已实现
且有测试的持久 Store（Artifact/Memory），补 SQLite ExperimentStore 与 WorkerRegistry
消灭 dev 路径 503；补齐低危写语义（删除、自定义 role/template/agent clone、
runs approvals 列表、compatibility 投影）；前端接回被绕开的请求 DTO、统一禁用逻辑、
隔离 live shell 中的 example fixture 泄漏、清理死代码。041（9 GAP 页新域）与
042（预算调整/真暂停/实验队列/Diff/预测）不在本轮。

## 范围

- 包含：
  - WP-A 后端组成浮现：`_assemble_sqlite` 接 `SqliteArtifactStore`（blob 目录持久，
    替换 in-memory FakeArtifactStore，同实例共享给 orchestration 与读端点）与
    `SqliteMemoryStore`；新增 `adapters/sqlite/experiment_store.py` 与
    `adapters/sqlite/worker_registry.py`（照 PG 版实现 Port，两组成注入）；
    `/runs/{id}/evidence|claims` 未知 run → 404；`GET /health` 组成摘要端点，
    compose healthcheck 改用之。
  - WP-B API 面补齐：`GET /runs/{id}/approvals`；`POST /roles/custom`、
    `POST /team-templates/custom`、`POST /agents/{id}/clone`（复用 catalog_merge
    SQLite override 链）；`DELETE /llm-endpoints/{id}`、`/models/{id}`、
    `/protocol-drafts/{id}`、`/agents/{id}`（Port 增删除语义 + SQLite/PG 实现，
    被引用 → 409）；`/models/{id}/compatibility` 的
    `hard_capability_requirements` 从 probe capability assertions 投影。
  - WP-C 前端契约与 fixture 隔离：4 个被绕开的请求 DTO 接入 client 调用点；
    `isOperationDisabled` 统一禁用面；`pageSupport.ts` 过期文案修正；
    dependency-cruiser 禁止 example-console 被 live 树 import + 四处 layout
    fixture 改 live fallback；`TeamPreflight` 改用项目引用协议；死代码清理
    （useOperations、Tooltip、DataViewFrame/useCombinedView、Donut/Heatmap、
    project.json/provenance.json 死 fixture）。
  - WP-D 收口：openapi 再生零漂移、`CONTROL_PLANE_API.md`（含 5 个高估路由的
    未提供标注）/`CONSOLE_PAGE_MAP.md`/G 表同步、stub-api 注册、live e2e 扩展、
    m0 全绿、独立 RECHECK-040。
- 不包含：041 的 9 个 GAP 新域与 projects 注册表、042 的 budget_adjust/真
  pause-resume/实验队列/Diff/预测、M18/M19（多用户/RBAC/身份）。

## 架构与数据流

与 PLAN-037 同一不变量：读取只经既有 Port 与 application use case，无第二套事实
源；写路径全部 Idempotency-Key，带版本资源 If-Match/412；store 未配置诚实 503
不伪装；UNKNOWN/第三态不并入健康或零值；PostgreSQL 为 Canonical State，SQLite 为
开发路径（本轮只增 SQLite 实现，不改 PG 语义）；OpenAPI 快照
`docs/api/openapi.m13.json` 单一 truth，contract 测试防漂移；example 树保持零
`/api`。

## 验收条件

- [ ] AC-01（WP-A）：dev 路径 artifacts 重启后仍可下载（SqliteArtifactStore）；
  memory GET/POST/DELETE 在 SQLite 组成可用；`/cluster/workers` 与项目实验
  GET/POST/archive 在 SQLite 组成不再 503；`/runs/{unknown}/evidence|claims`
  返回 404；`GET /health` 返回组成摘要且 compose 用之。
- [ ] AC-02（WP-B）：删除四端点在 SQLite/PG 双组成有测试（含引用中 409 与
  If-Match）；custom role/team-template 写入 override 并被 catalog_merge 读出；
  agent clone 产生新 agent；`GET /runs/{id}/approvals` 有数据；compatibility
  投影在有 probe 断言时非空。
- [ ] AC-03（WP-C）：tsc/eslint/unit/build 全绿；dependency-cruiser 新增规则生效
  （live 树 import example-console 即 fail）；live 模式 layout 不再渲染虚构用户/
  workspace fixture；`isOperationDisabled` 成为禁用判定单一来源。
- [ ] AC-04（WP-D）：openapi 再生零漂移；CONTROL_PLANE_API.md 无高估路由；
  stub e2e + live e2e + m0（python 6 / typescript 9 / framework 8）全绿；
  RECHECK-040 独立复审完成并回填本文件。

## 进度记录

- 2026-09-12 立项，Plan Mode 批准 PLAN-040/041/042 系列。
- 2026-09-12 WP-A 完成：`SqliteArtifactStore`（内容寻址、blob 目录默认
  `data/artifact-blobs`、写路径补 commit——原实现跨连接不可见，属既有缺陷）与
  `SqliteMemoryStore` 接入 `_assemble_sqlite`；新增
  `adapters/sqlite/experiment_store.py`、`adapters/sqlite/worker_registry.py`
  （后者注册进 WorkerRegistry contract suite，36 passed）；`/runs/{id}/evidence|
  claims` 未知 run → 404；`GET /health` 组成摘要 + compose healthcheck 改用；
  `experiment_rows` codec 移至 `adapters/contracts/`（双 store 共享）。
  tests/api 221 项通过（2 项 worker_plane 为既有 PG 环境依赖，按 DSN 固化配方
  复跑通过）；契约套件 333 passed；openapi 快照待 WP-B 后统一再生。
- 2026-09-12 WP-B 完成：`GET /runs/{run_id}/approvals`（list_for_run 历史面）；
  `POST /roles/custom` + `POST /team-templates/custom`（新 CatalogOverrideStore
  Port + Sqlite 实现，schema/domain 双校验、id 冲突 409、缺 store 503，合并视图
  与 examples 项同构）；`POST /agents/{id}/clone` + `DELETE /agents/{id}`；
  `DELETE /llm-endpoints/{id}`（被 model id/name 引用 → 409）、
  `DELETE /models/{id}`（agent 显式绑定 → 409）、`DELETE /protocol-drafts/{id}`
  （Port delete 扩到 InMemory/SQLite/PG 三实现 + 契约套件用例）；
  `/models/{id}/compatibility` 的 hard_capability_requirements 改为合并目录
  投影（roles.all_of/any_of + profiles.hard_capabilities）。
  conftest base deps 注入 catalog_overrides；mypy/ruff 干净；
  openapi 再生后 tests/api 241 passed + snapshot/boundaries 通过。
