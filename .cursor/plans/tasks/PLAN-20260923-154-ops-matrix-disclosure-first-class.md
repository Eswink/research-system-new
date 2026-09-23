---
id: PLAN-20260923-154
slug: ops-matrix-disclosure-first-class
title: EC-04 `ops/matrix` 单独处置：取 (ii)「界面状态说明页（非实时运维状态）」成四处同源的一等事实 + 页面判据
status: IN_PROGRESS
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260923-013
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-013 建档授权（2026-09-23 用户 goal 模式指令）的 **EC-04**：
    20 条里唯一的 `gap` 项 `ops/matrix` **单独处置**，二选一且**不留含糊** ——
    **(i) 收敛**（给出真实消费者 + live 用例、等级上调）或 **(ii) 一等事实**
    （把「界面状态说明页（非实时运维状态）」写成一等事实：**页面文案**（页面上可见的说明，
    不是代码注释）与文档同源，`pageSupport.ts` 的 `reason` + `CONSOLE_PAGE_MAP.md` 的
    `#/ops/matrix` 小节 + 矩阵文档三处**措辞一致**，并说明**为什么不做实时运维状态**）。
    **不得**用「设计如此」一句话代替「为什么不做」。本 PLAN 取 **(ii)**。
    改动面严格限于：`docs/frontend/` 的两份文档措辞、一条**离线** stub e2e 页面判据、
    一条离线一致性判据、`scratch/` 的按压证据（**不进仓库**）、本 PLAN 的 RECHECK 与工程记忆。
    **不改** `pageSupport.ts` 的 `reason` 文字（设计基线 `design-outlines.json` 会渲染它，
    改文字等于改设计基线）、**不改** `level`（`resolveDataSource` 对 `gap` 落 `example` 是
    **真实消费者**，F-3）、**不改**门禁/validator/既有断言、**不改**既有 live spec、零出网、
    零凭据读取。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-154 — `ops/matrix` 的 (ii) 一等事实化

## 目标

把 `ops/matrix` 这条唯一的 `gap` 页处置成**一等事实**：页面可见文案 + 三处文档措辞同源，
并给出**可核对的**「为什么不做实时运维状态」，最后落一条**离线页面判据**（stub e2e）
与一条**离线一致性判据**（unit）。**不**新增读面、**不**动 `level`、**不**动 `reason` 文字。

## 计划开始前的定案（写死）

### 起点事实（**直接读代码实测**，不当作验收依据）

| # | 事实 | 来源 |
| --- | --- | --- |
| F1 | `pageSupport("ops/matrix")` = `{ level: "gap", reason: "界面状态说明页（非实时运维状态）" }`，是 `SUPPORT` 表里**唯一**的 `gap` | `apps/web/src/navigation/pageSupport.ts:183` |
| F2 | 该 `reason` 文本**会被渲染**（`GapLayout` 的 `ReasonBanner`），且设计基线 `design-outlines.json` 也会渲染它 ⇒ **文字动不得**（cycle 1 实测） | `apps/web/src/features/shared/GapLayout.tsx:42` |
| F3 | `resolveDataSource` 只在 `auto` 且 `level === "gap"` 时落 `example` ⇒ 这条 `level` 是**真实消费者** | `apps/web/src/navigation/presentationPolicy.ts:9` |
| F4 | 路由默认（auto）渲染的是**示例面** `example-page-ops-matrix`；`?source=live#/ops/matrix` 才渲染**说明面** `gap-page-ops-matrix`（`StateReferencePage`） | `useSourceSelection.ts` + `console-shell.spec.ts:31` |
| F5 | 说明面**已有可见文案**：`matrix.hint` =「本页为界面状态说明：呈现加载/空/错误/权限/未知等组件状态，非实时运维状态。」（渲染在详情栏）+ `reason` 横幅 | `apps/web/src/i18n/zh.ts:254` |
| F6 | page map 的 `#/ops/matrix` 小节已含「界面状态说明」「不冒充实时运维状态」，**但没有**「为什么不做实时运维状态」 | `docs/frontend/CONSOLE_PAGE_MAP.md:306-309` |
| F7 | 矩阵第 15 行已含两短语 + `DESIGN:not-a-live-ops-surface`（不做的原因），但「为什么不做」只到「设计口径而非待建功能」 | `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md:49` |

### 本 PLAN 的定案

- **D-1｜取 (ii)**，不取 (i)：不新增读面、不动 `level`。理由：`level: gap` 有真实消费者
  （`resolveDataSource`，F-3），且该页**按设计**是**界面状态词表**的说明页；
  把等级上调反而要伪造一个「实时运维状态」读面。
