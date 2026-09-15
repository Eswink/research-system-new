---
id: PLAN-20260915-061
slug: project-delete-and-archive-semantics
title: 项目删除语义（G2）：被引用即 409 不级联，默认项目不可删
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 7 = EC-06（G2 项目归档/删除 + 每 cycle 门禁/CI 全绿 + 收口复检）。授权来源同 GOAL-20260915-002：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-061-project-delete-and-archive-semantics.md
memory_entries:
  - MEM-20260915-037-delete-must-refuse-when-referenced
---

# PLAN-20260915-061 — 项目删除语义（GOAL-002 cycle 7 / EC-06）

## 目标

把 `#/portfolio/projects` 的 G2 缺口（"不提供项目删除，归档即终态"）变成真实能力，
并且**删除必须有可读的拒绝语义**，不是一个"删了会连坐研究数据"的入口：

- `DELETE /projects/{id}` 无引用 → 204，注册行与随项目创建的设置行一起删除；
- 仍被 runs / 协议草稿 / 实验队列 / 库资源 / ops 规则或事故引用 → **409 且列出引用计数**
  （`runs=2, drafts=1` 形式），**不级联**——用户须先自行处置研究数据；
- `example-project` 由 examples 契约合成 → 409 `Project Reserved`（删了也还在，
  返回 204 就是"删除成功但列表里还有"的静默陷阱）；
- 未知 id → 404；未装配 store → 503；
- 前端每行一个删除动作（默认项目按钮禁用 + 原因），删除活动项目后活动上下文回退默认项目。

## 口径（诚实边界，先写清楚再写代码）

1. **不级联**：存储层 `delete_project` 只删它被要求删的那一行；"是否允许删"的决策在
   路由层（那里才有给出原因所需的 context）。
2. **只报能证实的引用**：`_references()` 只枚举控制面**项目作用域**的存储；run 的从属
   事实（approvals/budget/evidence/eval report）由 runs 承载，`runs=N` 已经代表它们，
   不重复计数。
3. **设置行不是研究数据**：它与项目注册同生（`POST /projects` 自动落默认设置行），
   项目不存在时留着只会成为孤儿行 ⇒ 随项目一并清理，并在路由 docstring 里显式声明。
4. **归档 ≠ 删除**：`PATCH status=ARCHIVED` 改状态、可恢复；`DELETE` 移除注册行。
   页面两个动作并列，不得再用"归档即终态"当缺口说辞（`GAPS.delete` 同步收敛）。
5. **替身必须与真后端同因果**：删除后 `GET /projects` 真的变化、有引用真的 409；
   静态替身表达不了这个，因此项目路由改为状态可变模块并每用例复位。

## 背景（已核实的事实，决定了本计划的形状）

- 删除面已有先例：端点/模型/草稿/用户 Agent 的 `DELETE` 早就落地，语义一致
  （被引用 → 409）。项目是**第一个引用面横跨多个存储**的删除点，因此多一个聚合器。
- 既有端口 `ProjectStore` / `ProjectSettingsStore` 都只有读/写，没有删除；两侧 SQLite
  实现是新增方法的位置（`adapters/sqlite/project_store.py` /
  `project_settings_store.py`），沿用 `SqliteAdapterBase._record` 的事件记账。
- `services/api/routers/projects.py` 已有 `_merged_projects()`（examples 契约 + store 合并）
  与 `_store_of()`（未装配 → 503），删除路由复用这两条既有路径，不新造项目解析。
- 前端 `projectsClient` 的注释当时明确写着"无 DELETE：归档即终态"——本轮把它改成事实。

## 范围

- Domain/Port：`packages/application/ports/project_store.py`（`delete_project`）、
  `packages/application/ports/project_settings_store.py`（`delete`，幂等）。
- 适配器：`adapters/sqlite/project_store.py`（rowcount 0 → `KeyError`）、
  `adapters/sqlite/project_settings_store.py`。
- API：`services/api/routers/projects.py`（`DELETE /projects/{id}` + `_references()` +
  6 个 `_count_*` 聚合器）。
- 前端：`apps/web/src/api/{projectsClient,client}.ts`、
  `features/projects/{ProjectDeleteAction.tsx,useProjectDeletion.ts,ProjectsPage.tsx}`、
  `i18n/{zh,en}.ts`、`navigation/pageSupport.ts`。
- 测试：`tests/api/test_projects_api.py`（7 条删除语义）、
  `tests/contracts/test_openapi_snapshot.py`（EC-06 写方法断言）、
  stub e2e `apps/web/tests/e2e/{stub-routes-projects.ts,project-delete.spec.ts}`、
  live e2e `apps/web/tests/e2e/live-project-registry.spec.ts`（+ `live-specs.ts` 登记）。
- 文档/基线：`docs/api/openapi.m13.json` 重生成、`docs/api/CONTROL_PLANE_API.md`、
  `docs/frontend/CONSOLE_PAGE_MAP.md`、`portfolio-projects` 的 win32 + linux 设计基线。

## 验收条件

