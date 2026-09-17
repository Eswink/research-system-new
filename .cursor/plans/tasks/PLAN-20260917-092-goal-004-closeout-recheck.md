---
id: PLAN-20260917-092
slug: goal-004-closeout-recheck
title: GOAL-004 收口复检：EC-01…EC-07 在当前树上的证据 + 全部 CI run 逐 job 复核 + 终止条款判定
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 9 = 收口复检（README 终止条款前置）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-092-goal-004-closeout-recheck.md
memory_entries:
  - MEM-20260917-059
  - MEM-20260917-060
  - MEM-20260917-061
  - MEM-20260917-062
  - MEM-20260917-063
  - MEM-20260917-064
  - MEM-20260917-065
  - MEM-20260917-066
---

# PLAN-20260917-092 — GOAL-004 收口复检（cycle 9）

## 目标

七个 EC 已全部 PASS。按 README 的终止条款，`ACHIEVED` 还需**独立复检**：不读历史 RECHECK 的
结论文本，直接在**当前树**上复核七个 EC 的证据面，并把本 GOAL 的**全部 CI run 逐 job 重读**，
最后写「终止与收口」。

## 口径

- 复检脚本只读当前工作树（源码标记 / 文档 / 登记表），并且**真的跑**每个 EC 的定向套件；
  任何一条断言失败即非零退出（不接受"记录里说 PASS"）。
- CI 复核以 GitHub API 的**逐 job conclusion** 为准；不臆测、不省略失败项（本 GOAL 唯一一次
  失败是建档 run，其修复 run 在同一个 cycle 内已记录）。
- 复检**不新增**产品能力；只做证据复核与登记面收口。

## 验收条件

- AC-01 `scratch/verify_goal004_closeout.py` 在当前树全绿（46 条断言：EC-01 6 / EC-02 4 /
  EC-03 5 / EC-04 4 / EC-05 8 / EC-06 4 / EC-07 6 / 治理登记面 9）。
- AC-02 每个 EC 的**定向套件**在当前树真的通过（不是只查文件存在）。
- AC-03 本 GOAL 的全部 CI run 逐 job 复核，失败项如实列出并给出修复 run。
- AC-04 治理 validator 绿 + 本地 m0 全绿。
- AC-05 GOAL 写入「终止与收口」（结论 + 仍开放的长程项表 + 后继入口建议），
  `status=ACHIEVED`、`latest_recheck` 指向本轮的 PASS_WITH_WARNINGS 复检、
  `memory_entries` 列出本 GOAL 沉淀的 8 条记忆。

## 实施清单

- [x] WP-A 写复检脚本（`scratch/verify_goal004_closeout.py`）并对当前树跑通。
- [x] WP-B CI 台账复核：44 个 GOAL-004 commit → 16 个 run，逐 job 读终态。
- [x] WP-C 收口登记：RECHECK-092 + GOAL「终止与收口」+ ALL_PLAN 行 + 门禁 + push + CI。

## 证据

- **复检脚本**：46 条断言全 PASS（见 AC-01）；每个 EC 的定向套件在同一脚本内以子进程真跑，
  退出码非 0 即记 FAIL（`tests/domain` / `tests/adapters/sqlite` / `tests/api` / `tests/e2e` /
  `tests/application` / `tests/postgres` 共 15 个文件）。
- **CI 台账**：`#133`（建档，`7c0d9f2`）= `collector-quality` 失败（测试墙钟依赖，非代码缺陷）
  ⇒ 同 cycle 修复提交 `5607992` 的 `#134` 全绿；`#134`…`#147` **每个 run 六个 job 全 success**；
  `#137`（`ffa272c`）此前只在 cycle 3 语境里出现、未进 GOAL 台账 ⇒ 本轮如实补记。
- **门禁**：治理 validator 绿；本地 m0 全绿（23 项，结果见「状态历史」）。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 9 = 收口复检，driver=client-goal / owner=root-agent）；
  `status: IN_PROGRESS`。
- 2026-09-17 收口：复检 46 条断言全 PASS、CI 台账 16 run 逐 job 复核完成；GOAL 写入
  「终止与收口」并置 `status=ACHIEVED`；`status: DONE`。

## 影响报告

- **Domain / API / schema / 持久化**：无变化（本 PLAN 只做证据复核与登记）。
- **安全 / 凭据**：无变更；把 EC-07 的未决项（依赖 advisory 未署名、hook 侧 enobufs、
  未跟踪明文 token）原样写进「终止与收口」，不在收口时隐藏缺口。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无（未新增依赖；pin 未变）。
- **下一项任务**：无（本 GOAL 收口）；后继入口见「终止与收口」的长程项表。
