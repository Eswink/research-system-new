---
id: PLAN-20260923-150
slug: console-real-data-matrix
title: 逐页真实数据验收矩阵：20 条 partial/gap 逐条终态 + 离线三方同源判据（GOAL-013 EC-01）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-013
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-013 建档授权（2026-09-23 用户 goal 模式指令）的 **EC-01**：
    把 19 条 `partial` + 1 条 `gap` 共 20 条页面逐条给出**终态二选一**（收敛 / 保持并点名缺口），
    **零条待定**，且 `pageSupport`、`CONSOLE_PAGE_MAP.md` 与矩阵**三方同源**。
    授权含 **`pageSupport`/页面的诚实标注**补充（**改小注记必须有真实消费者与真实页面为证**）。
    本 PLAN 的改动面严格限于：矩阵文档 + 离线判据（web unit）+ 一条**页面级 live 用例**
    （`#/plan/overview`，判据形态「页面 == 读面」+ 成对反证）+ 该页注记的收敛
    （`pageSupport.ts` 与 `CONSOLE_PAGE_MAP.md` 对应小节）。
    **不改**产品 UI 组件、**不改** API/DTO/合约、**不改**任何门禁/validator/既有测试断言、
    **不改**设计基线；零出网（浏览器只打本机 127.0.0.1 的 live app 与 vite dev）、
    零凭据读取、零真实 LLM 调用。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-151-console-real-data-matrix.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-115-convergence-proof-structural-vs-semantic.md
---

# PLAN-20260923-150 — 逐页真实数据验收矩阵（GOAL-013 EC-01）

## 目标

把 `apps/web/src/navigation/pageSupport.ts` 里 **19 条 `partial` + 1 条 `gap`** 共 20 条路由
逐条判定终态，形成 `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md`，并落**离线机械判据**
（完备性 / 三方同源 / 收敛有证 / 不混写），使「矩阵」「pageSupport」「CONSOLE_PAGE_MAP」
三处不可能各自漂移。

## 计划开始前的定案（写死）

- **D-1｜(a)/(b) 判定边界**：**(a) 收敛** = 该页**呈现的**每个面都由已交付读面服务
  （页面无消费不到的后端缺口），且有**页面级** live 用例为证，且 `pageSupport` 等级按
  `CONSOLE_PAGE_MAP.md` 自身的定义（FULL＝数据与操作真实、无禁用操作）相应收敛；
  **(b) 保持** = 其余，**必须点名缺哪条 API／哪个字段／哪张读面**，并写明为什么现在不做。
- **D-2｜「读面级 live」不算「页面级 live」**：只 `page.request.get(...)` 而不断言 DOM 的
  用例（如 `live-project-lineage`、`live-project-cost-forecast`）**不构成** (a) 的依据——
  它们证明读面存在，不证明页面渲染正确。
- **D-3｜缺口记法（机器可查）**：矩阵每条**保持**行的点名列必须含缺口 token
  （`API:<路径>` / `FIELD:<字段>` / `SURFACE:<读面>` / `DESIGN:<slug>`）**并**含一段
  **「」引文**，该引文须逐字出现在 `pageSupport.ts` 或 `CONSOLE_PAGE_MAP.md` 里
  ——**矩阵不得自造缺口事实**；`SURFACE:`/`DESIGN:` 还须写 `不做的原因：`。
- **D-4｜收敛不能只靠标注**：每条**收敛**行必须含 `LIVE:<spec 文件名>`，该文件须存在、
  须在白名单内、须**真的 `page.goto` 到该路由**并对 DOM 断言（`toHaveText`/`toBeVisible`/
  `toContainText`）。且判据**反向**要求：收敛行在 `pageSupport` 里必须确为 `full`。
- **D-5｜不混写**：收敛行不得带缺口 token；保持行不得带 `LIVE:`。
- **D-6｜改小注记的门槛**：`plan/overview` 从 `partial` 收敛为 `full` 的依据是
  **真实消费者**（`resolveDataSource`/`isOperationDisabled` 读 `level`，页面无禁用操作）
  与**真实页面**（`live-plan-overview.spec.ts` 的「页面 == 读面」+ 成对反证）两者齐备；
  page map 里「原型 manifest 摘要字段（objectives/autonomy）无对应 DTO」一行经核对
  **页面上没有消费这两字段的代码路径** ⇒ 就地改写为原型设计偏差，不留假缺口。

## 验收条件

- [x] `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md` 恰好 20 行，每行终态 ∈ {收敛, 保持}，
      零条待定；每行的「点名缺口 / 证据」列按 D-3/D-4/D-5 可机械判定。
- [x] 离线判据 4 条全绿：① 完备性 ② 三方同源（非 full 路由无遗漏 + 收敛行确为 full +
      引文逐字来自权威）③ 收敛有证（存在 + 白名单 + 真的 `page.goto` 该路由 + DOM 断言）
      ④ 不混写。
- [x] `#/plan/overview` 的页面级 live 用例落地并通过：判据形态「页面 == 读面」
      （先 HTTP 取四条读面，再与 DOM 逐值比对），并配**成对反证**
      （另一条 run 的论断读面为空 ⇒ 同一组件显示读面自己的零与空态，不伪造）。
- [x] 成对反证**先红后绿**：① 页面按压（论断卡钉常量）⇒ 两条 live 用例红；
      ② 矩阵按压（缺口改写成「已交付」）⇒ 三方同源判据红；
      ③ live 用例按压（不再 `goto` 该路由）⇒ 收敛有证判据红。
