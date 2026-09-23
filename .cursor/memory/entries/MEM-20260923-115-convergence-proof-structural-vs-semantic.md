---
id: MEM-20260923-115
title: "「收敛有证」类判据：`includes` 判路由会被注释骗过；结构判据与语义判据要分开披露"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-150-console-real-data-matrix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-151-console-real-data-matrix.md
supersedes: []
---

## 做了什么

GOAL-20260923-013 EC-01 要求「收敛项必须有**页面级** live 为证」。第一版判据是
`spec.includes("#/" + route)`：文件里出现这条路由就算有证 —— 它**被一句文件头注释骗过**。
改后的判据（`apps/web/tests/unit/console-real-data-matrix.test.ts` 的第 ③ 组）要求四件事
同时成立：具名 spec 文件存在、suite 在白名单内、**路由串出现在一次 `page.goto(` 调用里**、
且该文件对 DOM 有断言；另加一条**反向**要求——收敛行在 `pageSupport` 里必须确为 `full`。

## 为什么这样做

- **`includes` 是这类判据最容易变成空断言的地方**：注释、快照文件名、断言文案里出现一次
  路由串就能满足它。按压实测：把 live spec 的 `page.goto` 目标换成别的路由后判据**仍然绿**，
  因为该 spec 的文件头注释第 2 行写着 `` `#/plan/overview` ``。
- **「有 DOM 断言」必须显式要求**：否则「页面级」会退化成一个名词——只 `page.request.get(...)`
  的用例（本仓的 `live-project-lineage` / `live-project-cost-forecast`）证明的是**读面**存在，
  不是页面渲染正确。二者不可互相顶替。
- **反向要求同样必要**：只查「文档说收敛了」而不查「代码里真的收敛了」，标注就能脱离代码单独写。

## 怎么做与复现

1. 取路由串的**每一处**出现，检查其**前 300 字符内**是否有 `page.goto(` ——
   注释、快照名、断言文案都骗不过它。可复用的写法：

   ```ts
   function drivesRoute(spec: string, route: string): boolean {
     const needle = `#/${route}`;
     for (let at = spec.indexOf(needle); at >= 0; at = spec.indexOf(needle, at + 1)) {
       if (spec.slice(Math.max(0, at - 300), at).includes("page.goto(")) return true;
     }
     return false;
   }
   ```

2. 同组再断言 `toHaveText|toBeVisible|toContainText` 至少出现一次（DOM 断言）。
3. 再加反向断言：`levelOf(route) === "full"`。
4. **复现按压**：把 spec 的 `page.goto` 目标换成别的路由 ⇒ 同一条判据立刻变红，
   判词点名 `live spec never navigates to plan/overview`；改回即绿
   （红/绿证据见 `scratch/goal013-c1-press-live-route.txt`）。
5. **独立复检脚本要独立实现归一化**：`pageSupport.ts` 的字符串拼接形态是 `" +` 换行 `"`，
   只 `replace('"\n    "', "")` **不生效** ⇒ 会给出**假红**（本 cycle 实测撞到一条）。
   正确写法是 `re.sub(r'"\s*\+\s*\n\s*"', "", text)`。两套实现分歧时，先对齐归一化，
   再判断是**事实**问题还是**实现**问题。

## 适用边界

- 这是一条**结构判据**：它保证「矩阵 / `pageSupport` / page map 三处不会各自漂移」，
  **不**保证 live 用例的断言够强——**改 spec 的断言强度不会让它红**。记录里必须写明这一点，
  不能只写「判据绿」。
- 语义正确性由 live 用例承载，而 live 用例自身的敏感面是**页面那一段**：按**数据**按压对
  「页面 == 读面」**不敏感**（两侧同源，一起变），按**页面**按压才敏感
  （把论断卡数值钉成常量 ⇒ 用例红）。同源按压口径另见
  `.cursor/memory/entries/MEM-20260923-113-live-page-equals-read-face-judge.md`。
- 换到别的「必须驱动某个界面并断言」的判据上也成立；但若被测面本身没有 DOM
  （纯 API 判据），第 ③ 组不适用，应改用读面级的独立判据。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260923-150-console-real-data-matrix.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260923-151-console-real-data-matrix.md`
- 判据：`apps/web/tests/unit/console-real-data-matrix.test.ts`
- 按压证据：`scratch/goal013-c1-press-live-route.txt`、`scratch/goal013-c1-press-matrix.txt`、
  `scratch/goal013-c1-pressA-page.txt`
