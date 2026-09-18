---
id: PLAN-20260918-106
slug: goal-006-closeout-recheck
title: GOAL-006 收口复检：EC-01…EC-06 在当前树上的证据 + 干净 checkout 封印 + 终止条款判定
status: IN_PROGRESS
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 7 = 收口（README/GOAL 终止条款前置）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-106-goal-006-closeout-recheck.md
memory_entries: []
---

# PLAN-20260918-106 — GOAL-006 收口复检（cycle 7 = 收口）

## 目标

六条 EC 已全部 PASS。按 GOAL 格式契约的终止条款，`ACHIEVED` 还需**独立复检**：不读历史
RECHECK 的结论文本，直接在**当前树**上复核六条 EC 的证据面（交付物 / 判据用例 / 文档同源），
取得**新的安全封印**并逐类处置，最后写「终止与收口」。

## 口径

- 复检脚本 `scratch/verify_goal006_closeout.py` **只读**当前树，三层判据 = 交付物在树 /
  判据用例在树 / 登记面一致（GOAL `status`、`latest_recheck`、EC 表、ALL_PLAN 行、
  child_plans 指向的文件存在）；任何一条不成立即非零退出（不接受"记录里说 PASS"）。
- 定向套件在同一轮里**真跑**（六条 EC 的判据文件 + 受影响套件合并），CI 台账以 GitHub API
  的**逐 job conclusion** 为准。
- 安全面取**干净 checkout** 的深扫封印（`git archive HEAD` 导出，树内无 `scratch/`/
  `artifacts/`），并保留工作树对照扫以量"输入边界改变剖面"。
- **附带更正**（复检发现的登记面缺陷，如实登记为返工事实）：EC 状态表的 EC-03 / EC-04 行在
  cycle 3 / cycle 4 回写时**漏改**（仍写 `PENDING`，与两条 EC 的 frontmatter `status: PASS`
  和「状态历史」矛盾）；收口时按 frontmatter 与 RECHECK 更正为 PASS。
- 复检**不新增**产品能力；只做证据复核与登记面收口。残余**不得**因收口而消失。

## 验收条件

- **AC-01** `scratch/verify_goal006_closeout.py` 在当前树全绿（层级 A/B/C，条数实测登记）。
- **AC-02** 六条 EC 的判据用例在当前树真跑通过（合并 passed 数登记；含 PG 单语句快照探针、
  批量读上限与弱同判、补偿失败留痕读面、重建就绪读面、时钟覆盖矩阵、ADR 登记判据）。
- **AC-03** 干净 checkout 深扫取得 scanId/seal，**每条发现**有处置依据；工作树对照扫如实记录
  差集（gitignored `scratch/` 等）。
- **AC-04** 治理 validator 绿 + 本地 m0 全绿（23 项）。
- **AC-05** GOAL 写入「终止与收口 · 收口结论」（EC 终态表 + 仍未处理的长程项 + 恢复条件），
  `status=ACHIEVED`、`latest_recheck` 指向 RECHECK-20260918-106。
- **AC-06** 本 GOAL 全部 CI run 终态登记（含 cycle 6 实现+回写推送 `3b189c8` 的 run
  35403759948）；收口提交自身的 run 按闭合口径在**回合汇报**给出终态。

## 实施清单

- [ ] WP-A 复检脚本 + 当前树全绿（层级 A/B/C）。
- [ ] WP-B 六条 EC 判据套件合并真跑 + CI 台账复核（逐 job）。
- [ ] WP-C 安全封印（干净 checkout 深扫 + 工作树对照 + 逐类处置）。
- [ ] WP-D 收口登记：RECHECK-20260918-106 + GOAL「收口结论」/`status: ACHIEVED`、
  EC 表更正、ALL_PLAN、m0 23 项、push、CI 到终态。

## 证据

（执行后填写。）

## 状态历史

- 2026-09-18 建档（GOAL-20260918-006 cycle 7 = 收口，driver=client-goal / owner=root-agent）；
  `status: IN_PROGRESS`。

## 影响报告

- **Domain / API / schema / 持久化**：无变化（只做证据复核与登记）。
- **安全 / 凭据**：无变更；收口**不宣称"项目安全"**（扫描 coverage 缺口与残余照旧登记）。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无（未新增依赖；pin 未变）。
- **下一项任务**：无（本 GOAL 收口）；后继入口 = 收口结论里的长程项表（「不进入循环 /
  需人工拍板」六项 + 各 cycle 的 W 列表 + 扫描 coverage 缺口）。
