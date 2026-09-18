---
id: PLAN-20260918-099
slug: goal-005-closeout-recheck
title: GOAL-005 收口复检：EC-01…EC-06 在当前树上的证据 + 干净 checkout 封印 + 终止条款判定
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 7 = 收口（README 终止条款前置）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径：只推 main、不 force、不重写历史、不推旁支触发 CI。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-099-goal-005-closeout-recheck.md
memory_entries: []
---

# PLAN-20260918-099 — GOAL-005 收口复检（cycle 7 = 收口）

## 目标

六条 EC 已全部 PASS。按 GOP 格式契约的终止条款，`ACHIEVED` 还需**独立复检**：不读历史
RECHECK 的结论文本，直接在**当前树**上复核六条 EC 的证据面（交付物/判据用例/文档同源），
取得**新的安全封印**并逐类处置，最后写「终止与收口」。

## 口径

- 复检脚本 `scratch/verify_goal005_closeout.py` **只读**当前树（文件存在、符号存在、
  文档行存在、登记面一致），任何一条不成立即非零退出（不接受"记录里说 PASS"）。
- 定向套件在同一轮里**真跑**（九个子集合并 **130 passed**），并把六条 EC 的判据用例纳入；
  CI 台账以 GitHub API 的**逐 job conclusion** 为准。
- 安全面取**干净 checkout** 的深扫封印（`git archive HEAD` 导出，树内无 `scratch/`/
  `artifacts/`），并保留工作树对照扫以量"输入边界改变剖面"。
- 复检**不新增**产品能力；只做证据复核与登记面收口。残余**不得**因收口而消失。

## 验收条件

- AC-01 `scratch/verify_goal005_closeout.py` 在当前树全绿（层级 A/B/C：交付物 / 判据用例 /
  登记面）。
- AC-02 六条 EC 的判据用例在当前树真跑通过（合并 130 passed，含 dispatch 批量读、
  重建读面、契约清账、补偿、快照迁移）。
- AC-03 干净 checkout 深扫取得 scanId/seal，**每条发现**有处置依据；工作树对照扫如实记录
  差集（gitignored `scratch/`）。
- AC-04 治理 validator 绿 + 本地 m0 全绿（23 项）。
- AC-05 GOAL 写入「终止与收口 · 收口结论」（EC 终态表 + 仍未处理的长程项 + 恢复条件），
  `status=ACHIEVED`、`latest_recheck` 指向 RECHECK-20260918-099。
- AC-06 本 GOAL 全部 CI run 终态登记（含收口提交的 run）。

## 实施清单

- [x] WP-A 复检脚本 + 当前树全绿。
- [x] WP-B CI 台账复核（cycle 1…6 的 run 逐 job 读终态；收口提交的 run 到终态后登记）。
- [x] WP-C 安全封印（干净 checkout 深扫 + 工作树对照 + 逐类处置）。
- [x] WP-D 收口登记：RECHECK-099 + GOAL「收口结论」+ ALL_PLAN + m0 + push + CI。

## 证据

- **复检脚本**：见 RECHECK-20260918-099「检查结果」；脚本本身在 `scratch/`（gitignored，
  与 GOAL-004 收口脚本同处置）。
- **定向套件**：九个判据文件合并 **130 passed**（17.71s，DSN pin 配方）。
- **封印**：干净 checkout `seal sha256:c0202d05…`（25 条：1/19/5，逐类处置）；
  工作树对照 `seal sha256:2e666a4a…`（34 条：1/28/5，差集 = gitignored `scratch/` 探针）。
- **门禁**：m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3932 passed /
  10 skipped**，491.81s）；规模门禁 935 passed；web 六门（cycle 6 实跑）；治理 validator 绿。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 7 = 收口，driver=client-goal / owner=root-agent）；
  `status: IN_PROGRESS`。
- 2026-09-18 收口：复检脚本全绿、130 passed、干净 checkout 封印取得并逐类处置；GOAL 写入
  「收口结论」并置 `status=ACHIEVED`；`status: DONE`。

## 可复用事实

无可复用事实：本 PLAN 只做收口证据复核与登记，不产生新的可复用工程事实
（六条 EC 的事实已各自由 MEM-20260918-067…072 承载）。

## 影响报告

- **Domain / API / schema / 持久化**：无变化（只做证据复核与登记）。
- **安全 / 凭据**：无变更；**不宣称"项目安全"**——扫描 `verdictEffect=none`、coverage
  `inconclusive`；依赖结论仍以 EC-01 的联网查询（3 包 20 条，带署名）为准，
  离线 advisory 通道两次输入答案不同 ⇒ 不作依据。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无（未新增依赖；pin 未变）。
- **下一项任务**：无（本 GOAL 收口）；后继入口 = 收口结论里的长程项表（人工决策面六项 +
  EC-05 ② + `DEAD_LETTER` 消费 + 各 cycle 的 W 列表）。
