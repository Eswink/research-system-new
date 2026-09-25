---
id: PLAN-20260926-188
slug: goal-018-closeout-recheck
title: GOAL-018 收口复检（EC-04）：两树复检 + as-is m0 终态行 + 13 项 `D-NN` 终态表 + CI 台账到终态
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-018
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-018 的 **EC-04**（收口复检 + 残余登记）。授权沿用该 GOAL 的
    `child_plans` 与 `push-to-main-for-CI` 口径：**只推 main、不 force、不重写历史、不推旁支**；
    授权面**仅限收口复检**，**不扩面**。本 PLAN **不改产品代码**、**不改依赖 pin**、
    **不放宽任何判据 / 阈值 / 放行面**、**不做任何鉴权 / 中间件 / 路由保护改动**。
    交付物 = 独立复检脚本（两树同结论 + 非恒真）+ m0 终态行 + 13 项 `D-NN` 终态表
    + CI 台账到终态 + 承继残余逐条在位。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-189-goal-018-closeout-recheck.md
memory_entries: []
---

# PLAN-20260926-188 — GOAL-018 收口复检（EC-04）

## 目标

把 GOAL-018 前一轮的三件交付（EC-01 `yaml` patch / EC-02 `undici` 调研 / EC-03 13 项结清）
**换一个观察者**复检一遍：复检脚本**不复用 GOAL 的叙述**，自己重读树做结构断言，
并把该面的判据文件在**被测树**里以子进程实跑；同一脚本在**工作树**与**干净 checkout**
（`git worktree`，detached HEAD = cycle 1 推送 tip `83b782c`）给出**同一结论**且**非恒真**
（按压必须判红）。再补交 EC-04 的四件交付物：m0 终态行、13 项 `D-NN` 终态表、
CI 台账到终态、承继残余逐条在位。**本 PLAN 不改任何产品代码 / 判据口径的强度 / 阈值。**

## 验收条件

- **AC-1**：复检脚本两路同时成立——①「脚本自己重读树」的**结构半**；② 该面的判据文件
  在**被测树**里实跑（pytest / 治理 `validate.py` / `DOCS-CHECK`）。两路都过 ⇒ 该面复检成立。
- **AC-2**：**非恒真**——按压 `yaml-pin` / `undici-upgrade` / `terminal-row` / `terminal-state` /
  `goal-decl` / `residual` 六处（**只改内存，不写仓库文件**）⇒ 结构半**必须判红**且点名是哪一条。
- **AC-3**：**两棵树同结论**——工作树与干净 `git worktree`（detached HEAD `83b782c`）跑同一脚本：
  **判词列（名称 + OK）14/14 逐行相同**。
- **AC-4**：**as-is 本机 m0** 到 `PASS: profile=m0; 23 deterministic checks`（独占、仓库 `.venv`、
  DSN 固化、`--keep-going`）。
- **AC-5**：治理 `validate.py` 绿；13 项 `D-NN` 终态表在位且与 GOAL 人工面**逐条同词**；
  承继残余 `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` 逐条在位。
- **AC-6**：CI 台账到终态（M0 **八 job** + CodeQL + Dependabot run，含 `run_attempt`）。

## 实施清单

- [x] **WP1｜复检脚本**：`scratch/goal018-ec04-recheck.py`（**结构半**；**刻意不含任何进程执行**
      ——「改动面」由调用方先用 git 写成清单，脚本只读清单；判据实跑由调用方逐条执行）。
- [x] **WP2｜两树复检**：工作树 + 干净 checkout（`D:\rs-goal018-clean`，detached HEAD `83b782c`）
      各跑一次结构半 + 判据面；两树输出**逐字节相同**。
- [x] **WP3｜非恒真按压**：六个按压面各判红一次，并**逐条记下是哪一条判据被点红**。
- [x] **WP4｜m0 终态行 + 台账 + 残余登记**：as-is m0 全量；CI 台账补到终态；残余逐条确认。

## 证据

- **复检脚本（结构半，14 条）**：`EC-01 yaml pin 为 2.8.4` / `EC-01 lockfile yaml 解析唯一且为 2.8.4` /
  `EC-02 undici 仍锁 5.29.0 且入边恰好 1 条` / `EC-02 未出现 undici 6/7/8 解析` /
  `EC-02 无 overrides/resolutions 字段` / `EC-02 结论文档含三问与可拍板结论节` /
  `EC-02 Node 前提与结论一致 22.18.0` / `EC-03 终态表 13 行且编号齐` /
  `EC-03 终态全在词汇表内且汇总 9/1/3/0` / `EC-03 GOAL 侧 13 条声明与简报逐条同词` /
  `EC-04 承继残余在人工面逐条在位` / `EC-04 GOAL 人工面 13 条编号项` /
  `边界 鉴权/中间件/路由零改动` / `边界 依赖面改动恰为 yaml 两文件` ⇒ **`FAILED=[]`、`RECHECK: PASS`**。
