---
id: PLAN-20260923-149
slug: goal-012-closeout-recheck
title: GOAL-012 收口重检：两棵树同结论 + 门到终态 + 残余与本 GOAL 的 W 列表原样保留（EC-06）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）的 EC-06：**收口重检 + 残余登记**。
    本 PLAN **只做验证与登记**：不新增功能、不改产品代码/协议/合约/测试/门禁/策略面；零出网、
    零真实调用、零凭据读取。判据 = 独立复检脚本在**当前树**与**干净 checkout** 上同结论 +
    本地 m0 **23/23**（`make validate-all` 同一条）+ 治理 `validate.py` 绿 + CI 台账到终态 +
    13 条人工面与本 GOAL 的 W 列表原样保留 + `latest_recheck` 为仓库相对路径 + frontmatter 与状态表一致。
    **若任何一条不成立 ⇒ 如实记 RED/BLOCKED，不把 GOAL 收成 ACHIEVED。**
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-150-goal-012-closeout-recheck.md
memory_entries: []
---

# PLAN-20260923-149 — GOAL-012 收口重检（EC-06）

## 目标

把 GOAL-012 的五个 EC（EC-01…EC-05 全 PASS）**独立重检一遍**，然后决定 GOAL 能否收成
`ACHIEVED`：**不采信 GOAL 的状态表与五份子复检的结论文本**，只采信
① 独立复检脚本在两棵树上的同结论、② 本机门与治理、③ CI 台账逐 run 逐 job 的终态、④ 残余登记仍在。

## 计划开始前的定案（写死）

- **D-1 独立复检脚本**：`scratch/verify_goal012_c6.py`（**只读 / 只用标准库 / 不 import 仓库代码**
  ⇒ 可用主树解释器在干净 checkout 里跑，不可能与被测代码同谋通过）。六组判据：
  A 五个 EC 的判定面（frontmatter `status` + `status_note` + **正文状态表一致**）、
  B 每个 EC 的载体件在位、C 子 PLAN 全 `DONE` 且 `latest_recheck` 是**仓库相对路径**且复检通过、
  D 残余不得消失（13 条人工面 + 本 GOAL 的 W 列表 + 建档残余）、E 只读历史不动
  （GOAL-011 的 `W-P`/`W-Q`、`PLAN-138` 仍 BLOCKED、(B) 记录仍「已否证 / 待重新设计」）、
  F 姿态不变（egress 判据在位；`.env` 里**没有** `RESEARCHOS_AGENT_RUNTIME`——只看键名，不读值）。
- **D-2 干净 checkout**：仓外 `git worktree` 到**收口提交之前的那个 tip**，用同一脚本、同一解释器
  再跑一遍 ⇒ 两棵树必须**同一结论**（逐条判词也一致）。
- **D-3 门**：本地 m0（`--profile m0 --keep-going`，CI 同形 env：三条 DSN pin + `LLM_MAIN_KEY=""`）
  **23/23**；`validate.py` 绿；`docs_consistency_check` 绿。CI 台账：cycle 5 的两个提交
  （`d5baf05` 的功能提交判红 → `0584276` 的回写修复）到终态。
- **D-4 残余**：GOAL-008/009/010/011 的 **13 条人工面** + 本 GOAL 的 **W-A/W-C** + 建档残余
  `R-M1`/`R-D1`/`R-B1`/`R-N1` **原样保留**（不得因收口消失）；`W-B` 已闭合的事实保留其表述。
- **D-5 收口形态**：EC-06 判定 + GOAL `status: ACHIEVED` + `latest_recheck`（仓库相对路径）
  + 迭代日志第 6 行 + 状态历史；`ANTHROPIC` run 腿仍记为**可选**（本 GOAL 未做真实
  live 调用是 EC-02 已覆盖的最小必要次数之外**不做重复重跑**的既定口径）。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | 两棵树同结论 | `python scratch/verify_goal012_c6.py <root>` 在当前树与干净 checkout 上 `checked`/`failures` 与逐条判词一致 | **通过**：干净 checkout（`01bd789`）`checked=70 failures=1`，唯一那条红恰是「EC-06 尚未判定」；收口记录落盘后当前树 `checked=70 failures=0` ⇒ 同判据同结论 |
