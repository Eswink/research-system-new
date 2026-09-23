---
id: PLAN-20260923-151
slug: live-page-read-face-batch-two
title: EC-02 第二批页面级「页面 == 读面」live 用例：library/lineage 与 govern/audit（含成对反证）
status: IN_PROGRESS
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-013
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-013 建档授权（2026-09-23 用户 goal 模式指令）的 **EC-02**：
    真实数据 live 链，判据形态统一为「**页面 == 读面**」（先 HTTP 取读面再与 DOM 逐值比对），
    并配**成对反证**（读面为空/缺字段 ⇒ 页面显示诚实空态，不伪造数据）；
    域覆盖要求 `plan/overview`、`portfolio/*`、`library/lineage`、`insights/*`、`ops/*`、
    `govern/*` **各至少一条**。本 PLAN 是本批的**第二批**（第一批 = cycle 1 的 `plan/overview`）。
    本 PLAN 的改动面严格限于：`apps/web/tests/e2e/` 的新 live spec 与 suite 白名单、
    `scratch/` 的读面快照（**不进仓库**）。**不改**产品 UI/API/DTO/合约、**不改**门禁/validator/
    既有断言、**不改**设计基线、**不改** `pageSupport` 标注。
    零出网（浏览器只打本机 127.0.0.1 的 live app 与 vite dev）、零凭据读取、零真实 LLM 调用。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-151 — EC-02 第二批页面级 live（library/lineage、govern/audit）

## 目标

把 GOAL-013 EC-02 的域覆盖从「plan」推进到「library + govern」，并**同时**满足两件事：
① 判据形态统一为「**页面 == 读面**」——先经 HTTP 取该页消费的读面，再与 DOM **逐值**比对；
② 每条配**成对反证**——读面为空/缺字段时页面显示**诚实空态**（不伪造、不填占位常量）。

## 计划开始前的定案（写死）

- **D-1｜EC-02 的计数口径（避免含糊）**：计入 ≥6 的用例必须**同时**满足 ——
  (i) **页面级**：`page.goto` 到该路由并对 DOM 断言；
  (ii) **读面先行**：先经 HTTP 取该页消费的读面，DOM 断言的值**由读面响应导出**（不是硬编码常量）；
  (iii) 有成对反证。**只 `page.request.get(...)` 而不断言 DOM 的既有用例不计入**
  （本仓的 `live-project-lineage` / `live-project-cost-forecast` 就是这种）；
  **D-2 的既有点名**：`live-schedules-write`（`ops/schedules`）确实 `goto` 并断言 DOM，
  但它未先取读面再比对 ⇒ **不计入** EC-02 的 6 条，只作 ops 域的既有背景（ops 域的补位见「下一轮」）。
- **D-2｜本批覆盖**：`library/lineage`（library 域）与 `govern/audit`（govern 域）各一条，
  各配成对反证 ⇒ cycle 1 的 1 条 + 本批 2 条 = **3/6**。
- **D-3｜`govern/budget` 本批不做，理由落证据**：实测（本机 live app，`console_api_app`）
  该页消费的**三条读面全为空**——`GET /runs/{id}/usage` ⇒ `entries: []`、`total_estimated_cost_minor: null`；
  `GET /runs/{id}/cost-forecast` ⇒ `cost_status: "NO_DATA"`、`lines: []`、`consumed_cost_minor: null`；
  `GET /projects/{id}/cost-forecast` ⇒ `days: []`、`valued_days: 0`。
  ⇒ 该页**无法**演示「非空读面 → 非空渲染」的正向判据。按 **R-F2**（本 GOAL 建档时登记：
  数据不足无法演示非空渲染的用例**不得**计入 ≥6），本批**不为它建一个只覆盖空态的用例**来充数；
  它需要**带 usage 的受控 run 夹具**（走产品写入路径造 `usage` 条目），列为下一轮输入。
- **D-4｜`library/lineage` 的成对结构**：实测 `GET /projects/example-project/lineage` ⇒
  `run_count: 4`、`nodes: 18`、`edges: 11`、`library_resources: 0`、`reference_recording: "NOT_RECORDED"`。
  同一页上**同时**存在「非空表」（节点 18 / 边 11）与「诚实空态」（库资源 0 ⇒ 面板显示
  `项目内无库资源`）⇒ 正向与反证在**同一读面**上成立，不需要第二个 run。
- **D-5｜`govern/audit` 的成对结构**：实测 `GET /runs/{id}/events` ⇒
  run `44444444`（substrate）**1 条**、run `55555555`（experiment）**0 条** ⇒
  两个受控 run 走同一页面、同一组件，差别只在数据：一条渲染事件列表、另一条渲染空态文案
  （`没有匹配的正式事件`）。正向断言取 `ol > li` 计数 == 读面 `events.length`。
