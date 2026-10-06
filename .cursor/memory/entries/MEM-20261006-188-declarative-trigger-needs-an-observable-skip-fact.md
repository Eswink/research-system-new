---
id: MEM-20261006-188
title: "声明式触发面：判定只能看**声明字段的在场性**，且「跳过」必须是可观测事实（跳过 ≠ 静默降级，也 ≠ 失败）"
status: ACTIVE
created_at: 2026-10-06
updated_at: 2026-10-06
scope: repository
confidence: 0.93
review_after: 2027-04-06
source_plans:
  - .cursor/plans/tasks/PLAN-20261006-297-goal-031-ec03-two-round-derived-research-loop.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261006-297-goal-031-ec03-two-round-derived-research-loop.md
supersedes: []
tags: [declarative-trigger, run-chain, observable-fact, skip-not-silent, goal-031, plan-297]
---

## 做了什么

GOAL-031 EC-03 要给运行链补一个**声明式触发面**（「第二轮按第一轮的结果决定跑不跑」），
在既有 `RunChainCall` 上加三个字段：`requires_previous_ids`（触发条件）、`phase_id`（过滤
细化）、`artifact_from_previous`（从读面结果里**按声明后缀**选中制品）。三条实测教训：

1. **「跳过」必须是可观测事实**，且要走**既有读面**（这里 = `run.completed` 的 `skipped`
   载荷；事件词表 38 条不动、不新增事件类型）。跳过**不是失败**（run 照常 `SUCCEEDED`）、
   **也不是静默降级**（理由逐字点名工具 + 字段 + 触发形态）。跳过若只写在 skim 的日志里，
   「不触发」这条臂就无判据可依。
2. **判定只能看声明字段的在场性**：「未触发」的合法形态 = 路径在场但值为**空列表**；
   **路径缺失**（点分路径取不到）必须**点名失败**而不是被读成「未触发」——
   它是**声明坏掉**（写错路径 / 第二轮输入与第一轮结果脱钩）⇒ 这正好构成 EC-03(d)① 的
   反证臂：把 `ids_from_previous` 改成 `content.no_such_field` ⇒ run `FAILED` 且判词
   含 `carries no 'content.no_such_field'`。
3. **过滤必须细到 phase 级**：既有过滤只按 **provider**（`call.provider_id in
   spec.run_chain_tool_ids`）⇒ 一次 run 里两个 phase 声明**同一 provider 的不同调用**时，
   两个 phase 都会执行**全部**调用（第一轮 phase 会把第二轮的调用抢先跑掉，跳过判定落在
   错误的 phase 上）。加 `phase_id`（缺省 `None` ⇒ 沿用 provider 级过滤，既有行为逐字节
   不变）后两轮各跑各的。

## 为什么这样做

「声明式派生」的价值在于**判断依据是数据**（声明字段），不是代码里的「如果就」——
操作系统承接声明，不承接业务。任何把判定挪进应用层 if/else 的写法都会让协议声明与
实际行为脱钩（协议说一件事、代码做另一件事）。

同时，「跳过」这个新状态**天然容易被写成静默**（`continue` 就完事）——那样「不触发」臂
在 run 面上与「根本没这条声明」不可区分。所以跳过必须带**理由**流到读面，
且理由要能回答「哪条工具因哪个字段而没跑」。

## 怎么做与复现

- 新增「按条件执行」功能时：**条件面 = 声明字段**（判定读字段在场性 / 相等性），
  **结果面 = 可观测事实**（读面载荷 / 事件），两者缺一不可。
- 触发判定复用**同一取法**（`ids_from_previous` 的点分路径走既有 `_lookup`，不复制一份）。
- 复现（两臂 + 反证）：
  `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_research_loop_second_round_derived.py -q`
  ⇒ 13 passed（触发臂读取步 operation key 含第一轮 PMID `literature_read:39000001+39000002`；
  不触发臂 `skipped` 逐字点名；反证两向 FAILED）。
  协议 `examples/protocols/two_round_research_loop_v1.yaml`（两个 run-chain phase）。

## 适用边界

本仓所有「声明驱动执行」的面（运行链 / 会话工具 / 实验派发）；「跳过」这一形态的
**一般性**只由本协议的用例证明（未被第二个消费者证明，登记为 `W31-4` / `W-EC03-2`）。
`.skip` 相关的静态门（规模 / 类型）在应用层：新判定模块守 450 行 + 函数 50 行两道门
（实测：判定逻辑拆到 `phase_capability_triggers.py`）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261006-297-goal-031-ec03-two-round-derived-research-loop.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261006-297-goal-031-ec03-two-round-derived-research-loop.md`
- 事实：`tests/e2e/test_research_loop_second_round_derived.py`（13 passed）+ 判词归档
  `.cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt`
  （触发臂 operation key `literature_read:39000001+39000002`；不触发臂 `skipped` 逐字点名）
