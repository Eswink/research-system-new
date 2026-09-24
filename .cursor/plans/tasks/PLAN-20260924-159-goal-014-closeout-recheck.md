---
id: PLAN-20260924-159
slug: goal-014-closeout-recheck
title: 收口复检 + 残余登记：独立脚本两树同结论、m0 23/23、治理绿、CI 台账到终态（GOAL-014 EC-05）
status: DONE
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 建档授权（2026-09-24 用户 goal 模式指令）的 **EC-05**：
    「**收口复检 + 残余登记**：① 独立复检脚本（只读、标准库、**不 import 仓库代码**）
    在**当前树**与**干净 checkout**（`git worktree` / 临时克隆）两处**同判据同结论**；
    ② 本地 **m0 = 23/23**（终局行逐字 `PASS: profile=m0; 23 deterministic checks`）；
    ③ 治理 `validate.py` **绿**；④ **CI 台账到终态**（M0 六 job + CodeQL）；
    ⑤ **13 条人工面原样保留** + 本 GOAL 的 `W` 列表 + 承继残余逐条登记、不隐藏；
    ⑥ 收口 RECHECK 的 `result` = `PASS` 或 `PASS_WITH_WARNINGS`，且本文件的
    `latest_recheck` 为**仓库相对路径**」。
    **本 PLAN 的纪律**：收口只做**记录与复检**，**不**为了让终局行好看而改任何判据、
    **不**放宽任何门、**不**在授权外放宽策略面；干净 checkout 只用于复检，**不**是发布物。
    **本 PLAN 的结论必须如实**：`EC-02 = BLOCKED` 是**如实登记**，因此本 GOAL 的收口
    **不是** `ACHIEVED` —— 按建档时写死的规则，EC-01…EC-05 全 PASS 才是 `ACHIEVED`。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-161-goal-014-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-116-local-m0-green-recipe.md
---

# PLAN-20260924-159 — 收口复检 + 残余登记（GOAL-014 EC-05）

## 目标

按建档时写死的收口条件，对 GOAL-014 的六项做**独立复检**并对全部残余**逐条登记**；
把「本地 m0 未全绿」的**环境型残余**用**可核对的方式**处置成**可判读的终态**。

## 计划开始前的定案（写死）

- **D-1｜复检脚本必须独立**：`scratch/verify_goal014_c5.py` 只读、**只用标准库**、
  **不 import 仓库代码**；复检**哪棵树**由 `VERIFY_ROOT`（默认当前工作目录）决定 ——
  早期用 `Path(__file__).parents[1]` 会让「两棵树各跑一遍」实际跑主树两次（GOAL-013 教训）。
- **D-2｜两树同结论**：干净 checkout 用 `git worktree add --detach <仓外目录> <tip>`，
  并核对**无 `scratch/`**、`git ls-files` 计数与树内文件一致。
- **D-3｜`R-F3` 的处置口径（承 GOAL-013）**：本机 m0 的 `framework/validate_bundle` 会被
  **仓库外并发写者**的 gitignored `scratch/*.md` 判红（正文里的路径正则被纯文本链接扫描
  读成本地链接）。处置 = **临时代管（quarantine）该文件 → 跑完整 m0 → 立即还原**，
  全程记录 `sha256` / `size` / `mtime` 并在还原后**复核一致**；CI 侧检出无 `scratch/`
  ⇒ CI 不受影响。**不得**把「临时移出后 23/23」写成「本机一直 23/23」。
- **D-4｜收口结论必须与 EC 实况一致**：`EC-02 = BLOCKED`（`F-10` / `F-11` 待拍板）
  ⇒ 本 GOAL **不是** `ACHIEVED`；收口只把状态**收敛**为「可交接」。

## 验收条件

- [x] **AC-1｜独立复检两树同结论**：`verify_goal014_c5.py` 在**当前树**与**干净 checkout**
      均 `failures=0`（同一份脚本、同一批判据，共 42 项）。
- [x] **AC-2｜本地 m0 终局行**：代管 `R-F3` 文件后完整 m0 ⇒ 终局行
      `PASS: profile=m0; 23 deterministic checks`；还原后**逐字节复核**该文件与代管前一致。
- [x] **AC-3｜治理绿**：`validate.py` ⇒ `Cursor 治理验证通过`；
      `docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`。
- [x] **AC-4｜CI 台账到终态**：本 GOAL 的每个推送 tip 的 M0 六 job + CodeQL 结论逐 run 实查
      （含 cycle 3 `bf3ecdc`、cycle 4 `1d2482f`）。
