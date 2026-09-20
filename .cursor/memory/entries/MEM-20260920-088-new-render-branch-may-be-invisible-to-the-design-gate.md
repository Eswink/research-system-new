---
id: MEM-20260920-088
title: "新增的 web 渲染分支可能对设计门不可见：默认 stub 套件没给该路由注册 GET ⇒ 页面渲染错误态，像素与结构签名都不会变——要用自带 stub 的 e2e spec 钉住分支"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-115-model-parameter-persistence.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-115-model-parameter-persistence.md
supersedes: []
tags:
  - console
  - design-gate
  - playwright
  - stub-fixtures
  - i18n
---

# 设计门看不见「页面根本没渲染到」的新分支（GOAL-20260920-008 / cycle 2）

## 做了什么

模型页新增了两个渲染点（详情面板 `model-declared-parameters` + 目录表新列
`model-row-declared`）。改完跑设计对照（`design-fidelity`：34 路由像素截图 +
DOM 结构签名），**两条判据全绿、`apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/`
与 `design-outlines.json` 零 diff**——按直觉该重生成基线，实际**不需要**。

原因：默认替身 `stubApi` 的路由表里**没有 `GET /models`**，`library-model-registry`
这条基线渲染的是错误态（页面骨架 + `ErrorState`），表格与详情组件根本没有挂载。
设计门覆盖的是「渲染出来的东西」，覆盖不到一个「从未被渲染」的分支。

## 为什么这样做（可复用结论）

1. **判据的射程**：像素/结构签名判据的前提是**组件真的被渲染**。整条路由的数据入口缺
   替身时，该路由的基线只反映错误态，任何只在该数据态下出现的分支对它都是隐形的
   （与 GOAL-007 EC-04 的「加行后结构签名不变」同因：那次是没选中 run）。
2. **别按「改了页面就重生成基线」的惯性做事**：先跑一次判据、再看
   `git status --short apps/web/tests/e2e/` 是否真有 diff。零 diff 说明基线压根没覆盖到，
   此时重生成只会污染基线一致性（还要按配方补 linux 像素）。
3. **正确处置 = 给分支自带 spec**：写一条独立的 stub e2e（本轮的
   `models-declared-parameters.spec.ts`），用 `page.route` 覆盖该路由的 GET，
   提供「有值 / 无值」两种夹具，断言两态**可区分**。这类 spec 进默认 playwright 套件
   （`playwright.config.ts` 的 `testIgnore` 只排除 `live-*.spec.ts`）⇒ CI 的
   `console-frontend` job 会跑它。
4. **本地化文案必须先钉渲染语言**：页面文案随 `language` 变（默认 zh），
   断言英文诚实文案会红。用 `page.addInitScript` 写
   `localStorage["ros.console.preferences"] = {language, theme, density, editorMode, version}`
   再 `goto`（`design-fidelity.spec.ts::seedPrefs` 是同一手法）。
5. **类型的截图式耦合**：`apps/web/src/api/types.ts` 与 OpenAPI 快照**没有**自动比对门，
   真正的耦合来自 `tsc --noEmit`：夹具（`apiFixtures.ts` 的 `ModelReadDto`）与页面读字段
   一起被检查。删掉 DTO 里的新字段，`tsc` 会同时报出页面与新夹具——这就是「读面同步」的判据。

## 怎么做与复现

```sh
# 1) 改了页面后，先看设计门是否真的覆盖到了（不该盲目重生成基线）
pnpm --dir apps/web exec playwright test design-fidelity --reporter=line
git status --short apps/web/tests/e2e/     # 零 diff ⇒ 新分支对设计门不可见

# 2) 给新分支自带 stub spec（两种数据态），然后单独跑
pnpm --dir apps/web exec playwright test models-declared-parameters --reporter=line

# 3) 反证「渲染分支存在」：注释掉页面里的挂载点后再跑，spec 必须全红
```

## 适用边界

- 适用于**本仓 console 的 stub e2e 与设计对照门**（`apps/web/tests/e2e/`）。
- 「设计门零 diff」不代表没改页面：它只说明**被渲染的**部分没变；新增分支仍需自带 spec。
- 若某路由的 GET 本来就在 `stub-routes*.ts` 里注册过（页面真渲染数据），改页面**会**让结构
  签名变红 ⇒ 那时才需要按配方重生成（`UPDATE_OUTLINES=1` + 单路由 win32 像素 +
  容器生成 linux 像素 + 跨平台一致性复核）。
- live 套件（`live-*.spec.ts`）另有一套：清单单一来源是 `tests/e2e/live-specs.ts`，
  进 live 清单的 spec 会被默认套件排除。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-115-model-parameter-persistence.md`（WP-E）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-115-model-parameter-persistence.md`
- 代码：`apps/web/tests/e2e/stub-routes.ts`（无 `GET /models` 注册）、
  `apps/web/tests/e2e/models-declared-parameters.spec.ts`（本轮新增）、
  `apps/web/tests/e2e/design-fidelity.spec.ts`、`apps/web/src/api/types.ts`
