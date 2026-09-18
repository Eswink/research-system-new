---
id: PLAN-20260918-102
slug: console-consumes-rebuild-readiness
title: 控制台消费重建读面：三态可区分 + stub/live e2e 各一条链（EC-03）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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

- [ ] 新组件（`apps/web/src/features/runs/`）：渲染三态 + `missing` 字段名列表 + 文案映射
      （字段名 → 人话，集中一处，便于 W-4 的后续维护）。
- [ ] 接进 `RunPanel` 的渲染路径（`ResourceBoundary state={flow.run}` 内，`RunIdentity` 之后）。
- [ ] i18n：中英文案都写（仓库既有 `zh` 分支模式）。

### WP-B — stub e2e

- [ ] 新 spec（`apps/web/tests/e2e/`）：三态可区分 + `missing` 展示；
      **反证实跑**：临时去掉渲染分支 ⇒ 该 spec 红。
- [ ] 夹具：按既有 `stub-routes*.ts` 方式注入状态（不改既有夹具的默认值语义）。

### WP-C — live e2e

- [ ] 新 `live-*.spec.ts`：跑真实 app，断言 `rebuild` 在页面上可读；夹具由域代码生成；
      spec 幂等（可重复跑）。

### WP-D — 文档同源 + 设计基线

- [ ] `docs/api/CONTROL_PLANE_API.md` 的 `rebuild` 段补"控制台在哪展示、文案口径与读面一致"。
- [ ] 结构签名重生成 + 跨平台一致性复核（既有容器配方）。

### WP-E — 记录与回写

- [ ] RECHECK-20260918-102、MEM-20260918-075、PLAN/RECHECK/ALL_PLAN/`memory/INDEX.md`、
      GOAL-006 回写（EC-03 状态 / 迭代日志 / child_plans / 状态历史）。

## 证据

- 待记（执行后填写：反证实跑、web 六门、结构签名、m0、CI）。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 3 = EC-03，driver=client-goal / owner=root-agent）：
  只读勘察确认类型与 stub 夹具已带 `rebuild`、页面零消费；`status: IN_PROGRESS`。

## 影响报告

- **Domain / API / schema**：Domain 与 API **零变化**（只消费既有 DTO）；OpenAPI 快照不变。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无凭据面变化；页面只读既有字段。
- **兼容性 / 迁移风险**：低（新增一块只读展示）；设计基线需按流程重生成。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 4 = EC-04（时钟断言去调度依赖 + 真墙钟对照矩阵）。
