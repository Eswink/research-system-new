---
id: PLAN-20260918-102
slug: console-consumes-rebuild-readiness
title: 控制台消费重建读面：三态可区分 + stub/live e2e 各一条链（EC-03）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 3 = EC-03（GOAL-005 收口结论第 4 项 / RECHECK-098 W-3：`rebuild` 读面已存在但前端未消费）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-102-console-consumes-rebuild-readiness.md
memory_entries:
  - MEM-20260918-075
---

# PLAN-20260918-102 — 控制台消费重建读面（GOAL-006 cycle 3 = EC-03）

## 目标

GOAL-005 cycle 6 把"这份记录够不够重建、缺哪条事实"做成了一等读面
（`RunDetailDto.rebuild`：`SELF_CONTAINED` / `SOURCE_DEPENDENT` / `REFUSED` + `missing`），
但它**只在类型与夹具里**，控制台页面没有展示（RECHECK-098 W-3）。EC-03 要求：页面接入 +
**stub e2e 一条链 + live e2e 一条链**，并让「读面不预测结果」的口径在 UI 文案与文档**同源**。

## 先探明再动手（只读勘察）

1. **类型已在、页面未用**：`apps/web/src/api/types.ts` 有
   `RebuildReadinessDto { status, missing }` 与 `RunDetailDto.rebuild`；
   `apps/web/src/features/runs/RunPanel.tsx`（197 行）里 `grep rebuild` **零命中**。
2. **夹具已带字段**：`apps/web/tests/e2e/apiFixtures.ts` 的 run 详情夹具已有
   `rebuild: { status: "SELF_CONTAINED", missing: [] }` ⇒ stub 链的最小改动是**换状态**，
   不是补字段。
3. **页面结构**：`RunPanel` → `RunIdentity`（身份字段）→ `TaskList` / `TimelineView`；
   新增一块"重建就绪"面板应挂在 `RunIdentity` 之后（同一 `ResourceBoundary state={flow.run}` 内）。
4. **两条 e2e 渠道**：stub 走 `playwright.config.ts` + `tests/e2e/stub-routes*.ts`；
   live 走 `playwrightLive.config.ts` + `live-*.spec.ts`（live 夹具必须由域代码生成——
   内容寻址 digest 不可手写；见 GOAL-004 既有纪律）。
5. **设计基线门**：页面结构变化必须按既有流程重生成结构签名
   （`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`），
   跨平台一致性用既有容器配方复核。

## 口径

- **三态可区分，且不预测结果**（EC-03 原文）：
  - `SELF_CONTAINED` ⇒ 文案是"记录自足：重建所需输入都在库内"，**不得**写成"重建必过"；
  - `SOURCE_DEPENDENT` ⇒ 列出 `missing` 的**字段名**（W-4：字段名不是人话 ⇒ UI 做一层
    文案映射，但**不改** API 字段名）；
  - `REFUSED` ⇒ 文案是"读面拒绝给出结论"，**不得**写成"不可回填"（W-2：`REFUSED` 不裁决
    可回填性；`tools/snapshot_migrate.py` 仍是 opt-in 运营工具）。
- **零 API 变化**：不动 DTO、不动 `/runs/{id}` 响应、不重新生成 OpenAPI（本 PLAN 只消费）。
- **不改判定**：分类器（`rebuild_readiness.py`）与 `/resume` 同源关系不变。

## 验收条件

- **AC-01 页面消费**：结构判据 = `RunPanel` 的渲染路径里 `rebuild` 有渲染分支
  （不是"类型里存在"）；三态在页面上文案不同、`SOURCE_DEPENDENT` 列出 `missing`。
- **AC-02 stub e2e 一条链**：stub 夹具注入三态（至少 `SOURCE_DEPENDENT` 与非空 `missing`）
  ⇒ 页面上可区分；**反证**：去掉渲染分支 ⇒ 该 e2e 红。
- **AC-03 live e2e 一条链**：live app 上跑通一条（真实 `RunDetailDto.rebuild`，夹具由域代码
  生成）；spec 幂等。
- **AC-04 口径同源**：`docs/api/CONTROL_PLANE_API.md` 的 `rebuild` 段与 UI 文案同一口径
  （不预测结果；`REFUSED` ≠ 不可回填）——两处都点名同一判据。
- **AC-05 门禁**：web 六门（lint / typecheck / unit / build / stub e2e / live e2e）+
  设计基线/结构签名重生成（跨平台一致）+ 规模门禁 + 定向 + m0 全量 23 项 + CI 六 job 到终态。