- [x] AC-01：无引用项目删除成功——204，且 `GET /projects` 不再含该行、
  `GET /projects/{id}/settings` 404（注册行与设置行一起消失）。
- [x] AC-02：被引用即拒绝——草稿/Run/ops 记录任一存在时 `DELETE` 409，
  detail 含 `runs=N` / `drafts=N` / `ops_rules=N` / `ops_incidents=N` 形式；
  删除后研究数据**仍在**（不级联）。
- [x] AC-03：默认项目 409 `Project Reserved`（合成基线不做静默 no-op）；
  未知 id 404；未装配 store 503。
- [x] AC-04：`ProjectStore.delete_project` 单测/接口层验证 rowcount=0 → `KeyError`
  → 404（读时在、删时没了的情形不伪装成功）。
- [x] AC-05：OpenAPI 快照重生成（+34 行，仅新增 delete 操作）且快照自恰测试通过；
  新断言 `test_openapi_contains_project_delete_method` 检查路径 + 写方法 +
  schema 描述里记录了 409/不级联。
- [x] AC-06：前端 `#/portfolio/projects` 能删除无引用项目、默认项目无删除入口（禁用 +
  原因），被引用项目的 409 detail 原样呈现且行保留；删除活动项目后活动上下文回退
  默认项目；`pageSupport` 的 `disabledOperations: ["delete"]` 删除、`GAPS.multiProject`
  与 `GAPS.delete` 改写为收敛后的诚实口径。
- [x] AC-07：替身与真后端同因果——`stub-routes-projects.ts` 状态可变（删除后列表真的
  变化、有引用 409、默认项目 409、未知 404），`project-delete.spec.ts` 4 用例绿；
  live `live-project-registry.spec.ts` 2 用例绿（真实 HTTP：409 引用清单 / 204 / 再见 404 /
  默认项目 409）。
- [x] AC-08：`portfolio-projects` 设计基线 win32 + linux 重生成并目检；
  主动量化门禁漂移（0.48% / 0.47%，阈值 2% ⇒ 不报警）。
- [x] AC-09：本地 m0 = `profile=m0; 23 deterministic checks`（首跑红：治理校验拦下
  "MEM-037 的来源 PLAN/RECHECK 尚不存在"——本轮先写记忆后写计划所致，补文件后复跑绿）。
- [x] AC-10：文档同步——`CONTROL_PLANE_API.md` 的 Projects 段补 `DELETE` 判定顺序与
  不级联口径；`CONSOLE_PAGE_MAP.md` 的项目集条目与 G2 缺口行同步。

## 实施清单

