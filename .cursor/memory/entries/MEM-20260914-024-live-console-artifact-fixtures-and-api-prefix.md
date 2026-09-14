---
id: MEM-20260914-024
title: live e2e 的产物面靠受控 fixture 而非参考链；vite 代理剥 /api 前缀，两个 playwright 配置要同步登记
status: ACTIVE
created_at: 2026-09-14
updated_at: 2026-09-14
scope: repository
confidence: 0.85
review_after: 2026-12-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260914-047-artifact-content-diff.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260914-047-artifact-content-diff.md
supersedes: []
tags:
  - e2e
  - playwright
  - live-api
  - artifacts
  - fixtures
---

# MEM-20260914-024 — live 制品面 fixture 与 live 套件登记

## 做了什么

cycle 7（PLAN-047）为制品内容 diff 补 live e2e 时，实测发现 live 链拿不到制品，
于是把受控制品放进 test-only 的 FastAPI 装配，并同步登记两个 playwright 配置。

## 事实一：live 链的 m12 参考链不产出制品

`tests/api/console_api_app.py` 是 `create_app(make_run_ready_deps())` 的单进程装配
（Fake Ports，无后台 worker、无真实执行）。实测：`POST /projects/example-project/runs`
（`m12_reference_research_v1.yaml`）返回 200 但 run 终态 **FAILED**，且
`GET /runs/{id}/artifacts` 恒返回 **0 条**。所以任何需要真实制品内容的 live 断言
（diff、预览、下载、data-health 计数）都不能指望参考链产出。

处置：在装配里往共享 Fake store `put` 两份受控 JSON——
`LIVE_DIFF_ARTIFACTS = ("live-fixture:before.json", …) / ("live-fixture:after.json", …)`，
live spec 直接用这两个 id 断言真实 HTTP 形状（1 added / 1 removed / 3 context；
同制品自身 `identical=true`；未知 id → 404 `title=Artifact Not Found`）。

## 事实二：vite 代理会剥掉 `/api` 前缀

`apps/web/vite.config.ts` 的代理带 `rewrite: path.replace(/^\/api/, "")`。
浏览器/`page.request` 写 `/api/...` 是对的，但用 `TestClient(app)` 直连探针时必须写
**不带前缀**的路径（`/runs/...`、`/artifacts/...`）。带前缀会得到 FastAPI 裸 404
`{"detail":"Not Found"}`——与 ApiError 的 `{"type","title","status","detail","instance"}`
形状不同，可据此快速区分"路由没注册"与"路由注册了但对象不存在"。

## 事实三：live 与 stub 两套配置各自白名单

- `apps/web/playwright.config.ts`：`testIgnore: /live-(api-workflow|artifact-diff)\.spec\.ts/`
- `apps/web/playwrightLive.config.ts`：`testMatch: /live-(api-workflow|artifact-diff)\.spec\.ts/`

新增 live spec 必须同时改两处；只改一处会导致该 spec 要么被 stub 套件误跑
（无后端 → 全红），要么根本不进 live 套件（对 CI 静默失效）。

## 为什么这样做

"用空列表糊过去"会让 live 断言退化成只验状态码（假绿）；在 test-only 装配里放
带前缀的受控 fixture，既保住真实 HTTP + 真实计算，又不引入生产数据或凭据。

## 怎么做与复现

- live 装配：`tests/api/console_api_app.py::_with_artifacts`（`LIVE_DIFF_ARTIFACTS`）。
- live 断言：`apps/web/tests/e2e/live-artifact-diff.spec.ts`；运行
  `pnpm --dir apps/web test:e2e:live`（配置内起 uvicorn:8011 + vite:5174，17/17）。
- 探针（无需浏览器）：`uv run --frozen --no-sync python -c "…TestClient(app)…"`，
  路径不带 `/api`。

## 适用边界

- 只适用于 `tests/api/console_api_app.py` 驱动的 live e2e；不改变生产 `create_app`
  的装配（`services/api/composition.py` 不读这些 fixture）。
- 参考链 FAILED 是 Fake 执行链的既定事实；若将来给 live 装配加真实 worker，
  应同时复核本条目。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260914-047-artifact-content-diff.md`（WP-D）
- 复检：`.cursor/plans/rechecks/RECHECK-20260914-047-artifact-content-diff.md`
- 代码：`tests/api/console_api_app.py`、`apps/web/playwright.config.ts`、
  `apps/web/playwrightLive.config.ts`、`apps/web/tests/e2e/live-artifact-diff.spec.ts`
- 相关：MEM-20260913-021（夹具/CI 假绿）、MEM-20260910-018（质量门机制）
