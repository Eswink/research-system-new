---
id: PLAN-20261016-497
slug: goal-081-ec01-retrieval-excerpts-reach-the-prompt
title: GOAL-081 cycle 1 — 检索摘录进提示词（EC-01 / EC-02）
status: DONE
created_at: 2026-10-16
updated_at: 2026-10-16
parent_goal: GOAL-20261016-081
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-498-goal-081-ec01-retrieval-excerpts-reach-the-prompt.md
memory_entries: []
---

# PLAN-20261016-497 — GOAL-081 cycle 1

## 验收条件

- [x] 渲染器在树：`retrieval_prompt.py`（有界 / 截断可见 / 同源，**纯函数**）
- [x] `AgentSessionSpec.retrieval_prompt` 字段（缺省 `None` ⇒ 提示词**逐字**不变；fork 继承）
- [x] 会话创建点把那段拼在合约文本**之后**（先任务后来源）
- [x] 编排求值点：同一份视图既出快照又出提示词段（**同一处消费**，不各查一次）
- [x] 判据 14 例（正向 / 反证 / 上限 / 截断 / 同源 / 零回归）
- [x] e2e 两条**相反读数**（下游有那段且逐条标识在场 / 上游没有那段）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写；`ALL_PLAN` 投影

## 目标（本 cycle 的可独立验收主题）

**EC-01 / EC-02**：已进上下文的检索摘录**真的进到提示词里**，且有界、截断可见、同源。

## 实施清单

1. **WP-A**（渲染器）：`packages/application/run_orchestration/retrieval_prompt.py`。
2. **WP-B**（接线）：spec 新字段 + 会话创建点拼接 + 编排求值点取值。
3. **WP-C**（判据 + 记录）：14 例判据 + e2e 两向 + 本文件 + RECHECK + GOAL 回写。

## 影响报告

- **产品代码**：新增一个纯函数模块；`AgentSessionSpec` 新增一个**缺省 `None`** 的字段；
  `task_executor` 新增一个取值函数；`session_builder` 首条消息按字段拼接（缺省逐字不变）。
- **读面 / DTO / 路由 / 快照**：**零改动**。
- **判据面**：**只增**；既有判据一条不动（GOAL-078 的判据一字未改，只**加**两条读数）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 「立题质量因检索而不同」只判到「引用了标识」这一格（GOAL `W-2`）；
- 「看到全文」不在射程（GOAL `W-3`，§10 有界口径）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 渲染器判据 | **14 passed**（正向 / 反证 / 上限 / 截断 / 同源 / 零回归） | `uv run --frozen --no-sync python -B -m pytest tests/application/test_retrieval_prompt_renderer.py -q` |
| e2e 两向 | **7 passed**（下游有那段 + 逐条标识在场；上游没有那段） | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_retrieval_context_reaches_the_session.py -q` |
| 受影响套件 | **1184 passed, 1 skipped** | `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters/openhands tests/e2e/test_retrieval_context_reaches_the_session.py -q` |
| 规模门 | **1267 passed**（`retrieval_context_support` 承接搬出的记录器；用例文件回落到 450 行内） | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-16 | IN_PROGRESS | cycle 1 建档（渲染器 + 接线 + 两向读数）。 |
| 2026-10-16 | DONE | 渲染器与接线落地；14 例 + e2e 两向全绿；受影响套件 1184 passed。 |
