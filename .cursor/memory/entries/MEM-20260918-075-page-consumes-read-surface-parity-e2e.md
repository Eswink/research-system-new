---
id: MEM-20260918-075
title: "页面消费读面的判据：两渠道 e2e 断言'页面值 == 读面返回值'，夹具三态从分类器判据逐个构造"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.88
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-102-console-consumes-rebuild-readiness.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-102-console-consumes-rebuild-readiness.md
supersedes: []
tags:
  - console-frontend
  - e2e
  - read-surface
  - fixtures
  - test-determinism
---

# 页面消费读面：怎么证明"真的接上了"，以及 live 夹具该用哪条协议

## 做了什么

GOAL-005 交付了 `RunDetailDto.rebuild`（重建能力读面：`SELF_CONTAINED` /
`SOURCE_DEPENDENT` / `REFUSED` + `missing`），但前端只在 `types.ts` 里"有字段"、
页面零消费（RECHECK-098 W-3）。GOAL-006 cycle 3（EC-03）把它接上 `#/run/timeline`
（`RebuildReadiness.tsx`，三态文案 + `missing` 行字段名 + "不预告重建结果"固定注），
并给出两渠道证明。

## 为什么这样做

- **"类型里有" ≠ "页面接了"**：唯一站得住的判据是把渲染分支去掉后 e2e 会红。
- **断言页面值，不要断言 spec 常量**：live/stub 都先经 HTTP 取读面真值，再与 DOM 比对
  （`toHaveText(detail.rebuild.status)`、`missing` 逐名 `toContainText`）⇒ 页面自己算错、
  硬编码、或与服务端不同源时都会红。
- **三态夹具必须从分类器判据逐个构造**：`packages/application/run_orchestration/rebuild_readiness.py`
  的判据是"行上四个事实"（`manifest_digest` / `manifest_semantic_digest` / `protocol_body` /
  `protocol_source`），`missing` 的顺序由 `_MISSING_ORDER` 决定；夹具按这些事实造行，
  不要按"看起来像"造。

## 怎么做与复现

```bash
cd apps/web
pnpm exec playwright test run-rebuild-readiness --reporter=line          # stub 链：2 passed
pnpm exec playwright test --config playwrightLive.config.ts run-rebuild-readiness  # live 链：2 passed
# 反证：删掉 RunPanel 里 <RebuildReadiness .../> 渲染分支 ⇒ 上面 stub 链 2 failed
```

- **stub 侧替身此前没有 run 详情路由**：`tests/e2e/stub-routes*.ts` 里只有 `/runs/{id}/artifacts`
  等子资源，`GET /runs/{id}` 缺失 ⇒ 运行页在替身里只能取"未选择 run"的空壳基线。
  新增 `stub-routes-runs.ts`（`GET /runs/{id}` 用精确锚定 `^/runs/[^/]+$`，别遮蔽子资源；
  未注册 id 返回 404，不要静默空对象）。
- **`url.pathname.split("/")[2]` 是坑**：stub handler 拿到的是 `/api/runs/{id}`，
  id 在**索引 3**（0 空串、1 `api`、2 `runs`）。索引写错时错误信息是 `no stub run runs`。

## 适用边界（踩过的坑）

- **live app 里哪条协议给什么读面**（`tests/api/console_api_app.py`，Fake Ports）：
  - `m12_reference_research_v1.yaml` ⇒ 行上 freeze 完整（manifest digest + 语义 digest +
    冻结正文）⇒ `SELF_CONTAINED`（**即使 run 终态是 FAILED**：读面只回答"记录够不够重建"）；
  - `console_demo_research_v1.yaml` ⇒ 该夹具下 `manifest_digest` 为 `null` ⇒
    `REFUSED` + `missing: ["manifest_digest"]`；
  - 夹具历史行 `LIVE_SNAPSHOT_RUN_ID`（`11111111-1111-4111-8111-111111111111`，无任何装配输入）
    ⇒ `REFUSED` + 四个字段名。
  需要"记录自足"的 live 证据就用 m12；需要 `missing` 点名就用历史行。
- **`SOURCE_DEPENDENT` 在 live 夹具里造不出来**：它要求"两个 digest 齐、无冻结正文、来源仍可解析"
  ——人为形态，本轮没有 live 覆盖（stub 覆盖渲染、API 用例覆盖判定）。
- **新面板没有像素基线**：`#/run/timeline` 的设计基线**不选 run**（面板只在选中 run 时渲染），
  所以结构签名/截图判据实跑绿且未变 ≠ 新面板被视觉保护。要保护得新增"带 run 的 run/timeline"
  基线（含 win32/linux 双平台像素）。
- **`missing` 的人话映射允许留白**：`FIELD_LABELS` 只收录少数几个字段名，其余原样展示
  （不猜语义）；映射表里可以存在今天不可达的预留项，但要在复检里如实登记，别当它有来源。
- 相关：[[MEM-20260918-072]]（重建读面点名缺失事实）、
  [[MEM-20260918-073]]（组合读一次语句=一个快照）、
  [[MEM-20260918-069]]（死声明要么给消费者要么移除——`missing` 人话映射同理，留白要有理由）。

## 来源

- PLAN-20260918-102 / RECHECK-20260918-102（GOAL-20260918-006 cycle 3 = EC-03）。
- 上游：RECHECK-20260918-098 W-3（`rebuild` 读面前端未消费）、
  GOAL-20260918-005 收口结论第 4 项。
