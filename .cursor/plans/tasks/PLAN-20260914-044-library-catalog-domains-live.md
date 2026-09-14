---
id: PLAN-20260914-044
slug: library-catalog-domains-live
title: prompts/datasets/notebooks 最小库目录域 + 页面 live（GOAL-001 cycle 4：EC-03 第一批）
status: DONE
created_at: 2026-09-14
updated_at: 2026-09-14
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 4（/goal 持续循环迭代指令）；范围=EC-03 的 prompts/datasets/notebooks 三域；alerts/incidents/schedules/data-health 属 EC-03 第二批（cycle 5）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260914-044-library-catalog-domains-live.md
memory_entries:
  - .cursor/memory/entries/MEM-20260913-022-linux-baseline-worktree-overlay.md
---

# PLAN-20260914-044 — 库目录域（prompts/datasets/notebooks）翻 live（cycle 4）

## 目标

为 `#/library/prompts`、`#/library/datasets`、`#/library/notebooks` 三页建立最小
可用的**用户标注库目录**域：`LibraryResource`（kind 区分三类）+ 项目归属 + 生命周期
（创建/重命名/归档），SQLite 开发路径与 PG canonical 双支持，API + 前端 client +
三页翻 live。

诚实边界（不做假）：本域只承载**元数据与引用**（id/name/description/kind/tags/
content_ref/status），不伪造内容存储、版本树或 A-B 测试；`content_ref` 为不透明引用
（可空），不解析、不下载。datasets 的**评测输入**仍由既有 eval spec 承载（本域不与
其耦合，避免第二套真相）。

## 范围

- 包含：
  - WP-A 域与存储：`packages/domain/library.py`（`LibraryResource` +
    `ResourceKind` + 状态机 ACTIVE ⇄ ARCHIVED，有界校验）；
    `packages/application/ports/library_store.py`（Protocol）；
    `adapters/sqlite/library_store.py`（JSON-blob + upsert + 确定性排序 + KeyError）。
    **存储归属修正**：本域属**配置面**（与 projects/settings/agents/notification_reads
    同类）；实测 `composition.py::_sqlite_config_stores` 与
    `pg_composition.py::_pg_config_stores` 的配置面 store 在**两组成都用 SQLite
    同侧**（PG 侧无 projects 表）——故 library_store 同样只在两组成注册 SQLite
    实现，**不新增 PG 表/迁移**（新增才是第二套真相）。
  - WP-B API：`services/api/routers/library.py`（`GET/POST /projects/{id}/library`、
    `GET/PATCH /library/{resource_id}`；kind 过滤；未知 404；无 DELETE（归档终态）），
    DTO 与 composition/pg_composition 装配。
  - WP-C 前端：`libraryClient` + 三页消费真实端点（kind 参数化共享组件），
    pageSupport 等级与 disabledOperations、CONSOLE_PAGE_MAP/CONTROL_PLANE_API 同步。
  - WP-D 测试与收口：domain/store/api/前端单测；stub e2e 替身；live e2e；
    基线按需再生；m0 全绿；RECHECK + MEM。
- 不包含：内容存储/版本树/A-B/发布；datasets 与 eval spec 的耦合；
  PG 表/迁移（配置面同侧约定）；`alerts/incidents/schedules/data-health`
  （EC-03 第二批，cycle 5）。

## 架构与数据流

```
GET /projects/{id}/library?kind=prompt → LibraryStore.list(project_id, kind)
POST /projects/{id}/library           → 校验 + save（自动 project_id 归属）
PATCH /library/{id}                    → rename/archive（未知 404）
```

三页 = 同一列表/详情组件按 kind 实例化；无内容面，仅目录事实。

## 验收条件

- [x] AC-01（WP-A）：LibraryResource 有界校验（kind 非法/name 空超长拒绝）；
  store upsert/list 确定性/KeyError；SQLite 与 PG 语义一致。
- [x] AC-02（WP-B）：三端点（创建 201/列表按 kind 过滤/未知 404/PATCH 归档）；
  openapi 快照再生零漂移；无 DELETE。