- **D-2｜四处同源**（EC-04 说「三处」，本 PLAN 把**页面可见文案**也纳入成第四处）：
  ① `pageSupport.reason`（**逐字不改**，只做包含判据）② page map 小节 ③ 矩阵第 15 行
  ④ 页面可见文案（`matrix.hint` + `reason` 横幅）。四处的**共同不变量** =
  含「界面状态说明」与「非实时运维状态」两个语义，且**互不矛盾**（不得出现肯定式的
  「实时运维状态」而无否定前缀）。
- **D-3｜「为什么不做」的落点**：写进 ②（page map）与 ③（矩阵行），内容是**可核对的**——
  实时运维状态有自己的**读面与页面**：`#/ops/data-health`、`#/ops/observability`、
  `#/ops/compute`（各具名读面，等级 `full`）；本页只陈述**组件状态词表**
  （loading / empty / error / permission / unknown），不重复那些页面。**不写**「设计如此」。
- **D-4｜页面判据**用**离线 stub e2e**（`apps/web/tests/e2e/matrix-states.spec.ts`），两条成对：
  ① `/?source=live#/ops/matrix` ⇒ 断言 `reason` 横幅与 `matrix.hint` 文案**可见**；
  ② 默认（auto）⇒ 断言渲染的是**示例身份**（`example-page-ops-matrix`），
  证明本页**不冒充**实时运维状态。两条都在离线套件里（`testIgnore` 不排除 stub 套件）。
- **D-5｜一致性判据**用**离线 unit**（`apps/web/tests/unit/matrix-disclosure.test.ts`）：
  逐源解析并断言两短语在场、无肯定式矛盾、且「为什么不做」点名了 ≥2 个真实存在的
  live ops 路由（从 registry + pageSupport 读，不写死字符串）。
- **D-6｜按压**（EC-03 口径，逐条披露性质）：① 改 `matrix.hint` 文字 ⇒ 页面判据红（**按页面**）；
  ② 从 page map 小节删掉「非实时运维状态」⇒ 一致性判据红（**按文档源**）。
- **D-7｜不动**：`pageSupport.ts`、`presentationPolicy.ts`、`level`、设计基线、
  既有 live spec 与 stub spec、门禁与 validator。

## 实施清单

- **WP1** 文档同源：page map 小节补「为什么不做」（D-3）并保持两短语；矩阵第 15 行措辞对齐。
- **WP2** 页面判据：`matrix-states.spec.ts`（stub，两条成对）。
- **WP3** 一致性判据：`matrix-disclosure.test.ts`（离线 unit）。
- **WP4** 按压与证据：两处按压先红后绿，落 `scratch/`；报告披露性质。
- **WP5** 收口：`RECHECK-20260923-155` + 工程记忆 + GOAL 回写（EC-04 PASS）+ 门与 CI。

## 证据

- 待执行后回写。

## 状态历史

- 2026-09-24：**derive**（cycle 5）。定案 D-1…D-7 写死；起点事实 F1…F7 直接读代码实测。

## 验收条件

- EC-04 的判据全部成立：(ii) 成立、四处同源、**页面可见**该说明（stub 判据断言）、
  且写明**为什么不做**实时运维状态（可核对、非「设计如此」）。
- 离线判据（一致性 + 页面）在**默认门**（stub e2e + unit）跑绿；零出网。
- 两处按压**先红后绿**可复跑，披露落 RECHECK。
- 本地门：unit / lint / typecheck / build / stub e2e / `validate.py` / `docs_consistency_check`
  / m0（按既有配方；`R-F3` 那条外来 scratch 不影响本 PLAN 的判据）。

## 影响报告

- **产品面**：无。`pageSupport.ts` / `presentationPolicy.ts` / 页面组件**均不改**
  （F2 的基线渲染与 F-3 的消费者都保持原样）。
- **文档面**：`CONSOLE_PAGE_MAP.md`、`CONSOLE_REAL_DATA_MATRIX.md` 的措辞与「为什么不做」。
- **测试面**：新增 1 条 stub e2e spec + 1 条离线 unit 判据（均离线，默认门覆盖）。
- **治理面**：PLAN/RECHECK/GOAL 回写；`ALL_PLAN` 投影；`memory_entries` 视需要新增。
- **风险**：低。唯一要防的是「把 `reason` 或 `level` 顺手改了」——两者都明文禁改（F2/F3）。
