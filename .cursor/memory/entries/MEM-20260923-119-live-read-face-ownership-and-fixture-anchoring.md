---
id: MEM-20260923-119
title: "页面级 live 用例的前置两问：该页消费的读面是 per-run 还是 per-project？夹具该挂既有 run 还是新建？"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-152-live-page-read-face-batch-three.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-153-live-page-read-face-batch-three.md
supersedes: []
---

## 做了什么

GOAL-013 EC-02 第三批写三条页面级「页面 == 读面」用例时，**两处前置事实**各让第一版
用例失败一次，都不是被测代码的缺陷：

**前置一：同一域里 per-run 与 per-project 两条读面都存在，页面只消费其中一条。**
`#/portfolio/experiments` 消费的是 **`GET /runs/{id}/experiments`**（要 `?run=`），
而我先按项目级 `GET /projects/{id}/experiments`（确实存在、也有数据）写了用例。
实测**红**：没有 `?run=` 时页面渲染「未选择运行」空态，`table[aria-label="实验列表"]`
**在 DOM 里根本不存在**，`tbody tr` 永远等不到。
⇒ 教训：**同名读面存在 ≠ 页面消费它**。「先用 HTTP 打那条读面」这一步必须打**页面真正调用的那条**，
否则用例会以「读面有数据但页面空」的形态失败 —— 那正是被测对象无关的假失败。

**前置二：夹具挂既有 run 而不是新建 run。**
`insights/reports` 的非空方向需要一份持久化 `deliverable.json`，而 live app 的 Fake 链
不跑 M12 参考链（四条 run 全 `available: false`）。补夹具时**挂在既有 run** `1111…1111` 上，
而不是新建一条 run：新建 run 会改动 `GET /projects/{id}/runs` 的长度、`run_count`、
血缘图节点数等**既有读面数字**，别的 live 用例即使不读它也会被扰动。

## 为什么这样做

页面级 live 用例的价值全在「页面 == 读面」这条等式上；等式两边必须是**同一个对象的同一条读面**。
per-run / per-project 选错时，等式两边根本不是一个东西 ⇒ 用例失败但**结论无效**
（既不能证明页面坏，也不能证明页面好）。先把「哪条读面」钉死，再谈断言强度。
同理，夹具一旦扰动别人的读面，红的就是**别的用例**，而根因在本 cycle 的夹具上——
这种跨用例污染最难归因。

## 怎么做与复现

- 定读面前先读页面源码的**数据获取调用**（`useResource(...) => api.xxx(...)`），
  不要只按路由名或 `docs/frontend/CONSOLE_PAGE_MAP.md` 的域推断：
  `apps/web/src/features/experiments/ExperimentsPage.tsx` 取的是
  `api.runExperiments(runId)`，且 `runId === ""` 时直接渲染空态、**不渲染表**。
- 复现前置一的红线：用项目级读面 + 不带 `?run=` 写用例 ⇒ `toHaveCount` 等到超时，
  页面上是「未选择运行」而不是那张表。
- 夹具挂既有 run 的做法见 `tests/api/console_api_app.py` 的
  `LIVE_DELIVERABLE_RUN_ID = LIVE_SNAPSHOT_RUN_ID` 与其上方的注释：
  `store.put(Artifact(...), payload)`，artifact id 必须是域侧约定的
  `f"{run_id}:deliverable.json"`（`services/api/routers/deliverable.py` 按此查）。

```bash
# 确认页面消费哪条读面：直接打两条，看谁被页面用
curl -s "http://127.0.0.1:8011/projects/example-project/experiments" | head -c 200
curl -s "http://127.0.0.1:8011/runs/<run-id>/experiments" | head -c 200
```

## 适用边界

- 「先确认读面归属」对本仓所有 `*Page` 都适用：`run/*`、`govern/*`、`insights/*` 多数是
  per-run（`?run=` 或 `ctx.selectedRunId`），`ops/*`、`portfolio/projects` 多数是 per-project
  **或全局**（如 `GET /tool-providers` 根本没有 run/project 维度）。
- 「夹具挂既有实体」不是硬规则：当被测用例**需要**一条新 run（例如要一条全新的空 run 做反证）
  时，新建是正当的；代价是必须**同时**核对该改动有没有动到别的 live 用例的读面数字。
- 受控夹具必须在代码注释与记录里**如实标注**它不是真实执行产物（承 GOAL-012 EC-05 的口径）；
  否则「页面 == 读面」的等式会被误读成「页面 == 真实研究结果」。
- 相关：[[MEM-20260923-117-live-page-equals-read-face-writing-traps]]（同族判据写法陷阱）。

## 来源

- `apps/web/tests/e2e/live-portfolio-experiments.spec.ts`（per-run 读面 + `?run=`）、
  `apps/web/tests/e2e/live-insights-reports.spec.ts`（夹具消费方）、
  `tests/api/console_api_app.py`（受控交付物夹具）。
- `scratch/goal013-c3-press-*.txt`（三条按页面按压的红证）。
