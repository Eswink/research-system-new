---
id: PLAN-20260923-153
slug: frontend-criteria-disclosure-judge
title: EC-03 判据性质披露落成机械判据：逐条「能被什么按压 / 不能被什么按压」+ 抽查实跑证披露为真
status: IN_PROGRESS
created_at: 2026-09-23
updated_at: 2026-09-24
parent_goal: GOAL-20260923-013
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-013 建档授权（2026-09-23 用户 goal 模式指令）的 **EC-03**：
    对本 GOAL 新增的**每条**前端判据，在记录里写明它**能被什么按压**、**不能被什么按压**；
    已知的不可按压面必须**逐条点名**（当「页面 == 读面」两侧同源时，改数据对判据**不敏感**，
    此时必须改为按压**页面那一段**）。判据：每条新增判据的按压记录都有一句性质披露，
    **不得**只写「判据绿」；披露与实际按压结果**一致**（披露「按页面才敏感」的必须给出
    按页面的红证；披露「按数据也敏感」的必须给出按数据的红证）。披露以反证表形式落 RECHECK。
    EC-03 的 verify 还要求：**机械判据**抽取每个新增判据，检查其按压记录**同时**包含
    「按压对象」与「不敏感面」两个字段且非空；对每条披露做**一次抽查实跑**证明披露为真；
    治理层面新增工程记忆（`MEM-*`）承载该口径，且该记忆被 RECHECK 引用（**同一提交**内）。
    本 PLAN 的改动面严格限于：`apps/web/tests/unit/` 的披露登记册与机械判据测试、
    `docs/frontend/` 的披露文档、`scratch/` 的抽查证据（**不进仓库**）、
    以及本 PLAN 的 RECHECK 与工程记忆。**不改**产品 UI/API/DTO/合约、**不改**门禁/
    validator/既有断言、**不改**设计基线、**不改** `pageSupport` 标注、**不改**既有 live spec。
    零出网（浏览器只打本机 127.0.0.1 的 live app 与 vite dev）、零凭据读取、零真实 LLM 调用。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-153 — EC-03 判据性质披露的机械落地

## 目标

把前三个 cycle 在 RECHECK 里**散落**的按压披露，收成**单一来源 + 机械判据**：
每条前端判据一行登记（按压对象 / 不敏感面 / 敏感面 / 依据），并由离线测试强制：
① 无遗漏（本 GOAL 新增的每个 spec 的每条 test 都有登记）；
② 两个字段都非空（禁止只写「判据绿」）；
③ 披露与**实际按压敏感面**一致（披露「按页面」的必须引用页面按压证据）。

## 计划开始前的定案（写死）

- **D-1｜「本 GOAL 新增的前端判据」的**枚举口径**：以 `git diff 50afb3b..HEAD -- apps/web/tests`
  为准 —— **6 个新 live spec** 与 **1 个离线判据文件**
  （`live-plan-overview` / `live-library-lineage` / `live-govern-audit` /
  `live-portfolio-experiments` / `live-insights-reports` / `live-ops-integrations` +
  `unit/console-real-data-matrix.test.ts`）。`live-specs.ts` 是白名单，不是判据。
- **D-2｜登记册是单一来源**：`apps/web/tests/unit/frontendCriteriaDisclosure.ts` 导出
  `CRITERIA_DISCLOSURE`。每条含 `spec`（文件名）、`testTitle`（该 spec 内 test 名）、
  `pressTarget`（**能被什么按压**）、`insensitiveFace`（**不能被什么按压**）、
  `sensitiveFace`（`page` 或 `page+data`）、`evidence`（`scratch/` 下的红/绿证据路径）。
  文档 `docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md` 是本登记册的**人读视图**，
  由机械判据核对与登记册**逐条一致**（防两份手工表各漂）。
- **D-3｜断言的敏感面**（承 cycle 1/2/3 的实测，**已按压**）：
  - **离线矩阵判据**（`console-real-data-matrix.test.ts`）：**结构判据** ——
    能被「改行终态 / 改缺口 token / 改引文 / 删 `LIVE:`」按压；**不能**被「改 spec 的断言强度」按压
    （它只检查存在/白名单/驱动路由/有 DOM 断言，不读断言强弱）。
  - **live「页面 == 读面」判据**（6 个 spec）：三侧**页面**敏感（把渲染值钉成常量 ⇒ 红，三个 cycle
    共 9 条红证）；**数据侧不敏感**（两侧同源，数据一起变 ⇒ 等式仍成立）——
    但成对反证的**前提**（「一侧非空 / 两侧确实不同」）**是数据敏感的**，必须单独点名。