| AC-2 | 五份子复检 + 收口复检在位 | 五份 `RECHECK-14x` 与收口 `RECHECK-150` 文件存在、`result` 为 PASS，且各子 PLAN 的 `latest_recheck` 指向它们 | **通过**：脚本 C 组 25 条（五份子 PLAN 全 `DONE`、`latest_recheck` 全是仓库相对路径、复检 `result: PASS`） |
| AC-3 | 门 | 本地 m0 **23/23** + `validate.py` 绿 + `docs_consistency_check` 绿 | **通过**：m0 `PASS: profile=m0; 23 deterministic checks`（`scratch/goal012-c6-m0.log`；`python/tests` 4411 passed / 19 skipped）、治理绿、`DOCS-CHECK PASS: 6 deterministic checks` |
| AC-4 | CI 台账到终态 | cycle 5 的两个提交逐 run 逐 job 结论在册（含判红那条及其修复） | **通过**：`d5baf05` = M0 red（两个 quality job，根因入册）+ CodeQL success；`0584276` = M0 六 job 全 success + CodeQL 3/3 success |
| AC-5 | 残余原样保留 | 13 条人工面 + `W-A`/`W-C` + `R-M1`/`R-D1`/`R-B1`/`R-N1` 仍在 GOAL 正文；GOAL-011 的 `W-P`/`W-Q` 与 `PLAN-138` 的 BLOCKED 未动 | **通过**：脚本 D/E 组 10 条全绿 |
| AC-6 | 收口形态 | GOAL `status: ACHIEVED`、`latest_recheck` 为仓库相对路径、frontmatter 与状态表一致 | **通过**：脚本 A/C 组；治理 `validate.py` 绿（`child_plans` 六项、`latest_recheck` 相对路径） |

## 实施清单

- [x] **WP1** 独立复检脚本 + 两棵树各跑一遍（干净 checkout 在仓外）。
- [x] **WP2** 门：m0 23/23 + `validate.py` + `docs_consistency_check`。
- [x] **WP3** 收口：EC-06 判定 + GOAL `ACHIEVED` + 迭代日志/状态历史/台账；本 PLAN + `ALL_PLAN` + `child_plans`（同一提交）。
- [x] **WP4** 复检落盘（`RECHECK-150`）+ 推送 + CI 台账尾巴。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 五个 EC 的载体与复检 | `RECHECK-141/143/145/146/148` + 各子 PLAN 的 `latest_recheck` |
| E-2 | 两棵树 | `scratch/verify_goal012_c6.py` 的两份输出（当前树 / 干净 checkout） |
| E-3 | 门 | `scratch/goal012-c6-m0.log` + 两道文档/治理检查 |
| E-4 | CI | cycle 5 两个提交的 run/job 结论（含判红与修复） |
| E-5 | 残余 | GOAL 正文的 13 条人工面 + W/R 列表 |

## 影响报告

- **Domain / API / schema**：无。
- **产品代码 / 测试 / 协议 / 合约 / 门禁**：**零改动**（本 PLAN 只做验证与登记）。
- **CI / workflow**：不改。
- **安全 / 凭据**：零出网、零凭据读取（`.env` 只查键名）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-012 收成 `ACHIEVED` 后，残余（`R-M1`/`R-D1`/`W-A`/`W-C` 等）留给下一轮或用户拍板。

## 状态历史

- 2026-09-23：derive（EC-06 收口子计划）。定案 D-1…D-5 写死。

## 收口（cycle 6）

- **复检**：`RECHECK-20260923-150` = **PASS**（两棵树同结论 + 门 + 治理 + CI 台账 + 残余保留）。
- **状态**：`DONE`；`latest_recheck` 指向该复检（仓库相对路径）。GOAL-012 ⇒ **ACHIEVED**。
- **工程记忆**：**无可复用事实**——本 PLAN 是纯验证与登记（两棵树复检脚本的形态已由
  `MEM-20260905-105-closeout-recheck-script-shape` 承载；本 cycle 唯一新教训「引用方与产物必须
  同一次提交落地」产生于 cycle 5 并已进 `MEM-20260923-114`）。**不创建伪记忆**。
- **零改动**：本 PLAN 未改任何产品代码 / 协议 / 合约 / 测试 / 门禁 / 策略面。