- [x] WP-A 端口 + SQLite 适配器（`delete_project` / `delete`，幂等 + 事件记账）
- [x] WP-B 路由（判定顺序 + `_references()` 聚合）+ 7 条 API 用例 + OpenAPI 快照与断言
- [x] WP-C 前端（客户端方法 + 删除动作 + 状态机 + i18n）+ pageSupport 收敛
- [x] WP-D stub 替身改造（状态可变、拥有 /projects 四个方法）+ stub/live e2e + live-specs 登记
- [x] WP-E 文档、设计基线（含漂移量化）、RECHECK-061、GOAL/ALL_PLAN/记忆记账、m0、CI

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/api/test_projects_api.py -q` → **13 passed**（含 7 条删除语义：无引用 204 / 被运行引用 409 / 被持久化 run 引用 409 / 被草稿引用 409 / 被 ops 引用 409 / 默认项目 409 / 未装配 503） | PASS |
| WP-B | `pytest tests/api -q` → **361 passed**（无回归） | PASS |
| WP-B | `python -B tools/gen_openapi.py` 重生成（+34 行，仅 delete 操作）；`pytest tests/contracts -q` → **359 passed, 56 skipped** | PASS |
| WP-C | 根 `npx eslint .` = 0 error（1 条既有 soft warning）；web `tsc --noEmit` 通过；单测 **76 passed** | PASS |
| WP-D | stub e2e `project-delete.spec.ts` **4 passed**（默认项目禁用 / 引用 409 呈现 / 删除后消失 / 活动上下文回退）；全量 stub 套件 **59 passed in 15 files** | PASS |
| WP-D | live e2e `live-project-registry.spec.ts` **2 passed**（真实 HTTP）；全量 live 套件 **31 passed in 9 files** | PASS |
| WP-E | 基线：`portfolio-projects` win32（本地）+ linux（pinned noble）重生成并目检；漂移量化 `scratch/cycle7-baseline-drift/measure.py` → 0.48% / 0.47% | PASS |
| WP-E | 本地 m0：首跑 `FAILED [framework/validate]`（MEM-037 的来源文件尚不存在）→ 补 PLAN/RECHECK 后复跑 `profile=m0; 23 deterministic checks` | PASS（先失败后修复） |

## 已知风险

- **设计门禁的容差盲区（第三次复现）**：`portfolio-projects` 这轮多了整行项目与逐行删除
  动作，旧基线按 Playwright 判据（pixelmatch，YIQ 阈值 0.2）只差 **0.48%（win32）/
  0.47%（linux）**，低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁**不会报警**（与 cycle 3 的
  1.73%、cycle 5 的 1.02%/0.93%、cycle 6 的 0.79%/0.66% 同类）。
- **替身不校验 `Idempotency-Key`**：`DELETE` 属于 mutating 方法（中间件要求该头），
  但 `tests/e2e/stub-api.ts` 只做路由匹配 ⇒ "stub 全绿"不能证明写面可用；
  live 套件是这条约束的唯一守卫（本轮 live 用例正是这样发现并修正了漏带的 key）。
- **引用枚举有上限**：草稿计数走 `_DRAFT_SCAN_LIMIT = 200`（`protocol_draft_service.list`
  是分页接口），项目草稿超过 200 时计数封顶——只影响"引用清单里的数字"，不影响
  "是否 409"的判定（>0 即拒绝）。
- **删除不检查跨项目引用**：引用枚举全部按 `project_id` 过滤；若将来出现"跨项目引用"
  （例如共享数据集），需要新的引用面，本轮不预置。
- **活动项目回退是前端行为**：后端没有"当前项目"概念；如果用户在别的标签页删了当前
  活动项目，本地上下文仍指向已删 id（读面会 404，不会静默返回别的项目数据）。
- live 套件文件行数：`live-api-workflow.spec.ts` 逼近 450 行硬上限，本轮把项目链拆到
  `live-project-registry.spec.ts`；后续新增 live 用例优先新开文件，只在 `live-specs.ts`
  登记一处。

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 7，取 EC-06（G2）。
- 2026-09-16 WP-A/WP-B 完成：端口 + SQLite 删除方法、路由判定顺序与引用聚合、
  7 条删除语义用例、OpenAPI 快照重生成与写方法断言。
- 2026-09-16 WP-C/WP-D 完成：前端删除动作与状态机、i18n、pageSupport 收敛；
  替身改造为状态可变 + stub 4 用例 + live 2 用例（含 live-specs 登记与文件拆分）。
- 2026-09-16 WP-E：文档两处同步、基线重生成 + 漂移量化 0.48% / 0.47%；
  m0 首跑红（治理校验：记忆来源文件缺失）→ 补齐后复跑 23/23；RECHECK-061 =
  PASS_WITH_WARNINGS。

## 影响报告

- 改动：新增 `packages/application/ports/{project_store,project_settings_store}.py` 的删除
  方法、`adapters/sqlite/{project_store,project_settings_store}.py` 实现、
  `services/api/routers/projects.py` 的 `DELETE` 路由与引用聚合、
  `apps/web/src/features/projects/{ProjectDeleteAction.tsx,useProjectDeletion.ts}`、
  `apps/web/tests/e2e/{stub-routes-projects.ts,project-delete.spec.ts,live-project-registry.spec.ts}`、
  `.cursor/memory/entries/MEM-20260915-037-*.md`、`scratch/cycle7-baseline-drift/measure.py`；
  修改 `apps/web/src/api/{projectsClient,client}.ts`、`features/projects/ProjectsPage.tsx`、
  `i18n/{zh,en}.ts`、`navigation/pageSupport.ts`、
  `tests/api/test_projects_api.py`、`tests/contracts/test_openapi_snapshot.py`、
  `apps/web/tests/e2e/{stub-routes,live-api-workflow.spec.ts,live-specs}.ts`、
  `docs/api/{openapi.m13.json,CONTROL_PLANE_API.md}`、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `portfolio-projects` 基线 ×2 平台、`.cursor/memory/INDEX.md`。
- lint/typecheck/test：Python m0 = `profile=m0; 23 deterministic checks`（首跑红一次：
  治理校验的记忆来源缺失，补齐后绿）；API 361 passed；契约 359 passed / 56 skipped；
  前端 eslint 0 error、`tsc --noEmit` 通过、单测 76 passed、stub e2e 59 passed、
  live e2e 31 passed。
- Domain/API/schema 变化：**新增 1 条端点** `DELETE /projects/{project_id}`（204/404/409/503）；
  `ProjectStore` / `ProjectSettingsStore` 端口各加一个删除方法（**新增方法，非破坏性**：
  既有实现只需补一个方法）；OpenAPI 快照 +34 行（仅新增 delete 操作，无既有 DTO 变更）。
- 安全/凭据变化：删除面新增，默认仍是 deny 姿态——不级联、合成行拒绝、被引用拒绝并
  给出原因；无凭据/密钥面变化；`DELETE` 走既有 Idempotency-Key 中间件（重放返回同一
  响应，不重复执行删除）。
- 兼容性/迁移风险：SQLite 侧无 schema 变更（沿用既有 `projects` / `project_settings` 表）；
  PG 侧沿用既有 `delete_project` 语义面，无迁移脚本；老客户端不调用新端点即行为不变。
- 上游版本影响：无新依赖、无版本 pin 变更。
- 下一项任务：GOAL-20260915-002 收口复检（六个 EC 全 PASS 后立 `PLAN-20260915-062`
  作为 GOAL 收口 RECHECK），随后按 README 终止条款把 GOAL 状态置 ACHIEVED。
