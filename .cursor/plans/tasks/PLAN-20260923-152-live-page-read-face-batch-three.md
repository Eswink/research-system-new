---
id: PLAN-20260923-152
slug: live-page-read-face-batch-three
title: EC-02 第三批页面级「页面 == 读面」live 用例：portfolio/experiments、insights/reports、ops/integrations（满 6/6）
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
    `govern/*` **各至少一条**。本 PLAN 是**第三批**（cycle 1 = `plan/overview`；
    cycle 2 = `library/lineage` + `govern/audit`）⇒ 本批三条后域覆盖 **6/6**。
    本 PLAN 的改动面严格限于：`apps/web/tests/e2e/` 的新 live spec 与 suite 白名单、
    `tests/api/console_api_app.py` 的**受控夹具**（D-4；沿用该文件既有夹具模式）、
    `scratch/` 的读面快照（**不进仓库**）。**不改**产品 UI/API/DTO/合约、**不改**门禁/
    validator/既有断言、**不改**设计基线、**不改** `pageSupport` 标注。
    零出网（浏览器只打本机 127.0.0.1 的 live app 与 vite dev）、零凭据读取、零真实 LLM 调用。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-152 — EC-02 第三批页面级 live（满 6/6）

## 目标

把 EC-02 的域覆盖从 **3/6**（plan / library / govern）推进到 **6/6**（+ portfolio / insights / ops），
每条仍同时满足 **D-1** 的三件事：页面级 + 读面先行 + 成对反证。

## 计划开始前的定案（写死）

- **D-1｜EC-02 的计数口径（沿用 cycle 2，不放松）**：计入 ≥6 的用例必须**同时**满足 ——
  (i) **页面级**：`page.goto` 到该路由并对 DOM 断言；
  (ii) **读面先行**：先经 HTTP 取该页消费的读面，DOM 断言的值**由读面响应导出**（不是硬编码常量）；
  (iii) 有成对反证。只 `page.request.get(...)` 而不断言 DOM 的既有用例**不计入**
  （`live-project-lineage` / `live-project-cost-forecast` 就是这种）。
- **D-2｜本批覆盖（三域各一条，凑满 6/6）**：
  | 域 | 路由 | 读面 | suite 名 |
  | --- | --- | --- | --- |
  | `portfolio/*` | `#/portfolio/experiments` | `GET /projects/example-project/experiments` | `portfolio-experiments` |
  | `insights/*` | `#/insights/reports?run=…` | `GET /runs/{id}/deliverable` | `insights-reports` |
  | `ops/*` | `#/ops/integrations` | `GET /tool-providers` | `ops-integrations` |
- **D-3｜`portfolio/experiments` 的成对结构（实测）**：读面 2 条实验 ——
  `LIVE_EXPERIMENT_RUN_ID`（`5555…0001`）有 2 件产物（含 JSON `experiment_result.json` 带
  `metrics: {corpus_size: 2048, worst_case_comparisons: 19960}`）⇒ 页面指标字段有值；
  `LIVE_EXPERIMENT_BARE_RUN_ID`（`6666…0002`）只有 1 件**非 JSON** 产物 ⇒ 读面 `metrics` 为空
  ⇒ 页面指标字段缺省。**同一页面、同一组件，差别只在数据** —— 与 cycle 2 的 D-5 同型，
  也复用 `console_api_app._with_experiment_catalog` 既有的「rich / bare」两条受控 run。
