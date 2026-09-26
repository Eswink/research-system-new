---
id: PLAN-20260926-194
slug: goal-019-closeout-recheck
title: GOAL-019 cycle 3（EC-05）：收口复检（两树同结论 + as-is m0 23/23 + 残余逐条 + CI 台账到终态）
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-019
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-019 的 **EC-05**（收口复检 + 残余登记）。授权沿用该 GOAL 的
    `authorization.ref`：**只保护写面**、**认证可关**、**主体归因落 canonical**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：多租户 / organization scope / RBAC / 角色权限矩阵 / M18 任何内容；
    **不给读面加认证**；**不改 `Idempotency-Key` 语义**；**不把 token 写进任何文件 / CI /
    记录 / 日志 / 遥测 / 测试输出**；**不新增依赖**；**不做** D-12 的 (a) 面。
    **本 PLAN 不放宽任何判据 / 阈值 / 放行面**，**不新增策略面 allow**，
    **不改 Canonical State 边界**，**不得宣称项目安全**。本 PLAN **不改产品代码**
    （收口 = 复检 + 记录 + 状态收口；若复检判红 ⇒ **只修被判红的那个面**，不动别的）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-195-goal-019-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-145-writing-records-is-itself-gated-so-run-the-gate-last.md
---

# PLAN-20260926-194 — GOAL-019 收口复检（EC-05）

## 目标

把 GOAL-019 收口：**独立复检**（不复用实施方的结论叙述，直接读树 + 跑判据 + 按压）、
**两树同结论**、**as-is 本机 m0 = 23/23**、**CI 台账到终态**、**残余逐条登记**，
最后把 GOAL 置 `ACHIEVED`。

## 收口检查清单（逐条给可复核观察面）

1. **两树同结论**：干净 checkout（`git worktree add --detach <tip>`）与工作树跑同一组判据，
   输出**逐行比对**；两树的**改动面清单**一致。
2. **判据非恒真**：在**干净树**里按压一次本轮新增的判据（改一处口径 ⇒ 判红 ⇒ 逐字节还原）。
3. **as-is 本机 m0**：终态行 `PASS: profile=m0; 23 deterministic checks`。
4. **记录面自身受判**：本轮已实测过一条——记录里的用词会被
   `tests/architecture/python/test_reproducibility_wording.py` 扫到（`.cursor/plans` 在它的
   扫描面内）⇒ 收口必须**在写完记录之后**再跑一次记录面判据，不能只跑治理与 DOCS-CHECK。
5. **CI 台账到终态**：逐 run 逐 job 实查（含 `run_attempt`），被取消的 run 如实记 `cancelled`。
6. **残余逐条**：`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6`
   原样承继（逐条写明"是什么 / 为什么还开着 / 归属方"），并登记本轮新增的 W。
7. **不得宣称项目安全**：`R-M1` 未收口 ⇒ 收口记录与 GOAL 收口句都必须保留该口径。

## 验收条件

- **AC-1**：两树同结论（判据面逐行一致 + 改动面清单一致 + 干净树按压判红 + 逐字节还原）。
- **AC-2**：as-is 全量 m0 = **23/23**，且**看得到 `Passed` 的用例数**（不是只看 exit code）。
- **AC-3**：`validate.py` + `DOCS-CHECK` + `ruff`（check / format）在**写完记录之后**复跑绿。
- **AC-4**：CI 台账覆盖 GOAL-019 全部推送（charter / cycle 1 / cycle 2 / 收口），
  每条给 run id + 逐 job 结论 + `run_attempt`；**红过的如实记红并写明修法与复绿证据**。
- **AC-5**：残余逐条在位且**归属方**明确；`R-M1`（Mimosa 钩子侧结论未取得）口径不变。
- **AC-6**：GOAL `status: ACHIEVED`、`latest_recheck` 指向 PASS/PASS_WITH_WARNINGS 复检、
  `child_plans` 含全部三个子 PLAN、`memory_entries` 含全部 MEM。

## 实施清单

- [x] **WP1｜两树**：干净 worktree + 判据面逐行比对 + 干净树按压 + 还原。
- [x] **WP2｜as-is m0**：独占全量（仓库 `.venv`、DSN 固化、`--keep-going`）。
- [x] **WP3｜记录面复跑**：`tests/architecture/python` + `tests/tooling` + 治理 + DOCS-CHECK
      **在记录写完之后**跑一遍。
