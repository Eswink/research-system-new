---
id: MEM-20261103-238
title: "CSS-module 的键可以不存在：样式静默失效要有文本判据"
status: ACTIVE
created_at: 2026-11-03
updated_at: 2026-11-03
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261103-104-design-gate-and-integration-coverage.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261103-104-design-gate-and-integration-coverage.md
supersedes: []
---

# CSS-module 的键可以不存在

## 做了什么

`apps/web` 的 CSS-module 在 TypeScript 里的类型是 `{ readonly [key: string]: string }`，
因此 `styles.anything` **都能过 typecheck**；`var(--anything)` 同理不会被任何构建步骤拦下。
2026-11-03（GOAL-104 EC-01）实测到三处**静默失效**，且三处都不会让任何一道既有的门变红：

- `PhaseProgress.tsx` 引 `styles.muted`，而 `LivePage.module.css` 里没有 `.muted`
  ⇒ 渲染成 `className={undefined}`（两处）；
- `CommandCenterPage.module.css` / `ConsoleLoading.module.css` 用 `var(--bg)`
  （`tokens.css` 里叫 `--bg-app`）；
- `LivePage.module.css` 用 `var(--text-dim)`（最接近的是 `--fg-faint`）。

判据：`apps/web/tests/unit/css-token-references.test.ts`
- **token 面**：每个 `var(--x)` 必须在 `tokens.css` 或**同目录层叠**内被定义；
- **类名面**：每个 `styles.<key>` 必须在被 import 的那个 `*.module.css` 里有对应类；
- **反证臂**：注入 `var(--not-a-token)` ⇒ 判据点名文件与变量名（实测已红）。

## 为什么这样做

这类缺陷的形态是「页面能开、样式没了」：没有异常、没有红门、没有日志，**只有人眼**能发现，
而人眼不会去核对每个 class 名。把它写成文本判据才有一条会一直生效的失效机制。

## 怎么做与复现

```bash
cd apps/web && npx tsx --test tests/unit/css-token-references.test.ts
```

要按压判据本身：往任一 `*.module.css` 插 `color: var(--not-a-token);` ⇒ 应看到
`<rel>: var(--not-a-token) is not defined in tokens.css nor locally`；还原后 3 条全绿。
类名面同理：把某处 `xStyles.foo` 改成 `xStyles.nope` ⇒ 应点名「不是该模块里的类」。

## 适用边界

- `--cc-*` 一族是唯一豁免，且**按目录**登记（`features/example-console/command-center`）
  而不是按 token 名 —— 它们定义在 `CommandCenterStage.module.css` 的 `.wrapper` 上，
  靠 **DOM 嵌套**传给整棵子树。静态判据看不见 DOM，只能承认「同一层叠内的兄弟模块定义过」。
  这条放宽的方向是「谁定义了它」，**没有**放宽「必须有人定义」。
- 它不判样式**值**是否正确（`--fg-muted` 与 `--fg-faint` 用错地方它看不出来），
  也不判 CSS 属性合法性。

## 来源

- GOAL-20261103-104 EC-01（`RECHECK-20261103-104` 的「检查结果 / 逐条读数」首两行）。
- 三条缺陷的实测位置：`apps/web/src/features/runs/PhaseProgress.tsx:102,106`、
  `apps/web/src/features/command-center/CommandCenterPage.module.css:9`、
  `apps/web/src/layout/ConsoleLoading.module.css:9`、
  `apps/web/src/features/shared/LivePage.module.css:214`。