- **D-4｜`insights/reports` 需要一份新受控夹具（如实登记）**：实测本机 live app 上
  **四个 run 的 `/runs/{id}/deliverable` 全部 `available: false`**（判词：
  「该 Run 尚无持久化交付物（仅完成 M12 参考链的 Run 产出 deliverable.json）」）——
  live app 的 Fake 链**不跑 M12 参考链**，不产出 `deliverable.json` ⇒ **无法**演示
  「非空读面 → 非空渲染」。循环内**登记为 (a) 的前置缺口并补齐**：在
  `tests/api/console_api_app.py` 按**该文件既有夹具模式**（`_seed_artifact` + 域对象
  `Artifact` + `Digest.of_bytes`，digest 由域代码生成）为**既有** run
  `LIVE_SNAPSHOT_RUN_ID`（`1111…1111`）持久化 `"{run_id}:deliverable.json"`，
  使 `available: true`。**挂既有 run 而不新建 run**：新建 run 会改 `run_count` 等既有读面数字，
  挂既有 run 则读面**只增一个字段**，其余 live 用例的读面不受扰动。
  成对反证取另一条既有 run（`available: false`）⇒ 页面显示读面 `reason` **逐字**。
  **诚实边界**：该 deliverable 是**受控夹具**，不是一次真实 M12 参考链跑出来的；本用例只判
  「读面 → DTO → 页面」这一段，**不声称**「报告来自一次真实研究运行」。
- **D-5｜`ops/integrations` 的成对结构（实测）**：`GET /tool-providers` ⇒ 3 个 provider，
  健康态依次 `HEALTHY` / **`UNKNOWN`** / `HEALTHY`（`UNKNOWN` 那条是 `ncbi_eutils`）。
  ⇒ 正向：表格行数 == `providers.length`，且 `id` 与 `health` **逐值**来自读面；
  反证：`health: "UNKNOWN"` 的那条在页面上**必须**如实显示 `UNKNOWN`，**不得**显示为
  `HEALTHY`（「无法判定」不等于「健康」——不伪造健康）。
- **D-6｜按压必须按页面**（承 `MEM-20260923-113` / `-115` / `-117`）：本批三条判据两侧
  **同源**（DOM 的值来自读面）⇒ **按数据按压对它不敏感**；按压要打在**页面**那一段
  （把组件渲染的值钉成常量 ⇒ 判据必须红；改回即绿）。**空态/否定性断言必须两端锚定 `^…$`**
  （不锚定会被前缀扩展文案骗过）；**CSS 属性选择器不做候选**，多语言 `aria-label` 必须写成
  选择器列表。红/绿证据落 `scratch/`。
- **D-7｜live 面纪律**：新 spec 只加 `apps/web/tests/e2e/live-specs.ts` 的 `LIVE_SUITES`
  （两份 playwright config 共用该单一来源）；**不得**为跑通放宽出站判据
  （默认门仍离线，`tests/egress_guard.py` 不动）；浏览器只打 127.0.0.1。

## 验收条件

- [ ] `apps/web/tests/e2e/live-portfolio-experiments.spec.ts`：正向 = 实验表行数**等于**
      `GET /projects/example-project/experiments` 的 `experiments.length`，且至少一条的
      `experiment_run_id` 出现在页面上；反证 = `LIVE_EXPERIMENT_BARE_RUN_ID` 的读面
      `metrics` 为空 ⇒ 页面对该条**不渲染指标值**（不伪造指标）。
- [ ] `apps/web/tests/e2e/live-insights-reports.spec.ts`：正向 = `available: true` 的读面
      ⇒ 页面渲染 `deliverable.objective` 与 `Provenance` 里的 `run_id` / `artifact_id`
      （值均来自读面）；反证 = `available: false` 的读面 ⇒ 页面显示读面 `reason` **逐字**，
      且**不**渲染 `Provenance` 区块。
- [ ] `apps/web/tests/e2e/live-ops-integrations.spec.ts`：正向 = provider 行数**等于**
      `providers.length`，且 `ncbi_eutils` 的 `health` 显示为读面值；反证 = `UNKNOWN` 必须
      如实显示，页面**不得**把该条显示为 `HEALTHY`。
- [ ] 三条 spec 的 suite 名加入 `live-specs.ts`；`pnpm run test:e2e`（stub）仍绿
      （证明被 `testIgnore` 正确排除）。
