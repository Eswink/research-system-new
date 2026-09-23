---
id: MEM-20260923-113
title: "live e2e 的「页面 == 读面」判据：夹具走产品写入路径；按压要按页面那一段（数据按压只触发夹具自检）"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-147-experiments-read-face-in-browser.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-148-experiments-read-face-in-browser.md
supersedes: []
---

## 做了什么

GOAL-012 EC-05 把「实验读面在浏览器里用真实数据渲染」判成一条 live e2e
（`apps/web/tests/e2e/live-experiments.spec.ts`，后端 `tests/api/console_api_app.py`）。
判据形态：**先经 HTTP 取读面**（`page.request.get('/api/runs/{id}/experiments')`），
再与 DOM 逐值比对（制品引用数 / 镜像指纹 slice / 指标字段数 / 抽屉里的指标原始投影）。

## 为什么这样做

- **夹具不能手写 DTO JSON**：受控 run 的实验记录走 `register_experiment_evidence`
  （run 链调用的**同一个**准入函数），指标由**内容寻址制品**的 JSON 承载（读面
  `_experiments_of_run` + `_metrics_for` 就这么取）。这样「读面 → DTO → 页面」全段都是
  产品代码在跑，夹具只决定**数据内容**。
- **只 `register_evidence` 看不到**：读面是 claim → relation → evidence 聚合的，
  必须经准入函数一次性把 Source/Evidence/Claim/关系都写齐（与既有记忆一致）。
- **成对反证要落在同一组件上**：第二条 run 的实验**只有非 JSON 制品** ⇒ 读面 `metrics`
  为空 ⇒ 同一页面/同一组件显示空态（不是把上一条 run 的值留在页面上）。
- **按压的落点**（本 cycle 实测）：
  - 按**页面**（把指标投影临时改成常量）⇒ 主干红在 `toHaveText(JSON.stringify(metrics))`，
    **反证那条仍绿**（它期望没有 `<pre>`）——这才是判「页面 == 读面」的那一刀；
  - 按**数据**（制品 JSON 的 `metrics` 键改名）⇒ 主干只在**夹具自检**
    （`Object.keys(metrics).length > 0`）上红。**数据按压对「页面 == 读面」是不敏感的**
    （两边同源，怎么改都一致），所以别把数据按压当成判据的主要证据。

## 怎么做与复现

1. 夹具：`tests/api/console_api_app.py` 的 `_with_experiment_catalog`（两条 run +
   `LIVE_EXPERIMENT_PRODUCTS` 内容寻址制品 + `_admit_controlled_experiment`）。
2. 判据：`apps/web` 下
   `pnpm exec playwright test --config playwrightLive.config.ts live-experiments`
   ⇒ **2 passed**；快照/截图写到 `EC05_SNAPSHOT_DIR`（缺省 `scratch/goal012-c5/`，**不进仓库**）。
3. **新增 live suite 必须登记** `apps/web/tests/e2e/live-specs.ts` 的 `LIVE_SUITES`：
   同一清单同时是 stub 配置的 `testIgnore`，漏登记 ⇒ stub 套件会收进一个必然失败的用例。
4. stub 套件回归：`pnpm exec playwright test --config playwright.config.ts` ⇒ **96 passed**。

## 适用边界

- 夹具的**执行体**不是真容器：本判据只覆盖「读面 → DTO → 页面」，真实容器全链在 pytest 层
  （`tests/e2e/test_ec02_experiment_chain_offline.py`、`test_ec03_experiment_evidence_chain.py`）。
- 「页面 == 读面」对**显示格式**敏感：单元格做 `slice(0,20)`、抽屉里是 `JSON.stringify(…, 2)`
  的**原始投影**，比对必须照着组件真实的渲染口径写（改组件渲染口径 ⇒ 判据要同步重钉，不是放松）。
- 表格的 aria-label 随语言变（`实验列表` / `Experiments`）：选择器要两种都接受，
  别把文案钉死成语言常量。

## 来源

- GOAL-20260923-012 EC-05；PLAN-20260923-147；RECHECK-20260923-148（PASS）。
- 实测：`scratch/goal012-c5/{read-face.json,page-values.json,experiments-page.png}`、
  两次按压 `scratch/goal012-c5-press{1,2}.txt`（先红后绿，产品代码逐字复原）。