- [x] stub 套件仍绿（新 live spec 被 `testIgnore` 正确排除，白名单未漏加）：**96 passed**。
- [x] 本地门全绿：web lint / typecheck / unit（**80 passed**）/ build / stub e2e（96）/
      live e2e（**43 passed**）+ `validate.py` + docs-check（`DOCS-CHECK PASS: 6`）。

## 实施清单

### WP1 — 页面级 live 用例（`#/plan/overview`）
- [x] `apps/web/tests/e2e/live-plan-overview.spec.ts`：两条用例——「页面 == 读面」与
      「读面为空 ⇒ 诚实空态（成对反证）」；读面快照落 `scratch/`（不进仓库）。
- [x] `apps/web/tests/e2e/live-specs.ts` 白名单加 `plan-overview`（单一来源；两个 config
      共用同一 `LIVE_SPEC_PATTERN`，不需分别改）。

### WP2 — 注记收敛（`plan/overview`）
- [x] `apps/web/src/navigation/pageSupport.ts`：`plan/overview` 等级 `partial` → `full`，
      注记改写为聚合口径（不是缺口），并注明页面级证明文件。
- [x] `docs/frontend/CONSOLE_PAGE_MAP.md` 的 `#/plan/overview` 小节：等级改 `FULL`，
      数据面写实（四条读面），原型设计偏差就地登记为「已实现面的一部分」。

### WP3 — 矩阵文档
- [x] `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md`：20 行逐条终态 + 缺口记法说明 + 汇总 +
      与其它权威面的关系。

### WP4 — 离线判据与按压
- [x] `apps/web/tests/unit/console-real-data-matrix.test.ts`：① 完备 ② 三方同源
      ③ 收敛有证 ④ 不混写。
- [x] 三处按压（页面 / 矩阵缺口 / live 用例路由）先红后绿，红证落 `scratch/goal013-c1-*`。

## 证据

- 矩阵：`docs/frontend/CONSOLE_REAL_DATA_MATRIX.md`（**已收敛 1 / 保持 19 / 待定 0**）。
- 判据：`apps/web/tests/unit/console-real-data-matrix.test.ts`（离线，随 `pnpm run test` 跑）。
- 页面级 live：`apps/web/tests/e2e/live-plan-overview.spec.ts`（2 passed）。
- 按压：`scratch/goal013-c1-pressA-page.txt`（页面按压 ⇒ 2 failed）、
  `scratch/goal013-c1-press-matrix.txt`（矩阵按压 ⇒ 2 failed）、
  `scratch/goal013-c1-press-live-route.txt`（路由按压 ⇒ 1 failed）。
- 关键发现（判据自身的问题，当轮修掉）：初版「收敛有证」用 `spec.includes("#/<route>")`
  判定，**被文件头注释里的一句路由骗过**——按压实测暴露 ⇒ 改为「路由串前 300 字符内出现
  `page.goto(`」，同一按压随即变红。

## 状态历史

- 2026-09-23：**derive**（cycle 1）。定案 D-1…D-6 写死；起点事实：20 条名单来自
  `pageSupport.ts` 的 `SUPPORT` 表（`full` 13 / `partial` 19 / `gap` 1），既有 live 面 14 个
  suite，其中**只有 5 个**真的 `goto` 到具体路由（`live-experiments` / `live-run-rebuild-readiness` /
  `live-run-substrate-disclosure` / `live-schedules-write` / `live-tool-pack-write`），
  `live-project-lineage` 与 `live-project-cost-forecast` 是**纯读面**用例（按 D-2 不构成页面级证据）。
- 2026-09-23：**收口**（`status: DONE`）。独立复检 `RECHECK-20260923-151` = **PASS**
  （`scratch/verify_goal013_c1.py` 两棵树成对：当前树 `checked=218 failures=0`；
  干净 checkout `f45d6ec` `failures=3`，三条红**全部**是「尚未收口」时序项）。
  工程记忆 `MEM-20260923-115`（判据自身的问题：`includes` 判路由被注释骗过 ⇒ 改为
  「路由串前 300 字符内有 `page.goto(`」+ DOM 断言 + 反向要求收敛行在代码里确为 `full`；
  并披露结构判据 vs 语义判据的敏感面差异）。**顺带查出的一处事实**：设计基线
  `design-outlines.json` 会渲染 `pageSupport.reason` 文本，故收敛时**注记文字逐字未改**
  （改文字等于改设计基线，而本次是等级口径收敛）⇒ 基线无需重生成，`design-fidelity` 的结构
  签名判据实测保持绿。**未改**任何产品 UI 组件、API/DTO、门禁、既有断言与设计基线。

## 影响报告

- **Domain/API/schema**：无改动（不改 DTO、不改路由、不改合约）。
- **前端**：`pageSupport.ts` 一条路由的等级与注记；新增 1 个 live spec + 1 个 suite 白名单项；
  1 个 web unit 判据文件。产品 UI 组件**未改**。
- **文档**：新增矩阵文档；`CONSOLE_PAGE_MAP.md` 的 `#/plan/overview` 小节按实现改写。
- **安全/凭据**：零真实出网（浏览器只打 127.0.0.1）、零凭据读取、零真实 LLM 调用。
- **兼容性/迁移**：无。`level: partial→full` 在 `resolveDataSource` 下等价（两者都落到 `live`），
  无行为变化。
- **上游版本影响**：无新增依赖、无 pin 变更。