- **D-4｜抽查实跑证披露为真（本 cycle 必做一次）**：挑 `live-ops-integrations` 的第 1 条
  （逐行逐值），做**成对**实跑：
  ① **按数据**按压（改夹具里某个 provider 的 `kind`/`trust_level` —— 两侧一起变）⇒ 期望 **绿**；
  ② **按页面**按压（把 `health` 渲染钉成常量）⇒ 期望 **红**。
  两次红/绿落 `scratch/goal013-c4-spotcheck-*.txt`。**这一对就是披露「数据不敏感 / 页面敏感」的证据**。
  **注意**：② 的红证 cycle 3 已有；本 cycle 重跑一次以便与 ① 在同一组内成对。
- **D-5｜「不敏感」不等于「没有值」**：数据侧按压**可能**让成对反证的**前提**失败
  （例如把某一侧改成空）⇒ 那时红的是**前提**而不是等式。披露必须把这两件事分开写：
  **等式**数据不敏感、**前提**数据敏感（登记册里以 `insensitiveFace` 与
  `premiseIsDataSensitive` 两个字段分别承载）。
- **D-6｜不改既有判据**：本 cycle 只**新增**登记册、文档与机械判据；
  6 个 live spec 与离线矩阵判据**逐字不动**（用 `git diff` 证明）。
- **D-7｜同提交纪律**：新增 `MEM-*` 承载披露口径，且该记忆被 `RECHECK-154` 引用 ——
  **同一提交**内落盘（GOAL-012 cycle 5 的判红根因正是引用落在下一个提交）。

## 验收条件

- [ ] `apps/web/tests/unit/frontendCriteriaDisclosure.ts`：登记册覆盖 D-1 枚举出的
      **7 个判据文件**的**每一条 test**，每条含 `pressTarget` / `insensitiveFace` /
      `sensitiveFace` / `evidence` 四个非空字段。
- [ ] `apps/web/tests/unit/frontend-criteria-disclosure.test.ts`：机械判据 ——
      ① 完备性（spec 里解析出的 test 名集合 == 登记册集合，双向）；② 字段非空；
      ③ 敏感面与证据一致（`sensitiveFace === "page"` 的条目必须引用 `press-` 证据）；
      ④ 文档视图与登记册逐条一致。
- [ ] **抽查实跑**（D-4）：按数据按压 ⇒ **绿**；按页面按压 ⇒ **红**；
      证据落 `scratch/goal013-c4-spotcheck-{data,page}.txt`。
- [ ] `docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md`：人读视图 + 与 RECHECK 的反证表同源。
- [ ] 本地门全绿：web `lint` / `typecheck` / `unit` / `build` / stub e2e / live e2e（全套）+
      根 `eslint .` + `validate.py` + docs-check；m0 按 `MEM-20260923-116` 配方，
      终局行 `PASS: profile=m0; 23 deterministic checks`。
- [ ] `RECHECK-20260923-154` 引用 `MEM-*`（**同一提交**），且含反证表。
- [ ] **不改**既有 6 个 live spec 与离线矩阵判据（`git diff` 证明）；不改产品代码/门禁/设计基线。

## 实施清单

### WP1 — 登记册与机械判据
- [ ] `frontendCriteriaDisclosure.ts`（数据）+ `frontend-criteria-disclosure.test.ts`（判据）。
- [ ] `git diff --stat 50afb3b..HEAD -- apps/web/tests/e2e/live-*.spec.ts` 为空 ⇒ 既有判据未动。

### WP2 — 文档视图
- [ ] `docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md`。

### WP3 — 抽查实跑 + 记录
- [ ] D-4 的成对按压实跑，红/绿落 `scratch/`。
- [ ] `MEM-*` 承载披露口径；`RECHECK-154` 同提交引用。

## 证据

- 待执行后回写。

## 状态历史

- 2026-09-24：**derive**（cycle 4）。定案 D-1…D-7 写死。起点事实（**直接读代码与 git 实测**，
  不当作验收依据）：`git diff 50afb3b..HEAD -- apps/web/tests` 共 **6 个新 live spec + 1 个离线判据
  文件**（+ `live-specs.ts` 白名单修改）；三个 cycle 已累积 **9 条按页面红证**落 `scratch/`。

## 影响报告

- **Domain/API/schema**：无改动。
- **前端**：仅 `apps/web/tests/unit/` 新增 2 个文件（登记册 + 机械判据）。
  产品代码与既有 live spec **零改动**。
- **文档**：`docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md` + 本 PLAN + RECHECK + MEM。
- **安全/凭据**：零真实出网（浏览器只打 127.0.0.1）、零凭据读取、零真实 LLM 调用。
- **兼容性/迁移**：无。
- **上游版本影响**：无新增依赖、无 pin 变更。