- **判据面**：`tests/tooling/test_pending_decisions_briefing.py` = **14 passed**；
  `tests/tooling/test_python_source_limits.py` = **1029 passed**；
  治理 `validate.py` = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks`
  （**工作树与干净树同结论**）。
- **两树同结论**：`scratch/goal018-ec04-worktree.out` vs `scratch/goal018-ec04-clean.out` ——
  **判词列 14/14 相同**、且**整份输出逐字节相同**（`diff` 无输出）。
- **非恒真（6/6 判红）**：
  `yaml-pin` ⇒ 点红 `EC-01 yaml pin 为 2.8.4`；
  `undici-upgrade` ⇒ 点红 `EC-02 undici 仍锁 5.29.0 且入边恰好 1 条`；
  `terminal-row` / `terminal-state` / `goal-decl` ⇒ 点红 `EC-03 …` 三条中的相关项；
  `residual` ⇒ 点红 `EC-04 承继残余在人工面逐条在位`。
- **一次按压打偏（当场发现并修）**：`terminal-row` 与 `residual` 第一版**没判红**——
  ① 简报里有一张**同形状的索引表**（也以 `| D-05 | …` 开头），整份替换命中了错的那张；
  ② 残余检查当时扫的是**整份 GOAL**，而 `R-M1` 在别处还有一处提及。
  修法：① 按压加**作用域**（`terminal-block`：只在终态表块内替换，块内未命中即断言失败）；
  ② 残余检查改为**只在人工面节内**判定，并把按压锚点收到登记行的原文。
- **一次节边界缺陷（同一根因，已收紧）**：`_GOAL_SECTION` 原为 `^## .*不进入循环.*?^## `——
  前置 `.*` 是**贪婪**的，匹配会从文件里**更早的** `##`（实测是「目标与退出标准」）起算，
  把别处的编号项与 `**D-NN 终态 = …**` 声明一并吸进来 ⇒「13 条声明」就不再是绑在这一节上。
  收紧为 **标题行自身必须含该短语**（`^## [^\n]*不进入循环[^\n]*\n`）后重新通过；
  这是**加强**（声明被绑到该节），不是放宽。
- **`yaml` 告警真的清掉了（外部证据）**：`/dependabot/alerts?state=open` 在 `2.8.4` 落地 main 后
  **9 → 8 条**，且剩余 **8 条全部是 `undici`**（6 medium + 2 low）
  —— 同时**独立印证 EC-02 的「一字未升」**（存留数不变）。留档
  `scratch/goal018-gh-alerts-after.json`。
- **as-is 本机 m0**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24、
  `FAILED` 零命中、退出码 0；日志 `scratch/goal018-c2-m0-as-is.log`）。
- **CI 台账**：cycle 1 推送 tip `83b782c` ⇒ M0 run **36191382569**（`run_attempt=1`，**八 job 全
  success**）+ CodeQL run **36191381460**（`run_attempt=1`，3/3 success）+ Dependabot run
  **36191504926**（`success`）；`ALL_TERMINAL`。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 派生自 GOAL-20260926-018（cycle 2）：EC-04 收口复检。 |
| 2026-09-26 | VERIFYING | 复检脚本 + 两树同结论 + 6/6 按压 + as-is m0 23/23 + 台账到终态。 |
| 2026-09-26 | DONE | 独立复检 `RECHECK-20260926-189` = `PASS_WITH_WARNINGS`（W-1/W-2/W-3 见该记录）；GOAL-018 四条 EC 全部有实跑证据。 |

## 影响报告

- **改动面**：只动**记录面**（本 PLAN + 其复检 + `.cursor/plans/ALL_PLAN.md` + GOAL-018 回写）
  与一处**判据口径收紧**（`tests/tooling/test_pending_decisions_briefing.py` 的节边界正则）；
  复检脚本在 `scratch/`（**gitignored、不提交**）。
- **Domain / API / schema**：**零变化**。
- **安全 / 凭据**：**零变化**；依赖 pin **零变化**（本轮不碰 `yaml` / `undici`）。
- **判据强度**：**只增不减**——节边界收紧使「13 条声明」真正绑在人工面节上；
  六条按压全部判红。
- **兼容性 / 迁移风险**：无（记录面 + 一条正则收紧）。
- **本轮无可复用事实沉淀**：工程记忆已在 cycle 1 由 `MEM-20260926-142` 收口
  （「patch 的落地目标是最新 patch / 前置调研的交付标准是可拍板 / 按压必须落在判据自己的块内」），
  本 PLAN 的追加结论（**节边界要绑标题行**、**按压要带作用域**）是同一族的两条同源教训，
  已并入该记忆的正文，**不新增条目**。
- **下一项任务**：GOAL-018 收口后无下一轮；
  后续轮次 = **甲（主体模型 + 最小认证面）**，**需用户另行授权**。