## 实施清单

### WP-A — 页面接入

- [x] 新组件（`apps/web/src/features/runs/RebuildReadiness.tsx`，80 行）：渲染三态 + `missing`
      字段名列表 + 文案映射（`FIELD_LABELS`，集中一处）。
- [x] 接进 `RunPanel` 的渲染路径（`ResourceBoundary state={flow.run}` 内，`RunIdentity` 之后）。
- [x] i18n：中英文案都写（`zh` 分支模式）。

### WP-B — stub e2e

- [x] 新 spec（`run-rebuild-readiness.spec.ts`）：三态可区分 + `missing` 点名 + 文案不越界；
      **反证实跑**：临时去掉渲染分支 ⇒ **2 failed**，还原 ⇒ **2 passed**。
- [x] 夹具：新增 `stub-routes-runs.ts` 三条受控 run fixture（分类器三态）+ `GET /runs/{id}`
      路由（精确锚定，未注册 id ⇒ 404）。

### WP-C — live e2e

- [x] 新 `live-run-rebuild-readiness.spec.ts`：真启动 `m12_reference_research_v1.yaml` ⇒
      读面 `SELF_CONTAINED`、夹具历史行 ⇒ `REFUSED` + 四字段名；两处都断言"页面值 ==
      读面返回值"；spec 幂等（`Idempotency-Key` 带时间戳），两次实跑均 2 passed。

### WP-D — 文档同源 + 设计基线

- [x] `docs/api/CONTROL_PLANE_API.md` 的 `rebuild` 段补控制台消费点与同一口径；
      `docs/frontend/CONSOLE_PAGE_MAP.md` 的 `#/run/timeline` 条目同步。
- [x] 设计两门实跑：`design-outline-guard` 6 passed、`design-fidelity` 2 passed；
      该路由基线不选 run ⇒ 像素与结构签名**未变**，无需重生成（实跑结论，非省略）。

### WP-E — 记录与回写

- [x] RECHECK-20260918-102、MEM-20260918-075、PLAN/ALL_PLAN/`memory/INDEX.md`、
      GOAL-006 回写（EC-03 状态 / 迭代日志 / child_plans / 状态历史）。

## 证据

- **反证（页面渲染分支）**：删 `RunPanel` 的 `RebuildReadiness` 渲染 ⇒ stub spec
  **2 failed**；还原 ⇒ **2 passed**。
- **两条链**：stub `run-rebuild-readiness` **2 passed**（全量 stub 套件 **85 passed**）；
  live `run-rebuild-readiness` **2 passed**（全量 live 套件 **38 passed**）。
- **live 现场探针**（受控，起在 8012 后收掉）：m12 ⇒ 三 digest 齐 ⇒ `SELF_CONTAINED`；
  `console_demo_research_v1.yaml` ⇒ `manifest_digest: null` ⇒ `REFUSED` + `missing:
  ["manifest_digest"]`；历史行 ⇒ `REFUSED` + 四个字段名。
- **web 六门 / 规模门禁**：`run_all_checks.py --profile typescript` ⇒ **9/9 PASS**
  （首跑 1 红：live spec 内联 `import("...")` 类型触发 `no-restricted-syntax` ⇒ 顶层
  `import type { Page }`；未改任何断言）。
- **m0 全量**：`make validate-all`（DSN pin 配方）⇒ **PASS: profile=m0; 23 deterministic checks**。
- **执行修正（口径）**：分类器不变量是 `missing` 非空 ⇔ `REFUSED`（`SOURCE_DEPENDENT`
  本身不带 `missing`）。故"列出 `missing` 字段名"落在 `REFUSED` 态；面板不特判状态、
  有 `missing` 就列，两态都按读面值渲染。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 3 = EC-03，driver=client-goal / owner=root-agent）：
  只读勘察确认类型与 stub 夹具已带 `rebuild`、页面零消费；`status: IN_PROGRESS`。
- 2026-09-18 执行完成：WP-A…WP-E 全绿（反证 + 两渠道 e2e + 文档同源 + m0 23/23）；
  `status: DONE`；`latest_recheck` 指向 RECHECK-20260918-102（PASS_WITH_WARNINGS，W-1…W-5）。

## 影响报告

- **Domain / API / schema**：Domain 与 API **零变化**（只消费既有 DTO）；OpenAPI 快照不变。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无凭据面变化；页面只读既有字段。
- **兼容性 / 迁移风险**：低（新增一块只读展示）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 4 = EC-04（时钟断言去调度依赖 + 真墙钟对照矩阵）。