- **D-6｜按压必须按页面**（承 `MEM-20260923-113` / `MEM-20260923-115`）：本批两条判据
  两侧**同源**（DOM 的值来自读面）⇒ **按数据按压对它不敏感**。按压要打在**页面**那一段：
  把组件渲染的值钉成常量，判据必须红；改回即绿。红/绿证据落 `scratch/`。
- **D-7｜live 面纪律**：新 spec 仍只在 `apps/web/tests/e2e/live-specs.ts` 的 `LIVE_SUITES`
  加一项（两份 playwright config 共用该单一来源）；**不得**为跑通放宽出站判据
  （默认门仍离线，`tests/egress_guard.py` 不动）；浏览器只打 127.0.0.1。

## 验收条件

- [ ] `apps/web/tests/e2e/live-library-lineage.spec.ts`：正向判据 = 项目级合并图的摘要
      （运行 / 节点 / 边）与三张表的行数**逐值等于** `GET /projects/{id}/lineage` 的响应；
      成对反证 = `library_resources: 0` ⇒ 库资源面板显示诚实空态文案（不渲染空表）。
- [ ] `apps/web/tests/e2e/live-govern-audit.spec.ts`：正向判据 = Audit 页的事件行数**等于**
      `GET /runs/{id}/events` 的长度；成对反证 = 另一条 run 读面为 0 ⇒ 显示空态文案。
- [ ] 两条 spec 的 suite 名加入 `live-specs.ts`；`pnpm run test:e2e`（stub）仍绿
      （证明被 `testIgnore` 正确排除）。
- [ ] **按页面**按压：分别把两个组件渲染的值钉成常量 ⇒ 对应判据**红**；复原 ⇒ **绿**。
      红/绿证据落 `scratch/goal013-c2-press*.txt`，并在 RECHECK 里写明
      「能被什么按压 / 不能被什么按压」。
- [ ] 本地门全绿：web lint / typecheck / unit / build / stub e2e / live e2e（全套）+
      根 `eslint .`（测试面）+ `validate.py` + docs-check；m0 按既有配方（含 pinned OTel collector）。
- [ ] **不改**产品 UI/API/DTO/门禁/既有断言/设计基线/`pageSupport` 标注（用 `git diff --stat` 证明
      改动面只在 `apps/web/tests/e2e/` 与记录）。

## 实施清单

### WP1 — `library/lineage` 页面级 live
- [ ] 新 spec：读面先行（`GET /api/projects/example-project/lineage`）→ `goto #/library/lineage`
      → 断言合并摘要与三张表行数与读面一致；库资源为 0 时断言空态文案。
- [ ] 白名单加 `library-lineage`。

### WP2 — `govern/audit` 页面级 live
- [ ] 新 spec：读面先行（`GET /api/runs/{id}/events`）→ `goto #/govern/audit?run=…`
      → 断言 `[data-testid="run-timeline"]` 内的事件行数等于读面长度；
      另一条 run（读面 0 条）⇒ 断言空态文案。
- [ ] 白名单加 `govern-audit`。

### WP3 — 按压与记录
- [ ] 两处**按页面**按压先红后绿，证据落 `scratch/`。
- [ ] RECHECK 记录性质披露（能被什么按压 / 不能被什么按压）+ 两棵树成对复检。

## 证据

- 待补（执行后回写）。

## 状态历史

- 2026-09-23：**derive**（cycle 2）。定案 D-1…D-7 写死。起点事实（**直接读代码 + 打 live app 实测**，
  不当作验收依据）：`library/lineage` 的项目读面实测 `run_count=4 / nodes=18 / edges=11 /
  library_resources=0 / reference_recording=NOT_RECORDED`；`govern/audit` 的事件读面实测
  run `44444444` = 1 条、run `55555555` = 0 条；`govern/budget` 的三条读面**全空**
  （`entries: []` / `cost_status: NO_DATA` / `days: []`）⇒ 按 D-3 本批不做，理由落证据。

## 影响报告

- **Domain/API/schema**：无改动。
- **前端**：仅 `apps/web/tests/e2e/` 新增 2 个 live spec + 白名单 2 项。产品代码**零改动**。
- **文档**：本 PLAN + RECHECK（执行后）。
- **安全/凭据**：零真实出网（浏览器只打 127.0.0.1）、零凭据读取、零真实 LLM 调用。
- **兼容性/迁移**：无。
- **上游版本影响**：无新增依赖、无 pin 变更。
