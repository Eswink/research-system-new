---
id: RECHECK-20261018-508
slug: goal-082-ec01-prior-knowledge
title: GOAL-082 cycle 1 复检 — 前序知识进立题会话
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-507
parent_goal: GOAL-20261018-082
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261018-508 — GOAL-082 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **有前序记忆 ⇒ 在提示词里** | **PASS** | `test_prior_knowledge_in_prompt.py::test_prior_memory_reaches_the_prompt`：`memory_id` + 正文 + `provenance` 逐条在场 |
| AC-2 | **没有 ⇒ 没有那一段** | **PASS** | 同文件 `test_no_prior_memory_means_no_section`：空视图渲染成空串、`compose_prompt` 逐字返回 purpose；e2e 空库按压 `test_press_without_prior_memory_the_plan_sees_no_section` 在**真实 run 路径**上复述（3 passed） |
| AC-3 | **只收跨 run 档位** | **PASS** | `test_only_cross_run_tiers_are_read`：`RUN` / `SESSION` 在库但不进提示词；e2e `test_a_run_tier_memory_does_not_satisfy_the_prompt` |
| AC-4 | **有界 + 截断可见** | **PASS** | `test_entries_are_clipped_and_the_clip_is_visible`（`len(shown) == DEFAULT_MAX_CHARS` + `[truncated]`）；`test_item_limit_is_named`（前 N 条 + 确定性顺序） |
| AC-5 | **上限同源** | **PASS** | `test_the_limits_are_the_same_constants_as_the_retrieval_context`：`inspect.signature` 的默认值与 `retrieval_context.DEFAULT_MAX_*` **是同一对象**（`is` 判 —— 新造同值常量会让弱判据仍绿） |
| AC-6 | **时效与读面同源** | **PASS** | `test_expired_memory_is_excluded_and_review_due_is_marked`（`expires_at` 过 ⇒ 排除；`review_after` 过 ⇒ 收但 `[review-due]`）；e2e 明写「读面仍列、提示词排除」的口径差异 |
| AC-7 | **提示词那段 == 读面，逐条逐字** | **PASS** | e2e `test_the_prompt_section_matches_the_project_memory_read_face`：id / tier / provenance / 正文（未截断逐字、截断为前缀）三项逐条比对 |
| AC-8 | **反证：改一条记忆 ⇒ 判据红** | **PASS** | e2e `test_press_changing_a_memory_breaks_the_match`：新增一条 ⇒ 新提示词含它、旧段落不含、读面同步 —— 证明判的是同一份事实 |
| AC-9 | **两段并列（不互相替代）** | **PASS** | `test_both_sections_coexist_in_the_prompt`：两标题都在，且顺序为**先前序、后检索** |
| AC-10 | **装配没接 ⇒ 点名** | **PASS** | `test_no_memory_store_wired_is_named_not_silent`（`no memory store` 理由，与「没有记忆」分开） |
| AC-11 | **完整 run 路径上生效** | **PASS** | e2e `test_the_second_run_sees_the_first_runs_knowledge`：run `SUCCEEDED`，立题会话 spec 上 `prior_knowledge_prompt` 带 `mem-prior-lesson` + `run:round-1:claim:result` |
| AC-12 | **零回归** | **PASS** | application + architecture + integration **1408 passed, 1 skipped**；受影响 e2e **24 passed**；`tests/contracts` + `tests/loaders` **563 passed, 72 skipped** |
| AC-13 | **live 模块登记** | **PASS** | `test_live_switch_is_single_source.py` **14 passed**（`LIVE_MODULES` + `LITERAL_MENTIONS` 两处同轮登记） |
| AC-14 | **EC-04（真实模型引用前序知识）** | **未达成**（如实登记 + 点名阻塞点） | 三次真实 run：两段提示词都在场（302 + 595 字符，`contracts_with_prompts` 三会话为真），但计划正文 `memory_id` **零命中**；模型**采纳了内容**（run 2 的 `duplicate_pairs: 30` 来自那条 lesson）却不做标识引用。归档 `evidence/GOAL-20261018-082-ec04-evidence.txt` |

## 警告（如实登记）

- **`W-1`**：**EC-04 未达成** —— 按 GOAL 的降级梯记**未达成** + 点名阻塞点，**不**伪造。
- **`W-2`**：**判据第一版考了模型没被要求做的事**。首轮 live 失败后核查合约 purpose，
  发现它**只**要求引用「检索标识」，从未要求引用前序知识 ⇒ 我先补了 purpose 措辞
  （**前提**，不是放宽），再重跑两次 —— 仍不引用。这条要留档：**live 判据失败时先查
  「指令里有没有这件事」，再判「模型没做到」**。
- **`W-3`**：`prior_knowledge` 的 `now` 由组合根闭包在**每次求值**时取（装配器本身是纯函数）——
  因此**同一 run 的不同任务**看到的时效判定可能差几毫秒。这是有意的（时钟只在最外层读），
  但意味着「同一 run 内逐条时间戳完全一致」不是本设计的目标。
- **`W-4`**：`RUN` → `PROJECT` 的提升策略**不在**本轮：本轮只保证**已存在**的跨 run 记忆可读。
  谁来把 run 结论提升到项目档，是下一轮的事（GOAL `W-4`）。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- EC-04（阻塞）；EC-05 自举收口。

## 结论

**PASS_WITH_WARNINGS**。EC-01 / EC-02 / EC-03 各有判据且全绿（含读面同源与两条反证）；
**EC-04 未达成** —— 三次真实 run 上产品路径把前序知识送到了立题会话（提示词两段都在场、
与读面逐字对得上），但**模型不按 `memory_id` 引用**；按 GOAL 的降级梯如实记未达成并点名阻塞点。

`W-2` 是本轮最有价值的一条：**live 判据失败时先查「指令里有没有这件事」** —— 首轮我考的
行为在合约 purpose 里根本不存在；补上措辞后仍然不引用，才把它归为模型侧行为。