- [x] AC-03（WP-C）：三页消费真实端点、pageSupport 与文档一致；web
  lint/typecheck/test/build 全绿。
- [x] AC-04（WP-D）：m0 全绿 + stub/live e2e 绿；push 后 quality-ubuntu 与
  console-frontend 全绿；RECHECK-044 回填。

## 实施清单

- [x] WP-A 域 + Port + SQLite store（配置面同侧，无 PG 表）
- [x] WP-B API + DTO + 装配
- [x] WP-C 前端 client + 三页 live + 文档
- [x] WP-D 测试 + 本地门 + 收口

## 证据

- **WP-A 域与存储**（`packages/domain/library.py`、
  `packages/application/ports/library_store.py`、`adapters/sqlite/library_store.py`）：
  LibraryResource 有界校验（name/description/content_ref/tags/kind/status）；
  JSON-blob + upsert + `ORDER BY created_at, resource_id` 确定性排序 + KeyError。
  存储归属修正：本域属**配置面**，实测 `composition.py::_sqlite_config_stores`
  与 `pg_composition.py::_pg_config_stores` 在两组成都用 SQLite 同侧（PG 侧无
  projects 表），故只注册 SQLite 实现，不新增 PG 表/迁移（否则是第二套真相）。
  证据：`pytest tests/adapters/sqlite/test_library_store.py` = **13 passed**。
- **WP-B API**（`services/api/routers/library.py`、`services/api/dto/library.py`、
  ApiDeps 增 `library_store`、两组成装配、app.py 注册）：`GET/POST
  /projects/{id}/library`（kind 过滤、未注册项目 404）、`GET/PATCH
  /library/{resource_id}`（未知 404；空载荷 422；无 DELETE→405）。
  证据：`pytest tests/api/test_library_api.py` = **7 passed**；
  `gen_openapi.py` 再生后 `test_openapi_snapshot` 2 passed。
- **WP-C 前端**：`libraryClient` + 共享 `LibraryPage`（kind 参数化）+
  ResourceCreateBar/libraryColumns；prompts/datasets/notebooks 三页翻 live；
  pageSupport 等级（gap→partial）+ disabledOperations、
  CONSOLE_PAGE_MAP（3 节 + G7/G7b 表）、CONTROL_PLANE_API 同步。
  证据：`pnpm --dir apps/web run lint/typecheck/test/build` 全绿（test 73/73）。
- **WP-D 测试与收口**：stub-api 补 library 替身；design-fidelity testid 改 live；
  console-shell 的 example 用例改用仍为 gap 的 `ops/alerts`；新增 live e2e
  「library 库目录创建/过滤/归档」。基线：3 路由 × win32 + linux 各 1 张。
  证据：stub e2e 30/30、live e2e 13/13；全量 pytest/m0 见「状态历史」。

## 已知风险

- PG 路径需真 PG 跑迁移与 store 测试；无 PG 时按既有 marker 诚实 skip。
- 三页共享组件须通过命名门禁（PascalCase 文件名 == 唯一导出）与 50 行函数限制。
- design-fidelity 基线在容器内若与库中逐字节相同会假绿；再生脚本已改为先删除
  目标 linux 基线再重写（见 MEM-20260913-022 与 WP-D 记录）。

## 状态历史

- 2026-09-14 由 GOAL cycle 4 派生，进入执行。
- 2026-09-14 WP-A~WP-D 完成并本地验证（store 13 / api 7 / web 73 / stub 30 /
  live 13 / 全量 pytest 3094 passed 0 failed / m0 23-23 PASS）；提交并 push，
  CI 终态回填。

## 影响报告

- Domain/API/schema：新增 `LibraryResource` 域 + `LibraryStore` Port + 4 个
  HTTP 端点；openapi 快照再生；无破坏性变更。
- 安全/凭据：只读目录 + 归属校验；无凭据材料；content_ref 为不透明引用不解析。
- 兼容性/迁移：无数据迁移；配置面 SQLite 同侧（不新增 PG 表）。
- 上游版本：无。
- 下一项：EC-03 第二批（alerts/incidents/schedules/data-health 最小域 + live），
  cycle 5。
