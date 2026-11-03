---
id: PLAN-20261103-104
slug: design-gate-and-integration-coverage
title: GOAL-104 子计划 —— 悬空样式判据 + 四组合设计门禁 + 联调补齐
status: DONE
created_at: 2026-11-03
updated_at: 2026-11-03
parent_goal: GOAL-20261103-104
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261103-104-design-gate-and-integration-coverage.md
memory_entries:
  - .cursor/memory/entries/MEM-20261103-238-a-css-module-key-can-be-undefined.md
---

# PLAN-20261103-104

## 背景与靶子

GOAL-20261103-104 的七个 EC。按**提交面**分三个 cycle：

1. **cycle 1（最小、最确定）**：三条悬空样式 + `css-token-references.test.ts`（EC-01）。
   放第一个是因为新判据会在后续所有前端改动上持续生效。
2. **cycle 2（设计门禁）**：四组合参数化 + `run-timeline-phases` 入基线 + 元素级像素
   （EC-02）。这一件要重生成**两平台** PNG 基线（win32 本地、linux 容器）。
3. **cycle 3（联调 + 收口）**：routes 接线与登记（EC-03/EC-04）+ 收口资产（EC-05）+
   宪章记账（EC-06）+ `W-5`/`W-7` 核对（EC-07）。

## 交付面（checkbox）

- [x] WP-A 三条悬空样式 + `css-token-references.test.ts`（EC-01）
- [x] WP-B 四组合参数化 + `run-timeline-phases` 路由 + outline 重生成（EC-02）
- [x] WP-C 元素级像素判据 + 两平台基线各 144 张（EC-02）
- [x] WP-D reviews 读面 + `ReviewPanelSection`（EC-03）
- [x] WP-E 研究方向写面 + `ProjectDirectionEditor`（EC-03）
- [x] WP-F `programsClient.ts` + `ProgramsSection`（EC-03）
- [x] WP-G 三条 client-only 方法 + `UNCONSUMED.md` 白名单（EC-03/EC-04）
- [x] WP-H `backend-route-coverage.test.ts` + `unconsumed-registry.test.ts` + `unconsumedRegistry.ts`（EC-04）
- [x] WP-I `verify_goal104_closeout.py` + `goal104_closeout_assertions.py` + 两处登记（EC-05）
- [x] WP-J 宪章记账（EC-06）
- [x] WP-K `W-5` / `W-7` 核对不回退（EC-07）

## 复检

收口复检：`tools/verify_goal104_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，`verify_paths` ≥ 2 路，见 GOAL 的 `latest_recheck`）。
实测 **82 判词全 PASS / 0 FAIL**，判词不含树的绝对路径。

## 影响报告

（首行写「预判」，收口时改成「实测」。本轮全部为实测。）

- **Domain/API/schema**：**零后端改动**。新增的 `MemoryValidityDto` /
  `MemoryValidityViewDto` 是 `types.ts` 对**既有** OpenAPI schema 的补登记（`docs/api/
  openapi.m13.json` 未变，故快照判据不动）；`ProgramDetailDto` 等早已在 `types.ts` 里。
  **OpenAPI 快照零 diff** ⇒ `test_openapi_snapshot` 不受影响。
- **安全/凭据**：零变化（无新凭据、无新出网面、无新工具面）。新增的读面方法都是既有
  路由的既有鉴权面；`ProgramsSection` 的「推进一轮」按钮调用的是**已有**的写面。
- **兼容性/迁移**：零 migration。前端新增组件全是**加性**；`.muted` 改成局部类
  **改变观感**（两处此前是 `className={undefined}`），这是修复本身的目的。
- **上游**：零依赖变化（`@playwright/test` 仍 1.56.1，容器镜像 pinned 同版本 `noble`）。
- **视觉基线**：`design-fidelity` 从 68 张（34×2）扩到 **288 张**（36×4×2 组合��——
  实际为 35 路由 + 1 个元素级 `phase-track` 条目在四组合下各一，乘两平台）。其中
  **110 张是新增**、2 张（`portfolio-projects` / `run-timeline-substrate`）因 DOM 新增
  而重生成、其余旧基线**逐字节未动**（13 张被重跑产生的 ≤60 px 抗锯齿噪声已 `git
  checkout` 回退，两平台复跑仍绿）。

## 验收条件

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-02 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-03 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-04 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-05 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-06 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |
| EC-07 | **PASS** | 见 RECHECK-20261103-104 的逐条读数表 |

## 实施清单

（与「交付面」逐条对应；全部 DONE，详见上表。）

## 证据

（全部为**真实执行**的读数，非「文件在树」。）

- **前端单测**：`pnpm --dir apps/web test` ⇒ **97 passed**（含新增
  `css-token-references` 3 条、`backend-route-coverage` 3 条、`unconsumed-registry` 3 条）。
- **前端 e2e（win32）**：`npx playwright test` ⇒ **106 passed**（含 `design-fidelity`
  3 条与 `design-outline-guard` 6 条）。
- **前端 e2e（linux，pinned `mcr.microsoft.com/playwright:v1.56.1-noble` 容器）**：
  `design-fidelity` **3 passed**。
- **类型与静态面**：`npx tsc --noEmit` 无错；`npx eslint src tests --max-warnings 0`
  仅 2 条既有的 `max-lines-soft` 警告（`live-api-workflow.spec.ts` / `stub-routes-runs.ts`）。
- **反证臂（全部实测，随后还原）**：
  - `var(--not-a-token)` ⇒ `css-token-references` 判红并点名文件与变量；
  - 白名单路径 `/health-typo` ⇒ `unconsumed-registry` 判红并点名该行；
  - 白名单理由 `-` ⇒ 同上判红并点名 `GET /health`；
  - `.succeeded` 边框色 `--success`→`--danger`（DOM 未动）⇒ 结构签名**绿**、整页像素
    **绿**（0.36% < 2%）、元素级像素**红**（563 px）；
  - 把 `console-frontend` 的 `runs-on` 改回 `ubuntu-latest` ⇒ 收口验证器
    `workflow-console-frontend-fix-intact` 判红并点名两条形态（随后还原，`git diff` 为空）。
- **收口验证器**：`tools/verify_goal104_closeout.py --root .` ⇒ `SUMMARY total=82
  failed=0`；`--verdict-only` 输出里 `D:\` / `D:/` 命中 **0**。
- **Charter**：`tests/tooling/` ⇒ **1751 passed**（唯一失败是 m0 见证未刷新，属流程
  顺序而非缺陷 —— 见证在最后一次全量 m0 后重写）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-03 | CREATED | 建档（承 GOAL-20261103-104）。三个 cycle 按提交面划分。 |
| 2026-11-03 | DONE | 三个 cycle 全部交付；七条 EC 全 PASS；收口复检 `RECHECK-20261103-104` PASS。 |