- [ ] `tests/api/console_api_app.py` 只**增**受控 deliverable 夹具（D-4），不改任何既有夹具语义。
- [ ] **按页面**按压：分别把三条用例各自断言的页面值钉成常量 ⇒ 对应判据**红**；复原 ⇒ **绿**。
      红/绿证据落 `scratch/goal013-c3-press*.txt`，并在 RECHECK 里写明
      「能被什么按压 / 不能被什么按压」。
- [ ] 本地门全绿：web lint / typecheck / build / stub e2e / live e2e（全套）+ 根 `eslint .`
      （测试面）+ `validate.py` + docs-check；m0 按 `MEM-20260923-116` 的配方跑（含 pinned
      OTel collector），终局行 `PASS: profile=m0; 23 deterministic checks`。
- [ ] **不改**产品 UI/API/DTO/门禁/既有断言/设计基线/`pageSupport` 标注（用 `git diff --stat` 证明
      改动面只在 `apps/web/tests/e2e/`、`tests/api/console_api_app.py` 与记录）。

## 实施清单

### WP1 — `portfolio/experiments` 页面级 live
- [ ] 新 spec：读面先行（`GET /api/projects/example-project/experiments`）→ `goto #/portfolio/experiments`
      → 断言实验表行数 == 读面长度、`experiment_run_id` 可见；bare run 的指标不渲染。
- [ ] 白名单加 `portfolio-experiments`。

### WP2 — `insights/reports` 页面级 live（含受控夹具）
- [ ] `console_api_app.py`：为 `LIVE_SNAPSHOT_RUN_ID` 持久化受控 `deliverable.json`。
- [ ] 新 spec：读面先行（`GET /api/runs/{id}/deliverable`）→ `goto #/insights/reports?run=…`
      → 断言 objective / provenance 值来自读面；`available: false` 的 run ⇒ 显示 `reason` 逐字。
- [ ] 白名单加 `insights-reports`。

### WP3 — `ops/integrations` 页面级 live
- [ ] 新 spec：读面先行（`GET /api/tool-providers`）→ `goto #/ops/integrations`
      → 断言行数 == `providers.length`、`ncbi_eutils` 的 `health` 如实为 `UNKNOWN`。
- [ ] 白名单加 `ops-integrations`。

### WP4 — 按压与记录
- [ ] 三处**按页面**按压先红后绿，证据落 `scratch/`。
- [ ] RECHECK 记录性质披露（能被什么按压 / 不能被什么按压）+ 两棵树成对复检。

## 证据

- 待执行后回写。

## 状态历史

- 2026-09-23：**derive**（cycle 3）。定案 D-1…D-7 写死。起点事实（**直接打 live app 实测**，
  不当作验收依据）：四个 run 的 `deliverable` 全 `available: false`（D-4 因此需要夹具）；
  `/projects/example-project/experiments` = 2 条（rich 的 `metrics` 有值、bare 的为空）；
  `/tool-providers` = 3 条且健康态含一条 `UNKNOWN`（`ncbi_eutils`）；
  `/projects/example-project/ops/data-health` = 7 条 metrics 但 `aggregate_available: false`；
  `/ops/schedules` = 5 条 + 5 个 job 词表 + `management_available: true`。

## 影响报告

- **Domain/API/schema**：无改动。
- **前端**：仅 `apps/web/tests/e2e/` 新增 3 个 live spec + 白名单 3 项。产品代码**零改动**。
- **测试夹具**：`tests/api/console_api_app.py` **增**一份受控 deliverable（D-4），
  只服务 live e2e，不进入任何生产路径。
- **文档**：本 PLAN + RECHECK（执行后）。
- **安全/凭据**：零真实出网（浏览器只打 127.0.0.1）、零凭据读取、零真实 LLM 调用。
- **兼容性/迁移**：无。
- **上游版本影响**：无新增依赖、无 pin 变更。