- [x] **AC-5｜残余逐条登记**：13 条人工面（第 3 / 12 项已完成、第 13 项已豁免，按事实标注）
      + `W-A`/`W-C`（**本 GOAL 已消灭**）+ `R-M1`/`R-D1`/`R-B1`/`R-N1`/`R-F1`/`R-F2`/`R-F3`
      + 本 cycle 新登记的拍板项（`F-10`/`F-11`、读类成类预放行口径、三项残余处置），
      全部落 RECHECK-161 的残余表。
- [x] **AC-6｜`latest_recheck` 为仓库相对路径**，且收口 RECHECK 的 `result` ∈ {PASS, PASS_WITH_WARNINGS}。

## 实施清单

- [x] **WP1｜独立复检脚本**（`scratch/verify_goal014_c5.py`，42 项判据：A 策略面 / B 真实控制面
      装配边界 / C 差集审计 / D 记录自洽 / E 越权检查 / F 残余在册 / G 判据实跑）。
- [x] **WP2｜干净 checkout**：`git worktree add --detach <仓外> <tip>` → 两树同跑复检。
- [x] **WP3｜m0 终局行**：代管 `R-F3` 文件 → 完整 m0 → 还原 + 逐字节复核。
- [x] **WP4｜残余登记与收口**：RECHECK-161 + 本 PLAN + GOAL 收口回写。

## 证据

- **两树同结论**：`scratch/g014-c5-verify-current-tree.txt`（`VERIFY_ROOT = D:\research-system`）
  与 `scratch/g014-c5-verify-clean-checkout.txt`（`VERIFY_ROOT = …\Temp\g014final`）
  **都是 `checked=42 failures=0`**。干净 checkout = `git worktree add --detach <仓外> 1d2482f`，
  实测 **无 `scratch/`**、`git ls-files` = **3343**。
- **m0 终局行（代管 `R-F3` 文件后）**：`scratch/goal014-c5-m0-final.log` ⇒ 终局行**逐字**
  **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 行 24 条 = 23 项受检 +
  `release-assets-immutable` 在计数之外）；`python/tests` = **4429 passed / 19 skipped / 0 failed**。
  代管与还原记录：`scratch/g014-c5-quarantine-record.json`（`sha256:7af32093…` / 69944 B /
  mtime 1790187424.185179），还原后**逐字节复核一致**（`sha256` 与 `size` 相同、`mtime` 差 < 0.01s；
  见 RECHECK-161 的「代管与还原」节）。
- **一次失败如实登记**：第一次全量 m0（`scratch/goal014-c5-m0.log`）判红 **1 项 `framework/validate`**
  —— 根因是**本 cycle 自己的收口记录当时还没写完**（`PLAN-20260924-159` 缺「证据 / 影响报告」两节、
  未进 `ALL_PLAN`）⇒ **记录补齐后重跑**才拿到 23/23；不是产品缺陷，也不是「靠改门变的绿」。
- **治理与文档门**：`validate.py` ⇒ `Cursor 治理验证通过`；
  `docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`。
- **CI 台账**：见 GOAL 的台账表（cycle 3 `bf3ecdc` = M0 35969958027 六 job + CodeQL
  35969957120 3/3；cycle 4 `1d2482f` = M0 35972496231 六 job + CodeQL 35972494660 3/3）。

## 状态历史

- 2026-09-24：derive + 执行（GOAL-014 cycle 5）。复检脚本 42 项判据在**两棵树**同结论；
  `R-F3` 按 GOAL-013 的既有口径**代管→跑 m0→还原**，拿到逐字终局行；
  第一次 m0 判红 `framework/validate` 的根因是**本 cycle 记录未写完**，如实登记后补齐重跑。
  **未改任何产品代码 / 策略面 / 判据 / 门禁**；干净 checkout 仅用于复检，跑完即移除。

## 影响报告

- **改动面**：本 PLAN + `RECHECK-20260924-161` + `ALL_PLAN` 投影 + GOAL 收口回写；
  **零产品代码 / 零策略面 / 零判据 / 零门禁改动**。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：无。复检脚本只读、零出网（只跑本仓离线判据）。
- **兼容性/迁移风险**：无。干净 checkout 是非仓库内临时目录，**已移除**，不作为发布物。
- **上游版本影响**：无。
- **下一项任务**：GOAL-014 收敛为 `BLOCKED`（EC-02 的判据本体待用户拍板）。

