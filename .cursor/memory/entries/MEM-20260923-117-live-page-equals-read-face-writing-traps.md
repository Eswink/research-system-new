---
id: MEM-20260923-117
title: "「页面 == 读面」live 判据的两处写法陷阱：空态断言不加 `^…$` 会被前缀文案骗过；CSS 属性选择器不做候选"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-151-live-page-read-face-batch-two.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-152-live-page-read-face-batch-two.md
supersedes: []
---

## 做了什么

GOAL-20260923-013 EC-02 要求每条 live 用例都配**成对反证**（读面空 ⇒ 页面显示诚实空态）。
写这批用例时按压实测到两个**会让判据变空**的写法陷阱，都已修掉并把修法写进注释。

**陷阱一：空态断言用 `getByText(/项目内无库资源/)` 会被前缀扩展文案骗过。**
按压实验：把组件文案改成 `项目内无库资源占位`（伪造数据的形态），用例**仍然绿** ——
因为 Playwright 的 `getByText` 默认是**子串**匹配。修法：两端锚定到整串。

```ts
await expect(page.getByText(/^(没有匹配的正式事件|No matching persisted events)$/)).toBeVisible();
```

**陷阱二：CSS 属性选择器里写 `a|b` 不是「或」。**
`table[aria-label="项目血缘节点|Project lineage nodes"]` 被当成**字面量属性值**，
选不中任何元素 ⇒ 行数读到 0（实测 `Expected: 18, Received: 0`）。
修法：写成**选择器列表**（逗号分隔），必要时再 `.first()`。

```ts
page.locator(labels.map((label) => `table[aria-label="${label}"]`).join(", ")).first()
```

## 为什么这样做

这两处都不是「写法偏好」而是**判据强度问题**：
陷阱一让反证退化成空断言（伪造数据也会绿），陷阱二让正向判据读到 0
（要么判红到无法区分「页面坏了」与「选择器坏了」，要么被人随手把期望值改成 0）。
成对反证的价值全在「读面为空时页面**必须**显示空态」这条否定性上，被前缀骗过就等于没判。

## 怎么做与复现

按压实测记录（先红后绿，红即判据真的敏感）：

- 空态：把组件渲染的库资源面板文案钉成 `项目内无库资源占位`
  ⇒ 旧写法绿、锚定写法红（证据 `scratch/goal013-c2-press-empty-text.txt`）。
- 行数：把事件行数/血缘行数钉成常量 ⇒ 对应 `toHaveCount` 判红
  （证据 `scratch/goal013-c2-press-audit-rows.txt`、`-press-lineage-rows.txt`）。

两条 spec 的判据都还用「反证前提」自证非空，避免等式退化成 `0 == 0`：

```ts
expect(events.length).toBeGreaterThan(0);   // 否则 toHaveCount(0) 与页面坏掉不可分
expect(bare.length).toBe(0);
expect(rich.length).toBeGreaterThan(bare.length);
```

## 适用边界

- 「必须锚定」只针对**否定性/存在性**断言（空态、占位、缺省文案）。
  正向断言比对的是**由读面导出的值**（计数、字段值），不受子串匹配影响。
- 锚定要连**中英两条文案**一起写（本仓 UI 是双语），只锚一种语言时切语言就会漏判。
- 选择器陷阱对 `[class=…]`、`[data-testid=…]` 同样适用；`aria-label` 恰好最容易踩到，
  因为它的值是自然语言、最想「或」起来。
- 这两条与 [[MEM-20260923-115-convergence-proof-structural-vs-semantic]] 同源：
  判据要**先按压确认它真的会红**，再谈「全绿」。

## 来源

- `apps/web/tests/e2e/live-govern-audit.spec.ts`（86 行处注释写明锚定理由）、
  `apps/web/tests/e2e/live-library-lineage.spec.ts`（选择器列表写法）、
  `apps/web/tests/e2e/live-plan-overview.spec.ts`（cycle 1 的回填锚定）。
- 相关：[[MEM-20260923-116-local-m0-green-recipe]]（同 cycle 的门配方）。