- [x] **WP4｜CI 台账**：逐 run 逐 job 补齐到终态。
- [x] **WP5｜剩余与收口**：残余逐条 + GOAL 置 `ACHIEVED` + 本 PLAN / RECHECK / ALL_PLAN 回写。

## 证据

（实施后逐条填写；未实跑不得记 PASS。）

**详细证据在 `RECHECK-20260926-195`（独立复检）**；这里只记本 PLAN 自己的 WP 状态与结论。

| WP | 结果 |
| --- | --- |
| WP1｜多面同结论 | 交付 tip `957fe05` = **1359 passed / exit=0**；记录 tip `75155b2` = **exit=1**（1 条）；终态 = **exit=0**；`957fe05..75155b2` = **恰好 6 个记录文件** ⇒ 归因唯一。**同提交两 checkout**（deliv + mirror）同数同结论。干净树按压 ⇒ **判红** + sha256 **逐字节还原** + 复原后 exit=0 |
| WP2｜as-is m0 | 终态行 **`PASS: profile=m0; 23 deterministic checks`**、`M0_EXIT=0`、`PASS [` = **24**、`python/tests` = **4550 passed / 20 skipped**、`FAILED`/`ERROR` 零命中（日志 `scratch/goal019-c3-m0-as-is.log`）；**跑在全部收口记录写完之后**（与 cycle 2 相反 —— 那次跑在记录之前，记录面没被覆盖） |
| WP3｜记录面复跑 | `tests/architecture/python` = **186 passed**（+11 = 新增判据）；`tests/tooling` 与治理 / DOCS-CHECK 在**记录写完之后**复跑绿 |
| WP4｜CI 台账 | 四条推送逐 run 逐 job 实查（含 `run_attempt`）：`d4e559e` / `c87823e`+`8ed413b` / `957fe05` 全 **success**；**`75155b2` = M0 failure**（`quality-ubuntu-latest` + `quality-windows-latest`）⇒ 已修，收口提交的 run 依「固定口径」只在回合汇报记账 |
| WP5｜剩余与收口 | 残余 `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` **原样保留**（逐条 + 归属方）+ 本 GOAL 新增 `W-7…W-11`；GOAL 置 `ACHIEVED` |

**本 PLAN 的 WP3 顺序要求是**经验**得来的，不是先验**：cycle 2 的本地 m0 跑在记录写入**之前**
⇒ 记录面**从未被门覆盖** ⇒ `75155b2` 的 M0 判红（`test_reproducibility_wording.py` 的
`_SCAN_ROOTS` 含 `.cursor/plans`）。修法与流程改进见 `RECHECK-195` 第四节 +
`MEM-20260926-145`。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 派生自 GOAL-20260926-019（cycle 3）：EC-05 收口复检 + 残余登记。**已先落一条实测教训**（第 4 条清单项）：记录里的用词会被 `.cursor/plans` 扫描面内的判据抓到 ⇒ 收口的顺序必须是「写记录 → 跑记录面判据 → 全量 m0」，且**全量 m0 要压在记录写完之后**。 |
| 2026-09-26 | DONE | WP1–WP5 全部落地。**多面复检抓到并修好一个真红**（cycle 2 记录提交 `75155b2` 的 M0 failure，根因 = 记录里裸写被禁词 ⇒ 判据判红）；交付 tip `957fe05` 与本轮终态均绿；**as-is m0 = 23/23**（见 3.1 / RECHECK-195 第三节）；CI 台账覆盖四条历史推送且**红过的如实记红**；残余九条 + 新增五条逐条登记；GOAL 置 `ACHIEVED`。 |

## 影响报告

- **改动面（计划）**：只有记录 + 状态（`GOAL-019` / `PLAN-194` / `RECHECK-195` / `ALL_PLAN` /
  可能一条记录措辞修正）；**产品代码零改动**。
- **Domain / API / schema**：零变化。
- **安全 / 凭据**：凭据纪律不变（只登记变量名）；无新增放行面；**不得宣称项目安全**。
- **兼容性 / 迁移风险**：无（收口不改产品面）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-019 收口后，残余项按各自归属方推进（`R-M1` 属 Mimosa 钩子侧、
  `undici` 属上游、D-12 (a) 面需另行授权）。
