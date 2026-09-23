---
id: MEM-20260923-121
title: "判据性质披露要做成一等资产（登记册 + 机械判据 + 抽查实跑）；且「等式数据不敏感」与「前提数据敏感」必须分开写"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-24
scope: repository
confidence: 0.92
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-153-frontend-criteria-disclosure-judge.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-154-frontend-criteria-disclosure.md
supersedes: []
---

## 做了什么

GOAL-20260923-013 EC-03 要求「对本 GOAL 新增的**每条**前端判据，写明它能被什么按压、
不能被什么按压」。前三个 cycle 把这些披露**散写**在各自的 RECHECK 里 —— 散写的披露有两个
必然退化：谁也不会去数「是不是每条都写了」，而且两张手工表（RECHECK 里的、文档里的）
一定会各自漂。本 cycle 把它收成可机械强制的一等资产：

- **单一来源**：`apps/web/tests/unit/frontend-criteria-disclosure.ts` 的 `CRITERIA_DISCLOSURE`
  （每条判据含 `pressTarget` / `insensitiveFace` / `sensitiveFace` / `premiseIsDataSensitive` / `evidence`）。
- **机械判据**：`apps/web/tests/unit/frontend-criteria-disclosure.test.ts` 四条 ——
  ① 完备性**双向**（spec 里解析出的 test 名集合 == 登记册集合，查漏也查幽灵行）；
  ② 两个字段非空**且不是空话**（明文拒绝「判据绿」）；③ 披露的敏感面与所引证据类型一致；
  ④ 人读文档与登记册**同源**（文档缺一条即红）。
- **抽查实跑证披露为真**：`live-ops-integrations` 第 1 条做成对实跑 ——
  按**数据**（把 provider id 在 `examples/config/tool_providers.yaml` 改名）⇒ **2 passed**；
  按**页面**（把 `health` 渲染钉成常量）⇒ **2 failed**。

**本 cycle 补出的第二条口径**：`insensitiveFace` 必须同时说清两件事 ——
**等式**是数据不敏感的（两侧同源、一起变），但成对反证的**前提**是数据敏感的
（把某一侧改成空，红的会是 `toBeGreaterThan(0)` 这类自证，而不是等式）。
把这两件事写成一个字段会让人误以为「按数据随便改都无所谓」。

## 为什么这样做

「页面 == 读面」这类判据的绿，含义是**「页面与读面一致」**，不是**「页面上的值是对的」**。
不说清这一点，后来者会把一条恒真等式当成语义保证。披露从散文升级成登记册 + 判据之后，
「这条判据到底能抓住什么」变成可复核的仓库事实，而不是某份 RECHECK 里的一句话。

## 怎么做与复现

- 新增前端判据时，先在该登记册加一行，再让机械判据绿；文档视图照抄登记册行。
- **机械判据自己也要按**（否则判据可能恒真）：本 cycle 对四条判据各按压一次，
  红证落 `scratch/`：`goal013-c4-press-judge.txt`（②③ 2 failed）、
  `-press-judge-missing.txt`（① 1 failed）、`-press-judge-docdrift.txt`（④ 1 failed）。
- **实操陷阱（本 cycle 撞到）**：登记册是**未跟踪**的新文件时，`git checkout -- <文件>`
  **不会**还原按压改动（它不在索引里）⇒ 按压后必须**手工**把改动还原，且还原后再跑一次确认
  `# fail 0`。对未跟踪文件用「先备份再覆盖」比用 `git checkout` 可靠。

## 适用边界

- 登记册的**枚举口径**必须写死（本 GOAL：`git diff <建档提交>..HEAD -- apps/web/tests`；
  `live-specs.ts` 是白名单不是判据）。口径不写死，完备性判据会跟着感觉漂。
- 机械判据强制的是「披露在册且与**已落证据**对得上」；它**不重跑按压**。
  「披露为真」由抽查实跑承担，两者分工不可互相顶替。
- 判据数是**逐条 test**（本 GOAL 共 16 条：12 条 live + 4 条离线），不是逐文件；
  改 test 名会同时触发「旧条目成幽灵行」与「新条目缺失」，两条红都是预期的。
- 相关：[[MEM-20260923-117-live-page-equals-read-face-writing-traps]]（同族写法纪律）、
  [[MEM-20260923-115-convergence-proof-structural-vs-semantic]]（结构判据 vs 语义判据的分工）。

## 来源

- `apps/web/tests/unit/frontend-criteria-disclosure.ts`、
  `apps/web/tests/unit/frontend-criteria-disclosure.test.ts`、
  `docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md`。
- `scratch/goal013-c4-spotcheck-data.txt`（按数据 ⇒ 绿）、
  `scratch/goal013-c4-spotcheck-page.txt`（按页面 ⇒ 红）、
  `scratch/goal013-c4-press-judge*.txt`（机械判据自身的四组红证）。
