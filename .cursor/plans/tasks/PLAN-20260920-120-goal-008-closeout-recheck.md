---
id: PLAN-20260920-120
slug: goal-008-closeout-recheck
title: GOAL-008 收口复检：EC-01…EC-06 在当前树与干净 checkout 上的证据 + 终止条款判定
status: IN_PROGRESS
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 7 = 收口（GOAL「终止与收口」前置）。授权来源：2026-09-20 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；push-to-main-for-CI 授权见 GOAL-20260920-008 frontmatter `authorization.ref` 第 (4) 条（只推 main、不 force、不重写历史、不推旁支）。复检**不新增产品能力**：只做证据复核、登记面收口与**复检实测出的缺陷修复**；不得放松默认 deny / 不改 Accepted ADR / 不改门禁与断言强度 / 不把真实 runtime 设为默认。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260920-120 — GOAL-008 收口复检（cycle 7 = 收口）

## 目标

六条 EC 已全部 PASS（EC-06 于 cycle 6 收口）。按 GOAL「终止与收口」条款，`ACHIEVED`
还需**独立复检**：不读历史 RECHECK 的结论文本，直接在**当前树**与**干净 checkout** 上
复核六条 EC 的证据面（交付物 / 判据用例 / 登记一致），并写「终止与收口 · 收口结论」。

## 口径

- 复检脚本 `scratch/verify_goal008_closeout.py`（只读、gitignored；可用
  `GOAL008_ROOT=<path>` 指向另一棵树）三层判据：
  **A 交付物在树** / **B 判据用例在树** / **C 登记面一致**（GOAL 的 EC 表逐行 `status: PASS`、
  `latest_recheck` 指向存在的 RECHECK、child_plans 文件存在且 `status: DONE`、
  ALL_PLAN 各行 DONE、`memory_entries` 指向的文件存在）；任一不成立即非零退出
  （**不接受"记录里说 PASS"**）。
- **干净 checkout 封印**：`git clone --no-hardlinks` 到仓库外（推送后的 tip），在**克隆树**上
  跑同一份复检脚本与**六条 EC 判据套件合并**；克隆树用主仓库的 venv 解释器（依赖是安装物、
  不是仓库内容），如实披露这一点。克隆树上的判据结论必须与当前树**一致**——不引入新绿、
  也不引入新红。
- **live 分支的如实登记（GOAL 明文要求）**：EC-04 与 EC-05 的 live 分支在本机**没有发生过**
  （六项候选凭据环境变量全 absent、`RESEARCHOS_AGENT_RUNTIME` 未配置 ⇒ 门两条都关着）。
  收口结论里必须**逐字写明 skip 与原因**，并作为残余登记——**不得**写成「已实测通过」。
- **不做的事**：不新增依赖、不改 pin、不改门禁与断言强度、不改默认 runtime、
  不触碰凭据值、不把「未实测」改写成「已验证」。

## 验收条件

- **AC-01** `scratch/verify_goal008_closeout.py` 在当前树全绿（A/B/C 三层条数实测登记）。
- **AC-02** 六条 EC 的判据套件**合并**真跑通过（同一命令、同一进程；合并 passed/skipped 登记）。
- **AC-03** 干净 checkout 封印：clone 的 `git status` 干净、`git ls-files` 计数一致；
  复检脚本在 clone 上结论与当前树一致；合并判据套件在 clone 上结论与当前树一致。
- **AC-04** 治理 `validate.py` 绿 + `validate_bundle` 绿 + DOCS-CHECK 绿 + 本地 **m0 全量 23 项**绿。
- **AC-05** GOAL 写入「终止与收口 · 收口结论」（EC 终态表 + 仍未处理的长程项 + 恢复条件），
  `status: ACHIEVED`，`latest_recheck` 指向 RECHECK-20260920-120，EC 表逐行 PASS。
- **AC-06** 残余登记：六条 EC 的 W 列表汇总 + 「不因本 GOAL 存在而被宣称已解决」的项
  （ADR-0031 / 威胁建模 / `artifacts/` 明文 token 清理 / 450 行纪律 / 依赖 pin 升级 /
  hook 侧 L3 门）；并写明恢复条件。
- **AC-07** CI 台账尾巴：cycle 6 与本收口推送的 run 与六 job 结论全部记账（真实终态，禁止推测）。

## 实施清单

### WP-A — 复检脚本与当前树复核

- `scratch/verify_goal008_closeout.py`：A/B/C 三层；在当前树跑并登记条数。
- 提交：（脚本 gitignored，不提交）

### WP-B — 干净 checkout 封印

- `git clone --no-hardlinks` 到仓库外（tip = 本轮推送后的 SHA）；跑脚本 + 合并判据套件；
  与当前树对照。
- 提交：（无仓库改动）

### WP-C — 记录与收口

- RECHECK-20260920-120（收口复检）+ PLAN-120 收口 + GOAL「收口结论」+ `status: ACHIEVED`
  + 残余登记 + CI 台账尾巴。
- 提交：`docs(goals): close GOAL-008 ACHIEVED -- independent recheck + clean-checkout seal`

## 证据

见 `.cursor/plans/rechecks/RECHECK-20260920-120-goal-008-closeout-recheck.md`。

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 7 = 收口）：`status: IN_PROGRESS`。
  按 GOAL-20260919-007 的同名收口口径（三层判据脚本 + 干净 checkout 封印 + 残余登记 +
  CI 台账尾巴）执行。

## 影响报告

- **Domain/API/schema 变化**：无（收口不新增产品能力；若复检实测出缺陷，按缺陷修并如实登记）。
- **安全/凭据变化**：无；live 分支的 skip 事实如实登记（不写成已实测）。
- **兼容性/迁移风险**：无。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：GOAL-008 收口后，长程项按「仍需人工拍板」清单交用户决策
  （ADR-0031 / 威胁建模 / `artifacts/` 明文 token 清理 / 依赖 pin 升级 / hook 侧 L3 门）；
  真实端点上的第一次 live run 需要用户注入凭据后按
  `docs/integration/LIVE_MODEL_RUNBOOK.md` 执行。
